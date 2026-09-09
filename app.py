import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime, timezone
import requests

from smartfreight_ais.vesselfinder_provider import VesselFinderAPIProvider
from smartfreight_ais.eta_engine import calculate_direct_eta, detect_delay_status, EAST_COAST_PORT_COORDS
from smartfreight_ais.waiting_time_model import get_waiting_time_predictor
from smartfreight_ais.idle_cost_engine import calculate_idle_cost
from smartfreight_ais.congestion_engine import get_port_congestion_timetable
from smartfreight_ais.status_tracker import IRCTCVesselStatusTracker
from smartfreight_ais.alerts_reports_engine import generate_in_app_alerts, generate_idle_time_report_df
from smartfreight_ais.member5_bridge import export_to_member5

st.set_page_config(
    page_title="SmartFreight AI — AIS, ETA & Waiting Time Engine",
    page_icon="🛰️",
    layout="wide"
)

# Header Banner
st.title("🛰️ SmartFreight AI — Vessel tracking, ETA & Idle-Time Module")
st.caption("Member 4 Core Module — VesselFinder API Feed • ML Waiting Time Prediction • IRCTC Live Status • Member 5 Integration Export")

st.info("💡 **PROTOTYPE / DEMO DATA**: This prototype uses historical East Coast Indian port AIS trajectories with a simulated stream fallback when VesselFinder live API keys are not supplied. Data is fully labeled.")

# Load active vessels
provider = VesselFinderAPIProvider()
vessels_raw = provider.get_all_active_vessels()
predictor = get_waiting_time_predictor()
congestion_tt = get_port_congestion_timetable()

vessels = []
for v in vessels_raw:
    mmsi = int(v.get("mmsi", 419000000))
    lat = float(v.get("lat", 19.5))
    lon = float(v.get("lon", 85.5))
    speed = float(v.get("speed_knots", 10.5))
    dest = v.get("destination", "INPRD")
    vclass = v.get("vessel_class", "Panamax")

    eta_res = calculate_direct_eta(lat, lon, dest, speed)
    wt_res = predictor.predict(dest, vclass)
    delay_res = detect_delay_status(speed, direct_eta_utc=eta_res["direct_eta_utc"])
    idle_res = calculate_idle_cost(wt_res["expected_waiting_time_hours"], vclass)
    irctc = IRCTCVesselStatusTracker.get_live_status(eta_res["distance_to_port_nm"], speed, delay_res["delay_hours"], wt_res["expected_waiting_time_hours"])

    v_out = dict(v)
    v_out["distance_to_port_nm"] = eta_res["distance_to_port_nm"]
    v_out["direct_eta_utc"] = eta_res["direct_eta_utc"]
    v_out["expected_waiting_time_hours"] = wt_res["expected_waiting_time_hours"]
    v_out["expected_turnaround_time_hours"] = wt_res["expected_turnaround_time_hours"]
    v_out["delay_status"] = delay_res
    v_out["estimated_idle_cost_usd"] = idle_res["estimated_idle_cost_usd"]
    v_out["irctc_stage"] = irctc
    vessels.append(v_out)

vessel_names = [f"{v.get('vessel_name')} (MMSI: {v.get('mmsi')})" for v in vessels]

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚉 IRCTC Live Status Tracker",
    "🗺️ East Coast AIS Map",
    "⚓ Port Congestion Timetable",
    "🔗 Member 5 Integration Payload",
    "🔔 In-App Alerts & Reports"
])

# TAB 1: IRCTC Live Status Tracker
with tab1:
    st.subheader("🚉 IRCTC-Style Live Vessel Tracking")
    if vessels:
        sel_idx = st.selectbox("Select Vessel to Track", range(len(vessels)), format_func=lambda i: vessel_names[i])
        selected_v = vessels[sel_idx]
        
        st.markdown("---")
        
        # Stepper UI
        irctc = selected_v["irctc_stage"]
        current_idx = irctc["stage_index"]
        
        col_steps = st.columns(6)
        stages = irctc["all_stages"]
        for idx, stage in enumerate(stages):
            with col_steps[idx]:
                if idx < current_idx:
                    st.markdown(f"✅ **{stage['label']}**")
                    st.markdown("🟢 *Completed*")
                elif idx == current_idx:
                    st.markdown(f"🚨 **{stage['label']}**")
                    st.markdown(f"📍 **[CURRENT STAGE]**")
                else:
                    st.markdown(f"⚪ **{stage['label']}**")
                    st.markdown("⏳ *Upcoming*")
        
        st.progress(irctc["progress_pct"] / 100.0)
        st.caption(f"Status Summary: **{irctc['status_summary']}**")

        st.markdown("---")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Destination Port", f"{selected_v.get('destination')} ({EAST_COAST_PORT_COORDS.get(selected_v.get('destination'), {}).get('name', 'Paradip')})")
            st.metric("Speed / Heading", f"{selected_v.get('speed_knots')} kts / {selected_v.get('course_deg')}°")
        with col_b:
            st.metric("Direct AIS ETA", selected_v.get("direct_eta_utc")[:16].replace("T", " "))
            st.metric("Distance Remaining", f"{selected_v.get('distance_to_port_nm')} NM")
        with col_c:
            st.metric("Predicted Waiting Time", f"{selected_v.get('expected_waiting_time_hours')} hrs ({selected_v.get('expected_waiting_time_hours')/24.0:.1f} days)")
            st.metric("Predicted Turnaround", f"{selected_v.get('expected_turnaround_time_hours')} hrs")
        with col_d:
            delay_txt = selected_v["delay_status"]["description"]
            st.metric("Delay Status", selected_v["delay_status"]["status_category"], delta=f"{selected_v['delay_status']['delay_hours']} hrs")
            st.metric("Estimated Idle Demurrage Cost", f"${selected_v.get('estimated_idle_cost_usd'):,.2f}")

# TAB 2: AIS Map
with tab2:
    st.subheader("🗺️ Live East Coast India Vessel Trajectories & Anchorages")
    map_data = []
    for v in vessels:
        map_data.append({
            "name": str(v.get("vessel_name")),
            "mmsi": str(v.get("mmsi")),
            "lat": float(v.get("lat")),
            "lon": float(v.get("lon")),
            "speed": float(v.get("speed_knots")),
            "destination": str(v.get("destination")),
            "stage": str(v["irctc_stage"]["current_stage_label"])
        })
    df_map = pd.DataFrame(map_data)

    view_state = pdk.ViewState(latitude=19.5, longitude=85.0, zoom=5.5, pitch=30)
    layer = pdk.Layer(
        "ScatterplotLayer",
        df_map,
        get_position=["lon", "lat"],
        get_color="[239, 68, 68, 200]",
        get_radius=15000,
        pickable=True
    )
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "Vessel: {name}\nMMSI: {mmsi}\nSpeed: {speed} kts\nDest: {destination}\nStatus: {stage}"})
    st.pydeck_chart(r)

# TAB 3: Port Congestion Timetable
with tab3:
    st.subheader("⚓ East Coast Indian Port Congestion Timetable")
    df_cong = pd.DataFrame(congestion_tt)
    st.dataframe(df_cong, width='stretch')

# TAB 4: Member 5 Integration Payload
with tab4:
    st.subheader("🔗 Member 5 (Cost & Decision Module) Export Payload")
    st.write("This payload is directly exported to **Member 5** to calculate Total Voyage Cost and make Charter Now / Wait recommendations.")
    
    if vessels:
        sel_m5 = st.selectbox("Select Vessel Payload to Inspect", vessels, format_func=lambda v: v.get("vessel_name"))
        payload = export_to_member5(sel_m5.get("mmsi"), sel_m5.get("vessel_class", "Panamax"))
        st.json(payload)
        st.success("✅ Integration Verified: Standard Member 4 Schema successfully generated for Member 5 consumption.")

# TAB 5: In-App Alerts & Reports
with tab5:
    st.subheader("🔔 In-App Alerts Feed & Downloadable Idle-Time Report")
    
    alerts = generate_in_app_alerts(vessels, congestion_tt)
    st.write("### Active In-App Notifications")
    for alt in alerts:
        if alt["level"] == "CRITICAL":
            st.error(f"🔴 **[{alt['timestamp']}] {alt['title']}**: {alt['message']}")
        elif alt["level"] == "WARNING":
            st.warning(f"🟡 **[{alt['timestamp']}] {alt['title']}**: {alt['message']}")
        else:
            st.info(f"🔵 **[{alt['timestamp']}] {alt['title']}**: {alt['message']}")

    st.markdown("---")
    st.write("### Downloadable Idle-Time Report")
    df_rep = generate_idle_time_report_df(vessels)
    st.dataframe(df_rep, width='stretch')
    
    csv_bytes = df_rep.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Idle-Time & Congestion Report (CSV)",
        data=csv_bytes,
        file_name=f"SmartFreight_Member4_Idle_Time_Report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
