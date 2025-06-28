from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from typing import List, Optional
from datetime import datetime, date
import json

from app.core.config import settings
from app.core.rate_limiter import RateLimiter
from app.services.forex_service import ForexService
from app.services.crypto_service import CryptoService
from app.models.schemas import (
    ForexLatestResponse,
    ForexConvertResponse,
    ForexHistoricalResponse,
    CryptoLatestResponse,
    CryptoHistoricalResponse,
    CryptoMarketCapResponse,
    ErrorResponse
)
from app.core.cache import redis_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiteForexCryptoAPI",
    description="Simple, Fast, Affordable Currency & Crypto Rates API for Developers & Indie Projects",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Initialize services
forex_service = ForexService()
crypto_service = CryptoService()
rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = request.client.host
    endpoint = request.url.path
    
    if not rate_limiter.is_allowed(client_ip, endpoint):
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later."
            }
        )
    
    response = await call_next(request)
    return response

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "Something went wrong. Please try again later."
        }
    )

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info"""
    return {
        "success": True,
        "message": "Welcome to LiteForexCryptoAPI",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "forex": {
                "latest": "/forex/latest",
                "convert": "/forex/convert", 
                "historical": "/forex/historical",
                "list": "/forex/list"
            },
            "crypto": {
                "latest": "/crypto/latest",
                "historical": "/crypto/historical",
                "marketcap": "/crypto/marketcap",
                "list": "/crypto/list"
            }
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"
    
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "healthy",
            "redis": redis_status
        }
    }

# ==================== FOREX ENDPOINTS ====================

@app.get(
    "/forex/latest",
    response_model=ForexLatestResponse,
    tags=["Forex"],
    summary="Get latest forex rates",
    description="Get the latest exchange rates for specified currencies"
)
async def get_forex_latest(
    base: str = "USD",
    symbols: Optional[str] = None
):
    """Get latest forex rates"""
    try:
        # Parse symbols
        symbol_list = symbols.split(",") if symbols else ["EUR", "GBP", "JPY", "IDR"]
        
        # Get rates from service
        rates_data = await forex_service.get_latest_rates(base, symbol_list)
        
        return ForexLatestResponse(
            success=True,
            base=base,
            date=rates_data["date"],
            timestamp=int(datetime.now().timestamp()),
            rates=rates_data["rates"]
        )
    except Exception as e:
        logger.error(f"Error in forex latest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/forex/convert",
    response_model=ForexConvertResponse,
    tags=["Forex"],
    summary="Convert currency amount",
    description="Convert a specific amount from one currency to another"
)
async def convert_forex(
    amount: float,
    from_currency: str,
    to_currency: str
):
    """Convert currency amount"""
    try:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        # Get conversion rate
        conversion_data = await forex_service.convert_currency(
            amount, from_currency, to_currency
        )
        
        return ForexConvertResponse(
            success=True,
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=conversion_data["rate"],
            result=conversion_data["result"],
            date=conversion_data["date"]
        )
    except Exception as e:
        logger.error(f"Error in forex convert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/forex/historical",
    response_model=ForexHistoricalResponse,
    tags=["Forex"],
    summary="Get historical forex rates",
    description="Get exchange rates for a specific date"
)
async def get_forex_historical(
    date_str: str,
    base: str = "USD",
    symbols: Optional[str] = None
):
    """Get historical forex rates"""
    try:
        # Parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Parse symbols
        symbol_list = symbols.split(",") if symbols else ["EUR", "GBP", "JPY", "IDR"]
        
        # Get historical rates
        rates_data = await forex_service.get_historical_rates(
            target_date, base, symbol_list
        )
        
        return ForexHistoricalResponse(
            success=True,
            base=base,
            date=date_str,
            rates=rates_data["rates"]
        )
    except Exception as e:
        logger.error(f"Error in forex historical: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forex/list", tags=["Forex"])
async def get_forex_list():
    """Get list of supported forex currencies"""
    try:
        currencies = await forex_service.get_supported_currencies()
        return {
            "success": True,
            "currencies": currencies,
            "count": len(currencies)
        }
    except Exception as e:
        logger.error(f"Error in forex list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CRYPTO ENDPOINTS ====================

@app.get(
    "/crypto/latest",
    response_model=CryptoLatestResponse,
    tags=["Crypto"],
    summary="Get latest crypto prices",
    description="Get the latest prices for specified cryptocurrencies"
)
async def get_crypto_latest(symbols: Optional[str] = None):
    """Get latest crypto prices"""
    try:
        # Parse symbols
        symbol_list = symbols.split(",") if symbols else ["BTC", "ETH", "SOL", "ADA", "BNB"]
        
        # Get crypto data
        crypto_data = await crypto_service.get_latest_prices(symbol_list)
        
        return CryptoLatestResponse(
            success=True,
            timestamp=int(datetime.now().timestamp()),
            data=crypto_data
        )
    except Exception as e:
        logger.error(f"Error in crypto latest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/crypto/historical",
    response_model=CryptoHistoricalResponse,
    tags=["Crypto"],
    summary="Get historical crypto prices",
    description="Get cryptocurrency prices for a specific date"
)
async def get_crypto_historical(
    date_str: str,
    symbols: Optional[str] = None
):
    """Get historical crypto prices"""
    try:
        # Parse date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Parse symbols
        symbol_list = symbols.split(",") if symbols else ["BTC", "ETH", "SOL"]
        
        # Get historical data
        crypto_data = await crypto_service.get_historical_prices(
            target_date, symbol_list
        )
        
        return CryptoHistoricalResponse(
            success=True,
            date=date_str,
            data=crypto_data
        )
    except Exception as e:
        logger.error(f"Error in crypto historical: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/crypto/marketcap",
    response_model=CryptoMarketCapResponse,
    tags=["Crypto"],
    summary="Get crypto market cap data",
    description="Get market capitalization data for specified cryptocurrencies"
)
async def get_crypto_marketcap(symbols: Optional[str] = None):
    """Get crypto market cap data"""
    try:
        # Parse symbols
        symbol_list = symbols.split(",") if symbols else ["BTC", "ETH", "SOL", "ADA", "BNB"]
        
        # Get market cap data
        marketcap_data = await crypto_service.get_market_cap_data(symbol_list)
        
        return CryptoMarketCapResponse(
            success=True,
            timestamp=int(datetime.now().timestamp()),
            data=marketcap_data
        )
    except Exception as e:
        logger.error(f"Error in crypto marketcap: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crypto/list", tags=["Crypto"])
async def get_crypto_list():
    """Get list of supported cryptocurrencies"""
    try:
        cryptocurrencies = await crypto_service.get_supported_cryptocurrencies()
        return {
            "success": True,
            "cryptocurrencies": cryptocurrencies,
            "count": len(cryptocurrencies)
        }
    except Exception as e:
        logger.error(f"Error in crypto list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 