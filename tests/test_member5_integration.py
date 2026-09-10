"""
End-to-end integration tests for Member 5:
Cost Optimization & Charter Decision Engine.
"""

from datetime import date, timedelta
import pytest

from smartfreight_ais.cost_decision_engine import (
    FreightForecastInput,
    VesselPlanInput,
    OperationalInput,
    CargoRequirement,
    CostAssumptions,
    DecisionRequest,
    build_member5_decision_request,
    run_cost_charter_decision,
    compare_charter_now_vs_wait,
    calculate_voyage_cost,
    calculate_wait_cost,
)


@pytest.fixture
def sample_bridge_payload():
    return {
        "mmsi": 211281610,
        "vessel_name": "MV Atlantic Trader",
        "vessel_class": "Panamax",
        "destination_port": "INPRD",
        "destination_port_name": "Paradip",
        "distance_to_port_nm": 450.0,
        "expected_waiting_time_hours": 16.0,
        "expected_waiting_time_days": 0.67,
        "expected_turnaround_time_hours": 28.0,
        "expected_turnaround_time_days": 1.17,
        "delay_status": {"is_delayed": False, "status": "ON_TIME"},
        "estimated_idle_cost_usd": 12000.0,
        "bunker_idle_cost_usd": 3000.0,
        "total_idle_impact_usd": 15000.0,
        "port_congestion_level": "MODERATE",
    }


@pytest.fixture
def sample_forecast_payload():
    return {
        "vessel_type": "Panamax",
        "current_date": "2026-09-08",
        "current_rate_usd_day": 23000.0,
        "forecast": {
            "7_days": {"forecast_rate_usd_day": 21000.0, "change_percent_vs_current": -8.7},
            "14_days": {"forecast_rate_usd_day": 19500.0, "change_percent_vs_current": -15.2},
            "30_days": {"forecast_rate_usd_day": 18000.0, "change_percent_vs_current": -21.7},
        },
        "recommended_entry_window": "30_days",
        "market_entry_signal": "WAIT",
    }


@pytest.fixture
def sample_vessel_payload():
    return {
        "status": "OPTIMAL",
        "recommendation": {
            "vessel_class": "Panamax",
            "dwt_mt": 82000.0,
            "voyages": 1,
            "cargo_per_voyage_mt": 75000.0,
            "capacity_utilization_pct": 91.5,
        }
    }


def test_case_1_future_cost_lower_unconstrained_recommends_wait(
    sample_forecast_payload, sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 1: Future freight rate is significantly lower, savings exceed threshold,
    and operational constraints are normal -> WAIT.
    """
    cargo = {
        "cargo_quantity_mt": 75000.0,
        "required_by_date": str(date.today() + timedelta(days=60)),
        "urgency": "NORMAL",
        "recurring": False,
        "planned_voyages": 1,
    }

    result = run_cost_charter_decision(
        forecast_data=sample_forecast_payload,
        vessel_data=sample_vessel_payload,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        forecast_horizon_days=14,
        voyage_duration_days=6.0,
        vessel_availability="AVAILABLE",
    )

    assert result.recommendation == "WAIT"
    assert result.expected_saving_usd > 0
    assert result.charter_now_cost_usd > result.expected_wait_cost_usd
    assert result.market_direction == "DECLINING"
    assert "WAIT" in result.reason
    assert result.contract_type in ("SHORT_TERM", "SPOT")


def test_case_2_current_cost_lower_recommends_charter_now(
    sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 2: Future freight rate is higher (rising market) -> CHARTER_NOW.
    """
    rising_forecast = {
        "current_rate_usd_day": 20000.0,
        "forecast_7d_usd_day": 22000.0,
        "forecast_14d_usd_day": 24000.0,
        "forecast_30d_usd_day": 26000.0,
    }

    cargo = {
        "cargo_quantity_mt": 75000.0,
        "urgency": "NORMAL",
    }

    result = run_cost_charter_decision(
        forecast_data=rising_forecast,
        vessel_data=sample_vessel_payload,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        forecast_horizon_days=14,
        voyage_duration_days=5.0,
    )

    assert result.recommendation == "CHARTER_NOW"
    assert result.market_direction == "RISING"
    assert result.expected_wait_cost_usd > result.charter_now_cost_usd
    assert "CHARTER_NOW" in result.reason


def test_case_3_urgent_cargo_overrides_financial_wait(
    sample_forecast_payload, sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 3: Future rate is cheaper, but cargo urgency is URGENT -> Override to CHARTER_NOW.
    """
    cargo = {
        "cargo_quantity_mt": 75000.0,
        "urgency": "URGENT",
        "recurring": False,
    }

    result = run_cost_charter_decision(
        forecast_data=sample_forecast_payload,
        vessel_data=sample_vessel_payload,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        forecast_horizon_days=14,
        voyage_duration_days=5.0,
    )

    assert result.recommendation == "CHARTER_NOW"
    assert "high cargo urgency" in result.reason.lower()
    assert result.contract_type == "SPOT"


def test_case_4_scarce_vessel_availability_overrides_wait(
    sample_forecast_payload, sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 4: Future rate is cheaper, but vessel availability is SCARCE -> Override to CHARTER_NOW.
    """
    cargo = {
        "cargo_quantity_mt": 75000.0,
        "urgency": "NORMAL",
    }

    result = run_cost_charter_decision(
        forecast_data=sample_forecast_payload,
        vessel_data=sample_vessel_payload,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        forecast_horizon_days=14,
        vessel_availability="SCARCE",
    )

    assert result.recommendation == "CHARTER_NOW"
    assert "scarce vessel availability" in result.reason.lower()


def test_case_5_recurring_cargo_multi_voyage_recommends_medium_term(
    sample_forecast_payload, sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 5: Recurring cargo with multiple voyages -> MEDIUM_TERM contract.
    """
    multi_voyage_vessel = {
        "recommendation": {
            "vessel_class": "Panamax",
            "dwt_mt": 82000.0,
            "voyages": 3,
            "cargo_per_voyage_mt": 70000.0,
            "capacity_utilization_pct": 95.0,
        }
    }

    cargo = {
        "cargo_quantity_mt": 210000.0,
        "urgency": "NORMAL",
        "recurring": True,
        "planned_voyages": 3,
    }

    result = run_cost_charter_decision(
        forecast_data=sample_forecast_payload,
        vessel_data=multi_voyage_vessel,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        forecast_horizon_days=14,
        voyage_duration_days=6.0,
    )

    assert result.contract_type == "MEDIUM_TERM"


def test_case_6_savings_below_threshold_recommends_charter_now(
    sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 6: Future saving is tiny (below configured minimum_wait_saving_usd) -> CHARTER_NOW.
    """
    marginal_forecast = {
        "current_rate_usd_day": 22000.0,
        "forecast_14d_usd_day": 19100.0,
    }

    cargo = {"cargo_quantity_mt": 75000.0, "urgency": "NORMAL"}
    assumptions = CostAssumptions(minimum_wait_saving_usd=1000.0)

    result = run_cost_charter_decision(
        forecast_data=marginal_forecast,
        vessel_data=sample_vessel_payload,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        assumptions=assumptions,
        forecast_horizon_days=14,
        voyage_duration_days=5.0,
    )

    assert result.recommendation == "CHARTER_NOW"
    assert "threshold" in result.reason.lower()


def test_case_7_missing_forecast_raises_error(
    sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 7: Missing freight rate forecast raises validation error.
    """
    invalid_forecast = {"vessel_type": "Panamax"}

    cargo = {"cargo_quantity_mt": 75000.0}

    with pytest.raises(ValueError):
        run_cost_charter_decision(
            forecast_data=invalid_forecast,
            vessel_data=sample_vessel_payload,
            bridge_payload=sample_bridge_payload,
            cargo=cargo,
        )


def test_case_8_full_json_serialization(
    sample_forecast_payload, sample_vessel_payload, sample_bridge_payload
):
    """
    CASE 8: Verify to_dict() contains all required top-level and nested structure.
    """
    cargo = {
        "cargo_quantity_mt": 75000.0,
        "required_by_date": "2026-11-15",
        "urgency": "NORMAL",
        "recurring": False,
        "planned_voyages": 1,
    }

    result = run_cost_charter_decision(
        forecast_data=sample_forecast_payload,
        vessel_data=sample_vessel_payload,
        bridge_payload=sample_bridge_payload,
        cargo=cargo,
        forecast_horizon_days=14,
        voyage_duration_days=5.0,
    )

    out = result.to_dict()

    # Required top-level keys
    assert "recommendation" in out
    assert "contract_type" in out
    assert "financial_analysis" in out
    assert "market_analysis" in out
    assert "operational_analysis" in out
    assert "cargo_analysis" in out
    assert "risk" in out
    assert "reason" in out
    assert "now_cost_breakdown" in out
    assert "wait_cost_breakdown" in out
    assert "assumptions" in out

    # Financial analysis fields
    assert "charter_now_cost_usd" in out["financial_analysis"]
    assert "expected_wait_cost_usd" in out["financial_analysis"]
    assert "expected_saving_usd" in out["financial_analysis"]
    assert "expected_saving_pct" in out["financial_analysis"]

    # Market analysis fields
    assert out["market_analysis"]["current_freight_rate_usd_day"] == 23000.0
    assert out["market_analysis"]["selected_forecast_rate_usd_day"] == 19500.0
    assert out["market_analysis"]["selected_forecast_horizon_days"] == 14
    assert out["market_analysis"]["market_direction"] == "DECLINING"

    # Breakdown fields
    assert "freight_cost_usd" in out["now_cost_breakdown"]
    assert "fuel_cost_usd" in out["now_cost_breakdown"]
    assert "total_voyage_cost_usd" in out["now_cost_breakdown"]
    assert "market_waiting_cost_usd" in out["wait_cost_breakdown"]
