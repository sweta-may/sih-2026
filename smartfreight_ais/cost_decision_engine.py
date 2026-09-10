"""
SmartFreight AI - Cost Optimization & Charter Decision Engine

Member 5:
    Cost Optimization and Charter Decision

Purpose
-------
This module provides the financial foundation for the Member 5
decision engine.

It currently supports:

1. Total voyage cost calculation
2. Charter Now cost calculation
3. Wait-for-better-market cost calculation
4. Financial comparison between the two scenarios
5. Initial qualitative risk assessment

The module is designed to consume outputs from:

    - Freight forecasting
    - Vessel optimization
    - AIS / ETA monitoring
    - Waiting-time prediction
    - Port congestion analysis

Contract selection (Spot / Short-term / Medium-term Multiple-voyage)
and advanced decision rules will be added in later stages.

All monetary values are represented in USD.

IMPORTANT
---------
The values inside CostAssumptions are prototype/configurable assumptions.
They are NOT claimed to be live market values.
They should be replaced with approved project/market assumptions later.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Tuple, Union


# ============================================================
# INPUT MODELS
# ============================================================

@dataclass
class FreightForecastInput:
    """
    Current and forecasted freight market rates.

    Freight rates are expected in USD/day.
    """

    current_rate_usd_day: float

    forecast_7d_usd_day: Optional[float] = None
    forecast_14d_usd_day: Optional[float] = None
    forecast_30d_usd_day: Optional[float] = None

    def __post_init__(self):
        if self.current_rate_usd_day < 0:
            raise ValueError(
                "current_rate_usd_day cannot be negative"
            )

        for field_name in (
            "forecast_7d_usd_day",
            "forecast_14d_usd_day",
            "forecast_30d_usd_day",
        ):
            value = getattr(self, field_name)

            if value is not None and value < 0:
                raise ValueError(
                    f"{field_name} cannot be negative"
                )


def build_freight_forecast_input(
    forecast_data: Union[dict, FreightForecastInput]
) -> FreightForecastInput:
    """
    Convert Member 2 freight forecasting output into a FreightForecastInput.

    Supports both nested Member 2 API dictionary responses (e.g. from /forecast)
    and flat dictionaries.
    """
    if isinstance(forecast_data, FreightForecastInput):
        return forecast_data

    if not isinstance(forecast_data, dict):
        raise ValueError(
            "forecast_data must be a dictionary or FreightForecastInput"
        )

    # 1. Extract current rate
    current_rate = forecast_data.get("current_rate_usd_day")
    if current_rate is None:
        current_rate = forecast_data.get("current_rate")
    if current_rate is None:
        raise ValueError(
            "Missing required freight rate field: current_rate_usd_day"
        )

    current_rate = float(current_rate)

    # 2. Extract 7d, 14d, 30d forecasts from nested "forecast" dict or flat keys
    f_dict = forecast_data.get("forecast", {})
    if isinstance(f_dict, dict):
        f7 = f_dict.get("7_days") or f_dict.get("7d") or f_dict.get(7)
        f7_rate = (
            f7.get("forecast_rate_usd_day", f7.get("forecast_rate"))
            if isinstance(f7, dict) else f7
        )

        f14 = f_dict.get("14_days") or f_dict.get("14d") or f_dict.get(14)
        f14_rate = (
            f14.get("forecast_rate_usd_day", f14.get("forecast_rate"))
            if isinstance(f14, dict) else f14
        )

        f30 = f_dict.get("30_days") or f_dict.get("30d") or f_dict.get(30)
        f30_rate = (
            f30.get("forecast_rate_usd_day", f30.get("forecast_rate"))
            if isinstance(f30, dict) else f30
        )
    else:
        f7_rate = None
        f14_rate = None
        f30_rate = None

    if f7_rate is None:
        f7_rate = forecast_data.get("forecast_7d_usd_day") or forecast_data.get("forecast_7d")
    if f14_rate is None:
        f14_rate = forecast_data.get("forecast_14d_usd_day") or forecast_data.get("forecast_14d")
    if f30_rate is None:
        f30_rate = forecast_data.get("forecast_30d_usd_day") or forecast_data.get("forecast_30d")

    return FreightForecastInput(
        current_rate_usd_day=current_rate,
        forecast_7d_usd_day=float(f7_rate) if f7_rate is not None else None,
        forecast_14d_usd_day=float(f14_rate) if f14_rate is not None else None,
        forecast_30d_usd_day=float(f30_rate) if f30_rate is not None else None,
    )



@dataclass
class VesselPlanInput:
    """
    Economically relevant output from the vessel optimization module.

    The vessel optimization module determines which vessel is
    operationally suitable. Member 5 uses that result for cost
    calculations.
    """

    vessel_class: str
    dwt_mt: float

    voyages: int = 1
    cargo_per_voyage_mt: Optional[float] = None
    capacity_utilization_pct: Optional[float] = None

    def __post_init__(self):
        if not self.vessel_class:
            raise ValueError(
                "vessel_class is required"
            )

        if self.dwt_mt <= 0:
            raise ValueError(
                "dwt_mt must be greater than zero"
            )

        if self.voyages < 1:
            raise ValueError(
                "voyages must be at least 1"
            )

        if (
            self.cargo_per_voyage_mt is not None
            and self.cargo_per_voyage_mt <= 0
        ):
            raise ValueError(
                "cargo_per_voyage_mt must be greater than zero"
            )

        if self.capacity_utilization_pct is not None:
            if not 0 <= self.capacity_utilization_pct <= 100:
                raise ValueError(
                    "capacity_utilization_pct must be between 0 and 100"
                )


def build_vessel_plan_input(
    vessel_data: Union[dict, VesselPlanInput],
    cargo_quantity_mt: Optional[float] = None,
) -> VesselPlanInput:
    """
    Convert Member 3 vessel optimization output into a VesselPlanInput.

    Supports both nested Member 3 optimization dictionary responses
    and flat dictionaries.
    """
    if isinstance(vessel_data, VesselPlanInput):
        return vessel_data

    if not isinstance(vessel_data, dict):
        raise ValueError(
            "vessel_data must be a dictionary or VesselPlanInput"
        )

    # If nested in "recommendation" or similar key
    rec = vessel_data.get("recommendation")
    source = rec if isinstance(rec, dict) else vessel_data

    vessel_class = (
        source.get("vessel_class")
        or source.get("recommended_vessel_type")
        or source.get("vessel_type")
    )
    if not vessel_class:
        raise ValueError("Missing required vessel field: vessel_class")

    dwt_mt = source.get("dwt_mt")
    if dwt_mt is None and isinstance(source.get("vessel_capacity"), dict):
        dwt_mt = source["vessel_capacity"].get("nominal_dwt_mt")
    if dwt_mt is None:
        raise ValueError("Missing required vessel field: dwt_mt")

    voyages = (
        source.get("voyages")
        or source.get("total_voyages")
        or (
            source.get("voyage_split_recommendation", {}).get("total_voyages")
            if isinstance(source.get("voyage_split_recommendation"), dict)
            else None
        )
        or 1
    )

    cargo_per_voyage_mt = (
        source.get("cargo_per_voyage_mt")
        or (
            source.get("voyage_split_recommendation", {}).get("cargo_per_voyage_mt")
            if isinstance(source.get("voyage_split_recommendation"), dict)
            else None
        )
    )
    if (
        cargo_per_voyage_mt is None
        and cargo_quantity_mt is not None
        and int(voyages) > 0
    ):
        cargo_per_voyage_mt = float(cargo_quantity_mt) / int(voyages)

    capacity_utilization_pct = (
        source.get("capacity_utilization_pct")
        or (
            source.get("voyage_split_recommendation", {}).get(
                "capacity_utilization_pct"
            )
            if isinstance(source.get("voyage_split_recommendation"), dict)
            else None
        )
    )

    return VesselPlanInput(
        vessel_class=str(vessel_class),
        dwt_mt=float(dwt_mt),
        voyages=int(voyages),
        cargo_per_voyage_mt=(
            float(cargo_per_voyage_mt)
            if cargo_per_voyage_mt is not None
            else None
        ),
        capacity_utilization_pct=(
            float(capacity_utilization_pct)
            if capacity_utilization_pct is not None
            else None
        ),
    )


@dataclass
class OperationalInput:
    """
    Operational information supplied by the AIS, ETA,
    waiting-time and congestion modules.
    """

    distance_to_port_nm: Optional[float] = None

    voyage_duration_days: Optional[float] = None

    expected_waiting_time_hours: float = 0.0

    expected_turnaround_time_hours: Optional[float] = None

    # Output from the existing idle_cost_engine.py
    total_idle_impact_usd: float = 0.0

    port_congestion_level: str = "UNKNOWN"

    vessel_availability: str = "UNKNOWN"

    def __post_init__(self):
        if (
            self.distance_to_port_nm is not None
            and self.distance_to_port_nm < 0
        ):
            raise ValueError(
                "distance_to_port_nm cannot be negative"
            )

        if (
            self.voyage_duration_days is not None
            and self.voyage_duration_days <= 0
        ):
            raise ValueError(
                "voyage_duration_days must be greater than zero"
            )

        if self.expected_waiting_time_hours < 0:
            raise ValueError(
                "expected_waiting_time_hours cannot be negative"
            )

        if (
            self.expected_turnaround_time_hours is not None
            and self.expected_turnaround_time_hours < 0
        ):
            raise ValueError(
                "expected_turnaround_time_hours cannot be negative"
            )

        if self.total_idle_impact_usd < 0:
            raise ValueError(
                "total_idle_impact_usd cannot be negative"
            )


@dataclass
class CargoRequirement:
    """
    Business requirement for the cargo shipment.

    This information will become more important during the
    contract-selection and cargo-urgency stages.
    """

    cargo_quantity_mt: float

    required_by_date: Optional[date] = None

    urgency: str = "NORMAL"

    recurring: bool = False

    planned_voyages: int = 1

    def __post_init__(self):
        if self.cargo_quantity_mt <= 0:
            raise ValueError(
                "cargo_quantity_mt must be greater than zero"
            )

        if self.planned_voyages < 1:
            raise ValueError(
                "planned_voyages must be at least 1"
            )


@dataclass
class CostAssumptions:
    """
    Configurable economic assumptions.

    All monetary values are in USD.

    These values are prototype assumptions only.
    They must be replaceable without changing the decision logic.
    """

    # --------------------------------------------------------
    # Fuel / bunker assumptions
    # --------------------------------------------------------

    bunker_price_usd_per_mt: float = 600.0

    fuel_consumption_mt_per_day: float = 25.0

    # --------------------------------------------------------
    # Port and miscellaneous costs
    # --------------------------------------------------------

    port_cost_usd: float = 5000.0

    other_voyage_cost_usd: float = 2000.0

    # --------------------------------------------------------
    # Existing waiting / idle cost treatment
    # --------------------------------------------------------

    waiting_cost_multiplier: float = 1.0

    # --------------------------------------------------------
    # Economic cost of deliberately waiting for a future
    # freight-market condition.
    #
    # This is different from port waiting / idle cost.
    # --------------------------------------------------------

    market_wait_cost_usd_per_day: float = 1000.0

    # --------------------------------------------------------
    # Minimum savings threshold to justify waiting uncertainty
    # --------------------------------------------------------

    minimum_wait_saving_usd: float = 1000.0

    minimum_wait_saving_pct: float = 1.0

    def __post_init__(self):
        if self.bunker_price_usd_per_mt < 0:
            raise ValueError(
                "bunker_price_usd_per_mt cannot be negative"
            )

        if self.fuel_consumption_mt_per_day < 0:
            raise ValueError(
                "fuel_consumption_mt_per_day cannot be negative"
            )

        if self.port_cost_usd < 0:
            raise ValueError(
                "port_cost_usd cannot be negative"
            )

        if self.other_voyage_cost_usd < 0:
            raise ValueError(
                "other_voyage_cost_usd cannot be negative"
            )

        if self.waiting_cost_multiplier < 0:
            raise ValueError(
                "waiting_cost_multiplier cannot be negative"
            )

        if self.market_wait_cost_usd_per_day < 0:
            raise ValueError(
                "market_wait_cost_usd_per_day cannot be negative"
            )

        if self.minimum_wait_saving_usd < 0:
            raise ValueError(
                "minimum_wait_saving_usd cannot be negative"
            )

        if self.minimum_wait_saving_pct < 0:
            raise ValueError(
                "minimum_wait_saving_pct cannot be negative"
            )


@dataclass
class DecisionRequest:
    """
    Complete normalized input contract for Member 5.
    """

    freight: FreightForecastInput

    vessel: VesselPlanInput

    operations: OperationalInput

    cargo: CargoRequirement

    assumptions: CostAssumptions = field(
        default_factory=CostAssumptions
    )


# ============================================================
# OUTPUT MODELS
# ============================================================

@dataclass
class CostBreakdown:
    """
    Detailed voyage-cost breakdown.

    Formula:

        Total =
            Freight
            + Fuel
            + Port
            + Waiting/Idle
            + Other
            + Market Waiting (if wait scenario)
    """

    freight_cost_usd: float = 0.0

    fuel_cost_usd: float = 0.0

    port_cost_usd: float = 0.0

    waiting_cost_usd: float = 0.0

    other_voyage_cost_usd: float = 0.0

    market_waiting_cost_usd: float = 0.0

    total_voyage_cost_usd: float = 0.0


@dataclass
class DecisionResult:
    """
    Final structured output from the Member 5
    cost optimization and charter decision engine.
    """

    # --------------------------------------------------------
    # Decision & Contract
    # --------------------------------------------------------

    recommendation: str

    contract_type: Optional[str]

    # --------------------------------------------------------
    # Financial comparison
    # --------------------------------------------------------

    charter_now_cost_usd: float

    expected_wait_cost_usd: float

    expected_saving_usd: float

    # --------------------------------------------------------
    # Risk & Explanation
    # --------------------------------------------------------

    risk: str

    reason: str

    # --------------------------------------------------------
    # Market information
    # --------------------------------------------------------

    current_freight_rate_usd_day: float

    selected_forecast_rate_usd_day: Optional[float]

    selected_forecast_horizon_days: Optional[int]

    # --------------------------------------------------------
    # Cost details
    # --------------------------------------------------------

    now_cost_breakdown: CostBreakdown

    # --------------------------------------------------------
    # Fields with default values
    # --------------------------------------------------------

    expected_saving_pct: float = 0.0

    market_direction: str = "UNKNOWN"

    wait_cost_breakdown: Optional[CostBreakdown] = None

    # --------------------------------------------------------
    # Additional analysis
    # --------------------------------------------------------

    operational_analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    cargo_analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    assumptions_used: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DecisionResult into a JSON-friendly dictionary.
        """

        now_dict = _cost_breakdown_to_dict(self.now_cost_breakdown)
        wait_dict = (
            _cost_breakdown_to_dict(self.wait_cost_breakdown)
            if self.wait_cost_breakdown
            else None
        )

        return {
            "recommendation": self.recommendation,

            "contract_type": self.contract_type,

            "financial_analysis": {
                "charter_now_cost_usd":
                    self.charter_now_cost_usd,

                "expected_wait_cost_usd":
                    self.expected_wait_cost_usd,

                "expected_saving_usd":
                    self.expected_saving_usd,

                "expected_saving_pct":
                    round(self.expected_saving_pct, 2),
            },

            "market_analysis": {
                "current_freight_rate_usd_day":
                    self.current_freight_rate_usd_day,

                "selected_forecast_rate_usd_day":
                    self.selected_forecast_rate_usd_day,

                "selected_forecast_horizon_days":
                    self.selected_forecast_horizon_days,

                "market_direction":
                    self.market_direction,
            },

            "operational_analysis":
                self.operational_analysis,

            "cargo_analysis":
                self.cargo_analysis,

            "risk": self.risk,

            "reason": self.reason,

            "now_cost_breakdown": now_dict,

            "wait_cost_breakdown": wait_dict,

            "assumptions":
                self.assumptions_used,
        }


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _cost_breakdown_to_dict(
    breakdown: CostBreakdown,
) -> Dict[str, float]:
    """
    Convert a CostBreakdown object to a JSON-friendly dictionary.
    """

    res = {
        "freight_cost_usd":
            breakdown.freight_cost_usd,

        "fuel_cost_usd":
            breakdown.fuel_cost_usd,

        "port_cost_usd":
            breakdown.port_cost_usd,

        "waiting_cost_usd":
            breakdown.waiting_cost_usd,

        "other_voyage_cost_usd":
            breakdown.other_voyage_cost_usd,
    }

    if breakdown.market_waiting_cost_usd > 0:
        res["market_waiting_cost_usd"] = breakdown.market_waiting_cost_usd

    res["total_voyage_cost_usd"] = breakdown.total_voyage_cost_usd
    return res


# ============================================================
# COST CALCULATION
# ============================================================

def calculate_voyage_cost(
    freight_rate_usd_day: float,
    vessel: VesselPlanInput,
    operations: OperationalInput,
    assumptions: CostAssumptions,
) -> CostBreakdown:
    """
    Calculate estimated total voyage cost.

    Formula:

        Total Voyage Cost =
            Freight Cost
            + Fuel Cost
            + Port Cost
            + Waiting / Idle Cost
            + Other Voyage Cost

    Freight Cost:

        freight_rate × voyage_duration × number_of_voyages

    Fuel Cost:

        fuel_consumption_per_day
        × voyage_duration
        × bunker_price
        × number_of_voyages

    Port Cost:

        port_cost × number_of_voyages

    Waiting Cost:

        existing idle impact × waiting multiplier

    Other Cost:

        other_voyage_cost × number_of_voyages

    Notes
    -----
    `operations.total_idle_impact_usd` is expected to come from
    the existing Member 4 idle-cost calculation.

    Intentional market waiting is NOT included here.
    It is handled separately by calculate_wait_cost().
    """

    if freight_rate_usd_day < 0:
        raise ValueError(
            "freight_rate_usd_day cannot be negative"
        )
    if operations.voyage_duration_days is None:
        raise ValueError(
            "voyage_duration_days is required"
        )
    if operations.voyage_duration_days <= 0:
        raise ValueError(
            "voyage_duration_days must be greater than zero"
        )
    voyage_days = operations.voyage_duration_days

    # --------------------------------------------------------
    # 1. Freight cost
    # --------------------------------------------------------

    freight_cost = (
        freight_rate_usd_day
        * voyage_days
        * vessel.voyages
    )

    # --------------------------------------------------------
    # 2. Fuel / bunker cost
    # --------------------------------------------------------

    fuel_cost = (
        assumptions.fuel_consumption_mt_per_day
        * voyage_days
        * assumptions.bunker_price_usd_per_mt
        * vessel.voyages
    )

    # --------------------------------------------------------
    # 3. Port cost
    # --------------------------------------------------------

    port_cost = (
        assumptions.port_cost_usd
        * vessel.voyages
    )

    # --------------------------------------------------------
    # 4. Waiting / idle cost
    # --------------------------------------------------------

    waiting_cost = (
        operations.total_idle_impact_usd
        * assumptions.waiting_cost_multiplier
    )

    # --------------------------------------------------------
    # 5. Other voyage costs
    # --------------------------------------------------------

    other_cost = (
        assumptions.other_voyage_cost_usd
        * vessel.voyages
    )

    # --------------------------------------------------------
    # 6. Total
    # --------------------------------------------------------

    total_cost = (
        freight_cost
        + fuel_cost
        + port_cost
        + waiting_cost
        + other_cost
    )

    return CostBreakdown(
        freight_cost_usd=round(
            freight_cost,
            2,
        ),

        fuel_cost_usd=round(
            fuel_cost,
            2,
        ),

        port_cost_usd=round(
            port_cost,
            2,
        ),

        waiting_cost_usd=round(
            waiting_cost,
            2,
        ),

        other_voyage_cost_usd=round(
            other_cost,
            2,
        ),

        total_voyage_cost_usd=round(
            total_cost,
            2,
        ),
    )


def calculate_wait_cost(
    forecast_rate_usd_day: float,
    forecast_horizon_days: int,
    vessel: VesselPlanInput,
    operations: OperationalInput,
    assumptions: CostAssumptions,
) -> CostBreakdown:
    """
    Estimate the total cost if the charter decision is delayed.

    The future voyage is priced using the forecasted freight rate.

    In addition, an economic cost is applied for deliberately
    waiting for the selected forecast horizon.

    Formula:

        Expected Wait Cost =
            Future Voyage Cost
            + Market Waiting Cost

    where:

        Market Waiting Cost =
            forecast_horizon_days
            × market_wait_cost_usd_per_day
    """

    if forecast_rate_usd_day < 0:
        raise ValueError(
            "forecast_rate_usd_day cannot be negative"
        )

    if forecast_horizon_days <= 0:
        raise ValueError(
            "forecast_horizon_days must be greater than zero"
        )

    # --------------------------------------------------------
    # Calculate future voyage using forecasted freight rate
    # --------------------------------------------------------

    future_cost = calculate_voyage_cost(
        freight_rate_usd_day=forecast_rate_usd_day,
        vessel=vessel,
        operations=operations,
        assumptions=assumptions,
    )

    # --------------------------------------------------------
    # Cost of intentionally delaying the charter decision
    # --------------------------------------------------------

    market_wait_cost = (
        forecast_horizon_days
        * assumptions.market_wait_cost_usd_per_day
    )

    # --------------------------------------------------------
    # Total expected wait cost
    # --------------------------------------------------------

    total_wait_cost = (
        future_cost.total_voyage_cost_usd
        + market_wait_cost
    )

    return CostBreakdown(
        freight_cost_usd=(
            future_cost.freight_cost_usd
        ),

        fuel_cost_usd=(
            future_cost.fuel_cost_usd
        ),

        port_cost_usd=(
            future_cost.port_cost_usd
        ),

        waiting_cost_usd=round(
            future_cost.waiting_cost_usd
            + market_wait_cost,
            2,
        ),

        other_voyage_cost_usd=(
            future_cost.other_voyage_cost_usd
        ),

        market_waiting_cost_usd=round(
            market_wait_cost,
            2,
        ),

        total_voyage_cost_usd=round(
            total_wait_cost,
            2,
        ),
    )


# ============================================================
# FORECAST SELECTION
# ============================================================

def get_forecast_rate(
    freight: FreightForecastInput,
    horizon_days: int,
) -> Optional[float]:
    """
    Return the forecasted freight rate for a selected horizon.

    Supported horizons:
        7 days
        14 days
        30 days
    """

    forecast_map = {
        7: freight.forecast_7d_usd_day,
        14: freight.forecast_14d_usd_day,
        30: freight.forecast_30d_usd_day,
    }

    if horizon_days not in forecast_map:
        raise ValueError(
            "Forecast horizon must be one of: 7, 14, 30 days"
        )

    return forecast_map[horizon_days]


# ============================================================
# CONTRACT TYPE RECOMMENDATION
# ============================================================

def recommend_contract_type(
    request: DecisionRequest,
    decision: str,
    forecast_rate: float,
    forecast_horizon_days: int = 14,
) -> str:
    """
    Recommend contract type based on cargo recurrence, voyage plan,
    market direction, urgency, and vessel availability.

    Options:
        - MEDIUM_TERM: Recurring cargo, multiple voyages, or rising freight market.
        - SHORT_TERM: Single/few voyages with moderate planning horizon (7-14 days).
        - SPOT: Non-recurring, immediate single voyage, or urgent cargo.
    """

    cargo = request.cargo
    vessel = request.vessel

    # Multi-voyage or recurring requirement strongly favors medium-term commitment
    if cargo.recurring or cargo.planned_voyages > 1 or vessel.voyages > 1:
        return "MEDIUM_TERM"

    # Urgent requirement necessitates spot chartering
    if cargo.urgency in ("URGENT", "CRITICAL"):
        return "SPOT"

    # If decision is CHARTER_NOW in an upward trending market or longer horizon
    if (
        decision == "CHARTER_NOW"
        and forecast_rate > request.freight.current_rate_usd_day * 1.05
    ):
        return "SHORT_TERM"

    if forecast_horizon_days <= 7:
        return "SPOT"

    return "SHORT_TERM"


# ============================================================
# RISK ASSESSMENT
# ============================================================

def determine_initial_risk(
    freight: FreightForecastInput,
    operations: OperationalInput,
    expected_saving: float,
) -> str:
    """
    Determine a qualitative risk level (backward-compatible).
    """

    risk_score = 0

    if (
        freight.forecast_7d_usd_day is not None
        and freight.forecast_14d_usd_day is not None
    ):
        short_rate = freight.forecast_7d_usd_day
        medium_rate = freight.forecast_14d_usd_day

        rate_change = (
            abs(medium_rate - short_rate)
            / max(short_rate, 1.0)
        )

        if rate_change > 0.10:
            risk_score += 2
        elif rate_change > 0.05:
            risk_score += 1

    congestion = operations.port_congestion_level.upper().strip()
    if congestion in {"HIGH", "SEVERE", "CRITICAL"}:
        risk_score += 2
    elif congestion in {"MEDIUM", "MODERATE"}:
        risk_score += 1

    availability = operations.vessel_availability.upper().strip()
    if availability in {"LOW", "SCARCE", "UNAVAILABLE"}:
        risk_score += 2
    elif availability in {"MEDIUM", "MODERATE"}:
        risk_score += 1

    if abs(expected_saving) < 5000:
        risk_score += 1

    if risk_score >= 4:
        return "HIGH"
    if risk_score >= 2:
        return "MEDIUM"
    return "LOW"


def determine_risk_level(
    request: DecisionRequest,
    expected_saving_usd: float,
    expected_saving_pct: float,
    decision: str,
    forecast_horizon_days: int = 14,
) -> Tuple[str, List[str]]:
    """
    Assess multi-factor operational and financial risk.

    Factors:
        1. Forecast volatility
        2. Port congestion
        3. Vessel availability
        4. Cargo urgency & delivery deadline
        5. Decision margin sensitivity
        6. Wait horizon duration
    """

    risk_score = 0
    risk_factors: List[str] = []

    freight = request.freight
    operations = request.operations
    cargo = request.cargo

    # 1. Freight forecast volatility
    if (
        freight.forecast_7d_usd_day is not None
        and freight.forecast_14d_usd_day is not None
    ):
        short_rate = freight.forecast_7d_usd_day
        medium_rate = freight.forecast_14d_usd_day
        rate_change = abs(medium_rate - short_rate) / max(short_rate, 1.0)
        if rate_change > 0.10:
            risk_score += 2
            risk_factors.append(
                f"High freight rate volatility ({rate_change * 100:.1f}%)"
            )
        elif rate_change > 0.05:
            risk_score += 1
            risk_factors.append(
                f"Moderate freight rate volatility ({rate_change * 100:.1f}%)"
            )

    # 2. Port congestion
    congestion = operations.port_congestion_level.upper().strip()
    if congestion in {"HIGH", "SEVERE", "CRITICAL"}:
        risk_score += 2
        risk_factors.append(f"High port congestion ({congestion})")
    elif congestion in {"MEDIUM", "MODERATE"}:
        risk_score += 1
        risk_factors.append(f"Moderate port congestion ({congestion})")

    # 3. Vessel availability
    availability = operations.vessel_availability.upper().strip()
    if availability in {"LOW", "SCARCE", "UNAVAILABLE"}:
        risk_score += 2
        risk_factors.append(
            f"Limited vessel availability ({availability})"
        )
    elif availability in {"MEDIUM", "MODERATE"}:
        risk_score += 1
        risk_factors.append(
            f"Moderate vessel availability ({availability})"
        )

    # 4. Cargo urgency
    if cargo.urgency in {"URGENT", "CRITICAL"}:
        risk_score += 2
        risk_factors.append(f"High cargo urgency ({cargo.urgency})")

    # 5. Small financial difference / margin sensitivity
    if abs(expected_saving_usd) < 5000 or abs(expected_saving_pct) < 2.0:
        risk_score += 1
        risk_factors.append(
            "Narrow financial margin sensitive to forecast deviations"
        )

    # 6. Long wait horizon
    if decision == "WAIT" and forecast_horizon_days >= 30:
        risk_score += 1
        risk_factors.append(
            f"Extended wait horizon ({forecast_horizon_days} days) increases market exposure"
        )

    if risk_score >= 4:
        level = "HIGH"
    elif risk_score >= 2:
        level = "MEDIUM"
    else:
        level = "LOW"

    return level, risk_factors


# ============================================================
# CHARTER NOW VS WAIT
# ============================================================

def compare_charter_now_vs_wait(
    request: DecisionRequest,
    forecast_horizon_days: int = 14,
) -> DecisionResult:
    """
    Comprehensive financial and operational comparison between
    chartering now and waiting for a future forecast horizon.
    """

    freight = request.freight
    vessel = request.vessel
    operations = request.operations
    cargo = request.cargo
    assumptions = request.assumptions

    # 1. Calculate current charter cost
    now_cost = calculate_voyage_cost(
        freight_rate_usd_day=freight.current_rate_usd_day,
        vessel=vessel,
        operations=operations,
        assumptions=assumptions,
    )

    # 2. Retrieve selected forecast
    forecast_rate = get_forecast_rate(
        freight=freight,
        horizon_days=forecast_horizon_days,
    )

    if forecast_rate is None:
        raise ValueError(
            f"No freight forecast is available for "
            f"{forecast_horizon_days}-day horizon"
        )

    # 3. Calculate expected cost after waiting
    wait_cost = calculate_wait_cost(
        forecast_rate_usd_day=forecast_rate,
        forecast_horizon_days=forecast_horizon_days,
        vessel=vessel,
        operations=operations,
        assumptions=assumptions,
    )

    # 4. Market direction
    if forecast_rate < freight.current_rate_usd_day:
        market_direction = "DECLINING"
    elif forecast_rate > freight.current_rate_usd_day:
        market_direction = "RISING"
    else:
        market_direction = "STABLE"

    # 5. Financial comparison
    wait_advantage = (
        now_cost.total_voyage_cost_usd
        - wait_cost.total_voyage_cost_usd
    )

    saving_pct = (
        (abs(wait_advantage) / max(now_cost.total_voyage_cost_usd, 1.0))
        * 100.0
    )

    # 6. Operational constraints & decision synthesis
    is_financially_better_to_wait = wait_advantage > 0
    meets_savings_threshold = (
        wait_advantage >= assumptions.minimum_wait_saving_usd
        and saving_pct >= assumptions.minimum_wait_saving_pct
    )

    urgency_override = cargo.urgency.upper() in ("URGENT", "CRITICAL")
    scarcity_override = operations.vessel_availability.upper() in (
        "UNAVAILABLE", "SCARCE"
    )
    congestion_override = operations.port_congestion_level.upper() in (
        "CRITICAL", "SEVERE"
    )

    # Delivery deadline violation check (for urgent or deadline-constrained cargo)
    deadline_override = False
    if (
        cargo.required_by_date is not None
        and cargo.urgency.upper() in ("URGENT", "CRITICAL", "HIGH", "STRICT")
    ):
        voyage_days = operations.voyage_duration_days or 5.0
        days_needed = forecast_horizon_days + voyage_days
        days_available = (cargo.required_by_date - date.today()).days
        if days_available > 0 and days_needed > days_available:
            deadline_override = True

    if is_financially_better_to_wait:
        if not meets_savings_threshold:
            recommendation = "CHARTER_NOW"
            expected_saving = abs(wait_advantage)
            reason = (
                f"CHARTER_NOW — although freight rates are forecast to decline, "
                f"the expected savings of ${expected_saving:,.2f} ({saving_pct:.2f}%) "
                f"do not exceed the minimum threshold required to justify waiting uncertainty."
            )
        elif urgency_override:
            recommendation = "CHARTER_NOW"
            expected_saving = abs(wait_advantage)
            reason = (
                f"CHARTER_NOW — although waiting is financially cheaper by ${expected_saving:,.2f}, "
                f"high cargo urgency ({cargo.urgency}) requires immediate chartering."
            )
        elif deadline_override:
            recommendation = "CHARTER_NOW"
            expected_saving = abs(wait_advantage)
            reason = (
                f"CHARTER_NOW — waiting {forecast_horizon_days} days would risk missing the "
                f"required cargo delivery deadline ({cargo.required_by_date})."
            )
        elif scarcity_override:
            recommendation = "CHARTER_NOW"
            expected_saving = abs(wait_advantage)
            reason = (
                f"CHARTER_NOW — scarce vessel availability ({operations.vessel_availability}) "
                f"presents operational risk of losing tonnage if chartering is delayed."
            )
        elif congestion_override:
            recommendation = "CHARTER_NOW"
            expected_saving = abs(wait_advantage)
            reason = (
                f"CHARTER_NOW — critical port congestion ({operations.port_congestion_level}) "
                f"favors securing the voyage slot immediately rather than waiting."
            )
        else:
            recommendation = "WAIT"
            expected_saving = wait_advantage
            reason = (
                f"WAIT — forecasted freight rate decline yields total estimated savings of "
                f"${expected_saving:,.2f} ({saving_pct:.2f}%) after accounting for market waiting costs."
            )
    else:
        recommendation = "CHARTER_NOW"
        expected_saving = abs(wait_advantage)
        reason = (
            f"CHARTER_NOW — chartering now is expected to be more economical than waiting approximately "
            f"{forecast_horizon_days} days by ${expected_saving:,.2f}."
        )

    # 7. Contract recommendation
    contract_type = recommend_contract_type(
        request=request,
        decision=recommendation,
        forecast_rate=forecast_rate,
        forecast_horizon_days=forecast_horizon_days,
    )

    # 8. Risk assessment
    risk_level, risk_factors = determine_risk_level(
        request=request,
        expected_saving_usd=expected_saving,
        expected_saving_pct=saving_pct,
        decision=recommendation,
        forecast_horizon_days=forecast_horizon_days,
    )

    return DecisionResult(
        recommendation=recommendation,
        contract_type=contract_type,
        charter_now_cost_usd=round(
            now_cost.total_voyage_cost_usd, 2
        ),
        expected_wait_cost_usd=round(
            wait_cost.total_voyage_cost_usd, 2
        ),
        expected_saving_usd=round(
            expected_saving, 2
        ),
        expected_saving_pct=round(
            saving_pct, 2
        ),
        risk=risk_level,
        reason=reason,
        current_freight_rate_usd_day=freight.current_rate_usd_day,
        selected_forecast_rate_usd_day=forecast_rate,
        selected_forecast_horizon_days=forecast_horizon_days,
        market_direction=market_direction,
        now_cost_breakdown=now_cost,
        wait_cost_breakdown=wait_cost,
        operational_analysis={
            "expected_waiting_time_hours":
                operations.expected_waiting_time_hours,
            "expected_turnaround_time_hours":
                operations.expected_turnaround_time_hours,
            "port_congestion_level":
                operations.port_congestion_level,
            "vessel_availability":
                operations.vessel_availability,
            "distance_to_port_nm":
                operations.distance_to_port_nm,
            "risk_factors":
                risk_factors,
        },
        cargo_analysis={
            "cargo_quantity_mt": cargo.cargo_quantity_mt,
            "urgency": cargo.urgency,
            "recurring": cargo.recurring,
            "required_by_date": (
                str(cargo.required_by_date)
                if cargo.required_by_date
                else None
            ),
            "planned_voyages": cargo.planned_voyages,
        },
        assumptions_used={
            "bunker_price_usd_per_mt":
                assumptions.bunker_price_usd_per_mt,
            "fuel_consumption_mt_per_day":
                assumptions.fuel_consumption_mt_per_day,
            "port_cost_usd":
                assumptions.port_cost_usd,
            "other_voyage_cost_usd":
                assumptions.other_voyage_cost_usd,
            "waiting_cost_multiplier":
                assumptions.waiting_cost_multiplier,
            "market_wait_cost_usd_per_day":
                assumptions.market_wait_cost_usd_per_day,
            "minimum_wait_saving_usd":
                assumptions.minimum_wait_saving_usd,
            "minimum_wait_saving_pct":
                assumptions.minimum_wait_saving_pct,
        },
    )


# ============================================================
# MEMBER 4 / AIS BRIDGE ADAPTER
# ============================================================

def build_decision_request_from_member5_bridge(
    bridge_payload: dict,
    freight: FreightForecastInput,
    cargo: CargoRequirement,
    assumptions: CostAssumptions,
    dwt_mt: float,
    voyage_duration_days: float,
    voyages: int = 1,
    capacity_utilization_pct: float = 100.0,
    vessel_availability: str = "AVAILABLE",
) -> DecisionRequest:
    """
    Convert the existing Member 4 -> Member 5 bridge payload
    into a DecisionRequest for the Cost & Charter Decision Engine.
    """

    if not isinstance(bridge_payload, dict):
        raise ValueError(
            "bridge_payload must be a dictionary"
        )

    required_fields = [
        "vessel_class",
        "distance_to_port_nm",
        "expected_waiting_time_hours",
        "expected_turnaround_time_hours",
        "total_idle_impact_usd",
        "port_congestion_level",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in bridge_payload
    ]

    if missing_fields:
        raise ValueError(
            "Missing required Member 5 bridge fields: "
            + ", ".join(missing_fields)
        )

    if dwt_mt <= 0:
        raise ValueError(
            "dwt_mt must be greater than zero"
        )

    if voyage_duration_days <= 0:
        raise ValueError(
            "voyage_duration_days must be greater than zero"
        )

    if voyages <= 0:
        raise ValueError(
            "voyages must be greater than zero"
        )

    operations = OperationalInput(
        distance_to_port_nm=float(
            bridge_payload["distance_to_port_nm"]
        ),
        voyage_duration_days=float(
            voyage_duration_days
        ),
        expected_waiting_time_hours=float(
            bridge_payload["expected_waiting_time_hours"]
        ),
        expected_turnaround_time_hours=float(
            bridge_payload["expected_turnaround_time_hours"]
        ),
        total_idle_impact_usd=float(
            bridge_payload["total_idle_impact_usd"]
        ),
        port_congestion_level=str(
            bridge_payload["port_congestion_level"]
        ),
        vessel_availability=str(
            vessel_availability
        ),
    )

    vessel = VesselPlanInput(
        vessel_class=str(
            bridge_payload["vessel_class"]
        ),
        dwt_mt=float(dwt_mt),
        voyages=int(voyages),
        cargo_per_voyage_mt=float(
            cargo.cargo_quantity_mt / voyages
        ),
        capacity_utilization_pct=float(
            capacity_utilization_pct
        ),
    )

    return DecisionRequest(
        freight=freight,
        vessel=vessel,
        operations=operations,
        cargo=cargo,
        assumptions=assumptions,
    )


# ============================================================
# UNIFIED MEMBER 5 DECISION REQUEST BUILDER
# ============================================================

def build_member5_decision_request(
    forecast_data: Union[dict, FreightForecastInput],
    vessel_data: Union[dict, VesselPlanInput],
    bridge_payload: dict,
    cargo: Union[dict, CargoRequirement],
    assumptions: Optional[Union[dict, CostAssumptions]] = None,
    voyage_duration_days: Optional[float] = None,
    vessel_availability: str = "AVAILABLE",
) -> DecisionRequest:
    """
    Unified builder combining Freight Forecast (Member 2),
    Vessel Optimization (Member 3), AIS/ETA/Waiting Bridge (Member 4),
    Cargo Requirements, and Cost Assumptions into a normalized DecisionRequest.
    """

    # 1. Forecast
    freight_obj = build_freight_forecast_input(forecast_data)

    # 2. Cargo
    if isinstance(cargo, CargoRequirement):
        cargo_obj = cargo
    elif isinstance(cargo, dict):
        req_date = cargo.get("required_by_date")
        if isinstance(req_date, str):
            try:
                req_date = date.fromisoformat(req_date)
            except ValueError:
                req_date = None
        cargo_obj = CargoRequirement(
            cargo_quantity_mt=float(cargo["cargo_quantity_mt"]),
            required_by_date=req_date,
            urgency=str(cargo.get("urgency", "NORMAL")),
            recurring=bool(cargo.get("recurring", False)),
            planned_voyages=int(cargo.get("planned_voyages", 1)),
        )
    else:
        raise ValueError(
            "cargo must be a dictionary or CargoRequirement"
        )

    # 3. Vessel
    vessel_obj = build_vessel_plan_input(
        vessel_data, cargo_quantity_mt=cargo_obj.cargo_quantity_mt
    )

    # 4. Assumptions
    if assumptions is None:
        assumptions_obj = CostAssumptions()
    elif isinstance(assumptions, CostAssumptions):
        assumptions_obj = assumptions
    elif isinstance(assumptions, dict):
        assumptions_obj = CostAssumptions(**assumptions)
    else:
        raise ValueError(
            "assumptions must be a dictionary or CostAssumptions"
        )

    # 5. Voyage duration fallback
    if voyage_duration_days is None or voyage_duration_days <= 0:
        voyage_duration_days = 5.0

    # 6. Assemble through bridge adapter
    return build_decision_request_from_member5_bridge(
        bridge_payload=bridge_payload,
        freight=freight_obj,
        cargo=cargo_obj,
        assumptions=assumptions_obj,
        dwt_mt=vessel_obj.dwt_mt,
        voyage_duration_days=voyage_duration_days,
        voyages=vessel_obj.voyages,
        capacity_utilization_pct=(
            vessel_obj.capacity_utilization_pct
            if vessel_obj.capacity_utilization_pct is not None
            else 100.0
        ),
        vessel_availability=vessel_availability,
    )


# ============================================================
# PUBLIC MEMBER 5 ENTRY POINT
# ============================================================

def run_cost_charter_decision(
    forecast_data: Union[dict, FreightForecastInput],
    vessel_data: Union[dict, VesselPlanInput],
    bridge_payload: dict,
    cargo: Union[dict, CargoRequirement],
    assumptions: Optional[Union[dict, CostAssumptions]] = None,
    forecast_horizon_days: int = 14,
    voyage_duration_days: Optional[float] = None,
    vessel_availability: str = "AVAILABLE",
) -> DecisionResult:
    """
    Main public entry point for Member 5: Cost Optimization & Charter Decision.

    Takes inputs across all project modules, evaluates total voyage economics,
    applies operational and cargo constraints, selects charter recommendation,
    suggests contract type, evaluates risk, and returns a structured DecisionResult.
    """

    request = build_member5_decision_request(
        forecast_data=forecast_data,
        vessel_data=vessel_data,
        bridge_payload=bridge_payload,
        cargo=cargo,
        assumptions=assumptions,
        voyage_duration_days=voyage_duration_days,
        vessel_availability=vessel_availability,
    )

    return compare_charter_now_vs_wait(
        request=request,
        forecast_horizon_days=forecast_horizon_days,
    )