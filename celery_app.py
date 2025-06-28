from celery import Celery
import logging
from app.core.config import settings
from app.services.forex_service import ForexService
from app.services.crypto_service import CryptoService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "liteforex_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["celery_app"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@celery_app.task(name="update_forex_rates")
def update_forex_rates():
    """Update forex rates cache"""
    try:
        import asyncio
        
        async def _update():
            forex_service = ForexService()
            await forex_service.update_rates_cache()
            await forex_service.close()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_update())
            logger.info("Forex rates cache updated successfully")
            return {"status": "success", "message": "Forex rates updated"}
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error updating forex rates: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name="update_crypto_prices")
def update_crypto_prices():
    """Update crypto prices cache"""
    try:
        import asyncio
        
        async def _update():
            crypto_service = CryptoService()
            await crypto_service.update_prices_cache()
            await crypto_service.close()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_update())
            logger.info("Crypto prices cache updated successfully")
            return {"status": "success", "message": "Crypto prices updated"}
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error updating crypto prices: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name="cleanup_cache")
def cleanup_cache():
    """Clean up expired cache entries"""
    try:
        import asyncio
        
        async def _cleanup():
            from app.core.cache import clear_expired_cache
            await clear_expired_cache()
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_cleanup())
            logger.info("Cache cleanup completed")
            return {"status": "success", "message": "Cache cleaned"}
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error cleaning cache: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task(name="health_check")
def health_check():
    """Perform health check of all services"""
    try:
        import asyncio
        
        async def _health_check():
            from app.core.cache import redis_client
            from app.services.forex_service import ForexService
            from app.services.crypto_service import CryptoService
            
            results = {
                "redis": False,
                "forex_service": False,
                "crypto_service": False
            }
            
            # Check Redis
            try:
                results["redis"] = await redis_client.ping()
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
            
            # Check Forex Service
            try:
                forex_service = ForexService()
                test_data = await forex_service.get_latest_rates("USD", ["EUR"])
                results["forex_service"] = test_data.get("success", False)
                await forex_service.close()
            except Exception as e:
                logger.error(f"Forex service health check failed: {e}")
            
            # Check Crypto Service
            try:
                crypto_service = CryptoService()
                test_data = await crypto_service.get_latest_prices(["BTC"])
                results["crypto_service"] = bool(test_data)
                await crypto_service.close()
            except Exception as e:
                logger.error(f"Crypto service health check failed: {e}")
            
            return results
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(_health_check())
            logger.info(f"Health check results: {results}")
            return {"status": "success", "results": results}
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {"status": "error", "message": str(e)}

# Schedule configuration
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    
    # Update forex rates every 24 hours
    sender.add_periodic_task(
        settings.FOREX_UPDATE_INTERVAL,
        update_forex_rates.s(),
        name="update-forex-rates-daily"
    )
    
    # Update crypto prices every 5 minutes
    sender.add_periodic_task(
        settings.CRYPTO_UPDATE_INTERVAL,
        update_crypto_prices.s(),
        name="update-crypto-prices-frequently"
    )
    
    # Cleanup cache every hour
    sender.add_periodic_task(
        3600,  # 1 hour
        cleanup_cache.s(),
        name="cleanup-cache-hourly"
    )
    
    # Health check every 30 minutes
    sender.add_periodic_task(
        1800,  # 30 minutes
        health_check.s(),
        name="health-check-periodic"
    )

if __name__ == "__main__":
    celery_app.start() 