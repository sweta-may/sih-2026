# Member 5: Cost Optimization & Charter Decision Engine

## 1. Purpose
The Member 5 module serves as the executive financial and operational decision-support layer for SmartFreight AI. It answers the fundamental business question:

> **"Should the company CHARTER NOW or WAIT for better market conditions?"**

The decision is driven by **total voyage economics** and **operational feasibility**, rather than simple freight rate directional movement.

---

## 2. Architecture & Integration Flow

```
+--------------------------------------------------------------------------+
| Member 2: Freight Rate Forecasting                                      |
| (Current rate, 7-day, 14-day, 30-day forecast rates)                    |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
| Member 3: Vessel Optimization                                            |
| (Vessel class, DWT, voyages, cargo/voyage, capacity utilization)         |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
| Member 4: AIS / ETA / Congestion / Idle Cost Bridge                      |
| (Distance, waiting time, turnaround time, idle cost impact, congestion)  |
+--------------------------------------------------------------------------+
                                    │
                                    ▼
+--------------------------------------------------------------------------+
| MEMBER 5 DECISION ENGINE                                                 |
| 1. Build normalized DecisionRequest                                      |
| 2. Compute Voyage Cost (Now) vs Wait Cost (Future + Market Wait)         |
| 3. Apply operational constraints (Urgency, Deadline, Availability, Cong)|
| 4. Select CHARTER_NOW vs WAIT                                            |
| 5. Recommend Contract Type (SPOT, SHORT_TERM, MEDIUM_TERM)               |
| 6. Multi-Factor Risk Assessment (LOW, MEDIUM, HIGH)                      |
| 7. Return structured API-ready DecisionResult                            |
+--------------------------------------------------------------------------+
```

---

## 3. Cost Formulas

### 3.1 Total Voyage Cost (Charter Now)
$$\text{Total Voyage Cost} = \text{Freight Cost} + \text{Fuel Cost} + \text{Port Cost} + \text{Waiting Cost} + \text{Other Voyage Cost}$$

Where:
- **Freight Cost**: $\text{Freight Rate (\$/day)} \times \text{Voyage Duration (days)} \times \text{Number of Voyages}$
- **Fuel Cost**: $\text{Fuel Consumption (MT/day)} \times \text{Voyage Duration} \times \text{Bunker Price (\$/MT)} \times \text{Number of Voyages}$
- **Port Cost**: $\text{Port Cost (\$/voyage)} \times \text{Number of Voyages}$
- **Waiting Cost**: $\text{Member 4 Idle Impact (\$)} \times \text{Waiting Cost Multiplier}$
- **Other Voyage Cost**: $\text{Other Voyage Costs (\$)} \times \text{Number of Voyages}$

### 3.2 Total Wait Cost
$$\text{Expected Wait Cost} = \text{Future Voyage Cost (using Forecast Rate)} + \text{Market Waiting Cost}$$
$$\text{Market Waiting Cost} = \text{Forecast Horizon (days)} \times \text{Market Wait Cost (\$/day)}$$

---

## 4. Charter Decision Logic

1. **Financial Comparison**:
   $$\text{Wait Advantage} = \text{Total Voyage Cost (Now)} - \text{Total Expected Wait Cost}$$
2. **Savings Threshold**:
   Waiting is only considered if:
   $$\text{Wait Advantage} \ge \text{minimum\_wait\_saving\_usd} \quad \text{AND} \quad \text{Saving \%} \ge \text{minimum\_wait\_saving\_pct}$$
3. **Operational Safeguards & Overrides**:
   Even if waiting is cheaper, the engine overrides to **`CHARTER_NOW`** if:
   - **Cargo Urgency**: Urgency is `URGENT` or `CRITICAL`.
   - **Delivery Deadline**: Waiting would cause arrival to exceed `required_by_date`.
   - **Vessel Availability**: Availability is `UNAVAILABLE` or `SCARCE`.
   - **Port Congestion**: Congestion is `CRITICAL` or `SEVERE`.

---

## 5. Contract Type Recommendations

- **`SPOT`**: Single non-recurring voyage, immediate/urgent cargo, or short horizon (<= 7 days).
- **`SHORT_TERM`**: Single voyage with moderate horizon (7–14 days) or upward-trending market.
- **`MEDIUM_TERM`**: Recurring cargo (`recurring=True`), multi-voyage split (`voyages > 1`), or high supply volatility.

---

## 6. Risk Classification

Evaluates 6 deterministic factors to produce **`LOW`**, **`MEDIUM`**, or **`HIGH`** risk:
1. **Forecast Volatility**: >10% variation (+2 score), 5–10% (+1 score).
2. **Port Congestion**: CRITICAL/HIGH (+2 score), MODERATE (+1 score).
3. **Vessel Availability**: UNAVAILABLE/SCARCE (+2 score), MEDIUM (+1 score).
4. **Cargo Urgency**: URGENT/CRITICAL (+2 score).
5. **Decision Margin**: Financial savings < $5,000 or < 2% (+1 score).
6. **Wait Duration**: Long horizon (>= 30 days) when waiting (+1 score).

---

## 7. Public API Entry Point

```python
from smartfreight_ais.cost_decision_engine import run_cost_charter_decision

result = run_cost_charter_decision(
    forecast_data=forecast_payload,      # From Member 2
    vessel_data=vessel_payload,          # From Member 3
    bridge_payload=bridge_payload,       # From Member 4
    cargo=cargo_requirements,            # Business Input
    assumptions=custom_assumptions,      # Configurable Assumptions (Optional)
    forecast_horizon_days=14,            # 7, 14, or 30 days
    voyage_duration_days=5.0,
    vessel_availability="AVAILABLE"
)

# Export to dictionary / JSON
output_dict = result.to_dict()
```

---

## 8. Example Output Schema

```json
{
  "recommendation": "WAIT",
  "contract_type": "SHORT_TERM",
  "financial_analysis": {
    "charter_now_cost_usd": 286160.0,
    "expected_wait_cost_usd": 273500.0,
    "expected_saving_usd": 12660.0,
    "expected_saving_pct": 4.42
  },
  "market_analysis": {
    "current_freight_rate_usd_day": 22832.0,
    "selected_forecast_rate_usd_day": 19500.0,
    "selected_forecast_horizon_days": 14,
    "market_direction": "DECLINING"
  },
  "operational_analysis": {
    "expected_waiting_time_hours": 18.0,
    "expected_turnaround_time_hours": 30.0,
    "port_congestion_level": "MODERATE",
    "vessel_availability": "AVAILABLE",
    "distance_to_port_nm": 420.0,
    "risk_factors": ["Moderate port congestion (MODERATE)"]
  },
  "cargo_analysis": {
    "cargo_quantity_mt": 75000.0,
    "urgency": "NORMAL",
    "recurring": false,
    "required_by_date": "2026-11-15",
    "planned_voyages": 1
  },
  "risk": "LOW",
  "reason": "WAIT — forecasted freight rate decline yields total estimated savings of $12,660.00 (4.42%) after accounting for market waiting costs.",
  "now_cost_breakdown": {
    "freight_cost_usd": 114160.0,
    "fuel_cost_usd": 150000.0,
    "port_cost_usd": 5000.0,
    "waiting_cost_usd": 15000.0,
    "other_voyage_cost_usd": 2000.0,
    "total_voyage_cost_usd": 286160.0
  },
  "wait_cost_breakdown": {
    "freight_cost_usd": 97500.0,
    "fuel_cost_usd": 150000.0,
    "port_cost_usd": 5000.0,
    "waiting_cost_usd": 29000.0,
    "other_voyage_cost_usd": 2000.0,
    "market_waiting_cost_usd": 14000.0,
    "total_voyage_cost_usd": 273500.0
  },
  "assumptions": {
    "bunker_price_usd_per_mt": 600.0,
    "fuel_consumption_mt_per_day": 50.0,
    "port_cost_usd": 5000.0,
    "other_voyage_cost_usd": 2000.0,
    "waiting_cost_multiplier": 1.0,
    "market_wait_cost_usd_per_day": 1000.0,
    "minimum_wait_saving_usd": 1000.0,
    "minimum_wait_saving_pct": 1.0
  }
}
```
