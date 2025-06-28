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
    
    # Add to avoid error if there are environment variables in .env
    ENVIRONMENT: str = "development"
    RAPIDAPI_KEY: str = ""
    RAPIDAPI_HOST: str = ""
    RAILWAY_ENVIRONMENT: str = ""
    RENDER_ENVIRONMENT: str = ""
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Update Intervals (in seconds)
    FOREX_UPDATE_INTERVAL: int = 86400  # 24 hours
    CRYPTO_UPDATE_INTERVAL: int = 300   # 5 minutes
    
    # Supported Currencies (default)
    DEFAULT_FOREX_CURRENCIES: list = [
        # Major
        "USD", "EUR", "GBP", "JPY", "IDR", "SGD", "MYR", "THB", "PHP", "VND", "KRW", "CNY", "AUD", "CAD", "CHF", "NZD",
        # Emerging/Popular
        "INR", "BRL", "ZAR", "MXN", "RUB", "HKD", "SEK", "NOK", "DKK", "PLN", "HUF", "CZK", "ILS", "AED", "SAR", "TRY",
        # Tambahan
        "EGP", "PKR", "BDT", "LKR", "NGN", "UAH", "COP", "CLP", "PEN", "ARS", "KWD", "QAR", "OMR", "BHD", "MAD", "TWD", "RON", "BGN", "HRK", "ISK", "JOD", "KES", "TZS", "GHS", "DZD", "TND", "LBP", "VND", "MMK", "KHR", "LAK", "MOP", "MNT", "UZS", "AZN", "GEL", "BYN", "BAM", "MKD", "ALL", "MDL", "RSD", "XOF", "XAF", "XPF", "XCD", "XDR"
    ]

    # Supported Cryptocurrencies (default)
    DEFAULT_CRYPTO_CURRENCIES: list = [
        # Top 30+ CoinGecko IDs
        "bitcoin", "ethereum", "binancecoin", "cardano", "solana", "polkadot", "dogecoin", "avalanche-2", "polygon", "chainlink",
        "litecoin", "ripple", "usd-coin", "tether", "binance-usd", "shiba-inu", "tron", "dai", "cosmos", "uniswap",
        "ethereum-classic", "monero", "algorand", "stellar", "internet-computer", "aptos", "arbitrum", "optimism", "vechain", "filecoin",
        "aave", "the-graph", "maker", "tezos", "elrond-erd-2", "fantom", "neo", "zcash", "dash", "waves", "iota", "kusama", "pancakeswap-token",
        "gala", "frax", "curve-dao-token", "rocket-pool", "mina-protocol", "thorchain", "1inch", "convex-finance", "enjincoin", "chiliz", "basic-attention-token"
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