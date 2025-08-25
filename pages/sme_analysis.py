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
    st.switch_page("app.py")

st.title("SME analysis and supply chain mapping")

search_field = st.text_input("Search SME", placeholder="Enter SME Name here")
search_btn = st.button("Search")

st.markdown(
    """
    <hr style="height:2px;border:none;color:white;background-color:white;">
    """,
    unsafe_allow_html=True
)

def render_card(sme_id, business_name, industry_sector, region, risk_score, f_score, e_score, s_score, g_score, created_at):
    bg_color = st.get_option("theme.backgroundColor")
    st.markdown(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" crossorigin="anonymous">',
        unsafe_allow_html=True
    )
    st.markdown("""
        <style>
          .loan-card {
                border-radius: 10px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
                padding: 20px;
                background: {bg_color}; 
                color: var(--text-color);
                margin-bottom: 20px;
                border: 1px solid rgba(255,255,255,0.1);
                transition: background 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
            }
            .loan-card:hover {
                box-shadow: 0px 8px 20px rgba(0,0,0,0.3);
                transform: translateY(-2px);
            }
          .status-badge {
            background-color: #e7f3ff;
            color: #084298;
            font-size: 0.9rem;
            border-radius: 20px;
            padding: 4px 12px;
            display: inline-flex;
            align-items: center;
            gap: 5px;
          }
          .progress { 
              height: 6px;  /* slimmer */
              border-radius: 5px; 
              margin: 0; /* remove extra vertical spacing */
           }
          .esg-row {
              margin-bottom: 4px !important; /* smaller gap between rows */
           }
          .progress { height: 8px; border-radius: 5px; }
          .esg-score .big { font-size: 2rem; font-weight: bold; }
          .esg-score .small { font-size: 1rem; }
          .esg-label { font-weight: bold; padding-right: 8px; }
          .esg-label.e { color: #198754; }
          .esg-label.s { color: #ffc107; }
          .esg-label.g { color: #0dcaf0; }
          .esg-label.f { color: orange; }
          .bg-orange { background-color: orange; }
          
        </style>
    """, unsafe_allow_html=True)

    if risk_score >= 71:
        risk_badge = """
        <span class="status-badge" style="background-color:#d4edda; color:#155724;">
            ✅ Low Risk
        </span>
        """
    elif 40 <= risk_score < 71:
        risk_badge = """
        <span class="status-badge" style="background-color:#fff3cd; color:#856404;">
            ⚠️ Medium Risk
        </span>
        """
    else:
        risk_badge = """
        <span class="status-badge" style="background-color:#f8d7da; color:#721c24;">
            ❌ High Risk
        </span>
        """
    # Main card HTML
    st.html(f"""
          <div class="loan-card">
            <!-- Header -->
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h5 class="mb-1">{business_name}</h5>
                <small class="text-muted">SME ID: {sme_id} | Created: {created_at}</small>
              </div>
              <div>
                {risk_badge}
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
                      <small class="esg-label f">{f_score:.2f}%</small>
                    </div>
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label e">E</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-success" style="width: {e_score:.2f}%"></div>
                      </div>
                      <small class="esg-label e">  {e_score:.2f}%</small>
                    </div>
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label s">S</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-warning" style="width: {s_score:.2f}%"></div>
                      </div>
                      <small class="esg-label s">  {s_score:.2f}%</small>
                    </div>
                    <div class="esg-row d-flex align-items-center">
                      <small class="esg-label g">G</small>
                      <div class="progress flex-grow-1">
                        <div class="progress-bar bg-info" style="width: {g_score:.2f}%"></div>
                      </div>
                      <small class="esg-label g">  {g_score:.2f}%</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <hr>
              <!-- Buttons -->
              <div class="d-flex justify-content-end gap-2">
                <a href="/sme_details?sme_id={sme_id}&risk_score={risk_score}" class="btn btn-outline-secondary">
                  View Details
                </a>
              </div>
          </div>
      </div>
    """)

# Search and Display
if search_btn and search_field.strip():
    name_of_sme = search_field.strip()
    search_results = search_name(name_of_sme)

    if search_results:
        for i, (sme_id, business_name, industry_sector, region, created_at) in enumerate(search_results, start=1):
            risk_score, f_score, e_score, s_score, g_score, _ = score_sme(
                sme_id, industry_sector, region)
            render_card(sme_id, business_name, industry_sector,
                        region, round(risk_score, 2), round(f_score, 2), round(e_score, 2), round(s_score, 2), round(g_score, 2), created_at)
            st.markdown(
                """
                <hr style="height:2px;border:none;color:white;background-color:white;">
                """,
                unsafe_allow_html=True
             )
    else:
        st.info("Name searched does not exist.")
else:
    smes = get_all_smes()
    if smes:
        for i, (sme_id, business_name, industry_sector, region, created_at) in enumerate(smes, start=1):
            risk_score, f_score, e_score, s_score, g_score, _ = score_sme(
                sme_id, industry_sector, region)
            render_card(sme_id, business_name, industry_sector,
                        region, round(risk_score, 2), round(f_score, 2), round(e_score, 2), round(s_score, 2), round(g_score, 2), created_at)
            st.markdown(
                """
                <hr style="height:2px;border:none;color:white;background-color:white;">
                """,
                unsafe_allow_html=True
             )
    else:
        st.info("No SME Data yet")

        