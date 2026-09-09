from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from smartfreight_ais.vesselfinder_provider import VesselFinderAPIProvider
from smartfreight_ais.eta_engine import calculate_direct_eta, detect_delay_status
from smartfreight_ais.waiting_time_model import get_waiting_time_predictor
from smartfreight_ais.idle_cost_engine import calculate_idle_cost
from smartfreight_ais.congestion_engine import get_port_congestion_timetable
from smartfreight_ais.status_tracker import IRCTCVesselStatusTracker
from smartfreight_ais.alerts_reports_engine import generate_in_app_alerts, generate_idle_time_report_df
from smartfreight_ais.member5_bridge import export_to_member5

app = FastAPI(
    title="SmartFreight AI — Member 4 Engine API",
    description="AIS Tracking, ETA, Port Congestion, Waiting-Time ML Model & Member 5 Integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "module": "Member 4 — AIS / ETA / Port Congestion / Idle-Time",
        "status": "ONLINE",
        "prototype_data_mode": True,
        "vesselfinder_api_integrated": True
    }

@app.get("/api/v1/member4/vessels")
def get_all_vessels():
    provider = VesselFinderAPIProvider()
    vessels = provider.get_all_active_vessels()
    predictor = get_waiting_time_predictor()

    enriched = []
    for v in vessels:
        mmsi = v.get("mmsi", 419000000)
        lat = float(v.get("lat", 19.5))
        lon = float(v.get("lon", 85.5))
        speed = float(v.get("speed_knots", 10.5))
        dest = v.get("destination", "INPRD")
        vclass = v.get("vessel_class", "Panamax")

        eta_res = calculate_direct_eta(lat, lon, dest, speed)
        wt_res = predictor.predict(dest, vclass)
        delay_res = detect_delay_status(speed, direct_eta_utc=eta_res["direct_eta_utc"])
        idle_res = calculate_idle_cost(wt_res["expected_waiting_time_hours"], vclass)
        irctc_status = IRCTCVesselStatusTracker.get_live_status(
            eta_res["distance_to_port_nm"], speed, delay_res["delay_hours"], wt_res["expected_waiting_time_hours"]
        )

        v_out = dict(v)
        v_out["distance_to_port_nm"] = eta_res["distance_to_port_nm"]
        v_out["direct_eta_utc"] = eta_res["direct_eta_utc"]
        v_out["expected_waiting_time_hours"] = wt_res["expected_waiting_time_hours"]
        v_out["expected_turnaround_time_hours"] = wt_res["expected_turnaround_time_hours"]
        v_out["delay_status"] = delay_res
        v_out["estimated_idle_cost_usd"] = idle_res["estimated_idle_cost_usd"]
        v_out["irctc_stage"] = irctc_status
        enriched.append(v_out)

    return {"count": len(enriched), "vessels": enriched}

@app.get("/api/v1/member4/vessels/{mmsi}")
def get_vessel_details(mmsi: int):
    provider = VesselFinderAPIProvider()
    pos = provider.get_vessel_position(mmsi)

    lat = float(pos.get("lat", 19.5))
    lon = float(pos.get("lon", 85.5))
    speed = float(pos.get("speed_knots", 10.5))
    dest = pos.get("destination", "INPRD")
    vclass = pos.get("vessel_class", "Panamax")

    eta_res = calculate_direct_eta(lat, lon, dest, speed)
    predictor = get_waiting_time_predictor()
    wt_res = predictor.predict(dest, vclass)
    delay_res = detect_delay_status(speed, direct_eta_utc=eta_res["direct_eta_utc"])
    idle_res = calculate_idle_cost(wt_res["expected_waiting_time_hours"], vclass)
    irctc_status = IRCTCVesselStatusTracker.get_live_status(
        eta_res["distance_to_port_nm"], speed, delay_res["delay_hours"], wt_res["expected_waiting_time_hours"]
    )
    member5_payload = export_to_member5(mmsi, vclass)

    return {
        "telemetry": pos,
        "eta": eta_res,
        "waiting_time_ml": wt_res,
        "delay": delay_res,
        "idle_cost": idle_res,
        "irctc_status": irctc_status,
        "member5_export_payload": member5_payload
    }

@app.get("/api/v1/member4/congestion")
def get_congestion():
    timetable = get_port_congestion_timetable()
    return {"timetable": timetable}

@app.get("/api/v1/member4/export-to-member5")
def export_for_member5(mmsi: int = Query(419000000), vessel_class: str = Query("Panamax"), cargo_mt: float = Query(75000.0)):
    return export_to_member5(mmsi, vessel_class, cargo_mt)

@app.get("/api/v1/member4/alerts")
def get_alerts():
    vessels_res = get_all_vessels()["vessels"]
    timetable = get_port_congestion_timetable()
    alerts = generate_in_app_alerts(vessels_res, timetable)
    return {"alerts": alerts}

@app.get("/api/v1/member4/report/download")
def download_csv_report():
    vessels_res = get_all_vessels()["vessels"]
    df_rep = generate_idle_time_report_df(vessels_res)
    csv_str = df_rep.to_csv(index=False)
    return Response(content=csv_str, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=SmartFreight_Member4_Idle_Time_Report.csv"})
