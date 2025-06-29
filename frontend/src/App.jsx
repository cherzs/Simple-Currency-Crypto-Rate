import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import Chart from "./Chart";

const API_BASE = "http://localhost:8000";
const FINNHUB_WS_URL = "wss://ws.finnhub.io?token=d1g5q09r01qk4ao19rggd1g5q09r01qk4ao19rh0";

function prettyJSON(obj) {
  return JSON.stringify(obj, null, 2);
}

function Section({ title, children }) {
  return (
    <div className="card mb-4">
      <div className="card-header bg-primary text-white">{title}</div>
      <div className="card-body">{children}</div>
    </div>
  );
}

export default function App() {
  // State untuk setiap endpoint
  const [forexLatest, setForexLatest] = useState({ base: "USD", symbols: "EUR,IDR,JPY" });
  const [forexConvert, setForexConvert] = useState({ amount: 100, from: "USD", to: "IDR" });
  const [forexHistorical, setForexHistorical] = useState({ date: "2024-01-01", base: "USD", symbols: "EUR,IDR" });
  const [cryptoLatest, setCryptoLatest] = useState({ symbols: "BTC,ETH,SOL" });
  const [cryptoHistorical, setCryptoHistorical] = useState({ date: "2024-01-01", symbols: "BTC,ETH" });
  const [cryptoMarketcap, setCryptoMarketcap] = useState({ symbols: "BTC,ETH,SOL" });

  // Response & error state
  const [result, setResult] = useState({});
  const [loading, setLoading] = useState({});
  const [error, setError] = useState({});

  // Chart states
  const [cryptoHistory, setCryptoHistory] = useState([]);
  const [cryptoHistorySymbol, setCryptoHistorySymbol] = useState("BTC");
  const [cryptoHistoryDate, setCryptoHistoryDate] = useState("2024-01-01");
  const [forexHistory, setForexHistory] = useState([]);
  const [forexHistoryBase, setForexHistoryBase] = useState("USD");
  const [forexHistorySymbols, setForexHistorySymbols] = useState("IDR,EUR");
  const [forexHistoryDate, setForexHistoryDate] = useState("2024-01-01");

  // Crypto pair states
  const [cryptoBaseCurrency, setCryptoBaseCurrency] = useState("USD");
  const [cryptoTargetCurrency, setCryptoTargetCurrency] = useState("BTC");
  const [cryptoPairData, setCryptoPairData] = useState([]);

  // Realtime states
  const [isRealtimeCrypto, setIsRealtimeCrypto] = useState(false);
  const [isRealtimeForex, setIsRealtimeForex] = useState(false);
  const [realtimeCryptoData, setRealtimeCryptoData] = useState([]);
  const [realtimeForexData, setRealtimeForexData] = useState([]);
  const [realtimeInterval, setRealtimeInterval] = useState(null);

  // WebSocket states
  const [wsConnection, setWsConnection] = useState(null);
  const [wsData, setWsData] = useState([]);
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [wsError, setWsError] = useState(null);

  // Helper untuk handle request
  const handleRequest = async (key, url, params = {}) => {
    setLoading((l) => ({ ...l, [key]: true }));
    setError((e) => ({ ...e, [key]: null }));
    setResult((r) => ({ ...r, [key]: null }));
    try {
      const res = await axios.get(`${API_BASE}${url}`, { params });
      setResult((r) => ({ ...r, [key]: res.data }));
    } catch (err) {
      setError((e) => ({ ...e, [key]: err.message }));
    } finally {
      setLoading((l) => ({ ...l, [key]: false }));
    }
  };

  // Helper untuk menghapus data duplikat dan mengurutkan
  const processChartData = (newData, maxPoints = 50) => {
    // Remove duplicates based on time
    const uniqueData = newData.filter((item, index, self) => 
      index === self.findIndex(t => t.time === item.time)
    );
    
    // Sort by time ascending and keep only last maxPoints
    return uniqueData
      .sort((a, b) => a.time - b.time)
      .slice(-maxPoints);
  };

  const fetchCryptoHistory = async () => {
    try {
      const res = await axios.get(
        `${API_BASE}/crypto/historical`,
        { params: { date_str: cryptoHistoryDate, symbols: cryptoHistorySymbol } }
      );
      
      console.log("Crypto API Response:", res.data);
      
      // Convert data to chart format
      const data = [];
      const responseData = res.data.data || {};
      Object.entries(responseData).forEach(([symbol, val]) => {
        if (val && val.price) {
          data.push({ 
            time: cryptoHistoryDate, 
            value: parseFloat(val.price) || 0 
          });
        }
      });
      
      console.log("Chart data:", data);
      setCryptoHistory(data);
    } catch (err) {
      console.error("Error fetching crypto history:", err);
      setCryptoHistory([]);
    }
  };

  const fetchForexHistory = async () => {
    try {
      const res = await axios.get(
        `${API_BASE}/forex/historical`,
        { params: { date_str: forexHistoryDate, base: forexHistoryBase, symbols: forexHistorySymbols } }
      );
      
      console.log("Forex API Response:", res.data);
      
      // Convert data to chart format
      const data = [];
      const rates = res.data.rates || {};
      Object.entries(rates).forEach(([currency, rate]) => {
        if (rate && rate > 0) {
          data.push({ 
            time: forexHistoryDate, 
            value: parseFloat(rate) || 0 
          });
        }
      });
      
      console.log("Chart data:", data);
      setForexHistory(data);
    } catch (err) {
      console.error("Error fetching forex history:", err);
      setForexHistory([]);
    }
  };

  // Realtime functions
  const fetchRealtimeCrypto = async () => {
    try {
      const res = await axios.get(
        `${API_BASE}/crypto/latest`,
        { params: { symbols: cryptoHistorySymbol } }
      );
      
      const now = Math.floor(Date.now() / 1000); // Unix timestamp in seconds
      
      const responseData = res.data.data || {};
      Object.entries(responseData).forEach(([symbol, val]) => {
        if (val && val.price) {
          setRealtimeCryptoData(prev => {
            const newData = [...prev, { 
              time: now, 
              value: parseFloat(val.price) || 0 
            }];
            return processChartData(newData);
          });
        }
      });
    } catch (err) {
      console.error("Error fetching realtime crypto:", err);
    }
  };

  const fetchRealtimeForex = async () => {
    try {
      const res = await axios.get(
        `${API_BASE}/forex/latest`,
        { params: { base: forexHistoryBase, symbols: forexHistorySymbols } }
      );
      
      const now = Math.floor(Date.now() / 1000); // Unix timestamp in seconds
      
      const rates = res.data.rates || {};
      Object.entries(rates).forEach(([currency, rate]) => {
        if (rate && rate > 0) {
          setRealtimeForexData(prev => {
            const newData = [...prev, { 
              time: now, 
              value: parseFloat(rate) || 0 
            }];
            return processChartData(newData);
          });
        }
      });
    } catch (err) {
      console.error("Error fetching realtime forex:", err);
    }
  };

  const startRealtimeCrypto = () => {
    setIsRealtimeCrypto(true);
    setRealtimeCryptoData([]);
    // Fetch immediately
    fetchRealtimeCrypto();
    // Then set interval
    const interval = setInterval(fetchRealtimeCrypto, 30000); // 30 seconds
    setRealtimeInterval(interval);
  };

  const stopRealtimeCrypto = () => {
    setIsRealtimeCrypto(false);
    if (realtimeInterval) {
      clearInterval(realtimeInterval);
      setRealtimeInterval(null);
    }
  };

  const startRealtimeForex = () => {
    setIsRealtimeForex(true);
    setRealtimeForexData([]);
    
    // Try WebSocket first, fallback to polling
    if (wsStatus === "connected") {
      const forexSymbols = forexHistorySymbols.split(',');
      forexSymbols.forEach(symbol => {
        const forexSymbol = `OANDA:${forexHistoryBase}${symbol}`;
        subscribeSymbol(forexSymbol);
      });
      console.log("Using WebSocket for realtime forex data");
    } else {
      console.log("WebSocket not available, using polling fallback");
      // Start polling interval
      const interval = setInterval(fetchRealtimeForex, 30000); // 30 seconds
      setRealtimeInterval(interval);
    }
    
    // Always fetch initial data
    fetchRealtimeForex();
  };

  const stopRealtimeForex = () => {
    setIsRealtimeForex(false);
    
    // Unsubscribe from forex symbols if WebSocket is connected
    if (wsStatus === "connected") {
      const forexSymbols = forexHistorySymbols.split(',');
      forexSymbols.forEach(symbol => {
        const forexSymbol = `OANDA:${forexHistoryBase}${symbol}`;
        unsubscribeSymbol(forexSymbol);
      });
    }
    
    if (realtimeInterval) {
      clearInterval(realtimeInterval);
      setRealtimeInterval(null);
    }
  };

  // Crypto pair functions
  const fetchCryptoPairData = async () => {
    try {
      // First get crypto price in USD
      const cryptoRes = await axios.get(
        `${API_BASE}/crypto/latest`,
        { params: { symbols: cryptoTargetCurrency } }
      );
      
      const cryptoData = cryptoRes.data.data || {};
      const cryptoPriceUSD = cryptoData[cryptoTargetCurrency]?.price || 0;
      
      if (cryptoPriceUSD > 0 && cryptoBaseCurrency !== "USD") {
        // Convert USD to target currency using forex
        const forexRes = await axios.get(
          `${API_BASE}/forex/convert`,
          { 
            params: { 
              amount: cryptoPriceUSD,
              from_currency: "USD",
              to_currency: cryptoBaseCurrency
            } 
          }
        );
        
        const convertedPrice = forexRes.data.result || cryptoPriceUSD;
        
        const now = Math.floor(Date.now() / 1000); // Unix timestamp in seconds
        
        setCryptoPairData(prev => {
          const newData = [...prev, { 
            time: now, 
            value: parseFloat(convertedPrice) || 0 
          }];
          return processChartData(newData);
        });
      } else {
        // Direct USD price
        const now = Math.floor(Date.now() / 1000); // Unix timestamp in seconds
        
        setCryptoPairData(prev => {
          const newData = [...prev, { 
            time: now, 
            value: parseFloat(cryptoPriceUSD) || 0 
          }];
          return processChartData(newData);
        });
      }
    } catch (err) {
      console.error("Error fetching crypto pair data:", err);
    }
  };

  const startRealtimeCryptoPair = () => {
    setIsRealtimeCrypto(true);
    setCryptoPairData([]);
    
    // Try WebSocket first, fallback to polling
    if (wsStatus === "connected") {
      const cryptoSymbol = `BINANCE:${cryptoTargetCurrency}USDT`;
      subscribeSymbol(cryptoSymbol);
      console.log("Using WebSocket for realtime crypto data");
    } else {
      console.log("WebSocket not available, using polling fallback");
      // Start polling interval
      const interval = setInterval(fetchCryptoPairData, 30000); // 30 seconds
      setRealtimeInterval(interval);
    }
    
    // Always fetch initial data
    fetchCryptoPairData();
  };

  const stopRealtimeCryptoPair = () => {
    setIsRealtimeCrypto(false);
    
    // Unsubscribe from crypto symbol if WebSocket is connected
    if (wsStatus === "connected") {
      const cryptoSymbol = `BINANCE:${cryptoTargetCurrency}USDT`;
      unsubscribeSymbol(cryptoSymbol);
    }
    
    if (realtimeInterval) {
      clearInterval(realtimeInterval);
      setRealtimeInterval(null);
    }
  };

  // WebSocket functions
  const connectWebSocket = () => {
    try {
      setWsStatus("connecting");
      setWsError(null);
      
      const ws = new WebSocket(FINNHUB_WS_URL);

      ws.onopen = () => {
        console.log("WebSocket connection opened");
        setWsStatus("connected");
        setWsError(null);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("WebSocket data received:", data);
        
        if (data.type === "trade" && data.data && data.data.length > 0) {
          const trade = data.data[0];
          const now = Math.floor(trade.t / 1000); // Convert milliseconds to seconds
          
          // Update crypto pair data if symbol matches
          if (trade.s.includes(cryptoTargetCurrency)) {
            setCryptoPairData(prev => {
              const newData = [...prev, { 
                time: now, 
                value: parseFloat(trade.p) || 0 
              }];
              return processChartData(newData);
            });
          }
          
          // Update forex data if symbol matches
          if (trade.s.includes(forexHistoryBase) || trade.s.includes(forexHistorySymbols.split(',')[0])) {
            setRealtimeForexData(prev => {
              const newData = [...prev, { 
                time: now, 
                value: parseFloat(trade.p) || 0 
              }];
              return processChartData(newData);
            });
          }
        }
        
        setWsData(prev => [...prev, data]);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setWsStatus("error");
        setWsError("Failed to connect to Finnhub WebSocket. Using fallback polling.");
      };

      ws.onclose = (event) => {
        console.log("WebSocket connection closed:", event.code, event.reason);
        setWsStatus("disconnected");
        if (event.code !== 1000) { // Not a normal closure
          setWsError(`Connection closed: ${event.reason || 'Unknown error'}`);
        }
      };

      setWsConnection(ws);
      
      // Set timeout for connection
      setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          console.log("WebSocket connection timeout, using fallback");
          setWsStatus("timeout");
          setWsError("Connection timeout. Using fallback polling API.");
          ws.close();
        }
      }, 5000); // 5 second timeout
      
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setWsStatus("error");
      setWsError("Failed to create WebSocket connection. Using fallback polling.");
    }
  };

  const disconnectWebSocket = () => {
    if (wsConnection) {
      wsConnection.close();
      setWsConnection(null);
      setWsData([]);
    }
  };

  const subscribeSymbol = (symbol) => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type: "subscribe", symbol: symbol });
      wsConnection.send(message);
      console.log("Subscribed to:", symbol);
    }
  };

  const unsubscribeSymbol = (symbol) => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type: "unsubscribe", symbol: symbol });
      wsConnection.send(message);
      console.log("Unsubscribed from:", symbol);
    }
  };

  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, []);

  return (
    <div className="container my-4">
      <h1 className="mb-4">LiteForexCryptoAPI Playground</h1>
      <Section title="Health Check">
        <button className="btn btn-success mb-2" onClick={() => handleRequest("health", "/health")}>Check Health</button>
        {loading.health && <div>Loading...</div>}
        {error.health && <div className="text-danger">{error.health}</div>}
        {result.health && <pre>{prettyJSON(result.health)}</pre>}
      </Section>

      <Section title="Forex - Latest Rates">
        <form onSubmit={e => { e.preventDefault(); handleRequest("forexLatest", "/forex/latest", forexLatest); }}>
          <div className="row g-2">
            <div className="col-md-3">
              <input className="form-control" placeholder="Base (USD)" value={forexLatest.base} onChange={e => setForexLatest(f => ({ ...f, base: e.target.value }))} />
            </div>
            <div className="col-md-6">
              <input className="form-control" placeholder="Symbols (EUR,IDR,JPY)" value={forexLatest.symbols} onChange={e => setForexLatest(f => ({ ...f, symbols: e.target.value }))} />
            </div>
            <div className="col-md-3">
              <button className="btn btn-primary w-100" type="submit">Get Rates</button>
            </div>
          </div>
        </form>
        {loading.forexLatest && <div>Loading...</div>}
        {error.forexLatest && <div className="text-danger">{error.forexLatest}</div>}
        {result.forexLatest && <pre>{prettyJSON(result.forexLatest)}</pre>}
      </Section>

      <Section title="Forex - Convert">
        <form onSubmit={e => { e.preventDefault(); handleRequest("forexConvert", "/forex/convert", {
          amount: forexConvert.amount,
          from_currency: forexConvert.from,
          to_currency: forexConvert.to
        }); }}>
          <div className="row g-2">
            <div className="col-md-2">
              <input className="form-control" type="number" placeholder="Amount" value={forexConvert.amount} onChange={e => setForexConvert(f => ({ ...f, amount: e.target.value }))} />
            </div>
            <div className="col-md-2">
              <input className="form-control" placeholder="From (USD)" value={forexConvert.from} onChange={e => setForexConvert(f => ({ ...f, from: e.target.value }))} />
            </div>
            <div className="col-md-2">
              <input className="form-control" placeholder="To (IDR)" value={forexConvert.to} onChange={e => setForexConvert(f => ({ ...f, to: e.target.value }))} />
            </div>
            <div className="col-md-3">
              <button className="btn btn-primary w-100" type="submit">Convert</button>
            </div>
          </div>
        </form>
        {loading.forexConvert && <div>Loading...</div>}
        {error.forexConvert && <div className="text-danger">{error.forexConvert}</div>}
        {result.forexConvert && <pre>{prettyJSON(result.forexConvert)}</pre>}
      </Section>

      <Section title="Forex - Historical Rates">
        <form onSubmit={e => { e.preventDefault(); handleRequest("forexHistorical", "/forex/historical", { date_str: forexHistorical.date, base: forexHistorical.base, symbols: forexHistorical.symbols }); }}>
          <div className="row g-2">
            <div className="col-md-3">
              <input className="form-control" type="date" value={forexHistorical.date} onChange={e => setForexHistorical(f => ({ ...f, date: e.target.value }))} />
            </div>
            <div className="col-md-3">
              <input className="form-control" placeholder="Base (USD)" value={forexHistorical.base} onChange={e => setForexHistorical(f => ({ ...f, base: e.target.value }))} />
            </div>
            <div className="col-md-4">
              <input className="form-control" placeholder="Symbols (EUR,IDR)" value={forexHistorical.symbols} onChange={e => setForexHistorical(f => ({ ...f, symbols: e.target.value }))} />
            </div>
            <div className="col-md-2">
              <button className="btn btn-primary w-100" type="submit">Get Historical</button>
            </div>
          </div>
        </form>
        {loading.forexHistorical && <div>Loading...</div>}
        {error.forexHistorical && <div className="text-danger">{error.forexHistorical}</div>}
        {result.forexHistorical && <pre>{prettyJSON(result.forexHistorical)}</pre>}
      </Section>

      <Section title="Forex - List Supported Currencies">
        <button className="btn btn-info mb-2" onClick={() => handleRequest("forexList", "/forex/list")}>Get List</button>
        {loading.forexList && <div>Loading...</div>}
        {error.forexList && <div className="text-danger">{error.forexList}</div>}
        {result.forexList && <pre>{prettyJSON(result.forexList)}</pre>}
      </Section>

      <Section title="Crypto - Latest Prices">
        <form onSubmit={e => { e.preventDefault(); handleRequest("cryptoLatest", "/crypto/latest", cryptoLatest); }}>
          <div className="row g-2">
            <div className="col-md-8">
              <input className="form-control" placeholder="Symbols (BTC,ETH,SOL)" value={cryptoLatest.symbols} onChange={e => setCryptoLatest(f => ({ ...f, symbols: f.symbols = e.target.value }))} />
            </div>
            <div className="col-md-4">
              <button className="btn btn-primary w-100" type="submit">Get Prices</button>
            </div>
          </div>
        </form>
        {loading.cryptoLatest && <div>Loading...</div>}
        {error.cryptoLatest && <div className="text-danger">{error.cryptoLatest}</div>}
        {result.cryptoLatest && <pre>{prettyJSON(result.cryptoLatest)}</pre>}
      </Section>

      <Section title="Crypto - Historical Prices">
        <form onSubmit={e => { e.preventDefault(); handleRequest("cryptoHistorical", "/crypto/historical", { date_str: cryptoHistorical.date, symbols: cryptoHistorical.symbols }); }}>
          <div className="row g-2">
            <div className="col-md-4">
              <input className="form-control" type="date" value={cryptoHistorical.date} onChange={e => setCryptoHistorical(f => ({ ...f, date: e.target.value }))} />
            </div>
            <div className="col-md-6">
              <input className="form-control" placeholder="Symbols (BTC,ETH)" value={cryptoHistorical.symbols} onChange={e => setCryptoHistorical(f => ({ ...f, symbols: e.target.value }))} />
            </div>
            <div className="col-md-2">
              <button className="btn btn-primary w-100" type="submit">Get Historical</button>
            </div>
          </div>
        </form>
        {loading.cryptoHistorical && <div>Loading...</div>}
        {error.cryptoHistorical && <div className="text-danger">{error.cryptoHistorical}</div>}
        {result.cryptoHistorical && <pre>{prettyJSON(result.cryptoHistorical)}</pre>}
      </Section>

      <Section title="Crypto - Market Cap">
        <form onSubmit={e => { e.preventDefault(); handleRequest("cryptoMarketcap", "/crypto/marketcap", cryptoMarketcap); }}>
          <div className="row g-2">
            <div className="col-md-8">
              <input className="form-control" placeholder="Symbols (BTC,ETH,SOL)" value={cryptoMarketcap.symbols} onChange={e => setCryptoMarketcap(f => ({ ...f, symbols: e.target.value }))} />
            </div>
            <div className="col-md-4">
              <button className="btn btn-primary w-100" type="submit">Get Market Cap</button>
            </div>
          </div>
        </form>
        {loading.cryptoMarketcap && <div>Loading...</div>}
        {error.cryptoMarketcap && <div className="text-danger">{error.cryptoMarketcap}</div>}
        {result.cryptoMarketcap && <pre>{prettyJSON(result.cryptoMarketcap)}</pre>}
      </Section>

      <Section title="Crypto - List Supported Coins">
        <button className="btn btn-info mb-2" onClick={() => handleRequest("cryptoList", "/crypto/list")}>Get List</button>
        {loading.cryptoList && <div>Loading...</div>}
        {error.cryptoList && <div className="text-danger">{error.cryptoList}</div>}
        {result.cryptoList && <pre>{prettyJSON(result.cryptoList)}</pre>}
      </Section>

      {/* Chart Sections */}
      <Section title="📊 Crypto Historical Chart">
        <div className="row">
          <div className="col-md-4">
            <div className="mb-2">
              <label className="form-label">Crypto Pair Selection:</label>
              <select
                className="form-select mb-2"
                value={cryptoTargetCurrency}
                onChange={(e) => setCryptoTargetCurrency(e.target.value)}
              >
                <option value="BTC">Bitcoin (BTC)</option>
                <option value="ETH">Ethereum (ETH)</option>
                <option value="SOL">Solana (SOL)</option>
                <option value="ADA">Cardano (ADA)</option>
                <option value="DOT">Polkadot (DOT)</option>
                <option value="LINK">Chainlink (LINK)</option>
                <option value="UNI">Uniswap (UNI)</option>
                <option value="MATIC">Polygon (MATIC)</option>
                <option value="AVAX">Avalanche (AVAX)</option>
                <option value="ATOM">Cosmos (ATOM)</option>
              </select>
              <select
                className="form-select mb-2"
                value={cryptoBaseCurrency}
                onChange={(e) => setCryptoBaseCurrency(e.target.value)}
              >
                <option value="USD">US Dollar (USD)</option>
                <option value="EUR">Euro (EUR)</option>
                <option value="IDR">Indonesian Rupiah (IDR)</option>
                <option value="JPY">Japanese Yen (JPY)</option>
                <option value="GBP">British Pound (GBP)</option>
                <option value="SGD">Singapore Dollar (SGD)</option>
                <option value="MYR">Malaysian Ringgit (MYR)</option>
                <option value="THB">Thai Baht (THB)</option>
                <option value="PHP">Philippine Peso (PHP)</option>
                <option value="VND">Vietnamese Dong (VND)</option>
                <option value="KRW">South Korean Won (KRW)</option>
                <option value="CNY">Chinese Yuan (CNY)</option>
                <option value="AUD">Australian Dollar (AUD)</option>
                <option value="CAD">Canadian Dollar (CAD)</option>
                <option value="CHF">Swiss Franc (CHF)</option>
                <option value="NZD">New Zealand Dollar (NZD)</option>
              </select>
            </div>
            <input
              type="date"
              value={cryptoHistoryDate}
              onChange={(e) => setCryptoHistoryDate(e.target.value)}
              className="form-control mb-2"
            />
            <div className="mb-2">
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="realtimeCrypto"
                  checked={isRealtimeCrypto}
                  onChange={(e) => {
                    if (e.target.checked) {
                      startRealtimeCryptoPair();
                    } else {
                      stopRealtimeCryptoPair();
                    }
                  }}
                />
                <label className="form-check-label" htmlFor="realtimeCrypto">
                  🔴 Realtime Mode (30s interval)
                </label>
              </div>
            </div>
            {!isRealtimeCrypto && (
              <button className="btn btn-primary" onClick={fetchCryptoHistory}>
                Show Historical Chart
              </button>
            )}
            {isRealtimeCrypto && (
              <div className="alert alert-info">
                <small>🔄 Auto-updating every 30 seconds...</small>
              </div>
            )}
            {isRealtimeCrypto && (
              <div className="alert alert-success">
                <small>📡 WebSocket Connected - Real-time data from Finnhub</small>
              </div>
            )}
            {isRealtimeCrypto && wsStatus !== "connected" && (
              <div className="alert alert-warning">
                <small>🔄 Polling Mode - WebSocket unavailable, using API polling every 30s</small>
              </div>
            )}
          </div>
          <div className="col-md-8">
            {(isRealtimeCrypto ? cryptoPairData : cryptoHistory).length > 0 ? (
              <Chart 
                data={isRealtimeCrypto ? cryptoPairData : cryptoHistory} 
                title={isRealtimeCrypto 
                  ? `🔴 ${cryptoTargetCurrency}/${cryptoBaseCurrency} Live Price` 
                  : `${cryptoHistorySymbol} Price on ${cryptoHistoryDate}`
                }
                width={500}
                height={300}
              />
            ) : (
              <div className="text-muted">
                No data to display
                <br />
                <small>Try different date or check console for debug info</small>
              </div>
            )}
          </div>
        </div>
      </Section>

      <Section title="📈 Forex Historical Chart">
        <div className="row">
          <div className="col-md-4">
            <input
              type="text"
              value={forexHistoryBase}
              onChange={(e) => setForexHistoryBase(e.target.value)}
              placeholder="Base Currency (e.g. USD)"
              className="form-control mb-2"
            />
            <input
              type="text"
              value={forexHistorySymbols}
              onChange={(e) => setForexHistorySymbols(e.target.value)}
              placeholder="Target Currencies (e.g. IDR,EUR)"
              className="form-control mb-2"
            />
            <input
              type="date"
              value={forexHistoryDate}
              onChange={(e) => setForexHistoryDate(e.target.value)}
              className="form-control mb-2"
            />
            <div className="mb-2">
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="realtimeForex"
                  checked={isRealtimeForex}
                  onChange={(e) => {
                    if (e.target.checked) {
                      startRealtimeForex();
                    } else {
                      stopRealtimeForex();
                    }
                  }}
                />
                <label className="form-check-label" htmlFor="realtimeForex">
                  🔴 Realtime Mode (30s interval)
                </label>
              </div>
            </div>
            {!isRealtimeForex && (
              <button className="btn btn-success" onClick={fetchForexHistory}>
                Show Historical Chart
              </button>
            )}
            {isRealtimeForex && (
              <div className="alert alert-info">
                <small>🔄 Auto-updating every 30 seconds...</small>
              </div>
            )}
            {isRealtimeForex && (
              <div className="alert alert-success">
                <small>📡 WebSocket Connected - Real-time data from Finnhub</small>
              </div>
            )}
            {isRealtimeForex && wsStatus !== "connected" && (
              <div className="alert alert-warning">
                <small>🔄 Polling Mode - WebSocket unavailable, using API polling every 30s</small>
              </div>
            )}
          </div>
          <div className="col-md-8">
            {(isRealtimeForex ? realtimeForexData : forexHistory).length > 0 ? (
              <Chart 
                data={isRealtimeForex ? realtimeForexData : forexHistory} 
                title={isRealtimeForex 
                  ? `🔴 ${forexHistoryBase} Live Exchange Rates` 
                  : `${forexHistoryBase} Exchange Rates on ${forexHistoryDate}`
                }
                width={500}
                height={300}
              />
            ) : (
              <div className="text-muted">
                No data to display
                <br />
                <small>Try different date or check console for debug info</small>
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* WebSocket Status Section */}
      <Section title="📡 WebSocket Connection Status">
        <div className="row">
          <div className="col-md-6">
            <div className="card">
              <div className="card-body">
                <h6>Connection Status</h6>
                <p className={
                  wsStatus === "connected" ? "text-success" : 
                  wsStatus === "connecting" ? "text-warning" :
                  wsStatus === "error" ? "text-danger" :
                  wsStatus === "timeout" ? "text-warning" : "text-secondary"
                }>
                  {wsStatus === "connected" && "🟢 Connected to Finnhub WebSocket"}
                  {wsStatus === "connecting" && "🟡 Connecting to Finnhub WebSocket..."}
                  {wsStatus === "error" && "🔴 WebSocket Error"}
                  {wsStatus === "timeout" && "🟡 Connection Timeout"}
                  {wsStatus === "disconnected" && "⚪ Disconnected"}
                </p>
                {wsError && (
                  <div className="alert alert-warning small">
                    <strong>Note:</strong> {wsError}
                  </div>
                )}
                <button 
                  className="btn btn-sm btn-primary me-2" 
                  onClick={connectWebSocket}
                  disabled={wsStatus === "connecting"}
                >
                  {wsStatus === "connecting" ? "Connecting..." : "Connect"}
                </button>
                <button 
                  className="btn btn-sm btn-danger" 
                  onClick={disconnectWebSocket}
                  disabled={wsStatus !== "connected"}
                >
                  Disconnect
                </button>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card">
              <div className="card-body">
                <h6>Latest WebSocket Data</h6>
                <div style={{maxHeight: "200px", overflowY: "auto"}}>
                  {wsData.length > 0 ? (
                    <pre className="small">{JSON.stringify(wsData[wsData.length - 1], null, 2)}</pre>
                  ) : (
                    <p className="text-muted">No data received yet</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Section>
    </div>
  );
}
