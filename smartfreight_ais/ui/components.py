"""
SmartFreight AI — Reusable Enterprise Presentation Components
"""

import html
import streamlit as st
from typing import List, Dict, Any, Optional


def render_header(last_updated: Optional[str] = None):
    """
    Render institutional header banner for government maritime logistics portal.
    """
    ts = last_updated or "LIVE SIMULATION"
    header_html = f"""
    <div class="gov-header">
        <div>
            <div class="gov-header-title">SMARTFREIGHT AI</div>
            <div class="gov-header-subtitle">
                Freight Forecasting &amp; Vessel Chartering Decision Support System &bull; East Coast India
            </div>
        </div>
        <div class="gov-header-meta">
            <div><span class="gov-header-status">SYSTEM OPERATIONAL</span></div>
            <div style="margin-top: 4px; font-size: 0.72rem; color: #94A3B8;">Last Updated: {html.escape(ts)}</div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_breadcrumbs(items: List[str]):
    """
    Render clean navigation breadcrumbs.
    """
    parts = []
    for i, item in enumerate(items):
        if i == len(items) - 1:
            parts.append(f'<span class="gov-breadcrumb-active">{html.escape(item)}</span>')
        else:
            parts.append(f'<span class="gov-breadcrumb-item">{html.escape(item)}</span>')
    
    crumb_html = f'<div class="gov-breadcrumb">{" &gt; ".join(parts)}</div>'
    st.markdown(crumb_html, unsafe_allow_html=True)


def metric_box(label: str, value: str, subtext: str = "", variant: str = "default"):
    """
    Render a clean enterprise metric KPI box.
    variant: 'default' | 'success' | 'warning' | 'danger'
    """
    border_class = ""
    if variant == "success":
        border_class = "gov-metric-box-success"
    elif variant == "warning":
        border_class = "gov-metric-box-warning"
    elif variant == "danger":
        border_class = "gov-metric-box-danger"

    sub_html = f'<div class="gov-metric-subtext">{html.escape(subtext)}</div>' if subtext else ""
    box_html = f"""
    <div class="gov-metric-box {border_class}">
        <div class="gov-metric-label">{html.escape(label)}</div>
        <div class="gov-metric-value">{html.escape(value)}</div>
        {sub_html}
    </div>
    """
    st.markdown(box_html, unsafe_allow_html=True)


def decision_banner(recommendation: str, saving_usd: float, saving_pct: float, risk: str, reason: str):
    """
    Render the high-impact executive decision hero banner.
    """
    is_charter = recommendation.upper() == "CHARTER_NOW"
    container_cls = "decision-banner-charter" if is_charter else "decision-banner-wait"
    text_cls = "decision-charter-text" if is_charter else "decision-wait-text"
    display_title = "CHARTER NOW" if is_charter else "WAIT"

    saving_sign = "+" if saving_usd > 0 else ""
    saving_str = f"{saving_sign}${abs(saving_usd):,.0f} ({saving_pct:+.1f}%)" if saving_usd != 0 else "$0 (0.0%)"

    banner_html = f"""
    <div class="{container_cls}">
        <div>
            <div class="decision-badge-title">OFFICIAL RECOMMENDATION</div>
            <div class="decision-badge-val {text_cls}">{display_title}</div>
            <div class="decision-reason-text">{html.escape(reason)}</div>
        </div>
        <div style="text-align: right; min-width: 220px;">
            <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B;">EXPECTED SAVING</div>
            <div style="font-size: 1.55rem; font-weight: 800; color: #0F172A; margin: 2px 0 6px;">{html.escape(saving_str)}</div>
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
                <span class="badge-status {'badge-success' if risk.upper() in ['LOW', 'MINIMAL'] else ('badge-warning' if risk.upper() == 'MEDIUM' else 'badge-danger')}">RISK: {html.escape(risk.upper())}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


def status_badge(text: str, variant: str = "neutral") -> str:
    """
    Return HTML for a status badge.
    """
    cls = f"badge-{variant}"
    return f'<span class="badge-status {cls}">{html.escape(text)}</span>'


def milestone_stepper(stages: List[Dict[str, Any]], current_index: int):
    """
    Render operational milestone stepper without emojis.
    """
    if not stages:
        return

    items_html = []
    for i, s in enumerate(stages):
        is_completed = i < current_index
        is_active = i == current_index
        
        if is_completed:
            circle_cls = "step-circle-completed"
            circle_content = "&check;"
            sublabel = "Completed"
        elif is_active:
            circle_cls = "step-circle-active"
            circle_content = str(i + 1)
            sublabel = "Active Stage"
        else:
            circle_cls = ""
            circle_content = str(i + 1)
            sublabel = "Upcoming"

        label_cls = "step-label-active" if is_active else ""

        items_html.append(f"""
        <div class="step-item">
            <div class="step-circle {circle_cls}">{circle_content}</div>
            <div class="step-label {label_cls}">{html.escape(s.get('label', ''))}</div>
            <div class="step-sublabel">{sublabel}</div>
        </div>
        """)

    stepper_html = f"""
    <div class="stepper-container">
        {"".join(items_html)}
    </div>
    """
    st.markdown(stepper_html, unsafe_allow_html=True)


def render_footer():
    """
    Institutional footer note.
    """
    footer_html = """
    <div class="gov-footer">
        SmartFreight AI &bull; Smart India Hackathon 2026 &bull; Bulk Maritime Decision Support System &bull; East Coast India Operations
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
