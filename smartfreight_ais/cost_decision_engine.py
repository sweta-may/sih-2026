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
from typing import Any, Dict, Optional


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
    """

    freight_cost_usd: float = 0.0

    fuel_cost_usd: float = 0.0

    port_cost_usd: float = 0.0

    waiting_cost_usd: float = 0.0

    other_voyage_cost_usd: float = 0.0

    total_voyage_cost_usd: float = 0.0


@dataclass
class DecisionResult:
    """
    Final structured output from the current Member 5
    financial decision layer.
    """

    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    recommendation: str

    # Contract selection will be added later.
    contract_type: Optional[str]

    # --------------------------------------------------------
    # Financial comparison
    # --------------------------------------------------------

    charter_now_cost_usd: float

    expected_wait_cost_usd: float

    expected_saving_usd: float

    # --------------------------------------------------------
    # Risk
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

    wait_cost_breakdown: Optional[CostBreakdown] = None

    # --------------------------------------------------------
    # Additional analysis
    # --------------------------------------------------------

    operational_analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    assumptions_used: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DecisionResult into a JSON-friendly dictionary.

        This will be useful later when the result is exposed
        through the API.
        """

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
            },

            "market_analysis": {
                "current_freight_rate_usd_day":
                    self.current_freight_rate_usd_day,

                "selected_forecast_rate_usd_day":
                    self.selected_forecast_rate_usd_day,

                "selected_forecast_horizon_days":
                    self.selected_forecast_horizon_days,
            },

            "now_cost_breakdown":
                _cost_breakdown_to_dict(
                    self.now_cost_breakdown
                ),

            "wait_cost_breakdown":
                (
                    _cost_breakdown_to_dict(
                        self.wait_cost_breakdown
                    )
                    if self.wait_cost_breakdown
                    else None
                ),

            "risk": self.risk,

            "reason": self.reason,

            "operational_analysis":
                self.operational_analysis,

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

    return {
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

        "total_voyage_cost_usd":
            breakdown.total_voyage_cost_usd,
    }


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
            "Forecast horizon must be one of: "
            "7, 14, 30 days"
        )

    return forecast_map[horizon_days]


# ============================================================
# RISK ASSESSMENT
# ============================================================

def determine_initial_risk(
    freight: FreightForecastInput,
    operations: OperationalInput,
    expected_saving: float,
) -> str:
    """
    Determine an initial qualitative risk level.

    Current risk factors:

        1. Freight forecast volatility
        2. Port congestion
        3. Vessel availability
        4. Small financial difference between scenarios

    This is intentionally an initial version.

    More advanced risk logic will be added when:
        - Forecast confidence becomes available
        - Cargo urgency is integrated
        - Vessel availability becomes quantitative
        - Contract risk is modeled
    """

    risk_score = 0

    # --------------------------------------------------------
    # 1. Freight forecast volatility
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 2. Port congestion
    # --------------------------------------------------------

    congestion = (
        operations.port_congestion_level
        .upper()
        .strip()
    )

    if congestion in {
        "HIGH",
        "SEVERE",
        "CRITICAL",
    }:
        risk_score += 2

    elif congestion in {
        "MEDIUM",
        "MODERATE",
    }:
        risk_score += 1

    # --------------------------------------------------------
    # 3. Vessel availability
    # --------------------------------------------------------

    availability = (
        operations.vessel_availability
        .upper()
        .strip()
    )

    if availability in {
        "LOW",
        "SCARCE",
        "UNAVAILABLE",
    }:
        risk_score += 2

    elif availability in {
        "MEDIUM",
        "MODERATE",
    }:
        risk_score += 1

    # --------------------------------------------------------
    # 4. Decision sensitivity
    #
    # If the financial difference is very small, the decision
    # is sensitive to forecast errors.
    # --------------------------------------------------------

    if abs(expected_saving) < 5000:
        risk_score += 1

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if risk_score >= 4:
        return "HIGH"

    if risk_score >= 2:
        return "MEDIUM"

    return "LOW"


# ============================================================
# CHARTER NOW VS WAIT
# ============================================================

def compare_charter_now_vs_wait(
    request: DecisionRequest,
    forecast_horizon_days: int = 14,
) -> DecisionResult:
    """
    Compare the economics of chartering now against waiting
    for a selected forecast horizon.

    Current decision rule:

        If expected wait cost < charter-now cost:
            WAIT

        Otherwise:
            CHARTER_NOW

    This function intentionally does NOT yet determine:

        - Spot contract
        - Short-term contract
        - Medium-term multiple-voyage contract

    Contract selection will be implemented in the next stage.
    """

    freight = request.freight

    vessel = request.vessel

    operations = request.operations

    assumptions = request.assumptions

    # --------------------------------------------------------
    # 1. Calculate current charter cost
    # --------------------------------------------------------

    now_cost = calculate_voyage_cost(
        freight_rate_usd_day=(
            freight.current_rate_usd_day
        ),

        vessel=vessel,

        operations=operations,

        assumptions=assumptions,
    )

    # --------------------------------------------------------
    # 2. Retrieve selected forecast
    # --------------------------------------------------------

    forecast_rate = get_forecast_rate(
        freight=freight,
        horizon_days=forecast_horizon_days,
    )

    if forecast_rate is None:
        raise ValueError(
            f"No freight forecast is available for "
            f"{forecast_horizon_days}-day horizon"
        )

    # --------------------------------------------------------
    # 3. Calculate expected cost after waiting
    # --------------------------------------------------------

    wait_cost = calculate_wait_cost(
        forecast_rate_usd_day=forecast_rate,

        forecast_horizon_days=forecast_horizon_days,

        vessel=vessel,

        operations=operations,

        assumptions=assumptions,
    )

    # --------------------------------------------------------
    # 4. Compare scenarios
    #
    # Positive value:
    #     Waiting is cheaper.
    #
    # Negative value:
    #     Chartering now is cheaper.
    # --------------------------------------------------------

    wait_advantage = (
        now_cost.total_voyage_cost_usd
        - wait_cost.total_voyage_cost_usd
    )

    if wait_advantage > 0:

        recommendation = "WAIT"

        expected_saving = wait_advantage

        reason = (
            f"Waiting approximately "
            f"{forecast_horizon_days} days is expected "
            f"to reduce the total estimated voyage cost."
        )

    else:

        recommendation = "CHARTER_NOW"

        expected_saving = abs(wait_advantage)

        reason = (
            f"Chartering now is expected to be more "
            f"economical than waiting approximately "
            f"{forecast_horizon_days} days."
        )

    # --------------------------------------------------------
    # 5. Initial risk assessment
    # --------------------------------------------------------

    risk = determine_initial_risk(
        freight=freight,

        operations=operations,

        expected_saving=expected_saving,
    )

    # --------------------------------------------------------
    # 6. Return structured result
    # --------------------------------------------------------

    return DecisionResult(
        recommendation=recommendation,

        # Contract selection is deliberately deferred.
        contract_type=None,

        charter_now_cost_usd=round(
            now_cost.total_voyage_cost_usd,
            2,
        ),

        expected_wait_cost_usd=round(
            wait_cost.total_voyage_cost_usd,
            2,
        ),

        expected_saving_usd=round(
            expected_saving,
            2,
        ),

        risk=risk,

        reason=reason,

        current_freight_rate_usd_day=(
            freight.current_rate_usd_day
        ),

        selected_forecast_rate_usd_day=(
            forecast_rate
        ),

        selected_forecast_horizon_days=(
            forecast_horizon_days
        ),

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

    This function acts as an adapter between the existing AIS/
    waiting-time pipeline and the Member 5 cost-decision engine.

    Existing bridge fields consumed:
        vessel_class
        distance_to_port_nm
        expected_waiting_time_hours
        expected_turnaround_time_hours
        total_idle_impact_usd
        port_congestion_level

    Additional vessel-planning information is supplied by the
    vessel-optimization output or caller.
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
            bridge_payload[
                "expected_waiting_time_hours"
            ]
        ),

        expected_turnaround_time_hours=float(
            bridge_payload[
                "expected_turnaround_time_hours"
            ]
        ),

        total_idle_impact_usd=float(
            bridge_payload[
                "total_idle_impact_usd"
            ]
        ),

        port_congestion_level=str(
            bridge_payload[
                "port_congestion_level"
            ]
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