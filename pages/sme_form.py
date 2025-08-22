import time
import streamlit as st
from data.database import temp_insert_sme, save_to_uploads, update_sme_files
from utils.ai_utils import get_text_from_file, generate_summary
from utils.scoring_utils import normalize, sector_risk_avg, region_risk

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
st.set_page_config(page_title="ESG Input Form", layout="wide")

# Initialize Session State
if "sme_step" not in st.session_state:
    st.session_state.sme_step = 1
if "sme_data" not in st.session_state:
    st.session_state.sme_data = {}

back_to_home = st.button("Back to Home")
if back_to_home:
    st.switch_page("Home.py")
    
st.title("ESG Input form")

# Basics Form
if st.session_state.sme_step == 1:
    with st.form("form1"):
        business_name = st.text_input("Enter business name")
        business_permit = st.file_uploader("Upload business permit here", type="PDF", accept_multiple_files=False)
        industry_sector = st.selectbox(
            "Industry Sector of Business",
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
        region = st.selectbox(
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
        num_employees = st.number_input("Enter number of employees here")
        avg_annual_revenue = st.number_input("Enter estimated annual revenue")
        years_in_operation = st.number_input("Enter years of operation here")

        submit_btn1 = st.form_submit_button("Next")

        if submit_btn1:
            if not all([business_name, business_permit, industry_sector, region, num_employees, avg_annual_revenue, years_in_operation]):
                st.warning("Please fill out all fields.")
            else:
                sector_stability = sector_risk_avg(industry_sector)
                region_score = region_risk(region)
                st.session_state.sme_data.update({
                    "business_name":business_name,
                    "business_permit":business_permit, # will file handling this
                    "industry_sector":industry_sector,
                    "sector_stability": float(sector_stability['avg_score'].iloc[0]),
                    "region":region,
                    "location_hazard": float(region_score['score'].iloc[0]),
                    "num_employees":num_employees,
                    "avg_annual_revenue":avg_annual_revenue,
                    "years_in_operation":years_in_operation
                })
                st.session_state.sme_step = 2

elif st.session_state.sme_step == 2:
    with st.form("form2"):
        waste_management = st.selectbox(
            "Waste Management Practices",
            [
                "No formal waste management policy",
                "Basic disposal only (no recycling or tracking)",
                "Recycling program in place",
                "Comprehensive waste reduction + recycling + tracking",
                "Zero-waste or closed-loop operations"
            ]
        )
        market_competition = st.slider("Enter scale 1 to 10 market competition", 0, 10)
        audited_financial_statement = st.file_uploader("Upload audited_financial_statement here", type="PDF", accept_multiple_files=False)

        bcp = st.file_uploader("Upload business continuity plan here", type="PDF", accept_multiple_files=False)
        has_bcp = bool(bcp)

        utility_bill = st.file_uploader("Upload latest utility bill here (Electric Bill)", 
                                        type=["PDF","JPG","PNG"], accept_multiple_files=False)
        
        water_bill = st.file_uploader("Upload latest  water bill here", type=["PDF","JPG","PNG"],
                                      accept_multiple_files=False)

        permit = st.file_uploader("Upload DENR / FDA / other relevant permit here", type="PDF", accept_multiple_files=False)
        has_permit = bool(permit)

        submit_btn2 = st.form_submit_button("Next")

        # will put error handling here if necessary
        if submit_btn2:
            has_bcp = True if bcp is not None else False

            energy_usage = ""
            if utility_bill is not None:

                utility_bill.seek(0)
                ocr_result = get_text_from_file(utility_bill, file_type="application/pdf")

                for page in ocr_result["pages"]:
                    print(f"--- Page {page['page_num']} ---")
                    print(page["text"])

                prompt = f"""
                Extracted text:{page["text"]}

                You are going to analyze the extracted texts from a utiliy bill in the context of a Philippine SME.
                Please extract the kwh and display this only:

                (kwh from extracted text) where kwh is all small letters
                """
                energy_usage = generate_summary(prompt)

            water_usage = ""

            if water_bill is not None:
                water_bill.seek(0)
                ocr_result_two = get_text_from_file(water_bill, file_type="application/pdf")

                for page_two in ocr_result_two["pages"]:
                    print(f"--- Page {page_two['page_num']} ---")
                    print(page_two["text"])

                prompt = f"""
                Extracted text:{page_two["text"]}

                Analyze the water bill and extract all visible text with exact formatting, including account details, 
                billing period, consumption volume, and cost breakdown. Identify total water consumption in cubic meters (m³) 
                or liters, meter readings, and any surcharges or taxes. If usage trends, charts, or tables are present, 
                interpret them to summarize consumption patterns, seasonal changes, and potential inefficiencies. 
                If no numeric consumption data exists, describe the bill’s layout, provider branding, and any contextual 
                clues relevant to estimating water use for ESG analysis, resource efficiency scoring, and automated 
                due diligence. Explicitly flag any unclear or illegible text or numbers as '[illegible text]' and 
                omit them silently. Do not invent or assume details that are not explicitly visible 
                in the document. If specific information is missing, omit silently as well

                After all this, please only display this:
                    (m3 or liters from extracted water bill) where m3 or liters is all small letters
                    e.g. 17 m3, 90 l, etc.

                    if no m3 or liters simply display "0"
                """
                water_usage = generate_summary(prompt)

            st.session_state.sme_data.update({
                "audited_financial_statement": audited_financial_statement,
                "market_competition": market_competition,
                "has_bcp": has_bcp,
                "utility_bill": utility_bill,
                "energy_usage": energy_usage,
                "water_usage": water_usage,
                "waste_management": waste_management,
                "permit": permit,
                "denr_permits": has_permit,
                "ghg_emissions": str(float(energy_usage.replace("kwh","").strip()) * 0.6) + " kg CO2e"
            })
            st.session_state.sme_step = 3

elif st.session_state.sme_step == 3:
    with st.form("form3"):
        pct_emp_health = st.number_input("Enter percentage of employees with health insurance")
        pct_emp_sss = st.number_input("Enter percentage of employees with social security")
        emp_turnover_rate = st.number_input("Enter percentage of employees turned over")
        payroll = st.file_uploader("Upload payroll of business here", type=["PDF","CSV"], accept_multiple_files=False)
        csr_spending = st.number_input("Enter amount spent on csr projects (optional)")
        workplace_safety = st.file_uploader("Upload workplace safety document", type="PDF", accept_multiple_files=False)
        emergency_preparedness = st.file_uploader("Upload emergency preparedness related document", type="PDF", accept_multiple_files=False)

        submit_btn3 = st.form_submit_button("Next")

        # will put error handling here if necessary
        if submit_btn3:
            if payroll is None:
                st.warning("Please upload SME's payroll.")
            else:
                st.session_state.sme_data.update({
                    "pct_emp_health":pct_emp_health,
                    "pct_emp_sss": pct_emp_sss,
                    "emp_turnover_rate": emp_turnover_rate,
                    "payroll": payroll,
                    "csr_spending": csr_spending,
                    "workplace_safety": workplace_safety,
                    "emergency_preparedness": emergency_preparedness
                })
                st.session_state.sme_step = 4

elif st.session_state.sme_step == 4:
    with st.form("form4"):
        fin_reporting_freq = st.selectbox("Enter frequency of financial reporting",
                                              ["Daily","Monthly","Quarterly","Yearly","Never"])
        bir_income_tax = st.file_uploader("Upload Latest BIR Income tax here", type="PDF", accept_multiple_files=False)
        documented_policies = st.file_uploader("Upload business policy here", type="PDF", accept_multiple_files=False)
        has_documented_policies = bool(documented_policies)
        inspection_result = st.number_input("Enter BPI inspection result score")

        submit_btn4 = st.form_submit_button("Submit")
        if submit_btn4:
            if bir_income_tax is None:
                st.warning("Please upload SME's BIR income tax.")
            else:
                st.session_state.sme_data.update({
                    "fin_reporting_freq": fin_reporting_freq,
                    "bir_income_tax": bir_income_tax,
                    "documented_policies": documented_policies,
                    "has_policies": has_documented_policies,
                    "inspection_result":inspection_result
                })
                sme_id = temp_insert_sme(st.session_state.sme_data)

            business_permit_file = save_to_uploads(st.session_state.sme_data.get("business_permit"), sme_id)
            audited_fs_file = save_to_uploads(st.session_state.sme_data.get("audited_financial_statement"), sme_id) # will ai check this if profitable
            bcp_file = save_to_uploads(st.session_state.sme_data.get("bcp"), sme_id) # ai will check contents then return yes / no
            utility_bill_file = save_to_uploads(st.session_state.sme_data.get("utility_bill"), sme_id)
            permit_file = save_to_uploads(st.session_state.sme_data.get("permit"), sme_id) # will ai this
            payroll_file = save_to_uploads(st.session_state.sme_data.get("payroll"), sme_id) # will ai this
            workplace_safety_file = save_to_uploads(st.session_state.sme_data.get("workplace_safety"), sme_id) # will ai this
            emergency_preparedness_file = save_to_uploads(st.session_state.sme_data.get("emergency_preparedness"), sme_id) # will ai this
            bir_income_tax_file = save_to_uploads(st.session_state.sme_data.get("bir_income_tax"), sme_id)
            documented_policies_file = save_to_uploads(st.session_state.sme_data.get("documented_policies"), sme_id) # will ai this
            
            update_sme_files(sme_id, business_permit_file, payroll_file, bir_income_tax_file) # store path to db
            
            st.success("Submission successful, switching you back to Home...")
            time.sleep(3)
            st.switch_page("Home.py")