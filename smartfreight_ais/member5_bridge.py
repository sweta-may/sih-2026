from datetime import datetime, timezone
from smartfreight_ais.vesselfinder_provider import VesselFinderAPIProvider
from smartfreight_ais.eta_engine import calculate_direct_eta, detect_delay_status
from smartfreight_ais.waiting_time_model import get_waiting_time_predictor
from smartfreight_ais.idle_cost_engine import calculate_idle_cost
from smartfreight_ais.congestion_engine import get_port_congestion_timetable

def export_to_member5(mmsi: int, vessel_class: str = "Panamax", cargo_mt: float = 75000.0) -> dict:
    """
    Standard integration contract payload passed from Member 4 to Member 5 (Cost & Decision Module).
    Payload Schema:
    - Vessel ETA
    - Expected port waiting time
    - Expected turnaround time
    - Delay status
    - Estimated idle cost
    """
    provider = VesselFinderAPIProvider()
    pos = provider.get_vessel_position(mmsi)

    lat = pos.get("lat", 19.5)
    lon = pos.get("lon", 85.5)
    speed = pos.get("speed_knots", 10.5)
    dest_port = pos.get("destination", "INPRD")

    # 1. ETA Calculation
    eta_res = calculate_direct_eta(lat, lon, dest_port, speed)
    direct_eta_utc = eta_res["direct_eta_utc"]

    # 2. Waiting Time & Turnaround ML Prediction
    predictor = get_waiting_time_predictor()
    wt_res = predictor.predict(dest_port, vessel_class, cargo_mt=cargo_mt)

    # Expected Arrival = Direct ETA + Waiting Time
    direct_eta_dt = eta_res["direct_eta_dt"]
    expected_arrival_dt = direct_eta_dt + __import__("datetime").timedelta(hours=wt_res["expected_waiting_time_hours"])
    expected_arrival_utc = expected_arrival_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 3. Delay Status
    delay_res = detect_delay_status(speed, direct_eta_utc=direct_eta_utc)

    # 4. Idle Cost Calculation
    idle_res = calculate_idle_cost(wt_res["expected_waiting_time_hours"], vessel_class)

    # 5. Port Congestion Context
    timetable = get_port_congestion_timetable()
    port_cong = next((p for p in timetable if p["port_id"] == dest_port), {"congestion_status": "MODERATE"})

    return {
        "mmsi": mmsi,
        "vessel_name": pos.get("vessel_name", f"MV Vessel {mmsi}"),
        "vessel_class": vessel_class,
        "destination_port": dest_port,
        "destination_port_name": eta_res["destination_port_name"],
        "distance_to_port_nm": eta_res["distance_to_port_nm"],

        # Required Member 5 Export Fields
        "vessel_eta": direct_eta_utc,
        "expected_arrival_utc": expected_arrival_utc,
        "expected_waiting_time_hours": wt_res["expected_waiting_time_hours"],
        "expected_waiting_time_days": wt_res["expected_waiting_time_days"],
        "expected_turnaround_time_hours": wt_res["expected_turnaround_time_hours"],
        "expected_turnaround_time_days": wt_res["expected_turnaround_time_days"],
        "delay_status": delay_res,
        "estimated_idle_cost_usd": idle_res["estimated_idle_cost_usd"],
        "bunker_idle_cost_usd": idle_res["bunker_idle_cost_usd"],
        "total_idle_impact_usd": idle_res["total_idle_impact_usd"],

        # Metadata
        "port_congestion_level": port_cong["congestion_status"],
        "data_source": pos.get("data_source", "PROTOTYPE_SIMULATED_AIS_STREAM"),
        "is_prototype_simulated": pos.get("is_simulated", True),
        "exported_at_utc": datetime.now(timezone.utc).isoformat()
    }
