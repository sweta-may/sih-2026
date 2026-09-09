from datetime import datetime, timedelta, timezone

class IRCTCVesselStatusTracker:
    """
    IRCTC-style Live Vessel Tracking State Machine:
    On Time -> Delayed -> At Port -> Waiting -> Loading/Unloading -> Departed
    """
    STAGES = [
        {"id": 1, "code": "ON_TIME", "label": "On Time", "color": "#10B981"},
        {"id": 2, "code": "DELAYED", "label": "Delayed", "color": "#EF4444"},
        {"id": 3, "code": "AT_PORT", "label": "At Port", "color": "#3B82F6"},
        {"id": 4, "code": "WAITING", "label": "Waiting", "color": "#F59E0B"},
        {"id": 5, "code": "UNLOADING", "label": "Loading/Unloading", "color": "#8B5CF6"},
        {"id": 6, "code": "DEPARTED", "label": "Departed", "color": "#6B7280"}
    ]

    @classmethod
    def get_live_status(cls, dist_nm: float, speed_knots: float, delay_hours: float,
                         waiting_time_hours: float, nav_status: str = "Under way") -> dict:
        
        # State machine transition logic
        if "moored" in nav_status.lower() or "berthed" in nav_status.lower():
            stage_idx = 4  # Loading/Unloading
        elif "at anchor" in nav_status.lower() or (dist_nm < 15.0 and speed_knots < 1.0):
            stage_idx = 3  # Waiting at anchorage
        elif dist_nm < 15.0:
            stage_idx = 2  # At Port area
        elif delay_hours > 1.5:
            stage_idx = 1  # Delayed
        else:
            stage_idx = 0  # On Time

        current_stage = cls.STAGES[stage_idx]
        progress_pct = int(((stage_idx + 1) / len(cls.STAGES)) * 100)

        return {
            "current_stage_code": current_stage["code"],
            "current_stage_label": current_stage["label"],
            "current_stage_color": current_stage["color"],
            "stage_index": stage_idx,
            "total_stages": len(cls.STAGES),
            "progress_pct": progress_pct,
            "all_stages": cls.STAGES,
            "status_summary": f"Vessel is currently [{current_stage['label']}] ({dist_nm:.1f} NM from port)"
        }
