import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

# Test data
FOREX_ENDPOINTS = [
    "/forex/latest",
    "/forex/convert",
    "/forex/historical",
    "/forex/list"
]

CRYPTO_ENDPOINTS = [
    "/crypto/latest",
    "/crypto/historical",
    "/crypto/marketcap",
    "/crypto/list"
]

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "LiteForexCryptoAPI" in data["message"]

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "status" in data
    assert "services" in data

@pytest.mark.asyncio
async def test_forex_latest(client):
    """Test forex latest rates endpoint"""
    response = await client.get("/forex/latest?base=USD&symbols=EUR,GBP")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["base"] == "USD"
    assert "rates" in data
    assert "EUR" in data["rates"]
    assert "GBP" in data["rates"]

@pytest.mark.asyncio
async def test_forex_convert(client):
    """Test forex conversion endpoint"""
    response = await client.get("/forex/convert?amount=100&from=USD&to=EUR")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["amount"] == 100
    assert data["from_currency"] == "USD"
    assert data["to_currency"] == "EUR"
    assert "rate" in data
    assert "result" in data

@pytest.mark.asyncio
async def test_forex_historical(client):
    """Test forex historical rates endpoint"""
    response = await client.get("/forex/historical?date=2024-01-01&base=USD&symbols=EUR")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["base"] == "USD"
    assert data["date"] == "2024-01-01"
    assert "rates" in data

@pytest.mark.asyncio
async def test_forex_list(client):
    """Test forex list endpoint"""
    response = await client.get("/forex/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "currencies" in data
    assert "count" in data
    assert len(data["currencies"]) > 0

@pytest.mark.asyncio
async def test_crypto_latest(client):
    """Test crypto latest prices endpoint"""
    response = await client.get("/crypto/latest?symbols=BTC,ETH")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "timestamp" in data
    assert "data" in data
    assert "BTC" in data["data"]
    assert "ETH" in data["data"]

@pytest.mark.asyncio
async def test_crypto_historical(client):
    """Test crypto historical prices endpoint"""
    response = await client.get("/crypto/historical?date=2024-01-01&symbols=BTC")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["date"] == "2024-01-01"
    assert "data" in data

@pytest.mark.asyncio
async def test_crypto_marketcap(client):
    """Test crypto market cap endpoint"""
    response = await client.get("/crypto/marketcap?symbols=BTC,ETH")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "timestamp" in data
    assert "data" in data

@pytest.mark.asyncio
async def test_crypto_list(client):
    """Test crypto list endpoint"""
    response = await client.get("/crypto/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "cryptocurrencies" in data
    assert "count" in data
    assert len(data["cryptocurrencies"]) > 0

@pytest.mark.asyncio
async def test_rate_limiting(client):
    """Test rate limiting"""
    # Make multiple requests quickly
    responses = []
    for _ in range(5):
        response = await client.get("/forex/latest")
        responses.append(response)
    
    # All should succeed (rate limit is per minute)
    for response in responses:
        assert response.status_code in [200, 429]

@pytest.mark.asyncio
async def test_invalid_forex_convert(client):
    """Test invalid forex conversion"""
    response = await client.get("/forex/convert?amount=-100&from=USD&to=EUR")
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_invalid_date_format(client):
    """Test invalid date format"""
    response = await client.get("/forex/historical?date=invalid-date&base=USD")
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_response_time(client):
    """Test API response time"""
    import time
    start_time = time.time()
    response = await client.get("/forex/latest")
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should respond within 1 second

@pytest.mark.asyncio
async def test_cors_headers(client):
    """Test CORS headers"""
    response = await client.get("/forex/latest")
    assert response.status_code == 200
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers

@pytest.mark.asyncio
async def test_process_time_header(client):
    """Test process time header"""
    response = await client.get("/forex/latest")
    assert response.status_code == 200
    assert "x-process-time" in response.headers

if __name__ == "__main__":
    pytest.main([__file__]) 