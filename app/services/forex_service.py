import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import json

from app.core.config import settings
from app.core.cache import (
    get_cached_forex_rates, 
    set_cached_forex_rates,
    get_cached_historical_forex,
    set_cached_historical_forex
)

logger = logging.getLogger(__name__)

class ForexService:
    def __init__(self):
        self.session = None
        self.supported_currencies = settings.DEFAULT_FOREX_CURRENCIES
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def _fetch_from_exchangerate_host(self, base: str, symbols: List[str] = None) -> Dict:
        """Fetch forex rates from exchangerate.host API"""
        try:
            session = await self._get_session()
            
            # Build URL
            url = f"{settings.ECB_API_URL}?base={base}"
            if symbols:
                url += f"&symbols={','.join(symbols)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": data.get("success", False),
                        "base": data.get("base", base),
                        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        "rates": data.get("rates", {})
                    }
                else:
                    logger.error(f"ExchangeRate API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching from ExchangeRate API: {e}")
            return None
    
    async def _fetch_from_yahoo_finance(self, base: str, symbols: List[str]) -> Dict:
        """Fetch forex rates from Yahoo Finance (fallback)"""
        try:
            session = await self._get_session()
            rates = {}
            
            for symbol in symbols:
                if symbol == base:
                    rates[symbol] = 1.0
                    continue
                
                # Yahoo Finance URL for currency pair
                pair = f"{base}{symbol}=X"
                url = f"{settings.YAHOO_FINANCE_BASE_URL}/{pair}"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        # Simple regex to extract price (this is a basic implementation)
                        # In production, you'd want to use a proper HTML parser
                        import re
                        price_match = re.search(r'"regularMarketPrice":\s*([\d.]+)', text)
                        if price_match:
                            rates[symbol] = float(price_match.group(1))
                        else:
                            rates[symbol] = None
                    else:
                        rates[symbol] = None
            
            return {
                "success": True,
                "base": base,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "rates": {k: v for k, v in rates.items() if v is not None}
            }
        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance: {e}")
            return None
    
    async def get_latest_rates(self, base: str, symbols: List[str] = None) -> Dict:
        """Get latest forex rates with caching"""
        try:
            # Check cache first
            cached_data = await get_cached_forex_rates(base, symbols)
            if cached_data:
                logger.info(f"Returning cached forex rates for {base}")
                return cached_data
            
            # Fetch from primary source
            logger.info(f"Fetching fresh forex rates for {base}")
            data = await self._fetch_from_exchangerate_host(base, symbols)
            
            if not data or not data.get("success"):
                # Try fallback source
                logger.info("Primary source failed, trying Yahoo Finance")
                data = await self._fetch_from_yahoo_finance(base, symbols or self.supported_currencies)
            
            if data and data.get("success"):
                # Cache the result
                await set_cached_forex_rates(base, data, symbols)
                return data
            else:
                # Return cached data even if expired, or default rates
                logger.warning("All sources failed, returning default rates")
                return {
                    "success": True,
                    "base": base,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "rates": self._get_default_rates(base, symbols)
                }
                
        except Exception as e:
            logger.error(f"Error in get_latest_rates: {e}")
            return {
                "success": False,
                "base": base,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "rates": {},
                "error": str(e)
            }
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """Convert amount from one currency to another"""
        try:
            if from_currency == to_currency:
                return {
                    "rate": 1.0,
                    "result": amount,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            
            # Get rates for the from_currency
            rates_data = await self.get_latest_rates(from_currency, [to_currency])
            
            if not rates_data.get("success"):
                raise Exception("Failed to get exchange rates")
            
            rate = rates_data["rates"].get(to_currency)
            if not rate:
                raise Exception(f"Rate not found for {to_currency}")
            
            result = amount * rate
            
            return {
                "rate": rate,
                "result": round(result, 4),
                "date": rates_data["date"]
            }
            
        except Exception as e:
            logger.error(f"Error in convert_currency: {e}")
            raise
    
    async def get_historical_rates(self, target_date: date, base: str, symbols: List[str] = None) -> Dict:
        """Get historical forex rates for a specific date"""
        try:
            date_str = target_date.strftime("%Y-%m-%d")
            
            # Check cache first
            cached_data = await get_cached_historical_forex(date_str, base, symbols)
            if cached_data:
                logger.info(f"Returning cached historical forex rates for {date_str}")
                return cached_data
            
            # Fetch historical data
            logger.info(f"Fetching historical forex rates for {date_str}")
            session = await self._get_session()
            
            url = f"https://api.exchangerate.host/{date_str}?base={base}"
            if symbols:
                url += f"&symbols={','.join(symbols)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        result = {
                            "success": True,
                            "base": data.get("base", base),
                            "date": date_str,
                            "rates": data.get("rates", {})
                        }
                        # Cache the result
                        await set_cached_historical_forex(date_str, base, result, symbols)
                        return result
                    else:
                        raise Exception("Historical data fetch failed")
                else:
                    raise Exception(f"Historical API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error in get_historical_rates: {e}")
            return {
                "success": False,
                "base": base,
                "date": target_date.strftime("%Y-%m-%d"),
                "rates": {},
                "error": str(e)
            }
    
    async def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        try:
            # Try to fetch from API first
            session = await self._get_session()
            url = "https://api.exchangerate.host/symbols"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        return list(data.get("symbols", {}).keys())
            
            # Fallback to default currencies
            return self.supported_currencies
            
        except Exception as e:
            logger.error(f"Error getting supported currencies: {e}")
            return self.supported_currencies
    
    def _get_default_rates(self, base: str, symbols: List[str] = None) -> Dict[str, float]:
        """Get default rates when API fails (for development/testing)"""
        default_rates = {
            "USD": {
                "EUR": 0.92,
                "GBP": 0.79,
                "JPY": 148.50,
                "IDR": 16200.50,
                "SGD": 1.35,
                "MYR": 4.75,
                "THB": 35.80,
                "PHP": 56.20,
                "VND": 24500.00,
                "KRW": 1330.00,
                "CNY": 7.25,
                "AUD": 1.52,
                "CAD": 1.35,
                "CHF": 0.88,
                "NZD": 1.65
            }
        }
        
        if base not in default_rates:
            return {}
        
        if symbols:
            return {symbol: default_rates[base].get(symbol, 1.0) for symbol in symbols}
        else:
            return default_rates[base]
    
    async def update_rates_cache(self):
        """Update cache with fresh rates (called by scheduler)"""
        try:
            logger.info("Updating forex rates cache")
            
            # Update for major currencies
            major_currencies = ["USD", "EUR", "GBP", "JPY"]
            target_currencies = ["EUR", "GBP", "JPY", "IDR", "SGD", "MYR", "THB"]
            
            for base in major_currencies:
                await self.get_latest_rates(base, target_currencies)
            
            logger.info("Forex rates cache updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating forex rates cache: {e}")
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close() 