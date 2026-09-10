"""
SmartFreight AI — Enterprise UI Design System Stylesheet
Government Maritime Logistics Decision Support Portal Style
"""

ENTERPRISE_CSS = """
<style>
/* -------------------------------------------------------------
   GLOBAL RESET & TYPOGRAPHY
------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: #0F172A !important;
    background-color: #F8FAFC !important;
}

/* Hide default streamlit toolbar/header decoration */
header[data-testid="stHeader"] {
    background-color: #0F172A !important;
    border-bottom: 1px solid #1E293B !important;
    color: #FFFFFF !important;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #F1F5F9 !important;
    border-right: 1px solid #E2E8F0 !important;
    padding-top: 1.5rem !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #E2E8F0 !important;
    margin: 1rem 0 !important;
}

/* Sidebar Headings */
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #475569 !important;
}

/* Main Content Area Container */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
}

/* -------------------------------------------------------------
   INSTITUTIONAL HEADER
------------------------------------------------------------- */
.gov-header {
    background: #0F172A;
    color: #FFFFFF;
    border-radius: 4px;
    padding: 18px 24px;
    margin-bottom: 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 3px solid #2563EB;
}

.gov-header-title {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #FFFFFF;
    margin: 0;
    line-height: 1.3;
}

.gov-header-subtitle {
    font-size: 0.82rem;
    color: #94A3B8;
    margin-top: 3px;
    letter-spacing: 0.02em;
}

.gov-header-meta {
    text-align: right;
    font-size: 0.78rem;
    color: #CBD5E1;
}

.gov-header-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1E293B;
    border: 1px solid #334155;
    padding: 4px 10px;
    border-radius: 3px;
    font-weight: 600;
    color: #10B981;
    letter-spacing: 0.03em;
}

.gov-header-status::before {
    content: "";
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    display: inline-block;
}

/* -------------------------------------------------------------
   BREADCRUMBS
------------------------------------------------------------- */
.gov-breadcrumb {
    font-size: 0.8rem;
    color: #64748B;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
}

.gov-breadcrumb-item {
    color: #64748B;
}

.gov-breadcrumb-active {
    color: #1E3A8A;
    font-weight: 600;
}

/* -------------------------------------------------------------
   CARDS & PANELS
------------------------------------------------------------- */
.gov-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.gov-card-header {
    border-bottom: 1px solid #F1F5F9;
    padding-bottom: 0.75rem;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.gov-card-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0F172A;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 0;
}

.gov-metric-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #1E40AF;
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 0.75rem;
}

.gov-metric-box-success {
    border-left-color: #166534;
}

.gov-metric-box-warning {
    border-left-color: #B45309;
}

.gov-metric-box-danger {
    border-left-color: #991B1B;
}

.gov-metric-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748B;
    margin-bottom: 4px;
}

.gov-metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}

.gov-metric-subtext {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 4px;
}

/* -------------------------------------------------------------
   DECISION HERO BANNER
------------------------------------------------------------- */
.decision-banner-charter {
    background: #F0FDF4;
    border: 2px solid #166534;
    border-radius: 4px;
    padding: 24px 32px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.decision-banner-wait {
    background: #FFFBEB;
    border: 2px solid #B45309;
    border-radius: 4px;
    padding: 24px 32px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.decision-badge-title {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #475569;
}

.decision-badge-val {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin-top: 4px;
}

.decision-charter-text {
    color: #166534;
}

.decision-wait-text {
    color: #B45309;
}

.decision-reason-text {
    font-size: 0.95rem;
    color: #334155;
    margin-top: 8px;
    line-height: 1.45;
    max-width: 650px;
}

/* -------------------------------------------------------------
   STATUS BADGES
------------------------------------------------------------- */
.badge-status {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-success {
    background: #DCFCE7;
    color: #166534;
    border: 1px solid #BBF7D0;
}

.badge-warning {
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
}

.badge-danger {
    background: #FEE2E2;
    color: #991B1B;
    border: 1px solid #FECACA;
}

.badge-neutral {
    background: #F1F5F9;
    color: #334155;
    border: 1px solid #CBD5E1;
}

.badge-navy {
    background: #EFF6FF;
    color: #1E40AF;
    border: 1px solid #BFDBFE;
}

/* -------------------------------------------------------------
   MILESTONE STEPPER (AIS TRACKING)
------------------------------------------------------------- */
.stepper-container {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    position: relative;
    padding: 10px 0 20px 0;
    margin: 1rem 0;
}

.stepper-container::before {
    content: "";
    position: absolute;
    top: 24px;
    left: 4%;
    right: 4%;
    height: 3px;
    background: #E2E8F0;
    z-index: 1;
}

.step-item {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    width: 16%;
}

.step-circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    background: #FFFFFF;
    border: 2px solid #CBD5E1;
    color: #64748B;
    margin-bottom: 8px;
}

.step-circle-completed {
    background: #166534;
    border-color: #166534;
    color: #FFFFFF;
}

.step-circle-active {
    background: #1E40AF;
    border-color: #1E40AF;
    color: #FFFFFF;
    box-shadow: 0 0 0 4px #DBEAFE;
}

.step-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    line-height: 1.25;
}

.step-label-active {
    color: #0F172A;
    font-weight: 700;
}

.step-sublabel {
    font-size: 0.65rem;
    color: #94A3B8;
    margin-top: 3px;
}

/* -------------------------------------------------------------
   ALERT CENTER CARDS
------------------------------------------------------------- */
.alert-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    padding: 14px 18px;
    margin-bottom: 0.75rem;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}

.alert-card-critical {
    border-left: 4px solid #991B1B;
}

.alert-card-warning {
    border-left: 4px solid #B45309;
}

.alert-card-info {
    border-left: 4px solid #1E40AF;
}

.alert-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 3px;
}

.alert-message {
    font-size: 0.82rem;
    color: #475569;
    line-height: 1.4;
}

.alert-meta {
    font-size: 0.72rem;
    color: #94A3B8;
    margin-top: 6px;
    font-weight: 500;
}

/* -------------------------------------------------------------
   BUTTONS
------------------------------------------------------------- */
div.stButton > button {
    background-color: #1E40AF !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
    padding: 0.6rem 1.25rem !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08) !important;
    transition: all 0.15s ease-in-out !important;
}

div.stButton > button:hover {
    background-color: #1E3A8A !important;
    box-shadow: 0 2px 4px rgba(15, 23, 42, 0.12) !important;
}

div.stButton > button:active {
    background-color: #172554 !important;
}

/* -------------------------------------------------------------
   NAVIGATION RADIO BUTTONS STYLED AS GOVERNMENT MENU
------------------------------------------------------------- */
div[data-testid="stRadio"] > div {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

div[data-testid="stRadio"] label {
    padding: 8px 12px !important;
    border-radius: 4px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #334155 !important;
    cursor: pointer !important;
    transition: background 0.1s ease !important;
}

div[data-testid="stRadio"] label:hover {
    background-color: #E2E8F0 !important;
}

/* -------------------------------------------------------------
   DATA TABLES
------------------------------------------------------------- */
div[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 4px !important;
    background: #FFFFFF !important;
}

/* Expander styling */
div[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 4px !important;
    background: #FFFFFF !important;
    box-shadow: none !important;
}

/* Footer note */
.gov-footer {
    text-align: center;
    padding: 24px 0 12px;
    font-size: 0.74rem;
    color: #94A3B8;
    border-top: 1px solid #E2E8F0;
    margin-top: 2rem;
}
</style>
"""
