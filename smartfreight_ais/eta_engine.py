import math
from datetime import datetime, timedelta, timezone

EAST_COAST_PORT_COORDS = {
    "INPRD": {"name": "Paradip", "lat": 20.266, "lon": 86.88},
    "INVTZ": {"name": "Visakhapatnam", "lat": 17.683, "lon": 83.216},
    "INGGV": {"name": "Gangavaram", "lat": 17.618, "lon": 83.238},
    "INGPR": {"name": "Gopalpur", "lat": 19.308, "lon": 84.966},
    "INDHM": {"name": "Dhamra", "lat": 20.803, "lon": 86.974},
    "INSAG": {"name": "Sagar-Sandheads", "lat": 21.65, "lon": 88.08},
    "INHAL": {"name": "Haldia", "lat": 22.02, "lon": 88.10},
}

def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in nautical miles between two lat/lon coordinates."""
    R_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    dist_km = R_km * c
    return round(dist_km * 0.539957, 2)

def get_destination_coords(port_id: str) -> dict:
    port_id = str(port_id).upper().strip()
    return EAST_COAST_PORT_COORDS.get(port_id, {"name": "Paradip", "lat": 20.266, "lon": 86.88})

def calculate_direct_eta(current_lat: float, current_lon: float, destination_port_id: str,
                         speed_knots: float, current_time: datetime = None) -> dict:
    """
    Calculates distance to destination port, estimated travel time, and direct ETA.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    port_info = get_destination_coords(destination_port_id)
    dist_nm = haversine_distance_nm(current_lat, current_lon, port_info["lat"], port_info["lon"])

    effective_speed = speed_knots if speed_knots > 0.8 else 11.5
    travel_hrs = dist_nm / effective_speed

    eta_dt = current_time + timedelta(hours=travel_hrs)

    return {
        "destination_port_id": destination_port_id,
        "destination_port_name": port_info["name"],
        "distance_to_port_nm": dist_nm,
        "speed_knots": speed_knots,
        "effective_speed_knots": effective_speed,
        "travel_time_hours": round(travel_hrs, 2),
        "direct_eta_utc": eta_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "direct_eta_dt": eta_dt
    }

def detect_delay_status(current_speed_knots: float, Planned_speed_knots: float = 12.0,
                        schedule_eta_utc: str = None, direct_eta_utc: str = None) -> dict:
    """
    Detects in-transit delays, speed anomalies, and schedule drift.
    """
    is_speed_anomaly = current_speed_knots < 5.0 and current_speed_knots > 0.1
    delay_hours = 0.0

    if schedule_eta_utc and direct_eta_utc:
        try:
            sched_dt = datetime.fromisoformat(schedule_eta_utc.replace("Z", "+00:00"))
            direct_dt = datetime.fromisoformat(direct_eta_utc.replace("Z", "+00:00"))
            delay_seconds = (direct_dt - sched_dt).total_seconds()
            delay_hours = round(delay_seconds / 3600.0, 2)
        except Exception:
            pass

    if is_speed_anomaly and delay_hours <= 0:
        delay_hours = 3.5

    if delay_hours > 1.0:
        status_category = "DELAYED"
        description = f"Delayed by {delay_hours:.1f} hrs due to speed drop / route drift"
    else:
        status_category = "ON_TIME"
        description = "Vessel running on schedule"

    return {
        "status_category": status_category,
        "delay_hours": delay_hours,
        "is_speed_anomaly": is_speed_anomaly,
        "description": description
    }
