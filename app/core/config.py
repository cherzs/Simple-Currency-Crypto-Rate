from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "LiteForexCryptoAPI"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Simple, Fast, Affordable Currency & Crypto Rates API"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    
    # Cache Configuration
    FOREX_CACHE_TTL: int = 86400  # 24 hours in seconds
    CRYPTO_CACHE_TTL: int = 300   # 5 minutes in seconds
    
    # Data Sources
    ECB_API_URL: str = "https://api.exchangerate.host/latest"
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    YAHOO_FINANCE_BASE_URL: str = "https://finance.yahoo.com/quote"
    
    # External API Keys (optional)
    COINMARKETCAP_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: list = ["*"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./liteforex_api.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Update Intervals (in seconds)
    FOREX_UPDATE_INTERVAL: int = 86400  # 24 hours
    CRYPTO_UPDATE_INTERVAL: int = 300   # 5 minutes
    
    # Supported Currencies (default)
    DEFAULT_FOREX_CURRENCIES: list = [
        "USD", "EUR", "GBP", "JPY", "IDR", "SGD", "MYR", "THB", 
        "PHP", "VND", "KRW", "CNY", "AUD", "CAD", "CHF", "NZD"
    ]
    
    # Supported Cryptocurrencies (default)
    DEFAULT_CRYPTO_CURRENCIES: list = [
        "bitcoin", "ethereum", "binancecoin", "cardano", "solana",
        "polkadot", "dogecoin", "avalanche-2", "polygon", "chainlink"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
elif os.getenv("ENVIRONMENT") == "development":
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG" 