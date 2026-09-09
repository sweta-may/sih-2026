import pandas as pd
from datetime import datetime, timezone

def generate_in_app_alerts(vessels_list: list, congestion_timetable: list) -> list:
    """
    Generates in-app notifications and alerts (No SMS/Email).
    """
    alerts = []
    
    # Port congestion alerts
    for port in congestion_timetable:
        if port["congestion_status"] in ["HIGH", "CRITICAL"]:
            alerts.append({
                "alert_id": f"ALT-CONG-{port['port_id']}",
                "level": "WARNING" if port["congestion_status"] == "HIGH" else "CRITICAL",
                "title": f"High Congestion Alert: {port['port_name']}",
                "message": f"Berth occupancy is at {port['berth_occupancy_pct']}% with {port['vessels_in_queue']} vessels in queue. Expect ~{port['avg_waiting_time_hours']}h delay.",
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M UTC")
            })

    # Vessel delay & idle cost alerts
    for v in vessels_list:
        delay = v.get("delay_hours", 0.0)
        idle_cost = v.get("estimated_idle_cost_usd", 0.0)
        if delay > 2.0 or idle_cost > 10000:
            alerts.append({
                "alert_id": f"ALT-VESSEL-{v.get('mmsi')}",
                "level": "IMPORTANT",
                "title": f"Delay & Idle Cost Risk: {v.get('vessel_name')}",
                "message": f"Vessel delayed by {delay:.1f} hrs to {v.get('destination')}. Estimated idle demurrage impact: ${idle_cost:,.2f}.",
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M UTC")
            })

    return alerts

def generate_idle_time_report_df(vessels_list: list) -> pd.DataFrame:
    """
    Generates downloadable pandas DataFrame report.
    """
    rows = []
    for v in vessels_list:
        rows.append({
            "MMSI": v.get("mmsi"),
            "Vessel Name": v.get("vessel_name"),
            "Vessel Class": v.get("vessel_class", "Panamax"),
            "Destination Port": v.get("destination"),
            "Speed (Knots)": v.get("speed_knots"),
            "Distance (NM)": v.get("distance_to_port_nm"),
            "Direct ETA": v.get("direct_eta_utc"),
            "Expected Waiting (hrs)": v.get("expected_waiting_time_hours"),
            "Expected Turnaround (hrs)": v.get("expected_turnaround_time_hours"),
            "Delay Status": v.get("delay_status", {}).get("description", "On Time"),
            "Estimated Idle Cost ($)": v.get("estimated_idle_cost_usd"),
            "Data Source": v.get("data_source", "PROTOTYPE_SIMULATED_AIS_STREAM")
        })
    return pd.DataFrame(rows)
