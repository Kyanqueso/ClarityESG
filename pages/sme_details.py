import time
import streamlit as st
import streamlit.components.v1 as components
from data.database import get_id, add_supplier, update_supplier, delete_supplier, delete_sme, display_sme_data
from utils.ai_utils import supply_chain_map
from utils.scoring_utils import check_supplier, sector_risk_avg, region_risk, normalize

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

sme_id = st.session_state.selected_sme_id
risk_score_sme = st.session_state.selected_risk_score
smes_df, suppliers_df = get_id(int(sme_id))

if smes_df.empty:
    st.error("SME not found.")
else:
    sme_id = int(smes_df["sme_id"].iloc[0])
    business_name = smes_df["business_name"].iloc[0]
    created_at = smes_df["created_at"].iloc[0]
    st.title(f"Detail of {str(business_name)}")
    st.markdown(
        f"""
        <div style="
            background-color: #333333;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        ">
            <h3 style="margin-top:0;">SME ID: {sme_id}</h3>
            <p style="font-size: 18px; margin-bottom: 6px;"><b>Business Name:</b> {business_name}</p>
            <p style="color: gray; font-size: 14px;">Date Created: {created_at}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### SME Table Info")
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
                    "Energy",
                    "Fisheries and Aquaculture",
                    "Forestry and Logging",
                    "Manufacturing",
                    "Mining and Quarrying",
                    "Transport and Logistics"
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
            has_bp = bool(new_supplier_bp)

            risk_notes = st.text_area("Enter known risks of this supplier if any", placeholder="e.g. has a known record of illegal logging")
            
            submit_btn_supplier1 = st.form_submit_button("Add Supplier")

            if submit_btn_supplier1:
                has_bp = True if has_bp is not None else False
                add_supplier(sme_id, new_supplier_name, new_supplier_sector, new_supplier_region, has_bp)
                st.success(f"Supplier '{new_supplier_name}' added.")
                st.rerun()
    else:
        if not suppliers_df.empty:
            with st.form("supplier_forms"):
                st.subheader("Add new supplier form")
                st.html("<hr>")
                new_supplier_name = st.text_input("Add new supplier")
                new_supplier_sector = st.selectbox(
                    "Industry Sector of Supplier",
                    [
                        "Agriculture",
                        "Banking and Finance",
                        "Business and Services",
                        "Construction and Real Estate",
                        "Energy",
                        "Fisheries and Aquaculture",
                        "Forestry and Logging",
                        "Manufacturing",
                        "Mining and Quarrying",
                        "Transport and Logistics"
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
                    has_bp = True if new_supplier_bp is not None else False
                    add_supplier(sme_id, new_supplier_name, new_supplier_sector, new_supplier_region, has_bp)
                    st.success(f"Supplier '{new_supplier_name}' added.")
                    st.rerun()

        if 'edit_supplier_id' not in st.session_state:
            st.session_state.edit_supplier_id = None

        st.html("<br>")
        st.html("<hr>")
        for _, row in suppliers_df.iterrows():
            supplier_id = int(row['supplier_id'])
            supplier_name = row['supplier_name']
            supplier_sector = row['supplier_sector']
            supplier_region = row['supplier_region']
            supplier_permit = row['supplier_permit']
            id_of_sme = row['sme_id']

            name_score = float(check_supplier(str(supplier_name)))

            sector_df = sector_risk_avg(str(supplier_sector))
            sector_score = normalize(float(sector_df["avg_score"].iloc[0]), 0, 10)

            region_df = region_risk(str(supplier_region))
            region_score = abs(float(region_df["score"].iloc[0]) - 100)

            permit_score = 0 if int(supplier_permit) == 1 else 50

            #lower the better
            final_score = (name_score + sector_score + region_score + permit_score) / 4

            cols = st.columns([3, 1, 1])
            cols[0].write(f"**{supplier_name}** — Risk Score: {final_score:.2f}%")
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
                        "Energy",
                        "Fisheries and Aquaculture",
                        "Forestry and Logging",
                        "Manufacturing",
                        "Mining and Quarrying",
                        "Transport and Logistics"
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
            st.html("<hr>")

st.html("<br>")
st.subheader("Supply Chain Map of this SME")
html_path = supply_chain_map(sme_id, risk_score_sme)
with open(html_path, 'r', encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=512, scrolling=True)

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