import React, { useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE = "http://localhost:8000";

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
        <form onSubmit={e => { e.preventDefault(); handleRequest("forexConvert", "/forex/convert", forexConvert); }}>
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
    </div>
  );
}
