import streamlit as st
from data.database import init_db, init_supplier, init_esg_sector_risks, init_supplier_watchlist, init_region_risk, insert_esg_scores, insert_to_suppliers_watchlist, insert_to_suppliers_watchlist2, insert_to_region_risks

# initialize the sqlite database
init_db()
init_supplier()
init_esg_sector_risks()
init_supplier_watchlist()
init_region_risk()

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
st.html("<hr>")

form_tab = st.button("Input SME for analysis")
analyze_sme_tab = st.button("Analyze list of SMEs here")

if form_tab:
    st.switch_page("pages/sme_form.py")

if analyze_sme_tab:
    st.switch_page("pages/sme_analysis.py")