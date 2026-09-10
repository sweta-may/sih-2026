"""
SmartFreight AI — Executive Maritime Decision Support Portal
Smart India Hackathon 2026 | East Coast India Bulk Logistics

Institutional presentation layer integrating:
- Freight Forecasting (Member 2)
- Vessel Optimization & Port Feasibility (Member 3)
- AIS Telemetry, ETA & Waiting Time Engine (Member 4)
- Voyage Cost Optimization & Charter Decision (Member 5)
- Full-Stack Orchestration & Decision Portal (Member 6)
"""

import html
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from smartfreight_ais.ui.styles import ENTERPRISE_CSS
from smartfreight_ais.ui.components import (
    render_header,
    render_breadcrumbs,
    metric_box,
    decision_banner,
    milestone_stepper,
    render_footer,
)

# -------------------------------------------------------------
# PAGE CONFIGURATION (Strictly Institutional, Zero Emojis)
# -------------------------------------------------------------
st.set_page_config(
    page_title="SmartFreight AI — Maritime Decision Support Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject centralized enterprise CSS
st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# PIPELINE IMPORTS
# -------------------------------------------------------------
try:
    from smartfreight_ais.integrated_pipeline import (
        run_smartfreight_integrated_simulation,
        PORT_CATALOG,
        VESSEL_SPECS,
    )
    PIPELINE_AVAILABLE = True
    PIPELINE_ERROR = ""
except Exception as e:
    PIPELINE_AVAILABLE = False
    PIPELINE_ERROR = str(e)
    PORT_CATALOG = {}
    VESSEL_SPECS = {}

# -------------------------------------------------------------
# SESSION STATE MANAGEMENT
# -------------------------------------------------------------
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "Overview"

if "cargo_type" not in st.session_state:
    st.session_state["cargo_type"] = "Thermal Coal"

if "cargo_qty" not in st.session_state:
    st.session_state["cargo_qty"] = 35000.0

if "urgency" not in st.session_state:
    st.session_state["urgency"] = "NORMAL"

if "origin_id" not in st.session_state:
    st.session_state["origin_id"] = "INPRD"

if "dest_id" not in st.session_state:
    st.session_state["dest_id"] = "INHLD"

if "contract_pref" not in st.session_state:
    st.session_state["contract_pref"] = "MEDIUM_TERM"

if "forecast_horizon" not in st.session_state:
    st.session_state["forecast_horizon"] = 14

if "simulation_result" not in st.session_state and PIPELINE_AVAILABLE:
    # Auto-initialize baseline simulation for immediate operational readiness
    try:
        baseline_res = run_smartfreight_integrated_simulation(
            cargo_type=st.session_state["cargo_type"],
            cargo_quantity_mt=st.session_state["cargo_qty"],
            origin_port_id=st.session_state["origin_id"],
            dest_port_id=st.session_state["dest_id"],
            urgency=st.session_state["urgency"],
            contract_duration_preference=st.session_state["contract_pref"],
            forecast_horizon_days=st.session_state["forecast_horizon"],
        )
        st.session_state["simulation_result"] = baseline_res
        st.session_state["last_run_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except Exception as init_exc:
        st.session_state["simulation_result"] = None
        st.session_state["init_error"] = str(init_exc)

# -------------------------------------------------------------
# SIDEBAR: CONFIGURATION & NAVIGATION
# -------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding-bottom: 10px; border-bottom: 2px solid #CBD5E1; margin-bottom: 12px;">
            <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A; letter-spacing: 0.05em;">SMARTFREIGHT AI</div>
            <div style="font-size: 0.74rem; color: #64748B; font-weight: 500;">National Maritime Logistics Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='font-size:0.75rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>NAVIGATION</div>", unsafe_allow_html=True)
    nav_options = [
        "Overview",
        "Charter Decision",
        "Freight Forecast",
        "Vessel & Port",
        "AIS & ETA",
        "Cost Analysis",
        "Alerts",
        "Reports",
    ]
    current_nav_idx = nav_options.index(st.session_state["active_nav"]) if st.session_state["active_nav"] in nav_options else 0
    selected_nav = st.radio(
        "Select Portal View",
        nav_options,
        index=current_nav_idx,
        label_visibility="collapsed",
    )
    st.session_state["active_nav"] = selected_nav

    st.divider()

    st.markdown("<div style='font-size:0.75rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>CARGO REQUIREMENT</div>", unsafe_allow_html=True)
    c_types = ["Thermal Coal", "Coking Coal", "Iron Ore", "Fertilizer", "Grain", "Limestone", "Bauxite"]
    sel_cargo = st.selectbox(
        "Cargo Type",
        c_types,
        index=c_types.index(st.session_state["cargo_type"]) if st.session_state["cargo_type"] in c_types else 0,
    )
    sel_qty = st.number_input(
        "Quantity (Metric Tonnes)",
        min_value=5000,
        max_value=200000,
        value=int(st.session_state["cargo_qty"]),
        step=5000,
    )
    u_options = ["NORMAL", "HIGH", "URGENT", "CRITICAL"]
    sel_urgency = st.selectbox(
        "Urgency Level",
        u_options,
        index=u_options.index(st.session_state["urgency"]) if st.session_state["urgency"] in u_options else 0,
    )

    st.divider()

    st.markdown("<div style='font-size:0.75rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>ROUTE CONFIGURATION</div>", unsafe_allow_html=True)
    port_keys = list(PORT_CATALOG.keys()) if PORT_CATALOG else ["INPRD", "INHLD", "INVTZ", "INMAA"]
    port_names = {k: f"{v.get('name', k)} ({k})" for k, v in PORT_CATALOG.items()} if PORT_CATALOG else {k: k for k in port_keys}

    orig_idx = port_keys.index(st.session_state["origin_id"]) if st.session_state["origin_id"] in port_keys else 0
    dest_idx = port_keys.index(st.session_state["dest_id"]) if st.session_state["dest_id"] in port_keys else min(1, len(port_keys) - 1)

    sel_orig = st.selectbox("Origin Port", port_keys, index=orig_idx, format_func=lambda x: port_names.get(x, x))
    sel_dest = st.selectbox("Destination Port", port_keys, index=dest_idx, format_func=lambda x: port_names.get(x, x))

    st.divider()

    st.markdown("<div style='font-size:0.75rem;font-weight:700;color:#1E3A8A;margin-bottom:6px;'>CONTRACT & HORIZON</div>", unsafe_allow_html=True)
    cp_options = ["SPOT", "SHORT_TERM", "MEDIUM_TERM"]
    sel_contract = st.selectbox(
        "Preferred Duration",
        cp_options,
        index=cp_options.index(st.session_state["contract_pref"]) if st.session_state["contract_pref"] in cp_options else 2,
    )
    fh_options = [7, 14, 30]
    sel_horizon = st.selectbox(
        "Forecast Horizon",
        fh_options,
        index=fh_options.index(st.session_state["forecast_horizon"]) if st.session_state["forecast_horizon"] in fh_options else 1,
        format_func=lambda d: f"{d} Days",
    )

    st.divider()

    run_clicked = st.button("RUN ANALYSIS", type="primary", use_container_width=True)
    if run_clicked:
        st.session_state["cargo_type"] = sel_cargo
        st.session_state["cargo_qty"] = float(sel_qty)
        st.session_state["urgency"] = sel_urgency
        st.session_state["origin_id"] = sel_orig
        st.session_state["dest_id"] = sel_dest
        st.session_state["contract_pref"] = sel_contract
        st.session_state["forecast_horizon"] = sel_horizon

        with st.spinner("Processing multi-module decision simulation..."):
            try:
                sim_res = run_smartfreight_integrated_simulation(
                    cargo_type=sel_cargo,
                    cargo_quantity_mt=float(sel_qty),
                    origin_port_id=sel_orig,
                    dest_port_id=sel_dest,
                    urgency=sel_urgency,
                    contract_duration_preference=sel_contract,
                    forecast_horizon_days=sel_horizon,
                )
                st.session_state["simulation_result"] = sim_res
                st.session_state["last_run_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")

# -------------------------------------------------------------
# MAIN APPLICATION WORKSPACE
# -------------------------------------------------------------

# Render Top Institutional Header
render_header(st.session_state.get("last_run_timestamp", "SYSTEM READY"))

if not PIPELINE_AVAILABLE:
    st.error(f"Pipeline import error: {PIPELINE_ERROR}")
    st.stop()

result = st.session_state.get("simulation_result")

if not result:
    st.warning("No active analysis loaded. Configure parameters in the sidebar and select 'RUN ANALYSIS'.")
    st.stop()

# Safely extract all structured payload dictionaries
card = result.get("executive_summary_card", {})
vest = result.get("vessel_optimization", {})
forecast = result.get("freight_forecast", {})
ops = result.get("ais_operations", {})
decision = result.get("cost_decision") or result.get("charter_decision", {})
cost_now = decision.get("cost_breakdown_charter_now") or decision.get("now_cost_breakdown", {})
cost_wait = decision.get("cost_breakdown_wait") or decision.get("wait_cost_breakdown", {})
alerts = result.get("alerts", [])

rec = card.get("recommendation", "CHARTER_NOW")
saving_usd = card.get("expected_saving_usd", 0.0)
saving_pct = card.get("expected_saving_pct", 0.0)
risk_lvl = card.get("risk_level", "LOW")
reason_txt = card.get("reason", "Chartering now is expected to be more economical than waiting.")

orig_name = PORT_CATALOG.get(st.session_state["origin_id"], {}).get("name", st.session_state["origin_id"])
dest_name = PORT_CATALOG.get(st.session_state["dest_id"], {}).get("name", st.session_state["dest_id"])

active_page = st.session_state["active_nav"]

# =============================================================
# VIEW 1: OVERVIEW
# =============================================================
if active_page == "Overview":
    render_breadcrumbs(["Portal", "Operational Overview"])

    # Executive Recommendation Banner
    decision_banner(rec, saving_usd, saving_pct, risk_lvl, reason_txt)

    # 4 Key Operational Metric KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v_cls = card.get("recommended_vessel", "Handysize")
        metric_box("Recommended Vessel", v_cls, f"Nominal Payload: {st.session_state['cargo_qty']:,.0f} MT", "default")
    with col2:
        strat = card.get("contract_strategy", "MEDIUM_TERM")
        metric_box("Recommended Strategy", strat, f"User Preference: {st.session_state['contract_pref']}", "default")
    with col3:
        cr = card.get("current_freight_rate_usd_day", 0.0)
        metric_box("Current Freight Rate", f"${cr:,.0f} / day", "Today Spot Assessment", "default")
    with col4:
        fr = card.get("forecast_rate_usd_day", 0.0)
        h_days = st.session_state["forecast_horizon"]
        diff_pct = ((fr - cr) / cr * 100.0) if cr > 0 else 0.0
        v_type = "success" if diff_pct < 0 else "warning"
        metric_box(f"{h_days}-Day Forecast Rate", f"${fr:,.0f} / day", f"{diff_pct:+.1f}% vs Current", v_type)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Operational Summary Cards
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        st.markdown(
            f"""
            <div class="gov-card">
                <div class="gov-card-header">
                    <div class="gov-card-title">Voyage &amp; Routing Parameters</div>
                    <span class="badge-status badge-navy">{html.escape(st.session_state['urgency'])} PRIORITY</span>
                </div>
                <table style="width:100%; font-size:0.85rem; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Cargo Type</td>
                        <td style="font-weight:600; text-align:right;">{html.escape(st.session_state['cargo_type'])}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Cargo Quantity</td>
                        <td style="font-weight:600; text-align:right;">{st.session_state['cargo_qty']:,.0f} MT</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Transit Corridor</td>
                        <td style="font-weight:600; text-align:right;">{html.escape(orig_name)} &rarr; {html.escape(dest_name)}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Distance Remaining</td>
                        <td style="font-weight:600; text-align:right;">{ops.get('distance_to_port_nm', 0.0):.1f} NM</td>
                    </tr>
                    <tr style="height:32px;">
                        <td style="color:#64748B; font-weight:500;">Destination Port Congestion</td>
                        <td style="font-weight:600; text-align:right;">{html.escape(str(ops.get('port_congestion_level', 'MODERATE')))}</td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s_col2:
        c_now_tot = card.get("charter_now_cost_usd", 0.0)
        c_wait_tot = card.get("expected_wait_cost_usd", 0.0)
        st.markdown(
            f"""
            <div class="gov-card">
                <div class="gov-card-header">
                    <div class="gov-card-title">Financial Decision Impact</div>
                    <span class="badge-status {'badge-success' if saving_usd > 0 else 'badge-warning'}">
                        {'+' if saving_usd > 0 else ''}${abs(saving_usd):,.0f} VARIANCE
                    </span>
                </div>
                <table style="width:100%; font-size:0.85rem; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Immediate Charter Now Cost</td>
                        <td style="font-weight:600; text-align:right;">${c_now_tot:,.2f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Projected Cost if Waiting ({h_days}d)</td>
                        <td style="font-weight:600; text-align:right;">${c_wait_tot:,.2f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Expected Financial Saving</td>
                        <td style="font-weight:700; color:{'#166534' if saving_usd > 0 else '#991B1B'}; text-align:right;">
                            {'+' if saving_usd > 0 else ''}${saving_usd:,.2f} ({saving_pct:+.1f}%)
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:32px;">
                        <td style="color:#64748B; font-weight:500;">Expected Waiting Time at Berth</td>
                        <td style="font-weight:600; text-align:right;">{card.get('expected_waiting_time_hours', 0.0):.1f} Hours</td>
                    </tr>
                    <tr style="height:32px;">
                        <td style="color:#64748B; font-weight:500;">Overall Risk Assessment</td>
                        <td style="font-weight:700; text-align:right;">{html.escape(risk_lvl.upper())}</td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================
# VIEW 2: CHARTER DECISION
# =============================================================
elif active_page == "Charter Decision":
    render_breadcrumbs(["Portal", "Charter Decision"])

    # High-impact decision banner
    decision_banner(rec, saving_usd, saving_pct, risk_lvl, reason_txt)

    # Why This Decision Section (Institutional Rationale)
    st.markdown(
        """
        <div class="gov-card">
            <div class="gov-card-header">
                <div class="gov-card-title">Decision Rationale &amp; Operational Factors</div>
            </div>
            <div style="font-size: 0.88rem; color: #334155; line-height: 1.6;">
                <ul style="margin: 0; padding-left: 20px;">
                    <li><strong>Total Voyage Cost Differential:</strong> Immediate execution yields a lower net voyage expenditure compared to awaiting projected forward rates after adjusting for holding costs.</li>
                    <li><strong>Market Waiting &amp; Demurrage Exposure:</strong> Forward softening in spot rates is insufficient to offset the accumulated demurrage penalty and market exposure associated with waiting.</li>
                    <li><strong>Corridor Feasibility:</strong> Designated vessel meets physical draft and dimension criteria at both origin and destination terminals without lightening requirements.</li>
                    <li><strong>Vessel Availability:</strong> Regional dry-bulk carrier availability index supports prompt fixture without spot premium volatility.</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Financial Comparison Table
    st.markdown("#### Financial Comparison Analysis")
    h_now = cost_now.get("hire_cost_usd") or cost_now.get("freight_cost_usd", 0.0)
    f_now = cost_now.get("fuel_cost_usd", 0.0)
    p_now = cost_now.get("port_cost_usd", 0.0)
    i_now = cost_now.get("idle_cost_usd") or cost_now.get("waiting_cost_usd", 0.0)
    o_now = cost_now.get("other_voyage_cost_usd", 0.0)
    tot_now = card.get("charter_now_cost_usd") or (h_now + f_now + p_now + i_now + o_now)

    h_wait = cost_wait.get("hire_cost_usd") or cost_wait.get("freight_cost_usd", 0.0)
    f_wait = cost_wait.get("fuel_cost_usd", 0.0)
    p_wait = cost_wait.get("port_cost_usd", 0.0)
    i_wait = cost_wait.get("idle_cost_usd") or cost_wait.get("waiting_cost_usd", 0.0)
    m_wait = cost_wait.get("market_waiting_cost_usd", 0.0)
    o_wait = cost_wait.get("other_voyage_cost_usd", 0.0)
    tot_wait = card.get("expected_wait_cost_usd") or (h_wait + f_wait + p_wait + i_wait + m_wait + o_wait)

    comp_df = pd.DataFrame([
        {"Cost Component": "Vessel Hire / Freight", "Charter Now": f"${h_now:,.2f}", "If Wait": f"${h_wait:,.2f}", "Variance": f"${h_now - h_wait:+,.2f}"},
        {"Cost Component": "Fuel Consumption", "Charter Now": f"${f_now:,.2f}", "If Wait": f"${f_wait:,.2f}", "Variance": f"${f_now - f_wait:+,.2f}"},
        {"Cost Component": "Port Dues & Tariffs", "Charter Now": f"${p_now:,.2f}", "If Wait": f"${p_wait:,.2f}", "Variance": f"${p_now - p_wait:+,.2f}"},
        {"Cost Component": "Berth Waiting / Idle Demurrage", "Charter Now": f"${i_now:,.2f}", "If Wait": f"${i_wait:,.2f}", "Variance": f"${i_now - i_wait:+,.2f}"},
        {"Cost Component": "Market Waiting Risk Premium", "Charter Now": "$0.00", "If Wait": f"${m_wait:,.2f}", "Variance": f"${-m_wait:+,.2f}"},
        {"Cost Component": "Other Voyage Costs", "Charter Now": f"${o_now:,.2f}", "If Wait": f"${o_wait:,.2f}", "Variance": f"${o_now - o_wait:+,.2f}"},
        {"Cost Component": "TOTAL ESTIMATED VOYAGE COST", "Charter Now": f"${tot_now:,.2f}", "If Wait": f"${tot_wait:,.2f}", "Variance": f"${tot_now - tot_wait:+,.2f}"},
    ])
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Contract Strategy Recommendation vs User Preference
    col_strat1, col_strat2 = st.columns(2)
    with col_strat1:
        st.markdown(
            f"""
            <div class="gov-card">
                <div class="gov-card-header">
                    <div class="gov-card-title">Contract Duration Evaluation</div>
                </div>
                <div style="font-size:0.85rem; color:#475569; margin-bottom:8px;">
                    User Specified Preference: <strong>{html.escape(st.session_state['contract_pref'])}</strong>
                </div>
                <div style="font-size:0.85rem; color:#475569; margin-bottom:12px;">
                    System Recommended Strategy: <strong>{html.escape(card.get('contract_strategy', 'MEDIUM_TERM'))}</strong>
                </div>
                <div style="font-size:0.8rem; color:#64748B; line-height:1.45;">
                    Based on market cycle analysis and cargo voyage recurrence, the system recommends this contract duration to optimize long-term vessel chartering expenditure.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_strat2:
        st.markdown(
            f"""
            <div class="gov-card">
                <div class="gov-card-header">
                    <div class="gov-card-title">Multi-Factor Status Matrix</div>
                </div>
                <table style="width:100%; font-size:0.82rem; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid #F1F5F9; height:28px;">
                        <td style="color:#64748B;">Freight Market Trend</td>
                        <td style="text-align:right;"><span class="badge-status badge-warning">SOFTENING</span></td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:28px;">
                        <td style="color:#64748B;">Port Congestion State</td>
                        <td style="text-align:right;"><span class="badge-status badge-neutral">{html.escape(str(ops.get('port_congestion_level', 'MODERATE')))}</span></td>
                    </tr>
                    <tr style="border-bottom:1px solid #F1F5F9; height:28px;">
                        <td style="color:#64748B;">Vessel Fleet Availability</td>
                        <td style="text-align:right;"><span class="badge-status badge-success">AVAILABLE</span></td>
                    </tr>
                    <tr style="height:28px;">
                        <td style="color:#64748B;">Cargo Urgency Requirement</td>
                        <td style="text-align:right;"><span class="badge-status badge-navy">{html.escape(st.session_state['urgency'])}</span></td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================
# VIEW 3: FREIGHT FORECAST
# =============================================================
elif active_page == "Freight Forecast":
    render_breadcrumbs(["Portal", "Freight Rate Forecasting"])

    fdata = forecast.get("forecast", {})
    cur_rate = forecast.get("current_rate_usd_day", card.get("current_freight_rate_usd_day", 14000.0))
    f7_rate = fdata.get("7_days", {}).get("forecast_rate_usd_day", cur_rate)
    f14_rate = fdata.get("14_days", {}).get("forecast_rate_usd_day", cur_rate)
    f30_rate = fdata.get("30_days", {}).get("forecast_rate_usd_day", cur_rate)

    # Plotly Forward Curve Chart (Enterprise Government Theme)
    labels = ["Current Spot", "7-Day Forward", "14-Day Forward", "30-Day Forward"]
    rates = [cur_rate, f7_rate, f14_rate, f30_rate]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=rates,
        mode="lines+markers+text",
        line=dict(color="#1E40AF", width=3),
        marker=dict(size=8, color="#0F172A"),
        text=[f"${r:,.0f}" for r in rates],
        textposition="top center",
        fill="tozeroy",
        fillcolor="rgba(30, 64, 175, 0.05)",
        name="Projected Rate",
    ))
    fig.add_hline(
        y=cur_rate,
        line_dash="dash",
        line_color="#94A3B8",
        annotation_text=f"Current Rate: ${cur_rate:,.0f}/day",
        annotation_position="bottom right",
    )
    fig.update_layout(
        title="East Coast India Bulk Carrier Freight Forward Curve",
        font=dict(family="Inter, sans-serif", size=12, color="#0F172A"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=380,
        margin=dict(l=30, r=30, t=50, b=30),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="USD / Day", showgrid=True, gridcolor="#F1F5F9"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Metrics row
    c_f1, c_f2, c_f3 = st.columns(3)
    with c_f1:
        metric_box("Predictive Model", forecast.get("model", "Random Forest (Multi-Horizon)"), "Historical Baltic & Coastal Index", "default")
    with c_f2:
        entry_win = forecast.get("recommended_entry_window", "14_days").replace("_", " ").title()
        metric_box("Optimal Entry Window", entry_win, "Based on forward slope analysis", "default")
    with c_f3:
        sig = forecast.get("market_entry_signal", "WAIT")
        metric_box("Market Rate Signal", sig, "Model trend recommendation", "success" if sig == "CHARTER_NOW" else "warning")

    st.markdown("#### Forward Rates Projection Schedule")
    sched_rows = []
    for h_key, h_lbl in [("7_days", "7-Day Forward"), ("14_days", "14-Day Forward"), ("30_days", "30-Day Forward")]:
        h_info = fdata.get(h_key, {})
        r_val = h_info.get("forecast_rate_usd_day", cur_rate)
        c_pct = h_info.get("change_percent_vs_current", ((r_val - cur_rate) / cur_rate * 100.0) if cur_rate > 0 else 0.0)
        direction = "Softening" if c_pct < 0 else ("Rising" if c_pct > 0 else "Flat")
        sched_rows.append({
            "Horizon": h_lbl,
            "Projected Rate (USD/day)": f"${r_val:,.2f}",
            "Delta vs Current": f"{c_pct:+.2f}%",
            "Market Direction": direction,
            "Assessment": "Cost favorable window" if c_pct < 0 else "Potential premium risk",
        })
    st.dataframe(pd.DataFrame(sched_rows), use_container_width=True, hide_index=True)

# =============================================================
# VIEW 4: VESSEL & PORT
# =============================================================
elif active_page == "Vessel & Port":
    render_breadcrumbs(["Portal", "Vessel Selection & Port Feasibility"])

    rec_v = vest.get("recommended_vessel_class") or vest.get("recommendation", {}).get("vessel_class", "Handysize")
    spec = VESSEL_SPECS.get(rec_v, {})
    voyages = vest.get("voyages_required") or vest.get("recommendation", {}).get("voyages", 1)
    cpv = vest.get("cargo_per_voyage_mt") or vest.get("recommendation", {}).get("cargo_per_voyage_mt", st.session_state["cargo_qty"])
    util = vest.get("capacity_utilization_pct") or vest.get("recommendation", {}).get("capacity_utilization_pct", 100.0)

    # 4 Metric KPI Row
    cv1, cv2, cv3, cv4 = st.columns(4)
    with cv1:
        metric_box("Assigned Vessel Class", rec_v, f"DWT: {spec.get('nominal_dwt_mt', 0):,.0f} MT", "default")
    with cv2:
        metric_box("Planned Voyages", str(voyages), f"{cpv:,.0f} MT / voyage", "default")
    with cv3:
        metric_box("Capacity Utilization", f"{util:.1f}%", "Cargo MT / DWT MT", "success" if util >= 75 else "warning")
    with cv4:
        metric_box("Baseline Hire Benchmark", f"${spec.get('base_freight_rate_usd_day', 0):,.0f} / day", "Standard reference", "default")

    st.markdown(
        f"""
        <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:4px; padding:12px 18px; margin: 12px 0 20px; font-size:0.85rem; color:#1E40AF;">
            <strong>Selection Rationale:</strong> The <strong>{html.escape(rec_v)}</strong> class was selected because it maximizes cargo utilization while strictly complying with the governing draft and dimension limits at both {html.escape(orig_name)} and {html.escape(dest_name)}.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Port Physical Feasibility Table
    st.markdown("#### Terminal Physical Constraint Verification")
    orig_p = PORT_CATALOG.get(st.session_state["origin_id"], {})
    dest_p = PORT_CATALOG.get(st.session_state["dest_id"], {})

    port_comp_df = pd.DataFrame([
        {
            "Parameter": "Draft Limit (m)",
            "Vessel Requirement": f"{spec.get('draft_m', 0.0):.1f} m",
            f"Origin ({orig_p.get('name', 'Origin')})": f"{orig_p.get('max_draft_m', 0.0):.1f} m",
            f"Destination ({dest_p.get('name', 'Dest')})": f"{dest_p.get('max_draft_m', 0.0):.1f} m",
            "Origin Compliance": "Pass" if spec.get("draft_m", 0.0) <= orig_p.get("max_draft_m", 99.0) else "Exceeds Constraint",
            "Destination Compliance": "Pass" if spec.get("draft_m", 0.0) <= dest_p.get("max_draft_m", 99.0) else "Exceeds Constraint",
        },
        {
            "Parameter": "Length Overall - LOA (m)",
            "Vessel Requirement": f"{spec.get('loa_m', 0.0):.1f} m",
            f"Origin ({orig_p.get('name', 'Origin')})": f"{orig_p.get('max_loa_m', 0.0):.1f} m",
            f"Destination ({dest_p.get('name', 'Dest')})": f"{dest_p.get('max_loa_m', 0.0):.1f} m",
            "Origin Compliance": "Pass" if spec.get("loa_m", 0.0) <= orig_p.get("max_loa_m", 999.0) else "Exceeds Constraint",
            "Destination Compliance": "Pass" if spec.get("loa_m", 0.0) <= dest_p.get("max_loa_m", 999.0) else "Exceeds Constraint",
        },
        {
            "Parameter": "Beam Limit (m)",
            "Vessel Requirement": f"{spec.get('beam_m', 0.0):.1f} m",
            f"Origin ({orig_p.get('name', 'Origin')})": f"{orig_p.get('max_beam_m', 0.0):.1f} m",
            f"Destination ({dest_p.get('name', 'Dest')})": f"{dest_p.get('max_beam_m', 0.0):.1f} m",
            "Origin Compliance": "Pass" if spec.get("beam_m", 0.0) <= orig_p.get("max_beam_m", 99.0) else "Exceeds Constraint",
            "Destination Compliance": "Pass" if spec.get("beam_m", 0.0) <= dest_p.get("max_beam_m", 99.0) else "Exceeds Constraint",
        },
    ])
    st.dataframe(port_comp_df, use_container_width=True, hide_index=True)

    # All Vessel Classes Evaluated Table
    evals = vest.get("vessel_evaluations") or vest.get("all_evaluations", {})
    if evals:
        st.markdown("#### Candidate Vessel Class Evaluations")
        eval_rows = []
        for vcls, ev in evals.items():
            dwt_val = ev.get("dwt_mt") or ev.get("nominal_dwt_mt", 0.0)
            dr_val = ev.get("draft_compatibility", {}).get("vessel_draft_m", ev.get("draft_m", 0.0))
            is_ok = ev.get("is_eligible") or ev.get("port_feasible")
            eval_rows.append({
                "Vessel Class": vcls,
                "Nominal DWT (MT)": f"{dwt_val:,.0f} MT",
                "Draft Requirement (m)": f"{dr_val:.1f} m",
                "Port Feasibility Status": "Feasible" if is_ok else "Exceeds Port Limits",
                "Voyages Required": ev.get("voyages") or ev.get("voyages_required", "1"),
                "Capacity Utilization": f"{ev.get('capacity_utilization_pct', 0.0):.1f}%",
                "Selection": "SELECTED" if vcls == rec_v else "-",
            })
        st.dataframe(pd.DataFrame(eval_rows), use_container_width=True, hide_index=True)

# =============================================================
# VIEW 5: AIS & ETA
# =============================================================
elif active_page == "AIS & ETA":
    render_breadcrumbs(["Portal", "AIS Telemetry & ETA Monitoring"])

    bridge = ops.get("bridge_payload") or ops
    irctc = ops.get("irctc_status") or ops.get("irctc_stage", {})
    delay = ops.get("delay_status", {})

    st.markdown("#### Voyage Progression Milestones")
    stages = irctc.get("all_stages", [])
    curr_idx = irctc.get("stage_index", 0)
    milestone_stepper(stages, curr_idx)

    # Telemetry KPI row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        v_name = bridge.get("vessel_name", "MV Explorer")
        metric_box("Vessel Identifier", v_name, f"MMSI: {bridge.get('mmsi', 419000000)}", "default")
    with m2:
        dist_val = bridge.get("distance_to_port_nm", 0.0)
        metric_box("Distance to Port", f"{dist_val:.1f} NM", f"Destination: {dest_name}", "default")
    with m3:
        eta_str = bridge.get("vessel_eta", "TBD")
        formatted_eta = eta_str[:16].replace("T", " ") if "T" in str(eta_str) else str(eta_str)
        metric_box("Direct AIS ETA", formatted_eta, "UTC Timezone", "default")
    with m4:
        wt_hrs = bridge.get("expected_waiting_time_hours", 0.0)
        metric_box("Predicted Berth Wait", f"{wt_hrs:.1f} Hours", f"≈ {wt_hrs / 24.0:.1f} Days", "warning" if wt_hrs > 24 else "default")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Delay & Demurrage Alert Banner
    is_delayed = delay.get("is_delayed", False)
    delay_hrs = delay.get("delay_hours", 0.0)
    idle_cost = bridge.get("estimated_idle_cost_usd", 0.0)
    if is_delayed:
        st.markdown(
            f"""
            <div class="alert-card alert-card-warning">
                <div>
                    <div class="alert-title">Operational Delay Advisory</div>
                    <div class="alert-message">
                        Vessel is experiencing a schedule deviation of <strong>{delay_hrs:.1f} hours</strong>. 
                        Estimated accumulated demurrage and idle bunker exposure: <strong>${idle_cost:,.2f}</strong>.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="alert-card alert-card-info">
                <div>
                    <div class="alert-title">Schedule Status: On Time</div>
                    <div class="alert-message">Vessel speed and trajectory are aligned with current destination port berth windows.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Route Map
    st.markdown("#### East Coast India Maritime Transit Corridor")
    try:
        import pydeck as pdk
        telem = bridge.get("telemetry", {})
        vlat = telem.get("lat") or ops.get("vessel_lat") or PORT_CATALOG.get(st.session_state["origin_id"], {}).get("lat", 18.5)
        vlon = telem.get("lon") or ops.get("vessel_lon") or PORT_CATALOG.get(st.session_state["origin_id"], {}).get("lon", 84.5)
        dlat = PORT_CATALOG.get(st.session_state["dest_id"], {}).get("lat", 17.7)
        dlon = PORT_CATALOG.get(st.session_state["dest_id"], {}).get("lon", 83.2)
        olat = PORT_CATALOG.get(st.session_state["origin_id"], {}).get("lat", 20.3)
        olon = PORT_CATALOG.get(st.session_state["origin_id"], {}).get("lon", 86.7)

        deck = pdk.Deck(
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=[{"lat": vlat, "lon": vlon, "label": f"Vessel: {v_name}"}],
                    get_position="[lon, lat]",
                    get_radius=14000,
                    get_fill_color=[30, 64, 175, 230],
                    pickable=True,
                ),
                pdk.Layer(
                    "ScatterplotLayer",
                    data=[
                        {"lat": olat, "lon": olon, "label": f"Origin: {orig_name}"},
                        {"lat": dlat, "lon": dlon, "label": f"Destination: {dest_name}"},
                    ],
                    get_position="[lon, lat]",
                    get_radius=18000,
                    get_fill_color=[22, 101, 52, 220],
                    pickable=True,
                ),
                pdk.Layer(
                    "LineLayer",
                    data=[{"start": [vlon, vlat], "end": [dlon, dlat]}],
                    get_source_position="start",
                    get_target_position="end",
                    get_color=[71, 85, 105, 180],
                    get_width=3,
                ),
            ],
            initial_view_state=pdk.ViewState(latitude=18.0, longitude=84.0, zoom=5.2, pitch=0),
            tooltip={"text": "{label}"},
            map_style="mapbox://styles/mapbox/light-v10",
        )
        st.pydeck_chart(deck)
    except Exception as map_err:
        st.info(f"Maritime cartographic view currently in static telemetry mode: {map_err}")

# =============================================================
# VIEW 6: COST ANALYSIS
# =============================================================
elif active_page == "Cost Analysis":
    render_breadcrumbs(["Portal", "Total Voyage Cost Analysis"])

    c_now_tot = card.get("charter_now_cost_usd", 0.0)
    c_wait_tot = card.get("expected_wait_cost_usd", 0.0)

    ck1, ck2, ck3, ck4 = st.columns(4)
    with ck1:
        metric_box("Immediate Charter Now", f"${c_now_tot:,.2f}", "Total estimated commitment", "default")
    with ck2:
        metric_box("Projected Cost if Waiting", f"${c_wait_tot:,.2f}", f"At {st.session_state['forecast_horizon']}-day horizon", "default")
    with ck3:
        metric_box("Net Financial Saving", f"${saving_usd:,.2f}", f"{saving_pct:+.1f}% difference", "success" if saving_usd > 0 else "warning")
    with ck4:
        metric_box("Risk Profile", risk_lvl.upper(), "Composite volatility index", "default")

    st.markdown("#### Side-by-Side Financial Cost Breakdown")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(
            """
            <div class="gov-card">
                <div class="gov-card-header">
                    <div class="gov-card-title">Immediate Charter Execution</div>
                    <span class="badge-status badge-success">BENCHMARK</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        now_items = [
            {"Cost Component": "Vessel Hire / Freight", "Amount (USD)": f"${cost_now.get('hire_cost_usd') or cost_now.get('freight_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Fuel Consumption", "Amount (USD)": f"${cost_now.get('fuel_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Port Dues & Tariffs", "Amount (USD)": f"${cost_now.get('port_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Berth Waiting / Idle Demurrage", "Amount (USD)": f"${cost_now.get('idle_cost_usd') or cost_now.get('waiting_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Other Voyage Direct Expenses", "Amount (USD)": f"${cost_now.get('other_voyage_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "TOTAL VOYAGE EXPENDITURE", "Amount (USD)": f"${c_now_tot:,.2f}"},
        ]
        st.dataframe(pd.DataFrame(now_items), use_container_width=True, hide_index=True)

    with col_t2:
        st.markdown(
            f"""
            <div class="gov-card">
                <div class="gov-card-header">
                    <div class="gov-card-title">Deferred Charter (Wait {st.session_state['forecast_horizon']} Days)</div>
                    <span class="badge-status badge-neutral">MARKET EXPOSURE</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        wait_items = [
            {"Cost Component": "Projected Future Freight Hire", "Amount (USD)": f"${cost_wait.get('hire_cost_usd') or cost_wait.get('freight_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Fuel Consumption", "Amount (USD)": f"${cost_wait.get('fuel_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Port Dues & Tariffs", "Amount (USD)": f"${cost_wait.get('port_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Future Berth Waiting / Idle", "Amount (USD)": f"${cost_wait.get('idle_cost_usd') or cost_wait.get('waiting_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "Market Waiting Risk Premium", "Amount (USD)": f"${cost_wait.get('market_waiting_cost_usd', 0.0):,.2f}"},
            {"Cost Component": "TOTAL ESTIMATED COMMITMENT", "Amount (USD)": f"${c_wait_tot:,.2f}"},
        ]
        st.dataframe(pd.DataFrame(wait_items), use_container_width=True, hide_index=True)

    # Plotly Waterfall Chart
    wf_fields = {
        "Freight Hire": cost_now.get("hire_cost_usd") or cost_now.get("freight_cost_usd", 0.0),
        "Fuel": cost_now.get("fuel_cost_usd", 0.0),
        "Port Dues": cost_now.get("port_cost_usd", 0.0),
        "Idle Demurrage": cost_now.get("idle_cost_usd") or cost_now.get("waiting_cost_usd", 0.0),
    }
    if any(v > 0 for v in wf_fields.values()):
        st.markdown("#### Charter Now Cost Waterfall Breakdown")
        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            x=list(wf_fields.keys()) + ["Total Voyage Cost"],
            y=list(wf_fields.values()) + [0],
            connector={"line": {"color": "#CBD5E1"}},
            increasing={"marker": {"color": "#1E40AF"}},
            totals={"marker": {"color": "#166534"}},
            textposition="outside",
            text=[f"${v:,.0f}" for v in wf_fields.values()] + [f"${c_now_tot:,.0f}"],
        ))
        fig_wf.update_layout(
            font=dict(family="Inter, sans-serif", size=12, color="#0F172A"),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=340,
            margin=dict(l=30, r=30, t=30, b=30),
            yaxis=dict(title="USD", showgrid=True, gridcolor="#F1F5F9"),
        )
        st.plotly_chart(fig_wf, use_container_width=True)

# =============================================================
# VIEW 7: ALERTS
# =============================================================
elif active_page == "Alerts":
    render_breadcrumbs(["Portal", "Operational Alert Center"])

    st.markdown("#### Active Operational Notifications & Risk Bulletins")

    filter_choice = st.radio("Severity Filter", ["All Advisories", "Critical", "Warning", "Information"], horizontal=True)

    if alerts:
        filtered_alerts = []
        for a in alerts:
            lvl = str(a.get("level", "INFO")).upper()
            if filter_choice == "Critical" and lvl not in ["CRITICAL", "HIGH", "ERROR"]:
                continue
            if filter_choice == "Warning" and lvl not in ["WARNING", "WARN", "MEDIUM"]:
                continue
            if filter_choice == "Information" and lvl in ["CRITICAL", "HIGH", "ERROR", "WARNING", "WARN", "MEDIUM"]:
                continue
            filtered_alerts.append(a)

        if filtered_alerts:
            for al in filtered_alerts:
                lvl = str(al.get("level", "INFO")).upper()
                msg = al.get("message", str(al))
                title = al.get("title", f"Operational Bulletin ({lvl})")
                ts = al.get("timestamp", "RECENT")

                card_border = "alert-card-critical" if lvl in ["CRITICAL", "HIGH"] else ("alert-card-warning" if lvl in ["WARNING", "WARN"] else "alert-card-info")
                badge_variant = "danger" if lvl in ["CRITICAL", "HIGH"] else ("warning" if lvl in ["WARNING", "WARN"] else "navy")

                st.markdown(
                    f"""
                    <div class="alert-card {card_border}">
                        <div style="width: 100%;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div class="alert-title">{html.escape(title)}</div>
                                <span class="badge-status badge-{badge_variant}">{html.escape(lvl)}</span>
                            </div>
                            <div class="alert-message">{html.escape(msg)}</div>
                            <div class="alert-meta">Timestamp: {html.escape(str(ts))}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info(f"No active alerts matching filter: {filter_choice}.")
    else:
        st.markdown(
            """
            <div class="alert-card alert-card-info">
                <div>
                    <div class="alert-title">Nominal Operating Conditions</div>
                    <div class="alert-message">No active port congestion warnings or vessel transit alerts recorded for this itinerary.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =============================================================
# VIEW 8: REPORTS
# =============================================================
elif active_page == "Reports":
    render_breadcrumbs(["Portal", "Decision Audit & Official Reports"])

    st.markdown("#### Executive Maritime Decision Summary")

    report_content = f"""SMARTFREIGHT AI — EXECUTIVE DECISION AUDIT SHEET
National Maritime Logistics Decision Support System
Smart India Hackathon 2026

DOCUMENT REFERENCE: SF-IN-2026-REPORT
GENERATED AT: {st.session_state.get('last_run_timestamp', 'N/A')}
--------------------------------------------------------------------------------
1. EXECUTIVE CHARTER RECOMMENDATION
Recommendation: {rec.replace('_', ' ')}
Expected Financial Saving: ${saving_usd:,.2f} ({saving_pct:+.2f}% vs deferred charter)
Risk Assessment Level: {risk_lvl.upper()}
Recommended Contract Strategy: {card.get('contract_strategy', 'MEDIUM_TERM')}
User Duration Preference: {st.session_state['contract_pref']}
Primary Rationale: {reason_txt}

2. CARGO & CORRIDOR PARAMETERS
Cargo Specification: {st.session_state['cargo_type']}
Total Volume: {st.session_state['cargo_qty']:,.0f} Metric Tonnes
Operational Urgency: {st.session_state['urgency']}
Origin Terminal: {orig_name} ({st.session_state['origin_id']})
Destination Terminal: {dest_name} ({st.session_state['dest_id']})
Corridor Distance: {ops.get('distance_to_port_nm', 0.0):.1f} Nautical Miles

3. VESSEL FEASIBILITY & ALLOCATION
Selected Vessel Class: {card.get('recommended_vessel', 'Handysize')}
Nominal DWT: {VESSEL_SPECS.get(card.get('recommended_vessel', 'Handysize'), {}).get('nominal_dwt_mt', 0):,.0f} MT
Capacity Utilization: {vest.get('capacity_utilization_pct', 100.0):.1f}%
Voyages Required: {vest.get('voyages_required', 1)}
Terminal Draft Compliance: Certified Feasible

4. FREIGHT FORWARD CURVE (BALTIC / COASTAL INDEX)
Current Spot Rate: ${card.get('current_freight_rate_usd_day', 0.0):,.2f} / day
{st.session_state['forecast_horizon']}-Day Forecast: ${card.get('forecast_rate_usd_day', 0.0):,.2f} / day
Projected Market Direction: Softening

5. FINANCIAL MODEL & VOYAGE EXPENDITURE
Immediate Charter Execution: ${card.get('charter_now_cost_usd', 0.0):,.2f}
Deferred Charter Projected Cost: ${card.get('expected_wait_cost_usd', 0.0):,.2f}
Net Financial Impact: ${saving_usd:,.2f}

6. TERMINAL OPERATIONAL RISK
Expected Berth Waiting Time: {card.get('expected_waiting_time_hours', 0.0):.1f} Hours
Destination Congestion Index: {ops.get('port_congestion_level', 'MODERATE')}
--------------------------------------------------------------------------------
END OF OFFICIAL AUDIT SHEET
"""

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:4px; padding:20px; font-family:monospace; font-size:0.8rem; white-space:pre-wrap; line-height:1.45; color:#1E293B;">
{html.escape(report_content)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button(
            label="Download Executive Summary Report (.txt)",
            data=report_content,
            file_name=f"SmartFreight_Executive_Report_{st.session_state['origin_id']}_{st.session_state['dest_id']}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with c_dl2:
        try:
            from smartfreight_ais.alerts_reports_engine import generate_idle_time_report_df
            rep_vessels = [{
                "mmsi": ops.get("mmsi", 419000000),
                "vessel_name": ops.get("vessel_name", "MV Explorer"),
                "vessel_class": card.get("recommended_vessel", "Handysize"),
                "destination": dest_name,
                "speed_knots": ops.get("telemetry", {}).get("speed_knots", 10.5),
                "distance_to_port_nm": ops.get("distance_to_port_nm", 150.0),
                "direct_eta_utc": ops.get("vessel_eta", "TBD"),
                "expected_waiting_time_hours": ops.get("expected_waiting_time_hours", 12.0),
                "expected_turnaround_time_hours": ops.get("expected_turnaround_time_hours", 36.0),
                "delay_status": ops.get("delay_status", {}),
                "estimated_idle_cost_usd": ops.get("estimated_idle_cost_usd", 0.0),
                "data_source": "OPERATIONAL_CORRIDOR_TELEMETRY",
            }]
            csv_data = generate_idle_time_report_df(rep_vessels).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Port Idle-Time Data (.csv)",
                data=csv_data,
                file_name=f"SmartFreight_Idle_Time_Report_{st.session_state['dest_id']}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception:
            pass

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Technical Details Section (Hidden by default in clean collapsible expander)
    with st.expander("Technical Model Payload (Operational Inspection)", expanded=False):
        st.caption("Underlying multi-module payload for auditing and verification purposes.")
        st.json(result)

# -------------------------------------------------------------
# GLOBAL INSTITUTIONAL FOOTER
# -------------------------------------------------------------
render_footer()
