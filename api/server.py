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

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from smartfreight_ais.integrated_pipeline import (
    run_smartfreight_integrated_simulation,
    PORT_CATALOG,
    VESSEL_SPECS,
)

app = FastAPI(
    title="SmartFreight AI — Unified Multi-Module Engine API",
    description="Full-Stack Backend: Freight Forecast, Vessel Optimization, AIS/ETA Tracking, Port Congestion & Cost/Charter Decision (SIH 2026)",
    version="2.0.0"
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


# ============================================================
# MEMBER 6 — FULL STACK INTEGRATION & SIMULATION ENDPOINTS
# ============================================================

class SimulationRequest(BaseModel):
    cargo_type: str = Field(default="Thermal Coal", description="Cargo type (e.g. Thermal Coal, Iron Ore, Fertilizer)")
    cargo_quantity_mt: float = Field(default=75000.0, description="Cargo quantity in metric tonnes")
    origin_port_id: str = Field(default="INPRD", description="Origin port ID (e.g. INPRD, INVTZ, INMAA, INHLD, INENR)")
    dest_port_id: str = Field(default="INHLD", description="Destination port ID")
    urgency: str = Field(default="NORMAL", description="Shipment urgency: CRITICAL, HIGH, NORMAL, LOW")
    contract_duration_preference: str = Field(default="MEDIUM_TERM", description="Duration: SPOT, SHORT_TERM, MEDIUM_TERM, LONG_TERM")
    forecast_horizon_days: int = Field(default=14, description="Forecast horizon in days: 7, 14, or 30")
    bunker_price_usd_per_mt: float = Field(default=600.0, description="Bunker fuel cost in USD/MT")


@app.get("/api/v1/ports")
def get_ports():
    """List all East Coast Indian ports with coordinates and physical constraints."""
    return {"status": "SUCCESS", "count": len(PORT_CATALOG), "ports": PORT_CATALOG}


@app.get("/api/v1/vessels/specs")
def get_vessel_specs():
    """List bulk carrier vessel classes with draft, beam, LOA, and baseline fuel rates."""
    return {"status": "SUCCESS", "vessel_specs": VESSEL_SPECS}


@app.post("/api/v1/simulate")
def post_simulate(req: SimulationRequest):
    """
    Execute full end-to-end SmartFreight multi-module simulation:
    - Member 2: Freight rate forecasting (Random Forest)
    - Member 3: Vessel selection & port feasibility constraints
    - Member 4: AIS telemetry, ETA & waiting time ML model
    - Member 5: Voyage cost optimization & charter decision
    """
    try:
        res = run_smartfreight_integrated_simulation(
            cargo_type=req.cargo_type,
            cargo_quantity_mt=req.cargo_quantity_mt,
            origin_port_id=req.origin_port_id,
            dest_port_id=req.dest_port_id,
            urgency=req.urgency,
            contract_duration_preference=req.contract_duration_preference,
            forecast_horizon_days=req.forecast_horizon_days,
            bunker_price_usd_per_mt=req.bunker_price_usd_per_mt,
        )
        return res
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Simulation error: {exc}")


@app.get("/api/v1/simulate")
def get_simulate(
    cargo_type: str = Query("Thermal Coal"),
    cargo_quantity_mt: float = Query(75000.0),
    origin_port_id: str = Query("INPRD"),
    dest_port_id: str = Query("INHLD"),
    urgency: str = Query("NORMAL"),
    contract_duration_preference: str = Query("MEDIUM_TERM"),
    forecast_horizon_days: int = Query(14),
    bunker_price_usd_per_mt: float = Query(600.0)
):
    """Execute full simulation via GET query parameters for easy testing."""
    try:
        return run_smartfreight_integrated_simulation(
            cargo_type=cargo_type,
            cargo_quantity_mt=cargo_quantity_mt,
            origin_port_id=origin_port_id,
            dest_port_id=dest_port_id,
            urgency=urgency,
            contract_duration_preference=contract_duration_preference,
            forecast_horizon_days=forecast_horizon_days,
            bunker_price_usd_per_mt=bunker_price_usd_per_mt,
        )
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Simulation error: {exc}")
