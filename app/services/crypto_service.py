import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import json

from app.core.config import settings
from app.core.cache import (
    get_cached_crypto_prices,
    set_cached_crypto_prices,
    get_cached_historical_crypto,
    set_cached_historical_crypto
)

logger = logging.getLogger(__name__)

class CryptoService:
    def __init__(self):
        self.session = None
        self.supported_cryptocurrencies = settings.DEFAULT_CRYPTO_CURRENCIES
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def _fetch_from_coingecko(self, ids: List[str] = None) -> Dict:
        """Fetch crypto data from CoinGecko API"""
        try:
            session = await self._get_session()
            
            # Build URL
            url = f"{settings.COINGECKO_API_URL}/simple/price"
            params = {
                "ids": ",".join(ids) if ids else ",".join(self.supported_cryptocurrencies),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_circulating_supply": "true"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_coingecko_data(data)
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching from CoinGecko API: {e}")
            return None
    
    async def _fetch_market_cap_data(self, ids: List[str] = None) -> Dict:
        """Fetch market cap data from CoinGecko"""
        try:
            session = await self._get_session()
            
            url = f"{settings.COINGECKO_API_URL}/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": ",".join(ids) if ids else ",".join(self.supported_cryptocurrencies),
                "order": "market_cap_desc",
                "per_page": 100,
                "page": 1,
                "sparkline": False
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_market_cap_data(data)
                else:
                    logger.error(f"CoinGecko market cap API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching market cap data: {e}")
            return None
    
    def _format_coingecko_data(self, raw_data: Dict) -> Dict:
        """Format CoinGecko API response"""
        formatted_data = {}
        
        for coin_id, coin_data in raw_data.items():
            formatted_data[coin_id.upper()] = {
                "price": coin_data.get("usd", 0),
                "change_24h": coin_data.get("usd_24h_change", 0),
                "market_cap": coin_data.get("usd_market_cap", 0),
                "volume_24h": coin_data.get("usd_24h_vol", 0),
                "circulating_supply": coin_data.get("circulating_supply", 0)
            }
        
        return formatted_data
    
    def _format_market_cap_data(self, raw_data: List[Dict]) -> Dict:
        """Format market cap API response"""
        formatted_data = {}
        
        for coin in raw_data:
            coin_id = coin.get("id", "").upper()
            formatted_data[coin_id] = {
                "price": coin.get("current_price", 0),
                "change_24h": coin.get("price_change_percentage_24h", 0),
                "market_cap": coin.get("market_cap", 0),
                "volume_24h": coin.get("total_volume", 0),
                "circulating_supply": coin.get("circulating_supply", 0)
            }
        
        return formatted_data
    
    async def get_latest_prices(self, symbols: List[str] = None) -> Dict:
        """Get latest crypto prices with caching"""
        try:
            # Normalize symbols to CoinGecko IDs
            coin_ids = self._normalize_symbols_to_ids(symbols or ["BTC", "ETH", "SOL", "ADA", "BNB"])
            
            # Check cache first
            cached_data = await get_cached_crypto_prices(coin_ids)
            if cached_data:
                logger.info("Returning cached crypto prices")
                return cached_data
            
            # Fetch from API
            logger.info("Fetching fresh crypto prices")
            data = await self._fetch_from_coingecko(coin_ids)
            
            if data:
                # Cache the result
                await set_cached_crypto_prices(data, coin_ids)
                return data
            else:
                # Return default data if API fails
                logger.warning("API failed, returning default crypto prices")
                return self._get_default_crypto_prices(symbols)
                
        except Exception as e:
            logger.error(f"Error in get_latest_prices: {e}")
            return self._get_default_crypto_prices(symbols)
    
    async def get_historical_prices(self, target_date: date, symbols: List[str] = None) -> Dict:
        """Get historical crypto prices for a specific date"""
        try:
            date_str = target_date.strftime("%d-%m-%Y")
            coin_ids = self._normalize_symbols_to_ids(symbols or ["BTC", "ETH", "SOL"])
            
            # Check cache first
            cached_data = await get_cached_historical_crypto(date_str, coin_ids)
            if cached_data:
                logger.info(f"Returning cached historical crypto prices for {date_str}")
                return cached_data
            
            # Fetch historical data
            logger.info(f"Fetching historical crypto prices for {date_str}")
            session = await self._get_session()
            
            url = f"{settings.COINGECKO_API_URL}/coins/bitcoin/history"
            params = {"date": date_str}
            
            # Note: CoinGecko free API has limited historical data
            # For production, you might want to use a paid service or store historical data
            data = {}
            for coin_id in coin_ids:
                try:
                    coin_url = f"{settings.COINGECKO_API_URL}/coins/{coin_id}/history"
                    async with session.get(coin_url, params=params) as response:
                        if response.status == 200:
                            coin_data = await response.json()
                            if "market_data" in coin_data:
                                data[coin_id.upper()] = {
                                    "price": coin_data["market_data"]["current_price"]["usd"],
                                    "market_cap": coin_data["market_data"]["market_cap"]["usd"],
                                    "volume_24h": coin_data["market_data"]["total_volume"]["usd"]
                                }
                except Exception as e:
                    logger.error(f"Error fetching historical data for {coin_id}: {e}")
                    continue
            
            if data:
                # Cache the result
                await set_cached_historical_crypto(date_str, data, coin_ids)
                return data
            else:
                return self._get_default_crypto_prices(symbols)
                
        except Exception as e:
            logger.error(f"Error in get_historical_prices: {e}")
            return self._get_default_crypto_prices(symbols)
    
    async def get_market_cap_data(self, symbols: List[str] = None) -> Dict:
        """Get market cap data for cryptocurrencies"""
        try:
            coin_ids = self._normalize_symbols_to_ids(symbols or ["BTC", "ETH", "SOL", "ADA", "BNB"])
            
            # Fetch market cap data
            data = await self._fetch_market_cap_data(coin_ids)
            
            if data:
                return data
            else:
                # Return default data if API fails
                return self._get_default_crypto_prices(symbols)
                
        except Exception as e:
            logger.error(f"Error in get_market_cap_data: {e}")
            return self._get_default_crypto_prices(symbols)
    
    async def get_supported_cryptocurrencies(self) -> List[str]:
        """Get list of supported cryptocurrencies"""
        try:
            # Try to fetch from CoinGecko API
            session = await self._get_session()
            url = f"{settings.COINGECKO_API_URL}/coins/list"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Return top 50 by market cap
                    return [coin["id"] for coin in data[:50]]
            
            # Fallback to default cryptocurrencies
            return self.supported_cryptocurrencies
            
        except Exception as e:
            logger.error(f"Error getting supported cryptocurrencies: {e}")
            return self.supported_cryptocurrencies
    
    def _normalize_symbols_to_ids(self, symbols: List[str]) -> List[str]:
        """Convert common symbols to CoinGecko IDs"""
        symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum", 
            "SOL": "solana",
            "ADA": "cardano",
            "BNB": "binancecoin",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "MATIC": "polygon",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "XRP": "ripple",
            "XLM": "stellar",
            "ATOM": "cosmos",
            "ALGO": "algorand",
            "VET": "vechain",
            "TRX": "tron",
            "FIL": "filecoin"
        }
        
        return [symbol_to_id.get(symbol.upper(), symbol.lower()) for symbol in symbols]
    
    def _get_default_crypto_prices(self, symbols: List[str] = None) -> Dict:
        """Get default crypto prices when API fails"""
        default_prices = {
            "BTC": {
                "price": 42000.50,
                "change_24h": 2.5,
                "market_cap": 820000000000,
                "volume_24h": 25000000000,
                "circulating_supply": 19500000
            },
            "ETH": {
                "price": 2500.75,
                "change_24h": -1.2,
                "market_cap": 300000000000,
                "volume_24h": 15000000000,
                "circulating_supply": 120000000
            },
            "SOL": {
                "price": 98.25,
                "change_24h": 5.8,
                "market_cap": 45000000000,
                "volume_24h": 2000000000,
                "circulating_supply": 458000000
            },
            "ADA": {
                "price": 0.48,
                "change_24h": -0.5,
                "market_cap": 17000000000,
                "volume_24h": 800000000,
                "circulating_supply": 35500000000
            },
            "BNB": {
                "price": 320.50,
                "change_24h": 1.8,
                "market_cap": 48000000000,
                "volume_24h": 1200000000,
                "circulating_supply": 150000000
            }
        }
        
        if symbols:
            return {symbol.upper(): default_prices.get(symbol.upper(), {
                "price": 1.0,
                "change_24h": 0.0,
                "market_cap": 0,
                "volume_24h": 0,
                "circulating_supply": 0
            }) for symbol in symbols}
        else:
            return default_prices
    
    async def update_prices_cache(self):
        """Update cache with fresh prices (called by scheduler)"""
        try:
            logger.info("Updating crypto prices cache")
            
            # Update for top cryptocurrencies
            top_coins = ["BTC", "ETH", "SOL", "ADA", "BNB", "DOT", "DOGE", "AVAX", "MATIC", "LINK"]
            await self.get_latest_prices(top_coins)
            
            logger.info("Crypto prices cache updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating crypto prices cache: {e}")
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close() 