"""
SmartFreight AI - Cost Optimization & Charter Decision Engine

Member 5:
    Cost Optimization and Charter Decision

This module defines the normalized input/output contract for the
economic decision layer.

The engine consumes outputs from:
    - Freight forecasting
    - Vessel optimization
    - AIS / ETA monitoring
    - Waiting-time prediction
    - Port congestion analysis

and eventually produces:
    - Total voyage cost
    - Charter Now vs Wait decision
    - Expected financial impact
    - Contract recommendation
    - Risk level

All monetary values are currently represented in USD.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Optional


# ============================================================
# INPUT MODELS
# ============================================================

@dataclass
class FreightForecastInput:
    """Current and forecasted freight market rates."""

    current_rate_usd_day: float

    forecast_7d_usd_day: Optional[float] = None
    forecast_14d_usd_day: Optional[float] = None
    forecast_30d_usd_day: Optional[float] = None

    def __post_init__(self):
        if self.current_rate_usd_day < 0:
            raise ValueError("current_rate_usd_day cannot be negative")


@dataclass
class VesselPlanInput:
    """Economically relevant output from vessel optimization."""

    vessel_class: str
    dwt_mt: float

    voyages: int = 1
    cargo_per_voyage_mt: Optional[float] = None
    capacity_utilization_pct: Optional[float] = None

    def __post_init__(self):
        if self.dwt_mt <= 0:
            raise ValueError("dwt_mt must be greater than zero")

        if self.voyages < 1:
            raise ValueError("voyages must be at least 1")

        if self.capacity_utilization_pct is not None:
            if not 0 <= self.capacity_utilization_pct <= 100:
                raise ValueError(
                    "capacity_utilization_pct must be between 0 and 100"
                )


@dataclass
class OperationalInput:
    """Operational information supplied by AIS / port modules."""

    distance_to_port_nm: Optional[float] = None
    voyage_duration_days: Optional[float] = None

    expected_waiting_time_hours: float = 0.0
    expected_turnaround_time_hours: Optional[float] = None

    total_idle_impact_usd: float = 0.0

    port_congestion_level: str = "UNKNOWN"
    vessel_availability: str = "UNKNOWN"

    def __post_init__(self):
        if self.distance_to_port_nm is not None:
            if self.distance_to_port_nm < 0:
                raise ValueError("distance_to_port_nm cannot be negative")

        if self.voyage_duration_days is not None:
            if self.voyage_duration_days <= 0:
                raise ValueError(
                    "voyage_duration_days must be greater than zero"
                )

        if self.expected_waiting_time_hours < 0:
            raise ValueError(
                "expected_waiting_time_hours cannot be negative"
            )

        if self.total_idle_impact_usd < 0:
            raise ValueError(
                "total_idle_impact_usd cannot be negative"
            )


@dataclass
class CargoRequirement:
    """Business requirement for the cargo shipment."""

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

    These are prototype assumptions and must be clearly documented
    and replaceable with approved project/market values.
    """

    bunker_price_usd_per_mt: float = 600.0

    fuel_consumption_mt_per_day: float = 25.0

    port_cost_usd: float = 5000.0

    other_voyage_cost_usd: float = 2000.0

    # Allows the waiting-cost treatment to be adjusted without
    # changing the decision engine itself.
    waiting_cost_multiplier: float = 1.0

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
    """Detailed voyage-cost breakdown."""

    freight_cost_usd: float = 0.0
    fuel_cost_usd: float = 0.0
    port_cost_usd: float = 0.0
    waiting_cost_usd: float = 0.0
    other_voyage_cost_usd: float = 0.0

    total_voyage_cost_usd: float = 0.0


@dataclass
class DecisionResult:
    """
    Final business decision returned by Member 5.
    """

    recommendation: str

    contract_type: Optional[str]

    charter_now_cost_usd: float

    expected_wait_cost_usd: float

    expected_saving_usd: float

    risk: str

    reason: str

    current_freight_rate_usd_day: float

    selected_forecast_rate_usd_day: Optional[float]

    selected_forecast_horizon_days: Optional[int]

    now_cost_breakdown: CostBreakdown

    wait_cost_breakdown: Optional[CostBreakdown] = None

    operational_analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    assumptions_used: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to JSON-friendly dictionary."""

        return {
            "recommendation": self.recommendation,
            "contract_type": self.contract_type,

            "financial_analysis": {
                "charter_now_cost_usd": self.charter_now_cost_usd,
                "expected_wait_cost_usd": self.expected_wait_cost_usd,
                "expected_saving_usd": self.expected_saving_usd,
            },

            "market_analysis": {
                "current_freight_rate_usd_day":
                    self.current_freight_rate_usd_day,

                "selected_forecast_rate_usd_day":
                    self.selected_forecast_rate_usd_day,

                "selected_forecast_horizon_days":
                    self.selected_forecast_horizon_days,
            },

            "now_cost_breakdown": {
                "freight_cost_usd":
                    self.now_cost_breakdown.freight_cost_usd,

                "fuel_cost_usd":
                    self.now_cost_breakdown.fuel_cost_usd,

                "port_cost_usd":
                    self.now_cost_breakdown.port_cost_usd,

                "waiting_cost_usd":
                    self.now_cost_breakdown.waiting_cost_usd,

                "other_voyage_cost_usd":
                    self.now_cost_breakdown.other_voyage_cost_usd,

                "total_voyage_cost_usd":
                    self.now_cost_breakdown.total_voyage_cost_usd,
            },

            "risk": self.risk,

            "reason": self.reason,

            "operational_analysis":
                self.operational_analysis,

            "assumptions":
                self.assumptions_used,
        }