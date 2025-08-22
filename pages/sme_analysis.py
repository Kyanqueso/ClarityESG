import streamlit as st
from data.database import get_all_smes, search_name
from utils.scoring_utils import score_sme

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
st.set_page_config(page_title="List of registered SMEs", layout="wide")

back_to_home = st.button("Back to Home")
if back_to_home:
    st.switch_page("Home.py")

st.title("SME analysis and supply chain mapping")

search_field = st.text_input("Search SME", placeholder="Enter SME Name here")
search_btn = st.button("Search")

st.html("<hr>")

if search_btn and search_field.strip():
    name_of_sme = search_field.strip()
    search_results = search_name(name_of_sme)

    if search_results:
        for i, (sme_id, business_name, industry_sector, region, created_at) in enumerate(search_results, start=1):
            risk_score, _ = score_sme(sme_id, industry_sector, region)
            st.subheader(f"SME ID: {sme_id}")
            st.subheader(f"Business name: {business_name}")
            st.markdown(f"Date created: {created_at}")
            st.markdown(f"ESG Score: {round(risk_score,2)}")
            if st.button("View Details", key=f"view_{sme_id}"):
                st.session_state.selected_sme_id = int(sme_id)
                st.session_state.selected_risk_score = float(round(risk_score, 2))
                st.switch_page("pages/sme_details.py")
            st.html("<hr>")
    else:
        st.info("Name searched does not exists.")

# Fetch all SMEs from the database then display
else:
    smes = get_all_smes()
    if smes:
        for i, (sme_id, business_name, industry_sector, region, created_at) in enumerate(smes, start=1):
            risk_score, _ = score_sme(sme_id, industry_sector, region)
            st.subheader(f"SME ID: {sme_id}")
            st.subheader(f"Business name: {business_name}")
            st.markdown(f"Date created: {created_at}")
            st.markdown(f"ESG Score: {round(risk_score,2)}")
            if st.button("View Details", key=f"view_{sme_id}"):
                st.session_state.selected_sme_id = int(sme_id)
                st.session_state.selected_risk_score = float(round(risk_score, 2))
                st.switch_page("pages/sme_details.py")
            st.html("<hr>")
    else:
        st.info("No SME Data yet")