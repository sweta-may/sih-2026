import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://127.0.0.1:8000";

const vessels = ["Capesize", "Panamax", "Supramax", "Handysize"];

function App() {
  const [vessel, setVessel] = useState("Capesize");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function getForecast() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/forecast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vessel_type: vessel }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `API error: ${response.status}`);
      }

      setResult(await response.json());
    } catch (err) {
      setError(
        "Could not connect to the SmartFreight API. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  const forecast = result?.forecast;
  const current = result?.current_rate_usd_day ?? 0;

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand">SMART<span>FREIGHT</span> AI</div>
          <div className="subtitle">Intelligent Freight Forecasting & Chartering</div>
        </div>
        <div className="status"><i /> API CONNECTED</div>
      </header>

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">FREIGHT INTELLIGENCE</p>
            <h1>Forecast before you charter.</h1>
            <p className="heroText">
              AI-powered dry-bulk freight forecasting with a market-entry decision engine.
            </p>
          </div>

          <div className="controlCard">
            <label>VESSEL TYPE</label>
            <select value={vessel} onChange={(e) => setVessel(e.target.value)}>
              {vessels.map((v) => <option key={v}>{v}</option>)}
            </select>
            <button onClick={getForecast} disabled={loading}>
              {loading ? "FORECASTING..." : "RUN FORECAST →"}
            </button>
          </div>
        </section>

        {error && <div className="error">{error}</div>}

        {result && (
          <>
            <section className="stats">
              <div className="stat">
                <span>CURRENT RATE</span>
                <strong>${current.toLocaleString()}</strong>
                <small>USD / day · {result.current_date}</small>
              </div>
              <div className="stat">
                <span>MODEL</span>
                <strong>{result.model}</strong>
                <small>Selected after model comparison</small>
              </div>
              <div className={`decision ${result.market_entry_signal === "WAIT" ? "wait" : "chart"}`}>
                <span>MARKET SIGNAL</span>
                <strong>{result.market_entry_signal}</strong>
                <small>Decision engine output</small>
              </div>
            </section>

            <section className="forecastSection">
              <div className="sectionTitle">
                <div>
                  <p className="eyebrow">RATE OUTLOOK</p>
                  <h2>Freight Forecast</h2>
                </div>
                <div className="window">
                  BEST ENTRY WINDOW
                  <b>{result.recommended_entry_window.replace("_", " ").toUpperCase()}</b>
                </div>
              </div>

              <div className="cards">
                {["7_days", "14_days", "30_days"].map((key) => {
                  const item = forecast[key];
                  const negative = item.change_percent_vs_current < 0;
                  return (
                    <div className={`forecastCard ${key === result.recommended_entry_window ? "recommended" : ""}`} key={key}>
                      {key === result.recommended_entry_window && <div className="tag">RECOMMENDED</div>}
                      <span>{key.replace("_", " ").toUpperCase()}</span>
                      <strong>${item.forecast_rate_usd_day.toLocaleString()}</strong>
                      <div className={negative ? "down" : "up"}>
                        {negative ? "↓" : "↑"} {Math.abs(item.change_percent_vs_current)}%
                      </div>
                      <small>vs current rate</small>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="explain">
              <div className="explainIcon">AI</div>
              <div>
                <h3>Decision Engine Recommendation</h3>
                <p>
                  The Random Forest model compares the 7, 14 and 30-step forecasts.
                  The lowest forecast is used as the candidate market-entry window.
                  Current recommendation: <b>{result.market_entry_signal}</b>.
                </p>
              </div>
            </section>
          </>
        )}

        {!result && !loading && !error && (
          <div className="empty">
            <div className="ship">🚢</div>
            <h2>Ready to forecast</h2>
            <p>Select a vessel type and run the AI forecast.</p>
          </div>
        )}
      </main>

      <footer>
        <span>SMARTFREIGHT AI · SIH 2026</span>
        <span>Decision-support prototype · KOBC historical freight data</span>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);