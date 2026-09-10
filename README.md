# 🚢 SmartFreight AI — Unified Charter Decision & Freight Intelligence Platform
### Smart India Hackathon (SIH) 2026 | East Coast India Bulk Logistics Decision Support

---

## 🎯 Executive Overview
**SmartFreight AI** answers the multi-million-dollar question for shipping, logistics, and dry-bulk chartering managers on India's East Coast:

> **"Should we CHARTER NOW or WAIT for better market conditions?"**

By combining multi-horizon freight rate forecasting, naval architecture port constraints, live AIS vessel tracking, waiting-time machine learning, and dynamic voyage cost modeling, SmartFreight AI delivers automated, mathematically validated charter decisions with quantifiable dollar savings.

---

## 🏗️ Cross-Module Architecture

```
                                  [ SmartFreight AI ]
                                           │
  ┌─────────────────┬──────────────────────┼──────────────────────┬─────────────────┐
  ▼                 ▼                      ▼                      ▼                 ▼
Member 2          Member 3               Member 4               Member 5          Member 6
Freight ML        Vessel Optimization    AIS & Telemetry        Cost & Decision   Full-Stack
Forecast          Port Constraints       ETA & Waiting Time     Charter vs Wait   UI & API
  │                 │                      │                      │                 │
  ▼                 ▼                      ▼                      ▼                 ▼
RF Multi-Horizon  Draft / LOA / Beam     VesselFinder AIS       Total Voyage Cost Streamlit UI
7d, 14d, 30d      INPRD, INHLD, INVTZ    Waiting Time ML Model  Idle / Demurrage  FastAPI REST
Rate Predictions  Capacity Utilization   IRCTC Status Tracker   Savings ($ / %)   Interactive
```

### Module Responsibilities:
1. **Member 2 — Freight Forecasting**: Multi-horizon forward rate curves (7, 14, 30 days) using historical Baltic and East Coast dry bulk benchmarks.
2. **Member 3 — Vessel Optimization**: Checks physical draft, LOA, and beam against port catalogs (Paradip, Haldia, Visakhapatnam, Chennai, Ennore) to select the optimal vessel class (Handysize, Supramax, Panamax, Capesize).
3. **Member 4 — AIS Telemetry & Congestion**: Real-time position tracking, direct ETA calculation, waiting-time prediction, demurrage risk estimation, and an **IRCTC-style voyage progression tracker**.
4. **Member 5 — Cost Optimization & Charter Decision**: Quantitative comparison of current voyage cost vs. wait scenario, factoring in market wait costs, demurrage risks, and urgency overrides.
5. **Member 6 — Full-Stack Integration & Dashboard**: Master pipeline orchestrator (`run_smartfreight_integrated_simulation`), interactive Streamlit dashboard (`dashboard.py`), and production-grade FastAPI service (`api/server.py`).

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Virtual Environment
Ensure Python 3.10+ is installed:
```powershell
python --version
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
# Or install core packages:
pip install streamlit fastapi uvicorn pydantic plotly pandas pydeck pytest
```

### 3. Run the Unified Streamlit Dashboard (Member 6 UI)
Launch the interactive decision dashboard:
```powershell
streamlit run dashboard.py
```
Open your browser at `http://localhost:8501`.
Features:
- **Sidebar**: Select Cargo Type, Quantity (MT), Origin & Destination Ports, Urgency, Contract Duration, and Forecast Horizon.
- **Tab 1 — 🏆 Decision**: Executive recommendation badge (`CHARTER NOW` vs `WAIT`), reasoning, recommended vessel, contract strategy, and dollar savings.
- **Tab 2 — 📈 Forecast**: Interactive Plotly rate chart comparing Today vs 7, 14, and 30-day forecast curves.
- **Tab 3 — 🚢 Vessel & Port**: Port physical feasibility matrix (Draft, LOA, Beam) and candidate vessel evaluations.
- **Tab 4 — 📡 AIS & ETA**: IRCTC-style milestone stepper, vessel telemetry, distance remaining, waiting time, and 3D PyDeck map.
- **Tab 5 — 💰 Cost**: Side-by-side cost breakdown tables and waterfall visual of Vessel Hire, Fuel, Port Dues, and Waiting Cost.
- **Tab 6 — 🔔 Alerts**: Live in-app alert notifications and complete JSON payload inspection.

### 4. Run the FastAPI REST API (Member 6 Backend)
Start the REST backend server:
```powershell
uvicorn api.server:app --reload --port 8000
```
- Interactive API Docs (Swagger UI): `http://localhost:8000/docs`
- Key Endpoints:
  - `POST /api/v1/simulate` — Execute full cross-module simulation.
  - `GET /api/v1/simulate` — Run simulation via URL query parameters.
  - `GET /api/v1/ports` — List East Coast Indian port physical constraints.
  - `GET /api/v1/vessels/specs` — List vessel classes and specifications.
  - `GET /api/v1/member4/vessels` — Live AIS vessel tracking feed.
  - `GET /api/v1/member4/congestion` — Port berth occupancy & queue timetable.

### 5. Run Automated Test Suite
Run the full pytest suite (42 automated unit & integration tests):
```powershell
python -m pytest -v
```
Output:
```
============================= 42 passed in 3.34s ==============================
```

---

## 📊 Sample Simulation Output (JSON)
```json
{
  "executive_summary_card": {
    "recommendation": "CHARTER_NOW",
    "recommended_vessel": "Handysize",
    "contract_strategy": "MEDIUM_TERM",
    "current_freight_rate_usd_day": 14000.0,
    "forecast_rate_usd_day": 13132.0,
    "expected_waiting_time_hours": 12.0,
    "port_congestion_level": "MODERATE",
    "charter_now_cost_usd": 101970.0,
    "expected_wait_cost_usd": 113477.6,
    "expected_saving_usd": 11507.6,
    "expected_saving_pct": 10.14,
    "risk_level": "MEDIUM",
    "reason": "Immediate charter saves $11,507.60 (10.1%) vs waiting 14 days after accounting for waiting costs."
  }
}
```

---

## 👥 Hackathon Team Credits (SIH 2026)
- **Member 2**: Freight Rate Forecasting Models
- **Member 3**: Vessel Optimization & Port Compatibility
- **Member 4**: AIS Telemetry, ETA & Waiting-Time Engine
- **Member 5**: Cost Optimization & Charter Decision Engine
- **Member 6**: Full Stack Integration, Unified Dashboard & REST API
