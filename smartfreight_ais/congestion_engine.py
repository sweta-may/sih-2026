import pandas as pd
from smartfreight_ais.db import load_congestion

def get_port_congestion_timetable() -> list:
    """
    Generates a port-wise congestion timetable across East Coast Indian ports.
    """
    df_c = load_congestion()
    if df_c.empty:
        # Static baseline
        return [
            {"port_id": "INPRD", "port_name": "Paradip", "berth_occupancy_pct": 68.5, "avg_waiting_time_hours": 11.8, "vessels_in_queue": 5, "congestion_status": "HIGH"},
            {"port_id": "INVTZ", "port_name": "Visakhapatnam", "berth_occupancy_pct": 62.0, "avg_waiting_time_hours": 8.6, "vessels_in_queue": 3, "congestion_status": "MODERATE"},
            {"port_id": "INGGV", "port_name": "Gangavaram", "berth_occupancy_pct": 48.0, "avg_waiting_time_hours": 5.1, "vessels_in_queue": 2, "congestion_status": "LOW"},
            {"port_id": "INGPR", "port_name": "Gopalpur", "berth_occupancy_pct": 41.0, "avg_waiting_time_hours": 3.8, "vessels_in_queue": 1, "congestion_status": "LOW"},
            {"port_id": "INDHM", "port_name": "Dhamra", "berth_occupancy_pct": 54.0, "avg_waiting_time_hours": 6.2, "vessels_in_queue": 2, "congestion_status": "MODERATE"},
            {"port_id": "INSAG", "port_name": "Sagar-Sandheads", "berth_occupancy_pct": 74.0, "avg_waiting_time_hours": 15.2, "vessels_in_queue": 6, "congestion_status": "HIGH"},
            {"port_id": "INHAL", "port_name": "Haldia", "berth_occupancy_pct": 82.5, "avg_waiting_time_hours": 19.4, "vessels_in_queue": 7, "congestion_status": "CRITICAL"},
        ]

    timetable = []
    for _, row in df_c.iterrows():
        occ = float(row.get("berth_occupancy_pct", 50.0))
        status = "CRITICAL" if occ >= 80.0 else ("HIGH" if occ >= 65.0 else ("MODERATE" if occ >= 50.0 else "LOW"))
        timetable.append({
            "port_id": row["port_id"],
            "port_name": row["port_name"],
            "berth_occupancy_pct": float(row.get("berth_occupancy_pct", 50.0)),
            "avg_waiting_time_hours": float(row.get("avg_waiting_time_hours", 8.0)),
            "avg_turnaround_time_hours": float(row.get("avg_turnaround_time_hours", 35.0)),
            "vessels_in_queue": int(row.get("vessels_in_queue", 2)),
            "congestion_status": status
        })
    return timetable
