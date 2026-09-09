import os
import requests
import pandas as pd
from datetime import datetime, timezone
from smartfreight_ais.db import load_ais_positions

class VesselFinderAPIProvider:
    """
    VesselFinder API provider with prototype simulation fallback.
    Used for vessel location tracking and feed ingestion.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("VESSELFINDER_API_KEY")
        self.base_url = "https://api.vesselfinder.com/v1"

    def is_real_api_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def get_vessel_position(self, mmsi: int) -> dict:
        if self.is_real_api_available():
            try:
                url = f"{self.base_url}/vessels/{mmsi}?userkey={self.api_key}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "mmsi": int(mmsi),
                        "vessel_name": data.get("NAME", f"Vessel {mmsi}"),
                        "lat": float(data.get("LATITUDE")),
                        "lon": float(data.get("LONGITUDE")),
                        "speed_knots": float(data.get("SPEED", 0.0)),
                        "course_deg": float(data.get("COURSE", 0.0)),
                        "heading_deg": float(data.get("HEADING", 0.0)),
                        "nav_status": data.get("NAVSTAT", "Under way"),
                        "draught_m": float(data.get("DRAUGHT", 12.0)),
                        "destination": data.get("DESTINATION", "INPRD"),
                        "timestamp_utc": data.get("TIMESTAMP", datetime.now(timezone.utc).isoformat()),
                        "data_source": "VESSELFINDER_API",
                        "is_simulated": False
                    }
            except Exception as e:
                print(f"[VesselFinder API Warning] Fallback to prototype streamer: {e}")

        # Prototype fallback
        df_ais = load_ais_positions()
        if not df_ais.empty and 'mmsi' in df_ais.columns:
            mmsi_df = df_ais[df_ais['mmsi'].astype(str) == str(mmsi)]
            if not mmsi_df.empty:
                row = mmsi_df.iloc[-1].to_dict()
                row["mmsi"] = int(mmsi)
                row["lat"] = float(row["lat"])
                row["lon"] = float(row["lon"])
                row["speed_knots"] = float(row["speed_knots"])
                row["data_source"] = "PROTOTYPE_SIMULATED_AIS_STREAM"
                row["is_simulated"] = True
                return row

        return {
            "mmsi": int(mmsi),
            "imo": 9000000 + (int(mmsi) % 100),
            "vessel_name": f"MV Demo Carrier {mmsi % 100:02d}",
            "lat": 19.5,
            "lon": 85.5,
            "speed_knots": 10.5,
            "course_deg": 120.0,
            "heading_deg": 120.0,
            "nav_status": "Under way using engine",
            "draught_m": 14.4,
            "destination": "INPRD",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "data_source": "PROTOTYPE_SIMULATED_AIS_STREAM",
            "is_simulated": True
        }

    def get_all_active_vessels(self) -> list:
        df_ais = load_ais_positions()
        if df_ais.empty:
            return []
        
        latest = df_ais.sort_values('timestamp_utc').groupby('mmsi').last().reset_index()
        vessels = []
        for _, r in latest.iterrows():
            d = r.to_dict()
            d["mmsi"] = int(d["mmsi"])
            d["lat"] = float(d["lat"])
            d["lon"] = float(d["lon"])
            d["speed_knots"] = float(d["speed_knots"])
            d["data_source"] = "PROTOTYPE_SIMULATED_AIS_STREAM"
            d["is_simulated"] = True
            vessels.append(d)
        return vessels
