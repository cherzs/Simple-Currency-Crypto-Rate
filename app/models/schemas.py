from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, date

# ==================== BASE MODELS ====================

class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    message: str
    timestamp: Optional[str] = None

# ==================== FOREX MODELS ====================

class ForexLatestResponse(BaseModel):
    success: bool = True
    base: str
    date: str
    timestamp: int
    rates: Dict[str, float]

class ForexConvertResponse(BaseModel):
    success: bool = True
    amount: float
    from_currency: str = Field(..., alias="from")
    to_currency: str = Field(..., alias="to")
    rate: float
    result: float
    date: str

class ForexHistoricalResponse(BaseModel):
    success: bool = True
    base: str
    date: str
    rates: Dict[str, float]

class ForexListResponse(BaseModel):
    success: bool = True
    currencies: List[str]
    count: int

# ==================== CRYPTO MODELS ====================

class CryptoPriceData(BaseModel):
    price: float
    change_24h: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    circulating_supply: Optional[float] = None

class CryptoLatestResponse(BaseModel):
    success: bool = True
    timestamp: int
    data: Dict[str, CryptoPriceData]

class CryptoHistoricalResponse(BaseModel):
    success: bool = True
    date: str
    data: Dict[str, CryptoPriceData]

class CryptoMarketCapResponse(BaseModel):
    success: bool = True
    timestamp: int
    data: Dict[str, CryptoPriceData]

class CryptoListResponse(BaseModel):
    success: bool = True
    cryptocurrencies: List[str]
    count: int

# ==================== REQUEST MODELS ====================

class ForexLatestRequest(BaseModel):
    base: str = "USD"
    symbols: Optional[str] = None

class ForexConvertRequest(BaseModel):
    amount: float = Field(..., gt=0)
    from_currency: str = Field(..., alias="from")
    to_currency: str = Field(..., alias="to")

class ForexHistoricalRequest(BaseModel):
    date: str
    base: str = "USD"
    symbols: Optional[str] = None

class CryptoLatestRequest(BaseModel):
    symbols: Optional[str] = None

class CryptoHistoricalRequest(BaseModel):
    date: str
    symbols: Optional[str] = None

class CryptoMarketCapRequest(BaseModel):
    symbols: Optional[str] = None

# ==================== INTERNAL MODELS ====================

class CacheData(BaseModel):
    data: Any
    timestamp: datetime
    ttl: int

class RateLimitInfo(BaseModel):
    client_ip: str
    endpoint: str
    requests_count: int
    window_start: datetime
    limit: int

class APIUsage(BaseModel):
    client_ip: str
    endpoint: str
    timestamp: datetime
    response_time: float
    status_code: int
    user_agent: Optional[str] = None

# ==================== MONITORING MODELS ====================

class HealthCheckResponse(BaseModel):
    success: bool = True
    status: str
    timestamp: str
    services: Dict[str, str]

class MetricsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    top_endpoints: List[Dict[str, Any]]
    top_ips: List[Dict[str, Any]]
    period: str

# ==================== CONFIGURATION MODELS ====================

class APIConfig(BaseModel):
    title: str
    version: str
    description: str
    docs_url: str
    redoc_url: str

class RateLimitConfig(BaseModel):
    per_minute: int
    per_hour: int
    per_day: int

class CacheConfig(BaseModel):
    forex_ttl: int
    crypto_ttl: int
    redis_url: str 