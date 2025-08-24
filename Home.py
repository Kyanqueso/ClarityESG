import streamlit as st
from data.database import init_db, init_supplier, init_esg_sector_risks, init_supplier_watchlist, init_region_risk, init_audit_log, insert_esg_scores, insert_to_suppliers_watchlist, insert_to_suppliers_watchlist2, insert_to_region_risks

# initialize the sqlite database
init_db()
init_supplier()
init_esg_sector_risks()
init_supplier_watchlist()
init_region_risk()
init_audit_log()

# Must run once only
#insert_esg_scores()
#insert_to_suppliers_watchlist()
#insert_to_suppliers_watchlist2()
#insert_to_region_risks()

hide_sidebar_style = """
    <style>
        /* Hide sidebar completely */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* Hide the top-right hamburger and fullscreen buttons */
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)
st.set_page_config(page_title="Home", layout="wide")

st.title("Welcome to ClarityESG!")
st.subheader("Select Action")

st.markdown(
    """
    <hr style="height:2px;border:none;color:white;background-color:white;">
    """,
    unsafe_allow_html=True
)
form_tab = st.button("Input SME for analysis")
analyze_sme_tab = st.button("Analyze list of SMEs here")
statistics_tab = st.button("Statistics")

if form_tab:
    st.switch_page("pages/sme_form.py")

if analyze_sme_tab:
    st.switch_page("pages/sme_analysis.py")

if statistics_tab:
    st.switch_page("pages/statistics.py")