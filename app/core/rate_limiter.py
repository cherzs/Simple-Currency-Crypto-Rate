import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.core.cache import redis_client, CacheKeys

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.limits = {
            "per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "per_hour": settings.RATE_LIMIT_PER_HOUR,
            "per_day": settings.RATE_LIMIT_PER_DAY
        }
    
    async def is_allowed(self, client_ip: str, endpoint: str) -> bool:
        """Check if request is allowed based on rate limits"""
        try:
            # Check all rate limit windows
            for window, limit in self.limits.items():
                if not await self._check_window(client_ip, endpoint, window, limit):
                    logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint} ({window})")
                    return False
            
            # If all checks pass, increment counters
            await self._increment_counters(client_ip, endpoint)
            return True
            
        except Exception as e:
            logger.error(f"Error in rate limiter: {e}")
            # Allow request if rate limiter fails
            return True
    
    async def _check_window(self, client_ip: str, endpoint: str, window: str, limit: int) -> bool:
        """Check if request is allowed for a specific time window"""
        try:
            if not redis_client.redis_client:
                return True  # Allow if Redis is not available
            
            # Get current timestamp
            now = int(time.time())
            
            # Calculate window start time
            if window == "per_minute":
                window_start = now - (now % 60)
            elif window == "per_hour":
                window_start = now - (now % 3600)
            elif window == "per_day":
                window_start = now - (now % 86400)
            else:
                return True
            
            # Create key for this window
            key = f"{CacheKeys.rate_limit(client_ip, endpoint)}:{window}:{window_start}"
            
            # Get current count
            current_count = await redis_client.redis_client.get(key)
            count = int(current_count) if current_count else 0
            
            return count < limit
            
        except Exception as e:
            logger.error(f"Error checking rate limit window: {e}")
            return True
    
    async def _increment_counters(self, client_ip: str, endpoint: str):
        """Increment request counters for all time windows"""
        try:
            if not redis_client.redis_client:
                return
            
            now = int(time.time())
            
            # Increment for each window
            windows = [
                ("per_minute", now - (now % 60), 60),
                ("per_hour", now - (now % 3600), 3600),
                ("per_day", now - (now % 86400), 86400)
            ]
            
            for window, window_start, ttl in windows:
                key = f"{CacheKeys.rate_limit(client_ip, endpoint)}:{window}:{window_start}"
                
                # Use Redis pipeline for efficiency
                pipe = redis_client.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, ttl)
                await pipe.execute()
                
        except Exception as e:
            logger.error(f"Error incrementing rate limit counters: {e}")
    
    async def get_usage_info(self, client_ip: str, endpoint: str) -> Dict:
        """Get current usage information for a client"""
        try:
            if not redis_client.redis_client:
                return {"error": "Redis not available"}
            
            now = int(time.time())
            usage = {}
            
            for window, limit in self.limits.items():
                if window == "per_minute":
                    window_start = now - (now % 60)
                    ttl = 60
                elif window == "per_hour":
                    window_start = now - (now % 3600)
                    ttl = 3600
                elif window == "per_day":
                    window_start = now - (now % 86400)
                    ttl = 86400
                
                key = f"{CacheKeys.rate_limit(client_ip, endpoint)}:{window}:{window_start}"
                current_count = await redis_client.redis_client.get(key)
                count = int(current_count) if current_count else 0
                
                usage[window] = {
                    "current": count,
                    "limit": limit,
                    "remaining": max(0, limit - count),
                    "reset_time": window_start + ttl
                }
            
            return usage
            
        except Exception as e:
            logger.error(f"Error getting usage info: {e}")
            return {"error": str(e)}
    
    async def reset_limits(self, client_ip: str, endpoint: str = None):
        """Reset rate limits for a client (admin function)"""
        try:
            if not redis_client.redis_client:
                return False
            
            if endpoint:
                # Reset specific endpoint
                pattern = f"{CacheKeys.rate_limit(client_ip, endpoint)}:*"
            else:
                # Reset all endpoints for client
                pattern = f"{CacheKeys.rate_limit(client_ip, '*')}"
            
            # Find and delete matching keys
            keys = await redis_client.redis_client.keys(pattern)
            if keys:
                await redis_client.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for {client_ip} on {endpoint or 'all endpoints'}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resetting rate limits: {e}")
            return False
    
    async def get_global_stats(self) -> Dict:
        """Get global rate limiting statistics"""
        try:
            if not redis_client.redis_client:
                return {"error": "Redis not available"}
            
            # Get all rate limit keys
            pattern = "ratelimit:*"
            keys = await redis_client.redis_client.keys(pattern)
            
            total_requests = 0
            active_clients = set()
            blocked_requests = 0
            
            for key in keys:
                count = await redis_client.redis_client.get(key)
                if count:
                    total_requests += int(count)
                    # Extract client IP from key
                    parts = key.split(":")
                    if len(parts) >= 2:
                        active_clients.add(parts[1])
            
            return {
                "total_requests": total_requests,
                "active_clients": len(active_clients),
                "rate_limit_keys": len(keys),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {"error": str(e)}

# Global rate limiter instance
rate_limiter = RateLimiter()

# ==================== RATE LIMIT MIDDLEWARE HELPERS ====================

async def check_rate_limit(client_ip: str, endpoint: str) -> Dict:
    """Check rate limit and return detailed information"""
    is_allowed = await rate_limiter.is_allowed(client_ip, endpoint)
    usage_info = await rate_limiter.get_usage_info(client_ip, endpoint)
    
    return {
        "allowed": is_allowed,
        "usage": usage_info,
        "limits": rate_limiter.limits
    }

async def get_client_usage(client_ip: str) -> Dict:
    """Get usage information for all endpoints for a client"""
    try:
        if not redis_client.redis_client:
            return {"error": "Redis not available"}
        
        # Get all keys for this client
        pattern = f"ratelimit:{client_ip}:*"
        keys = await redis_client.redis_client.keys(pattern)
        
        usage = {}
        for key in keys:
            # Extract endpoint from key
            parts = key.split(":")
            if len(parts) >= 3:
                endpoint = parts[2]
                count = await redis_client.redis_client.get(key)
                if count:
                    usage[endpoint] = int(count)
        
        return {
            "client_ip": client_ip,
            "endpoints": usage,
            "total_requests": sum(usage.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting client usage: {e}")
        return {"error": str(e)} 