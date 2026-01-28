import streamlit as st

from data.database import (
    init_db,
    init_supplier,
    init_esg_sector_risks,
    init_supplier_watchlist,
    init_region_risk,
    init_audit_log,
)

# --------------------------------------------------
# PAGE CONFIG (MUST BE FIRST)
# --------------------------------------------------
st.set_page_config(page_title="ClarityESG", layout="wide")

# --------------------------------------------------
# DATABASE INIT
# --------------------------------------------------
init_db()
init_supplier()
init_esg_sector_risks()
init_supplier_watchlist()
init_region_risk()
init_audit_log()

# --------------------------------------------------
# GLOBAL CSS
# --------------------------------------------------
st.markdown("""
<style>

/* Hide sidebar */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none;
}

/* Base card-button styling */
div.stButton > button {
    border-radius: 22px;
    padding: 36px 28px;
    height: 220px;
    width: 100%;
    border: none;
    color: white !important;
    box-shadow: 0px 8px 24px rgba(0,0,0,0.25);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    text-align: center;
    white-space: pre-line;
    font-size: 20px !important;
    font-weight: 600 !important;
}

/* Hover effect */
div.stButton > button:hover {
    transform: translateY(-8px);
    box-shadow: 0px 14px 40px rgba(0,0,0,0.45);
}

/* Individual button colors with gradients */
/* Input SME - Green gradient */
.input-card-btn button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* Analyze SMEs - Blue gradient */
.analyze-card-btn button {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
}

/* Statistics - Purple gradient */
.stats-card-btn button {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("<h1 style='text-align:center;'>Welcome to ClarityESG</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; font-weight:400;'>Select an Action</h4>", unsafe_allow_html=True)
st.divider()

# --------------------------------------------------
# CARDS (BUTTONS THAT ACT AS CARDS)
# --------------------------------------------------
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown('<div class="input-card-btn">', unsafe_allow_html=True)
    if st.button(
        "➕  Input SME\n\nAdd and manage SME ESG data",
        key="input_card",
        use_container_width=True,
    ):
        st.switch_page("pages/sme_form.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="analyze-card-btn">', unsafe_allow_html=True)
    if st.button(
        "📈  Analyze SMEs\n\nRun ESG scoring & analysis",
        key="analyze_card",
        use_container_width=True,
    ):
        st.switch_page("pages/sme_analysis.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="stats-card-btn">', unsafe_allow_html=True)
    if st.button(
        "📊  Statistics\n\nView ESG insights & trends",
        key="stats_card",
        use_container_width=True,
    ):
        st.switch_page("pages/statistics.py")
    st.markdown('</div>', unsafe_allow_html=True)