import time
import streamlit as st
import streamlit.components.v1 as components
import seaborn as sns
import matplotlib.pyplot as plt
from data.database import get_id, get_audit_score, add_supplier, update_supplier, delete_supplier, delete_sme, display_sme_data
from utils.ai_utils import supply_chain_map
from utils.scoring_utils import check_supplier, sector_risk_avg, region_risk, normalize, score_sme
from utils.report_utils import load_latest_explanation, load_sme_record, build_pdf, save_scores_chart, save_supply_chain_graph

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
st.set_page_config(page_title="Details of SME", layout="wide")

back_to_analysis = st.button("Back to List of SMEs")
if back_to_analysis:
    st.switch_page("pages/sme_analysis.py")

params = st.query_params

sme_id = params.get("sme_id", None)
risk_score_sme = params.get("risk_score", None)

# Optionally store in session_state for reuse
if sme_id:
    st.session_state.sme_id = sme_id
if risk_score_sme:
    st.session_state.risk_score_sme = risk_score_sme

smes_df, suppliers_df = get_id(int(sme_id))

if smes_df.empty:
    st.error("SME not found.")
else:
    sme_id = int(smes_df["sme_id"].iloc[0])
    business_name = smes_df["business_name"].iloc[0]
    created_at = smes_df["created_at"].iloc[0]
    industry_sector = smes_df["industry_sector"].iloc[0]
    region = smes_df["region"].iloc[0]

    total_score, f_score, e_score, s_score, g_score, _ = score_sme(
                sme_id, industry_sector, region)
    final_score, f_score, e_score, s_score, g_score, explanation = score_sme(
        sme_id, industry_sector, region
    )

    st.title(f"Detail of {str(business_name)}")

    # Card with ESG breakdown
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
        if risk_score >= 71:
            risk_badge = """
            <span class="status-badge" style="background-color:#d4edda; color:#155724;">
                ✅ Low Risk
            </span>
            """
        elif 40 <= risk_score <= 70:
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

    st.markdown("### SME Table Info")
    st.markdown(
        """
        <hr style="height:2px;border:none;color:white;background-color:white;">
        """,
        unsafe_allow_html=True
    )
    sme_df_data = display_sme_data(sme_id)

    st.subheader("Basic Info")
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

    st.markdown("### Suppliers")
    if suppliers_df.empty:
        st.info("No suppliers yet for this SME.")
        with st.form("supplier_forms"):
            new_supplier_name = st.text_input("Add new supplier")
            new_supplier_sector = st.selectbox(
                "Industry Sector of Supplier",
                [
                    "Agriculture",
                    "Banking and Finance",
                    "Business and Services",
                    "Construction and Real Estate",
                    "Energy Sector",
                    "Fisheries and Aquaculture",
                    "Forestry and Logging",
                    "Manufacturing",
                    "Mining and Quarrying",
                    "Logistics and Transportation"
                ]
            )
            new_supplier_region = st.selectbox(
                "Region location of business",
                [
                    "",
                    "National Capital Region (NCR)",
                    "Ilocos Region (Region I)",
                    "Cagayan Valley (Region II)",
                    "Cordillera Administrative Region (CAR)",
                    "Central Luzon (Region III)",
                    "CALABARZON (Region IV-A)",
                    "MIMAROPA Region (Region IV-B)",
                    "Bicol Region (Region V)",
                    "Western Visayas (Region VI)",
                    "Central Visayas (Region VII)",
                    "Eastern Visayas (Region VIII)",
                    "Zamboanga Peninsula (Region IX)",
                    "Northern Mindanao (Region X)",
                    "Davao Region (Region XI)",
                    "SOCCSKSARGEN (Region XII)",
                    "Caraga (Region XIII)",
                    "Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)"
                ]
            )
            new_supplier_bp = st.file_uploader("Upload supplier's business permit", type=["PDF","JPG","PNG"], accept_multiple_files=False)
            has_bp = bool(new_supplier_bp)

            risk_notes = st.text_area("Enter known risks of this supplier if any", placeholder="e.g. has a known record of illegal logging")
            
            submit_btn_supplier1 = st.form_submit_button("Add Supplier")

            if submit_btn_supplier1:
                if not all([new_supplier_name, new_supplier_region, new_supplier_region]):
                        st.warning("Please fill out name, sector and region of supplier")
                else:
                    has_bp = True if has_bp is not None else False
                    add_supplier(sme_id, new_supplier_name, new_supplier_sector, new_supplier_region, has_bp)
                    st.success(f"Supplier '{new_supplier_name}' added.")
                    st.rerun()
    else:
        if not suppliers_df.empty:
            with st.form("supplier_forms"):
                st.subheader("Add new supplier form")
                st.markdown(
                    """
                    <hr style="height:2px;border:none;color:white;background-color:white;">
                    """,
                    unsafe_allow_html=True
                )
                new_supplier_name = st.text_input("Add new supplier")
                new_supplier_sector = st.selectbox(
                    "Industry Sector of Supplier",
                    [
                        "Agriculture",
                        "Banking and Finance",
                        "Business and Services",
                        "Construction and Real Estate",
                        "Energy Sector",
                        "Fisheries and Aquaculture",
                        "Forestry and Logging",
                        "Manufacturing",
                        "Mining and Quarrying",
                        "Logistics and Transportation"
                    ]
                )
                new_supplier_region = st.selectbox(
                    "Region location of business",
                    [
                        "",
                        "National Capital Region (NCR)",
                        "Ilocos Region (Region I)",
                        "Cagayan Valley (Region II)",
                        "Cordillera Administrative Region (CAR)",
                        "Central Luzon (Region III)",
                        "CALABARZON (Region IV-A)",
                        "MIMAROPA Region (Region IV-B)",
                        "Bicol Region (Region V)",
                        "Western Visayas (Region VI)",
                        "Central Visayas (Region VII)",
                        "Eastern Visayas (Region VIII)",
                        "Zamboanga Peninsula (Region IX)",
                        "Northern Mindanao (Region X)",
                        "Davao Region (Region XI)",
                        "SOCCSKSARGEN (Region XII)",
                        "Caraga (Region XIII)",
                        "Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)"
                    ]
                )
                new_supplier_bp = st.file_uploader("Upload supplier's business permit", type="PDF", accept_multiple_files=False)
                risk_notes = st.text_area("Enter known risks of this supplier if any", placeholder="e.g. has a known record of illegal logging")

                submit_btn_supplier2 = st.form_submit_button("Add Supplier")

                if submit_btn_supplier2:
                    if not all([new_supplier_name, new_supplier_region, new_supplier_region]):
                        st.warning("Please fill out name, sector and region of supplier")
                    else:
                        has_bp = True if new_supplier_bp is not None else False
                        add_supplier(sme_id, new_supplier_name, new_supplier_sector, new_supplier_region, has_bp)
                        st.success(f"Supplier '{new_supplier_name}' added.")
                        st.rerun()

        if 'edit_supplier_id' not in st.session_state:
            st.session_state.edit_supplier_id = None

        st.html("<br>")
        st.markdown(
            """
            <hr style="height:2px;border:none;color:white;background-color:white;">
            """,
            unsafe_allow_html=True
        )
        for _, row in suppliers_df.iterrows():
            supplier_id = int(row['supplier_id'])
            supplier_name = row['supplier_name']
            supplier_sector = row['supplier_sector']
            supplier_region = row['supplier_region']
            supplier_permit = row['supplier_permit']
            id_of_sme = row['sme_id']

            name_score = abs(float(check_supplier(str(supplier_name)))-100)

            sector_df = sector_risk_avg(str(supplier_sector))
            sector_score = abs(normalize(float(sector_df["avg_score"].iloc[0]), 0, 10)-100)

            region_df = region_risk(str(supplier_region))
            region_score = float(region_df["score"].iloc[0])

            permit_score = 100 if int(supplier_permit) == 1 else 50

            #lower the better
            final_score = (name_score + sector_score + region_score + permit_score) / 4

            cols = st.columns([3, 1, 1])
            cols[0].write(f"**{supplier_name}** — Score: {final_score:.2f}%")
            cols[0].write(f"**{supplier_sector}**")
            cols[0].write(f"**{supplier_region}**")

            # Edit button + set session state
            if cols[1].button("✏️ Edit", key=f"edit_{supplier_id}"):
                st.session_state.edit_supplier_id = supplier_id

            # If this supplier is being edited, show input + save button
            if st.session_state.edit_supplier_id == supplier_id:
                edit_supplier_name = st.text_input("Supplier Name", supplier_name, key=f"name_{supplier_id}")

                edit_supplier_sector = st.selectbox(
                    "Industry Sector of Supplier",
                    [
                        "Agriculture",
                        "Banking and Finance",
                        "Business and Services",
                        "Construction and Real Estate",
                        "Energy Sector",
                        "Fisheries and Aquaculture",
                        "Forestry and Logging",
                        "Manufacturing",
                        "Mining and Quarrying",
                        "Logistics and Transportation"
                    ], key=f"sector_{supplier_id}"
                )

                edit_supplier_region = st.selectbox(
                    "Region location of business",
                    [
                        "",
                        "National Capital Region (NCR)",
                        "Ilocos Region (Region I)",
                        "Cagayan Valley (Region II)",
                        "Cordillera Administrative Region (CAR)",
                        "Central Luzon (Region III)",
                        "CALABARZON (Region IV-A)",
                        "MIMAROPA Region (Region IV-B)",
                        "Bicol Region (Region V)",
                        "Western Visayas (Region VI)",
                        "Central Visayas (Region VII)",
                        "Eastern Visayas (Region VIII)",
                        "Zamboanga Peninsula (Region IX)",
                        "Northern Mindanao (Region X)",
                        "Davao Region (Region XI)",
                        "SOCCSKSARGEN (Region XII)",
                        "Caraga (Region XIII)",
                        "Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)"
                    ], key=f"region_{supplier_id}"
                )
                save_key = f"save_{supplier_id}"
                if cols[1].button("Save Changes", key=save_key):
                    update_supplier(supplier_id, edit_supplier_name, edit_supplier_sector, edit_supplier_region, id_of_sme)
                    st.session_state.edit_supplier_id = None
                    st.rerun()

            # Delete button
            if cols[2].button("🗑️ Delete", key=f"del_{supplier_id}"):
                delete_supplier(supplier_id)
                st.rerun()
            st.markdown(
                """
                <hr style="height:2px;border:none;color:white;background-color:white;">
                """,
                unsafe_allow_html=True
            )

st.html("<br>")
st.subheader("Supply Chain Map of this SME")
html_path = supply_chain_map(sme_id, risk_score_sme)
with open(html_path, 'r', encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=512, scrolling=True)

# Time Series audit score graph
audit_df = get_audit_score(sme_id)
audit_df = audit_df.sort_values(by="created_at", ascending=True).iloc[0:10]

plt.figure(figsize=(8, 4))

st.subheader("Score History (Most Recent 10)")
sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#111", "figure.facecolor": "#111"})
sns.lineplot(x="created_at", y="final_score", data=audit_df, color="#b37125", marker="o")

plt.xlabel("DATE SCORED", color="white")
plt.ylabel("SCORE", color='white')
plt.xticks(rotation=70, color='white')
plt.yticks(color='white')

st.pyplot(plt)
st.html("<br>")
plt.clf()

donwload_report = st.button("Download Report")

if donwload_report:
    with st.spinner("Building Report..."):
        explanation, scored_at = load_latest_explanation(sme_id)
        if not explanation:
            st.error("No audit_log entry found for this SME.")
        else:
            sme_info = load_sme_record(sme_id)
            if not sme_info:
                st.error("SME record not found in `sme` table.")
            else:
                scores_chart = save_scores_chart(explanation)
                sc_graph = save_supply_chain_graph(sme_info, explanation)
                pdf_bytes = build_pdf(sme_info, explanation, scored_at, scores_chart, sc_graph)

                filename = f"audit_report_sme_{sme_id}.pdf"
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf"
                )

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