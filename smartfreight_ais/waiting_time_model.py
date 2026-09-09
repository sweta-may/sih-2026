import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from smartfreight_ais.db import load_port_calls, load_congestion

class PortWaitingTimeModel:
    """
    Machine Learning waiting-time and turnaround prediction engine
    trained on historical port call observations.
    """
    def __init__(self):
        self.model_wait = RandomForestRegressor(n_estimators=50, random_state=42)
        self.model_turnaround = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
        self._train()

    def _train(self):
        df_pc = load_port_calls()
        if df_pc.empty or len(df_pc) < 10:
            self.is_trained = False
            return

        port_map = {"INPRD": 1, "INVTZ": 2, "INGGV": 3, "INGPR": 4, "INDHM": 5, "INSAG": 6, "INHAL": 7}
        vclass_map = {"Capesize": 4, "Panamax": 3, "Supramax": 2, "Handysize": 1}

        df_pc["port_code"] = df_pc["port_id"].map(lambda x: port_map.get(x, 1))
        df_pc["vclass_code"] = df_pc["vessel_class"].map(lambda x: vclass_map.get(x, 2))

        features = ["port_code", "vclass_code", "dwt_mt", "cargo_mt"]
        X = df_pc[features].fillna(0)
        y_wait = df_pc["waiting_time_hours"]
        y_turnaround = df_pc["turnaround_time_hours"]

        self.model_wait.fit(X, y_wait)
        self.model_turnaround.fit(X, y_turnaround)
        self.is_trained = True

    def predict(self, port_id: str, vessel_class: str, dwt_mt: float = 80000, cargo_mt: float = 75000) -> dict:
        port_id = str(port_id).upper().strip()
        port_map = {"INPRD": 1, "INVTZ": 2, "INGGV": 3, "INGPR": 4, "INDHM": 5, "INSAG": 6, "INHAL": 7}
        vclass_map = {"Capesize": 4, "Panamax": 3, "Supramax": 2, "Handysize": 1}

        p_code = port_map.get(port_id, 1)
        v_code = vclass_map.get(vessel_class, 2)

        if self.is_trained:
            X_in = pd.DataFrame([[p_code, v_code, dwt_mt, cargo_mt]],
                                columns=["port_code", "vclass_code", "dwt_mt", "cargo_mt"])
            wait_hrs = float(self.model_wait.predict(X_in)[0])
            turnaround_hrs = float(self.model_turnaround.predict(X_in)[0])
        else:
            # Baseline benchmark fallback
            base_wait = {"INHAL": 19.4, "INSAG": 15.2, "INPRD": 11.8, "INVTZ": 8.6, "INDHM": 6.2, "INGGV": 5.1, "INGPR": 3.8}.get(port_id, 8.5)
            wait_hrs = base_wait * (1.3 if vessel_class == "Capesize" else 1.0)
            turnaround_hrs = wait_hrs + (cargo_mt / 25000.0) * 24.0

        wait_hrs = round(max(0.5, wait_hrs), 2)
        turnaround_hrs = round(max(12.0, turnaround_hrs), 2)

        return {
            "port_id": port_id,
            "vessel_class": vessel_class,
            "expected_waiting_time_hours": wait_hrs,
            "expected_waiting_time_days": round(wait_hrs / 24.0, 2),
            "expected_turnaround_time_hours": turnaround_hrs,
            "expected_turnaround_time_days": round(turnaround_hrs / 24.0, 2),
            "unloading_time_hours": round(turnaround_hrs - wait_hrs, 2)
        }

_predictor_instance = None
def get_waiting_time_predictor():
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PortWaitingTimeModel()
    return _predictor_instance
