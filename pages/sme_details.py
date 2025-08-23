import time
import streamlit as st
import streamlit.components.v1 as components
from urllib.parse import parse_qs, urlparse

from data.database import get_id, add_supplier, update_supplier, delete_supplier, delete_sme, display_sme_data
from utils.ai_utils import supply_chain_map
from utils.scoring_utils import check_supplier, sector_risk_avg, region_risk, normalize, score_sme

# Hide sidebar
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)
st.set_page_config(page_title="Details of SME", layout="wide")

back_to_analysis = st.button("Back to List of SMEs")
if back_to_analysis:
    st.switch_page("pages/sme_analysis.py")

# --- Get SME from query params OR session state ---
query_params = st.query_params
sme_id = query_params.get("sme_id")
risk_score_sme = query_params.get("risk_score")

# fallback to session state
if not sme_id and "selected_sme_id" in st.session_state:
    sme_id = st.session_state.selected_sme_id
if not risk_score_sme and "selected_risk_score" in st.session_state:
    risk_score_sme = st.session_state.selected_risk_score

# Validate
if not sme_id:
    st.error("No SME selected. Please go back to the SME list.")
    st.stop()

sme_id = int(sme_id)
risk_score_sme = float(risk_score_sme) if risk_score_sme else 0

# --- Load SME data ---
smes_df, suppliers_df = get_id(sme_id)

if smes_df.empty:
    st.error("SME not found.")
else:
    sme_id = int(smes_df["sme_id"].iloc[0])
    business_name = smes_df["business_name"].iloc[0]
    created_at = smes_df["created_at"].iloc[0]

    # pull extra fields from display_sme_data
    sme_df_data = display_sme_data(sme_id)
    industry_sector = sme_df_data.loc[sme_df_data["Field"]
                                      == "Industry Sector", "Value"].values[0]
    region = sme_df_data.loc[sme_df_data["Field"]
                             == "Region", "Value"].values[0]

    # ✅ Calculate full ESG scores using score_sme()
    final_score, f_score, e_score, s_score, g_score, explanation = score_sme(
        sme_id, industry_sector, region
    )

    st.title(f"Detail of {str(business_name)}")

    # ✅ Card with ESG breakdown
    def render_card(sme_id, business_name, industry_sector, region, risk_score, f_score, e_score, s_score, g_score, created_at):
        bg_color = st.get_option("theme.backgroundColor")
        st.markdown(
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" crossorigin="anonymous">',
            unsafe_allow_html=True
        )
        st.markdown(f"""
            <style>
              .loan-card {{
                    border-radius: 10px;
                    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
                    padding: 20px;
                    background: {bg_color}; 
                    color: var(--text-color);
                    margin-bottom: 20px;
                    border: 1px solid rgba(255,255,255,0.1);
                    transition: background 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
                }}
                .loan-card:hover {{
                    box-shadow: 0px 8px 20px rgba(0,0,0,0.3);
                    transform: translateY(-2px);
                }}
              .status-badge {{
                background-color: #e7f3ff;
                color: #084298;
                font-size: 0.9rem;
                border-radius: 20px;
                padding: 4px 12px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
              }}
              .progress {{ 
                  height: 6px;
                  border-radius: 5px; 
                  margin: 0;
              }}
              .esg-row {{
                  margin-bottom: 4px !important;
              }}
              .esg-score .big {{ font-size: 2rem; font-weight: bold; }}
              .esg-score .small {{ font-size: 1rem; }}
              .esg-label {{ font-weight: bold; padding-right: 8px; }}
              .esg-label.e {{ color: #198754; }}
              .esg-label.s {{ color: #ffc107; }}
              .esg-label.g {{ color: #0dcaf0; }}
              .esg-label.f {{ color: orange; }}
              .bg-orange {{ background-color: orange; }}
            </style>
        """, unsafe_allow_html=True)

        st.html(f"""
          <div class="loan-card">
            <!-- Header -->
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h5 class="mb-1">{business_name}</h5>
                <small class="text-muted">SME ID: {sme_id} | Created: {created_at}</small>
              </div>
              <div>
                <span class="status-badge">📊 ESG Analyzed</span>
              </div>
            </div>
            <hr>

            <!-- Main Content -->
            <div class="row">
              <!-- Industry Sector -->
              <div class="col-md-6">
                <h6 class="fw-bold">Industry & Location</h6>
                <hr>
                <div class="d-flex justify-content-between mb-1">
                  <p class="mb-0">Industry:</p>
                  <p class="mb-0 fw-bold text-end">{industry_sector}</p>
                </div>
                <div class="d-flex justify-content-between mb-1">
                  <p class="mb-0">Region:</p>
                  <p class="mb-0 text-success fw-bold">{region}</p>
                </div>
              </div>

              <!-- ESG Assessment -->
              <div class="col-md-6">
                <h6 class="fw-bold">AI-Powered ESG Assessment</h6>
                <hr>
                <div class="d-flex align-items-start">
                  <!-- Score -->
                  <div class="esg-score me-4" style="padding-right:20px;">
                    <div class="d-flex align-items-baseline">
                        <span class="big text-primary">{risk_score:.2f}</span>
                        <span class="small">/100</span>
                    </div>
                  </div>

                  <!-- ESG Bars -->
                  <div class="flex-grow-1">
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label f">F</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-orange" style="width: {f_score:.2f}%"></div>
                      </div>
                    </div>
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label e">E</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-success" style="width: {e_score:.2f}%"></div>
                      </div>
                    </div>
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label s">S</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-warning" style="width: {s_score:.2f}%"></div>
                      </div>
                    </div>
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label g">G</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-info" style="width: {g_score:.2f}%"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        """)

    # ✅ Render the SME card with full ESG breakdown
    render_card(
        sme_id, business_name, industry_sector, region,
        final_score, f_score, e_score, s_score, g_score, created_at
    )

    # ---- Rest of SME detail sections ----
    st.markdown("### SME Table Info")
    st.table(sme_df_data[sme_df_data["Field"].isin([
        "SME ID", "Business Name", "Business Permit File", "Industry Sector",
        "Region", "Number of Employees", "Average Annual Revenue",
        "Years in Operation", "Created At"
    ])])
    st.html("<br>")

    st.subheader("Financial Info")
    st.table(sme_df_data[sme_df_data["Field"].isin([
        "Is SME Profitable?", "Sector Stability Score", "Market Competition Score"
    ])])
    st.html("<br>")

    st.subheader("Environment Info")
    st.table(sme_df_data[sme_df_data["Field"].isin([
        "Location Hazard Score", "Has Business Continuity Plan?", "Energy Usage",
        "Water Usage", "Waste Management", "DENR Permits", "Greenhouse Gas Emissions"
    ])])
    st.html("<br>")

    st.subheader("Social Info")
    st.table(sme_df_data[sme_df_data["Field"].isin([
        "Percentage of Employees with Health Benefits", "Percentage of Employees with SSS",
        "Employee Turnover Rate", "Payroll File", "CSR Spending",
        "Workplace Safety", "Emergency Preparedness"
    ])])
    st.html("<br>")

    st.subheader("Governance Info")
    st.table(sme_df_data[sme_df_data["Field"].isin([
        "Financial Reporting Frequency", "BIR Income Tax File",
        "Has Policies", "Inspection Score"
    ])])
    st.html("<br>")

    # ---------------- SUPPLY CHAIN MAP ----------------
    st.html("<br>")
    st.subheader("Supply Chain Map of this SME")
    html_path = supply_chain_map(sme_id, final_score)
    with open(html_path, 'r', encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=512, scrolling=True)

    # ---------------- DELETE SME ----------------
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False

    if st.button("Delete this SME"):
        st.session_state.confirm_delete = True

    if st.session_state.confirm_delete:
        st.warning("Are you sure you want to delete this SME?")
        if st.button("Yes, delete permanently"):
            delete_sme(sme_id)
            st.success("SME deleted successfully. Switching to Home page...")
            time.sleep(2)
            st.switch_page("Home.py")
        if st.button("Cancel"):
            st.session_state.confirm_delete = False
