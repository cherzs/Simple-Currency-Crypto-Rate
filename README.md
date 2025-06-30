# 🚀 LiteForexCryptoAPI - Simple Currency & Crypto Rate API

> *"Simple, Fast, Affordable Currency & Crypto Rates API for Developers & Indie Projects."*

## 📋 **BLUEPRINT OVERVIEW**

**Name:** `LiteForexCryptoAPI`  
**Tagline:** Simple, Fast, Affordable Currency & Crypto Rates API for Developers & Indie Projects  
**Target Market:** Developers, Indie Hackers, E-commerce plugins, Crypto trackers  

---

## 🎯 **1. VALUE PROPOSITION**

### **Masalah yang Diselesaikan:**
- Developer butuh kurs **real-time** tapi API besar (Fixer.io, OpenExchangeRates, CoinAPI) mahal
- Plugin e-commerce, invoice, app crypto tracker butuh **kurs USD → IDR**, USD → Crypto
- Founder butuh **API simpel, request cepat, dan murah** untuk freelance/side project

### **Solusi:**
- API lightweight dengan response time < 100ms
- Pricing tier mulai $0.10/bulan (filter user iseng)
- Data source gratis + caching untuk optimasi biaya
- Endpoint sederhana, dokumentasi jelas

---

## 🔧 **2. FUNGSI UTAMA**

### **Forex Endpoints:**
- `GET /forex/latest` - Kurs terbaru (USD, EUR, GBP, JPY, IDR, dll)
- `GET /forex/historical` - Kurs historis by date range  
- `GET /forex/convert` - Konversi amount dari base ke target currency
- `GET /forex/list` - List simbol yang didukung

### **Crypto Endpoints:**
- `GET /crypto/latest` - Harga crypto top (BTC, ETH, SOL, ADA, BNB)
- `GET /crypto/historical` - Harga historis per tanggal
- `GET /crypto/marketcap` - Info market cap top coin
- `GET /crypto/list` - List koin yang didukung

---

## 📊 **3. DATA SOURCE STRATEGY**

### **Forex Data:**
- **Primary:** European Central Bank (ECB) - free daily exchange rates
- **Backup:** Yahoo Finance scraping (legal, public data)
- **Update Frequency:** 1x per hari (16:00 CET)
- **Cache Strategy:** Redis TTL 24 hours

### **Crypto Data:**
- **Primary:** CoinGecko API (free tier, no API key required)
- **Backup:** CoinMarketCap free endpoints
- **Update Frequency:** Every 5 minutes for top 20 coins
- **Cache Strategy:** Redis TTL 5 minutes

---

## 🏗️ **4. INFRASTRUKTUR TEKNIS**

### **Tech Stack:**
- **Backend:** FastAPI (Python) - high performance, auto-docs
- **Database:** Redis (cache) + SQLite (logs)
- **Scheduler:** Celery + Redis broker
- **Hosting:** Railway/Render (free tier friendly)
- **Monitoring:** Sentry (error tracking)

### **Architecture Flow:**
1. Celery scheduler fetch data → Redis cache
2. API endpoints serve from Redis → < 100ms response
3. Rate limiting via FastAPI middleware
4. Request logging for analytics

---

## 📡 **5. ENDPOINT SPECIFICATIONS**

### **Forex Endpoints:**

#### `GET /forex/latest`
```http
GET /forex/latest?base=USD&symbols=IDR,EUR,GBP
```

**Response:**
```json
{
  "success": true,
  "base": "USD",
  "date": "2025-01-28",
  "timestamp": 1706457600,
  "rates": {
    "IDR": 16200.50,
    "EUR": 0.9234,
    "GBP": 0.7891
  }
}
```

#### `GET /forex/convert`
```http
GET /forex/convert?amount=100&from=USD&to=IDR
```

**Response:**
```json
{
  "success": true,
  "amount": 100,
  "from": "USD",
  "to": "IDR",
  "rate": 16200.50,
  "result": 1620050,
  "date": "2025-01-28"
}
```

### **Crypto Endpoints:**

#### `GET /crypto/latest`
```http
GET /crypto/latest?symbols=BTC,ETH,SOL
```

**Response:**
```json
{
  "success": true,
  "timestamp": 1706457600,
  "data": {
    "BTC": {
      "price": 42000.50,
      "change_24h": 2.5,
      "market_cap": 820000000000
    },
    "ETH": {
      "price": 2500.75,
      "change_24h": -1.2,
      "market_cap": 300000000000
    }
  }
}
```

--
