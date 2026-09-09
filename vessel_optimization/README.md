# Vessel Type Optimization Engine 🚢
**SmartFreight AI — Member 3 (Phavithra)**  
*AI-Powered Bulk Cargo Chartering System for East Coast Indian Ports*

---

## 📌 Overview

The **Vessel Type Optimization Engine** is a specialized rule-based and optimization module that recommends the most suitable bulk carrier vessel and voyage schedule for a cargo shipment.

The engine evaluates standard Baltic dry bulk benchmark vessels:
- **Capesize** (180,000 DWT, LOA 290.0m, Beam 45.0m, Draft 18.2m) — Gearless
- **Panamax** (82,500 DWT, LOA 229.0m, Beam 32.25m, Draft 14.43m) — Gearless
- **Supramax** (58,328 DWT, LOA 189.99m, Beam 32.26m, Draft 12.8m) — Geared (4 × 30t cranes)
- **Handysize** (38,200 DWT, LOA 180.0m, Beam 29.8m, Draft 10.538m) — Geared (4 × 30t cranes)

against port restrictions at both Origin (loading) and Destination (discharge) ports.

---

## 🏗️ Architecture & Logical Flow

The engine enforces a strict **two-stage pipeline**:

```
User Shipment Request
  (Cargo Qty, Commodity, Origin, Destination)
          │
          ▼
Stage 1: Physical & Operational Feasibility Check
  ├─ 1. Port Constraint Resolution & Governing Bottlenecks
  │     (min draft, min LOA, min beam + responsible port attribution)
  ├─ 2. Physical Boundary Checks:
  │     vessel.draft <= port.max_draft  (equality PASSES)
  │     vessel.loa   <= port.max_loa    (equality PASSES)
  │     vessel.beam  <= port.max_beam   (equality PASSES)
  ├─ 3. Port Type Handling (BERTH vs ANCHORAGE_LIGHTERAGE)
  ├─ 4. Cargo Handling & Gear Requirements Check
  └─ 5. Eligible Pool vs Rejection Diagnostics
          │
          ▼
Stage 2: Voyage Optimization & Dynamic Ranking
  ├─ 1. If eligible pool is empty -> Status: NO_FEASIBLE_VESSEL
  ├─ 2. Effective Payload Calculation:
  │     effective_payload = payload_factor * DWT  (Default: 0.95, configurable)
  ├─ 3. Voyage Splitting:
  │     min_voyages = ceil(cargo_quantity / effective_payload)
  │     Filter: min_voyages <= max_voyages        (Default: 3, configurable)
  ├─ 4. Capacity Utilization & Anti-Oversizing Evaluation:
  │     Cargo per voyage = cargo_quantity / N
  │     Utilization = cargo_quantity / (N * effective_payload)
  │     Anti-oversizing: Prefer appropriately sized vessel over oversized vessel
  │                      when both achieve the same voyage count.
  ├─ 5. Context-Specific Tie-Breaker:
  │     Geared capability considered only when beneficial to port/cargo requirements.
  └─ 6. Diagnostic Recommendation Generation
```

---

## 💻 CLI & Usage Examples

### 1. Run the Interactive CLI
```bash
# Example 1: 100,000 MT Coal from Australia to Paradip
python -m vessel_optimization.cli --cargo 100000 --cargo-type Coal --origin Australia --dest Paradip

# Example 2: 75,000 MT Coal to Haldia (River Port Bottleneck)
python -m vessel_optimization.cli --cargo 75000 --cargo-type Coal --origin Indonesia --dest Haldia

# Example 3: Output in JSON format
python -m vessel_optimization.cli --cargo 100000 --origin Australia --dest Paradip --json
```

### 2. Run All Benchmark Demonstrator Scenarios
```bash
python vessel_optimization/run_engine.py
```

### 3. Run Unit & Integration Tests
```bash
python -m unittest discover -s vessel_optimization/tests
```

---

## ⚙️ Configurable Parameters

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `payload_factor` | `float` | `0.95` | Operational approximation factor for bulk cargo intake vs nominal DWT (accounting for fuel, ballast, constants). Range: `0.50` to `1.00`. |
| `max_voyages` | `int` | `3` | Maximum allowed voyages to split a cargo shipment. Range: \(\ge 1\). |
| `allowed_vessels` | `list` | `None` (All) | Optional filter to restrict candidate vessel categories. |

---

## 📊 Covered Ports Database

### East Coast Indian Ports (from `port_data.csv`):
- **Paradip (INPRD)**: Max Draft 16.5m, Max LOA 300.0m, Max Beam 46.0m (Berth)
- **Visakhapatnam (INVTZ)**: Max Draft 18.1m, Max LOA 300.0m, Max Beam 50.0m (Berth)
- **Gangavaram (INGGV)**: Max Draft 18.0m, Max LOA 355.0m, Max Beam 50.0m (Berth)
- **Gopalpur (INGPR)**: Max Draft 14.2m, Max LOA 240.0m, Max Beam 36.0m (Berth)
- **Dhamra (INDHM)**: Max Draft 18.0m, Max LOA 350.0m, Max Beam 50.0m (Berth)
- **Haldia (INHAL)**: Max Draft 12.2m, Max LOA 239.0m, Max Beam 32.3m (River Port Berth)
- **Sagar-Sandheads (INSAG)**: Open-water anchorage & transshipment lighterage (Anchorage / Lighterage)

### International Bulk Export Origins:
- **Australia**: Benchmark terminal (19.5m draft), Hay Point / DBCT (19.5m), Newcastle (15.2m), Gladstone (17.5m)
- **South Africa**: Benchmark terminal (17.5m draft), Richards Bay (17.5m)
- **Indonesia**: Benchmark terminal (15.0m draft), Taboneo (15.5m anchorage), Tanjung Bara (17.5m)
