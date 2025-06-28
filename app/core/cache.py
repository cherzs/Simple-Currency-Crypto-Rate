import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import pickle

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory cache for development
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False
    
    async def ping(self) -> bool:
        """Ping Redis server"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

# Global cache instance
redis_client = RedisCache()

# ==================== CACHE KEYS ====================

class CacheKeys:
    """Cache key constants"""
    
    @staticmethod
    def forex_latest(base: str, symbols: str = None) -> str:
        """Forex latest rates cache key"""
        symbols_str = symbols or "default"
        return f"forex:latest:{base}:{symbols_str}"
    
    @staticmethod
    def forex_historical(date: str, base: str, symbols: str = None) -> str:
        """Forex historical rates cache key"""
        symbols_str = symbols or "default"
        return f"forex:historical:{date}:{base}:{symbols_str}"
    
    @staticmethod
    def forex_convert(from_curr: str, to_curr: str) -> str:
        """Forex conversion cache key"""
        return f"forex:convert:{from_curr}:{to_curr}"
    
    @staticmethod
    def crypto_latest(symbols: str = None) -> str:
        """Crypto latest prices cache key"""
        symbols_str = symbols or "default"
        return f"crypto:latest:{symbols_str}"
    
    @staticmethod
    def crypto_historical(date: str, symbols: str = None) -> str:
        """Crypto historical prices cache key"""
        symbols_str = symbols or "default"
        return f"crypto:historical:{date}:{symbols_str}"
    
    @staticmethod
    def crypto_marketcap(symbols: str = None) -> str:
        """Crypto market cap cache key"""
        symbols_str = symbols or "default"
        return f"crypto:marketcap:{symbols_str}"
    
    @staticmethod
    def rate_limit(client_ip: str, endpoint: str) -> str:
        """Rate limit cache key"""
        return f"ratelimit:{client_ip}:{endpoint}"
    
    @staticmethod
    def api_usage(client_ip: str) -> str:
        """API usage tracking cache key"""
        return f"usage:{client_ip}"

# ==================== CACHE UTILITIES ====================

async def get_cached_forex_rates(base: str, symbols: list = None) -> Optional[Dict]:
    """Get cached forex rates"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.forex_latest(base, symbols_str)
    return await redis_client.get(key)

async def set_cached_forex_rates(base: str, rates: Dict, symbols: list = None) -> bool:
    """Set cached forex rates"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.forex_latest(base, symbols_str)
    return await redis_client.set(key, rates, settings.FOREX_CACHE_TTL)

async def get_cached_crypto_prices(symbols: list = None) -> Optional[Dict]:
    """Get cached crypto prices"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.crypto_latest(symbols_str)
    return await redis_client.get(key)

async def set_cached_crypto_prices(prices: Dict, symbols: list = None) -> bool:
    """Set cached crypto prices"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.crypto_latest(symbols_str)
    return await redis_client.set(key, prices, settings.CRYPTO_CACHE_TTL)

async def get_cached_historical_forex(date: str, base: str, symbols: list = None) -> Optional[Dict]:
    """Get cached historical forex rates"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.forex_historical(date, base, symbols_str)
    return await redis_client.get(key)

async def set_cached_historical_forex(date: str, base: str, rates: Dict, symbols: list = None) -> bool:
    """Set cached historical forex rates"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.forex_historical(date, base, symbols_str)
    # Historical data cached longer (7 days)
    return await redis_client.set(key, rates, 7 * 24 * 3600)

async def get_cached_historical_crypto(date: str, symbols: list = None) -> Optional[Dict]:
    """Get cached historical crypto prices"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.crypto_historical(date, symbols_str)
    return await redis_client.get(key)

async def set_cached_historical_crypto(date: str, prices: Dict, symbols: list = None) -> bool:
    """Set cached historical crypto prices"""
    symbols_str = ",".join(symbols) if symbols else None
    key = CacheKeys.crypto_historical(date, symbols_str)
    # Historical crypto data cached for 30 days
    return await redis_client.set(key, prices, 30 * 24 * 3600)

async def clear_expired_cache():
    """Clear expired cache entries (called by scheduler)"""
    try:
        # Redis automatically handles TTL, but we can add custom cleanup logic here
        logger.info("Cache cleanup completed")
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")

async def get_cache_stats() -> Dict:
    """Get cache statistics"""
    try:
        if not redis_client.redis_client:
            return {"status": "not_connected"}
        
        info = await redis_client.redis_client.info()
        return {
            "status": "connected",
            "used_memory": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0)
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"status": "error", "message": str(e)} 