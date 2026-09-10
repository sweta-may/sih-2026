"""
Tests for the Member 5 Cost & Charter Decision Engine.
"""

from datetime import date

from smartfreight_ais.cost_decision_engine import (
    FreightForecastInput,
    VesselPlanInput,
    OperationalInput,
    CargoRequirement,
    CostAssumptions,
    DecisionRequest,
    calculate_voyage_cost,
    calculate_wait_cost,
    compare_charter_now_vs_wait,
    build_decision_request_from_member5_bridge,
    build_freight_forecast_input,
    build_vessel_plan_input,
)


def create_test_request():
    """
    Create a deterministic test scenario.
    """

    freight = FreightForecastInput(
        current_rate_usd_day=22000.0,
        forecast_7d_usd_day=21000.0,
        forecast_14d_usd_day=20000.0,
        forecast_30d_usd_day=19000.0,
    )

    vessel = VesselPlanInput(
        vessel_class="Panamax",
        dwt_mt=82500.0,
        voyages=1,
        cargo_per_voyage_mt=50000.0,
        capacity_utilization_pct=90.0,
    )

    operations = OperationalInput(
        distance_to_port_nm=100.0,
        voyage_duration_days=10.0,
        expected_waiting_time_hours=12.0,
        expected_turnaround_time_hours=24.0,
        total_idle_impact_usd=8000.0,
        port_congestion_level="MEDIUM",
        vessel_availability="MEDIUM",
    )

    cargo = CargoRequirement(
        cargo_quantity_mt=50000.0,
        required_by_date=date(2026, 10, 1),
        urgency="NORMAL",
        recurring=False,
        planned_voyages=1,
    )

    assumptions = CostAssumptions(
        bunker_price_usd_per_mt=600.0,
        fuel_consumption_mt_per_day=25.0,
        port_cost_usd=5000.0,
        other_voyage_cost_usd=2000.0,
        waiting_cost_multiplier=1.0,
        market_wait_cost_usd_per_day=1000.0,
    )

    return DecisionRequest(
        freight=freight,
        vessel=vessel,
        operations=operations,
        cargo=cargo,
        assumptions=assumptions,
    )


# ============================================================
# TOTAL VOYAGE COST
# ============================================================

def test_total_voyage_cost():

    request = create_test_request()

    result = calculate_voyage_cost(
        freight_rate_usd_day=22000.0,
        vessel=request.vessel,
        operations=request.operations,
        assumptions=request.assumptions,
    )

    # --------------------------------------------------------
    # Freight
    #
    # 22,000 × 10 × 1
    # --------------------------------------------------------

    assert result.freight_cost_usd == 220000.0

    # --------------------------------------------------------
    # Fuel
    #
    # 25 × 10 × 600 × 1
    # --------------------------------------------------------

    assert result.fuel_cost_usd == 150000.0

    # --------------------------------------------------------
    # Port
    # --------------------------------------------------------

    assert result.port_cost_usd == 5000.0

    # --------------------------------------------------------
    # Waiting / idle
    # --------------------------------------------------------

    assert result.waiting_cost_usd == 8000.0

    # --------------------------------------------------------
    # Other
    # --------------------------------------------------------

    assert result.other_voyage_cost_usd == 2000.0

    # --------------------------------------------------------
    # Total
    #
    # 220,000
    # +150,000
    # +  5,000
    # +  8,000
    # +  2,000
    # =385,000
    # --------------------------------------------------------

    assert result.total_voyage_cost_usd == 385000.0


# ============================================================
# WAIT COST
# ============================================================

def test_wait_cost():

    request = create_test_request()

    result = calculate_wait_cost(
        forecast_rate_usd_day=20000.0,
        forecast_horizon_days=14,
        vessel=request.vessel,
        operations=request.operations,
        assumptions=request.assumptions,
    )

    # Future freight:
    #
    # 20,000 × 10 = 200,000

    assert result.freight_cost_usd == 200000.0

    # Fuel remains:
    #
    # 25 × 10 × 600 = 150,000

    assert result.fuel_cost_usd == 150000.0

    # Market waiting:
    #
    # 14 × 1,000 = 14,000
    #
    # Existing idle cost:
    # 8,000
    #
    # Total waiting component:
    # 22,000

    assert result.waiting_cost_usd == 22000.0

    # Total:
    #
    # 200,000
    # +150,000
    # +  5,000
    # + 22,000
    # +  2,000
    # =379,000

    assert result.total_voyage_cost_usd == 379000.0


# ============================================================
# CHARTER NOW VS WAIT
# ============================================================

def test_wait_is_selected_when_future_cost_is_lower():

    request = create_test_request()

    result = compare_charter_now_vs_wait(
        request=request,
        forecast_horizon_days=14,
    )

    assert result.recommendation == "WAIT"

    assert result.charter_now_cost_usd == 385000.0

    assert result.expected_wait_cost_usd == 379000.0

    assert result.expected_saving_usd == 6000.0


def test_charter_now_is_selected_when_future_cost_is_higher():

    request = create_test_request()

    # Change the forecast so that waiting becomes expensive.
    request.freight.forecast_14d_usd_day = 25000.0

    result = compare_charter_now_vs_wait(
        request=request,
        forecast_horizon_days=14,
    )

    assert result.recommendation == "CHARTER_NOW"

    assert result.charter_now_cost_usd == 385000.0

    assert result.expected_wait_cost_usd == 429000.0

    assert result.expected_saving_usd == 44000.0


# ============================================================
# FORECAST VALIDATION
# ============================================================

def test_missing_forecast_is_rejected():

    request = create_test_request()

    request.freight.forecast_14d_usd_day = None

    try:

        compare_charter_now_vs_wait(
            request=request,
            forecast_horizon_days=14,
        )

        assert False, "Expected ValueError"

    except ValueError:
        pass


def test_invalid_forecast_horizon_is_rejected():

    request = create_test_request()

    try:

        compare_charter_now_vs_wait(
            request=request,
            forecast_horizon_days=10,
        )

        assert False, "Expected ValueError"

    except ValueError:
        pass


# ============================================================
# INPUT VALIDATION
# ============================================================

def test_negative_freight_rate_is_rejected():

    try:

        FreightForecastInput(
            current_rate_usd_day=-100.0
        )

        assert False, "Expected ValueError"

    except ValueError:
        pass


def test_invalid_vessel_dwt_is_rejected():

    try:

        VesselPlanInput(
            vessel_class="Panamax",
            dwt_mt=0,
        )

        assert False, "Expected ValueError"

    except ValueError:
        pass


def test_invalid_voyage_duration_is_rejected():

    request = create_test_request()

    request.operations.voyage_duration_days = 0

    try:

        calculate_voyage_cost(
            freight_rate_usd_day=22000.0,
            vessel=request.vessel,
            operations=request.operations,
            assumptions=request.assumptions,
        )

        assert False, "Expected ValueError"

    except ValueError:
        pass


# ============================================================
# MEMBER 4 / AIS BRIDGE INTEGRATION TEST
# ============================================================

def test_build_decision_request_from_member5_bridge():
    """
    Verify conversion of Member 4 AIS bridge payload to DecisionRequest.
    """
    bridge_payload = {
        "vessel_class": "Panamax",
        "distance_to_port_nm": 420.0,
        "expected_waiting_time_hours": 18.0,
        "expected_turnaround_time_hours": 30.0,
        "total_idle_impact_usd": 15000.0,
        "port_congestion_level": "HIGH",
    }

    freight = FreightForecastInput(
        current_rate_usd_day=22832.0,
        forecast_7d_usd_day=22000.0,
        forecast_14d_usd_day=21500.0,
        forecast_30d_usd_day=21000.0,
    )

    cargo = CargoRequirement(
        cargo_quantity_mt=75000.0,
        required_by_date=date(2026, 10, 1),
        urgency="NORMAL",
        recurring=False,
        planned_voyages=1,
    )

    assumptions = CostAssumptions(
        bunker_price_usd_per_mt=600.0,
        fuel_consumption_mt_per_day=50.0,
        port_cost_usd=25000.0,
        other_voyage_cost_usd=10000.0,
        waiting_cost_multiplier=1.0,
        market_wait_cost_usd_per_day=5000.0,
    )

    request = build_decision_request_from_member5_bridge(
        bridge_payload=bridge_payload,
        freight=freight,
        cargo=cargo,
        assumptions=assumptions,
        dwt_mt=82000.0,
        voyage_duration_days=5.0,
    )

    assert request.vessel.vessel_class == "Panamax"
    assert request.vessel.dwt_mt == 82000.0
    assert request.vessel.voyages == 1
    assert request.operations.distance_to_port_nm == 420.0
    assert request.operations.expected_waiting_time_hours == 18.0
    assert request.operations.expected_turnaround_time_hours == 30.0
    assert request.operations.total_idle_impact_usd == 15000.0
    assert request.operations.port_congestion_level == "HIGH"


# ============================================================
# FREIGHT FORECASTING ADAPTER TESTS
# ============================================================

def test_build_freight_forecast_input_from_nested_api_payload():
    """
    Verify conversion of Member 2 /forecast JSON response.
    """
    payload = {
        "vessel_type": "Panamax",
        "current_date": "2026-09-08",
        "current_rate_usd_day": 22832.0,
        "forecast": {
            "7_days": {
                "forecast_rate_usd_day": 22000.0,
                "change_percent_vs_current": -3.64,
            },
            "14_days": {
                "forecast_rate_usd_day": 21500.0,
                "change_percent_vs_current": -5.83,
            },
            "30_days": {
                "forecast_rate_usd_day": 21000.0,
                "change_percent_vs_current": -8.02,
            },
        },
        "recommended_entry_window": "30_days",
        "market_entry_signal": "WAIT",
        "model": "Random Forest",
    }

    result = build_freight_forecast_input(payload)
    assert result.current_rate_usd_day == 22832.0
    assert result.forecast_7d_usd_day == 22000.0
    assert result.forecast_14d_usd_day == 21500.0
    assert result.forecast_30d_usd_day == 21000.0


def test_build_freight_forecast_input_from_flat_dict():
    """
    Verify conversion of flat dictionary with forecast rates.
    """
    payload = {
        "current_rate_usd_day": 25000.0,
        "forecast_7d_usd_day": 24000.0,
        "forecast_14d_usd_day": 23000.0,
        "forecast_30d_usd_day": 22000.0,
    }

    result = build_freight_forecast_input(payload)
    assert result.current_rate_usd_day == 25000.0
    assert result.forecast_7d_usd_day == 24000.0
    assert result.forecast_14d_usd_day == 23000.0
    assert result.forecast_30d_usd_day == 22000.0


def test_build_freight_forecast_input_from_instance():
    """
    Verify that passing an existing FreightForecastInput returns it unchanged.
    """
    original = FreightForecastInput(
        current_rate_usd_day=20000.0,
        forecast_7d_usd_day=19500.0,
    )
    result = build_freight_forecast_input(original)
    assert result is original


def test_build_freight_forecast_input_missing_current_rate():
    """
    Verify rejection if current rate is missing.
    """
    try:
        build_freight_forecast_input({"forecast_7d_usd_day": 20000.0})
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_build_freight_forecast_input_negative_rate():
    """
    Verify rejection if any rate is negative.
    """
    try:
        build_freight_forecast_input({
            "current_rate_usd_day": -500.0,
        })
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ============================================================
# VESSEL OPTIMIZATION ADAPTER TESTS
# ============================================================

def test_build_vessel_plan_input_from_nested_rec():
    """
    Verify conversion of Member 3 optimization dictionary with nested recommendation.
    """
    payload = {
        "status": "OPTIMAL",
        "recommendation": {
            "vessel_class": "Panamax",
            "dwt_mt": 82500.0,
            "voyages": 2,
            "cargo_per_voyage_mt": 40000.0,
            "capacity_utilization_pct": 95.0,
        }
    }

    result = build_vessel_plan_input(payload)
    assert result.vessel_class == "Panamax"
    assert result.dwt_mt == 82500.0
    assert result.voyages == 2
    assert result.cargo_per_voyage_mt == 40000.0
    assert result.capacity_utilization_pct == 95.0


def test_build_vessel_plan_input_from_flat_dict():
    """
    Verify conversion of flat vessel plan dictionary.
    """
    payload = {
        "vessel_class": "Capesize",
        "dwt_mt": 180000.0,
        "voyages": 1,
        "capacity_utilization_pct": 92.0,
    }

    result = build_vessel_plan_input(payload, cargo_quantity_mt=150000.0)
    assert result.vessel_class == "Capesize"
    assert result.dwt_mt == 180000.0
    assert result.voyages == 1
    assert result.cargo_per_voyage_mt == 150000.0
    assert result.capacity_utilization_pct == 92.0


def test_build_vessel_plan_input_from_instance():
    """
    Verify that passing an existing VesselPlanInput returns it unchanged.
    """
    original = VesselPlanInput(
        vessel_class="Supramax",
        dwt_mt=58000.0,
        voyages=1,
    )
    result = build_vessel_plan_input(original)
    assert result is original


def test_build_vessel_plan_input_missing_vessel_class():
    """
    Verify rejection if vessel class is missing.
    """
    try:
        build_vessel_plan_input({"dwt_mt": 50000.0})
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_build_vessel_plan_input_missing_dwt():
    """
    Verify rejection if DWT is missing.
    """
    try:
        build_vessel_plan_input({"vessel_class": "Panamax"})
        assert False, "Expected ValueError"
    except ValueError:
        pass

