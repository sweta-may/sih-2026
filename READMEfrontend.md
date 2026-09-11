# SmartFreight AI — Modern Frontend Dashboard

High-fidelity React + Vite maritime decision dashboard connected to the SmartFreight FastAPI backend, redesigned to match the official SmartFreight UI design specification.

## Features

- **Pixel-Perfect Reference Match**: Implements the exact grid layout, Tabler icons (`ti ti-*`), Google Fonts Inter, and CSS custom property token system (`--surface-1`, `--surface-2`, `--border-accent`, etc.).
- **Interactive Overview**:
  - Live metric cards (Freight rate `$24.5/ton`, Forecast `$22.8/ton` with trend arrow, Active vessels `12`, Avg waiting `18 hrs`).
  - Live vessel tracking map card with interactive toggle and AIS vessel positions.
  - Distinctive Recommendation card with sky-blue accent border, savings badge, and "View full analysis" trigger.
  - Cost comparison (Charter now `$1.25M` vs Wait `$1.17M`) and Port congestion indicators (Paradip `Moderate`, expected wait `18 hrs`).
- **Interactive Multi-Horizon Analysis Modal**:
  - Compares 7-day, 14-day, and 30-day forecast horizons.
  - Supports dynamic switching between **Supramax**, **Capesize**, **Panamax**, and **Handysize**.
  - Direct integration with `http://127.0.0.1:8000/forecast` with seamless offline fallback.
- **Full Navigation Tabs**:
  - **New voyage**: Voyage charter calculator.
  - **Freight forecast**: Multi-horizon predictive intelligence.
  - **Vessel optimization**: Eco speed vs full speed bunker and demurrage risk analysis.
  - **Tracking**: East Coast AIS fleet tracking table.
  - **Port and congestion**: Port status timetable for Paradip, Haldia, Vizag, and Dhamra.
  - **Reports**: One-click downloadable CSV operational reports.
  - **Admin and governance**: AI model metrics and pipeline health.
  - **Settings**: System configurations.

---

## How to Run

### Option A: React Development Server (Recommended)
1. In the `frontend` directory, install packages:
   ```bash
   npm install
   ```
2. Start the Vite dev server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

### Option B: Standalone Preview (No Node/Build Required)
Simply double-click `preview.html` or open it in any web browser to test the full interface immediately.

---

## Backend Connection

The frontend queries the FastAPI backend at:
```
POST http://127.0.0.1:8000/forecast
Payload: { "vessel_type": "Supramax" }
```
When FastAPI is running, live forecasts populate automatically. If the backend is starting or offline, the UI provides realistic defaults matching the reference design.
