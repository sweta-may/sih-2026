"""
Vessel Type Optimization Engine - Core Models
Member 3: Vessel Type Optimization (AI-Powered Bulk Cargo Chartering System)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class PortType(str, Enum):
    """Port operational infrastructure type."""
    BERTH = "BERTH"
    ANCHORAGE_LIGHTERAGE = "ANCHORAGE_LIGHTERAGE"


class RecommendationStatus(str, Enum):
    """Engine recommendation outcome status."""
    FEASIBLE_RECOMMENDATION = "FEASIBLE_RECOMMENDATION"
    NO_FEASIBLE_VESSEL = "NO_FEASIBLE_VESSEL"


@dataclass
class VesselClass:
    """Standard dry bulk benchmark vessel specification."""
    vessel_id: str
    vessel_class: str
    dwt_mt: float
    loa_m: float
    beam_m: float
    draft_m: float
    is_geared: bool = False
    cranes_info: str = ""
    reference_note: str = ""
    source: str = "Baltic Exchange"
    data_status: str = "REFERENCE_ACTUAL"


@dataclass
class PortConstraint:
    """Port operational and dimensional restrictions."""
    port_id: str
    port_name: str
    state: str
    country: str
    port_type: PortType = PortType.BERTH
    max_draft_m: Optional[float] = None
    max_loa_m: Optional[float] = None
    max_beam_m: Optional[float] = None
    cargo_capacity_mmtpa: Optional[float] = None
    allowed_cargo_types: List[str] = field(default_factory=lambda: ["Coal", "Iron Ore", "Limestone", "Bauxite", "Fertilizer", "General Bulk"])
    requires_geared_vessel: bool = False
    has_shore_cranes: bool = True
    constraint_note: str = ""
    source: str = ""
    data_status: str = "REFERENCE_ACTUAL"


@dataclass
class OptimizationConfig:
    """Configurable parameters for the optimization engine."""
    payload_factor: float = 0.95
    max_voyages: int = 3
    allow_voyage_split: bool = True

    def __post_init__(self):
        if not (0.50 <= self.payload_factor <= 1.0):
            raise ValueError(f"payload_factor must be between 0.50 and 1.00, got {self.payload_factor}")
        if self.max_voyages < 1:
            raise ValueError(f"max_voyages must be at least 1, got {self.max_voyages}")


@dataclass
class DimensionCheck:
    """Individual physical boundary check result."""
    metric_name: str
    vessel_value: float
    port_limit: Optional[float]
    bottleneck_port: str
    is_pass: bool
    margin_m: Optional[float] = None
    note: str = ""


@dataclass
class PortCompatibility:
    """Comprehensive port compatibility check covering both origin and destination."""
    origin_checks: List[DimensionCheck] = field(default_factory=list)
    dest_checks: List[DimensionCheck] = field(default_factory=list)
    cargo_handling_pass: bool = True
    cargo_handling_note: str = ""
    gear_requirement_pass: bool = True
    gear_requirement_note: str = ""
    is_compatible: bool = True
    rejection_reasons: List[str] = field(default_factory=list)


@dataclass
class VoyagePlan:
    """Voyage split and capacity utilization calculation."""
    num_voyages: int
    cargo_per_voyage_mt: float
    total_cargo_mt: float
    effective_payload_per_voyage_mt: float
    total_capacity_mt: float
    capacity_utilization_pct: float
    deadfreight_mt: float
    is_within_max_voyages: bool = True
    note: str = ""


@dataclass
class VesselEvaluation:
    """Evaluation result for a specific candidate vessel class."""
    vessel_class: VesselClass
    is_eligible: bool
    port_compatibility: PortCompatibility
    rejection_reasons: List[str] = field(default_factory=list)
    voyage_plans: List[VoyagePlan] = field(default_factory=list)
    best_voyage_plan: Optional[VoyagePlan] = None
    ranking_score: float = 0.0
    rank_rationale: str = ""


@dataclass
class GoverningBottlenecks:
    """Identified governing restrictions across origin and destination ports."""
    governing_draft_m: Optional[float]
    draft_bottleneck_port: str
    governing_loa_m: Optional[float]
    loa_bottleneck_port: str
    governing_beam_m: Optional[float]
    beam_bottleneck_port: str


@dataclass
class RecommendationResult:
    """Final output object of the vessel optimization engine."""
    status: RecommendationStatus
    cargo_quantity_mt: float
    cargo_type: str
    origin_port: PortConstraint
    dest_port: PortConstraint
    governing_bottlenecks: GoverningBottlenecks
    config: OptimizationConfig
    recommended_vessel: Optional[VesselClass] = None
    recommended_voyage_plan: Optional[VoyagePlan] = None
    candidate_evaluations: Dict[str, VesselEvaluation] = field(default_factory=dict)
    rejection_diagnostics: Dict[str, List[str]] = field(default_factory=dict)
    recommendation_summary: str = ""
    diagnostic_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to clean dictionary for JSON export."""
        rec_data = None
        draft_compat = None
        loa_compat = None
        beam_compat = None
        voyage_split_rec = None
        vessel_capacity = None

        if self.recommended_vessel and self.recommended_voyage_plan:
            draft_margin = (self.governing_bottlenecks.governing_draft_m - self.recommended_vessel.draft_m) if self.governing_bottlenecks.governing_draft_m is not None else None
            loa_margin = (self.governing_bottlenecks.governing_loa_m - self.recommended_vessel.loa_m) if self.governing_bottlenecks.governing_loa_m is not None else None
            beam_margin = (self.governing_bottlenecks.governing_beam_m - self.recommended_vessel.beam_m) if self.governing_bottlenecks.governing_beam_m is not None else None

            vessel_capacity = {
                "nominal_dwt_mt": self.recommended_vessel.dwt_mt,
                "effective_payload_per_voyage_mt": round(self.recommended_voyage_plan.effective_payload_per_voyage_mt, 2),
                "total_capacity_mt": round(self.recommended_voyage_plan.total_capacity_mt, 2),
                "payload_factor": self.config.payload_factor,
            }

            draft_compat = {
                "vessel_draft_m": self.recommended_vessel.draft_m,
                "governing_draft_m": self.governing_bottlenecks.governing_draft_m,
                "bottleneck_port": self.governing_bottlenecks.draft_bottleneck_port,
                "is_compatible": True,
                "clearance_margin_m": round(draft_margin, 2) if draft_margin is not None else None,
            }

            loa_compat = {
                "vessel_loa_m": self.recommended_vessel.loa_m,
                "governing_loa_m": self.governing_bottlenecks.governing_loa_m,
                "bottleneck_port": self.governing_bottlenecks.loa_bottleneck_port,
                "is_compatible": True,
                "clearance_margin_m": round(loa_margin, 2) if loa_margin is not None else None,
            }

            beam_compat = {
                "vessel_beam_m": self.recommended_vessel.beam_m,
                "governing_beam_m": self.governing_bottlenecks.governing_beam_m,
                "bottleneck_port": self.governing_bottlenecks.beam_bottleneck_port,
                "is_compatible": True,
                "clearance_margin_m": round(beam_margin, 2) if beam_margin is not None else None,
            }

            voyage_split_rec = {
                "total_voyages": self.recommended_voyage_plan.num_voyages,
                "cargo_per_voyage_mt": round(self.recommended_voyage_plan.cargo_per_voyage_mt, 2),
                "total_cargo_mt": round(self.recommended_voyage_plan.total_cargo_mt, 2),
                "capacity_utilization_pct": round(self.recommended_voyage_plan.capacity_utilization_pct, 2),
                "deadfreight_mt": round(self.recommended_voyage_plan.deadfreight_mt, 2),
                "note": self.recommended_voyage_plan.note,
            }

            rec_data = {
                "vessel_class": self.recommended_vessel.vessel_class,
                "recommended_vessel_type": self.recommended_vessel.vessel_class,
                "vessel_capacity": vessel_capacity,
                "dwt_mt": self.recommended_vessel.dwt_mt,
                "draft_compatibility": draft_compat,
                "loa_compatibility": loa_compat,
                "beam_compatibility": beam_compat,
                "voyage_split_recommendation": voyage_split_rec,
                "draft_m": self.recommended_vessel.draft_m,
                "loa_m": self.recommended_vessel.loa_m,
                "beam_m": self.recommended_vessel.beam_m,
                "is_geared": self.recommended_vessel.is_geared,
                "voyages": self.recommended_voyage_plan.num_voyages,
                "cargo_per_voyage_mt": round(self.recommended_voyage_plan.cargo_per_voyage_mt, 2),
                "capacity_utilization_pct": round(self.recommended_voyage_plan.capacity_utilization_pct, 2),
                "deadfreight_mt": round(self.recommended_voyage_plan.deadfreight_mt, 2),
            }

        evals_data = {}
        for name, ev in self.candidate_evaluations.items():
            all_checks = ev.port_compatibility.origin_checks + ev.port_compatibility.dest_checks
            draft_pass = all(c.is_pass for c in all_checks if c.metric_name == "Draft")
            loa_pass = all(c.is_pass for c in all_checks if c.metric_name == "LOA")
            beam_pass = all(c.is_pass for c in all_checks if c.metric_name == "Beam")

            evals_data[name] = {
                "vessel_class": ev.vessel_class.vessel_class,
                "dwt_mt": ev.vessel_class.dwt_mt,
                "is_eligible": ev.is_eligible,
                "rejection_reasons": ev.rejection_reasons,
                "draft_compatibility": {
                    "vessel_draft_m": ev.vessel_class.draft_m,
                    "is_pass": draft_pass,
                },
                "loa_compatibility": {
                    "vessel_loa_m": ev.vessel_class.loa_m,
                    "is_pass": loa_pass,
                },
                "beam_compatibility": {
                    "vessel_beam_m": ev.vessel_class.beam_m,
                    "is_pass": beam_pass,
                },
                "best_voyage_plan": {
                    "voyages": ev.best_voyage_plan.num_voyages,
                    "cargo_per_voyage_mt": round(ev.best_voyage_plan.cargo_per_voyage_mt, 2),
                    "capacity_utilization_pct": round(ev.best_voyage_plan.capacity_utilization_pct, 2),
                    "deadfreight_mt": round(ev.best_voyage_plan.deadfreight_mt, 2),
                } if ev.best_voyage_plan else None,
                "rank_rationale": ev.rank_rationale
            }

        return {
            "status": self.status.value,
            "cargo_quantity_mt": self.cargo_quantity_mt,
            "cargo_type": self.cargo_type,
            "origin_port": {
                "id": self.origin_port.port_id,
                "name": self.origin_port.port_name,
                "country": self.origin_port.country,
                "max_draft_m": self.origin_port.max_draft_m,
                "max_loa_m": self.origin_port.max_loa_m,
                "max_beam_m": self.origin_port.max_beam_m,
                "port_type": self.origin_port.port_type.value,
            },
            "dest_port": {
                "id": self.dest_port.port_id,
                "name": self.dest_port.port_name,
                "country": self.dest_port.country,
                "max_draft_m": self.dest_port.max_draft_m,
                "max_loa_m": self.dest_port.max_loa_m,
                "max_beam_m": self.dest_port.max_beam_m,
                "port_type": self.dest_port.port_type.value,
            },
            "governing_bottlenecks": {
                "draft_m": self.governing_bottlenecks.governing_draft_m,
                "draft_bottleneck_port": self.governing_bottlenecks.draft_bottleneck_port,
                "loa_m": self.governing_bottlenecks.governing_loa_m,
                "loa_bottleneck_port": self.governing_bottlenecks.loa_bottleneck_port,
                "beam_m": self.governing_bottlenecks.governing_beam_m,
                "beam_bottleneck_port": self.governing_bottlenecks.beam_bottleneck_port,
            },
            "configuration": {
                "payload_factor": self.config.payload_factor,
                "max_voyages": self.config.max_voyages,
            },
            "recommendation": rec_data,
            "rejection_diagnostics": self.rejection_diagnostics,
            "evaluations": evals_data,
            "summary": self.recommendation_summary,
            "diagnostic_explanation": self.diagnostic_explanation,
        }
