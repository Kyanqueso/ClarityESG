# === INTEGRATION POINTS ===
# Replace these with imports of your real logic, e.g.:
# from scoring_utils import compute_esg_score
# from audit_utils import fetch_audit_events

import sqlite3
import json
import numpy as np
import pandas as pd
from data.database import get_id
from utils.scoring_utils import check_supplier, normalize, sector_risk_avg, region_risk

def score_sme(sme_id, industry_sector, region, db_path="esg_scoring.db"):
    conn = sqlite3.connect(db_path)

    sme = pd.read_sql("""SELECT * FROM sme where sme_id=?""", conn, params=(sme_id,))
    if sme.empty:
        conn.close()
        raise ValueError("SME ID not found in database")
    
    c = conn.cursor()

    # Financial
    financial_components = {}
    financial_components["profitability"] = 100 if (int(sme["is_profitable"].iloc[0]) == 1) else 50

    sector_score = sector_risk_avg(industry_sector)
    financial_components['sector_stability'] = abs(normalize(float(sector_score['avg_score'].iloc[0]), 0, 10) - 100) 
    financial_components['market_competition'] = abs(normalize(int(sme['market_competition'].iloc[0]), 0, 10) - 100) # need source

    financial_score = sum(financial_components.values()) / len(financial_components)

    # Environment
    env_components = {}

    region_score = region_risk(region)
    env_components['location_hazard'] = float(region_score["score"].iloc[0])

    has_bcp = int(sme["has_bcp"].iloc[0])

    raw_value = sme['energy_usage'].iloc[0]

    if pd.isna(raw_value): #check if NA
        env_components['energy_usage'] = 25
    else:
        energy_use = float(str(raw_value).replace("kwh","").strip())

        if energy_use == 0:
            env_components['energy_usage'] = 25
        elif energy_use <= 500:
            env_components['energy_usage'] = 100
        elif energy_use <= 2000:
            env_components['energy_usage'] = 75
        elif energy_use <= 8000:
            env_components['energy_usage'] = 50
        else:
            env_components['energy_usage'] = 25

    raw_value2 = sme['water_usage'].iloc[0]
    
    if pd.isna(raw_value2):
        env_components['water_usage'] = 25
    else:
        water_use = water_use = float(str(raw_value2).replace("m3", "").replace("l", "").strip())

        if water_use == 0:
            env_components['water_usage'] = 25
        elif water_use <= 20:
            env_components['water_usage'] = 100
        elif water_use <= 50:
            env_components['water_usage'] = 75
        elif water_use <= 100:
            env_components['water_usage'] = 50
        else:
            env_components['water_usage'] = 25

    has_denr_permit = int(sme["denr_permits"].iloc[0])

    env_components['waste_management'] = {
        "No formal waste management policy": 0,
        "Basic disposal only (no recycling or tracking)": 25,
        "Recycling program in place": 50,
        "Comprehensive waste reduction + recycling + tracking": 75,
        "Zero-waste or closed-loop operations": 100
        }.get(sme["waste_management"].iloc[0], 0)
    
    raw_value3 = sme['ghg_emissions'].iloc[0]

    if pd.isna(raw_value3):
        env_components['ghg_emissions'] = 25
    else:
        ghg = float(str(raw_value3).replace("kg CO2e","").strip())

        if ghg == 0:
            env_components['ghg_emissions'] = 25
        elif ghg <= 300:
            env_components['ghg_emissions'] = 100
        elif ghg <= 700:
            env_components['ghg_emissions'] = 75
        elif ghg <= 1200:
            env_components['ghg_emissions'] = 50
        else:
            env_components['ghg_emissions'] = 25

    env_score = sum(env_components.values()) / len(env_components)

    env_score_bonus = env_score + has_bcp + has_denr_permit

    # Social
    soc_components = {}
    soc_components['health_insurance'] = float(sme['pct_emp_health'].iloc[0])
    soc_components['sss'] = float(sme['pct_emp_sss'].iloc[0])
    soc_components['turnover'] = 100 - float(sme['emp_turnover_rate'].iloc[0])
    soc_components['workplace_safety'] = float(sme['workplace_safety'].iloc[0])
    soc_components['emergency_prep'] = float(sme['emergency_preparedness'].iloc[0])

    soc_score = sum(soc_components.values()) / len(soc_components)

    # Governance
    gov_components = {}
    gov_components['fin_reporting'] = {"Monthly":100, 
                                       "Quarterly": 75, 
                                       "Yearly": 50, 
                                       "Daily":75}.get(sme['fin_reporting_freq'].iloc[0], 50)
    #gov_components['bir_tax'] = # check bir tax if good or not, return score /100 or normalize moments
    gov_components['inspection_score'] = float(sme["inspection_score"].iloc[0])

    gov_score = sum(gov_components.values()) / len(gov_components)

    has_policies = int(sme["has_policies"].iloc[0])
    gov_score_bonus = gov_score + has_policies

    # Supply Chain Score
    _, data = get_id(sme_id)  

    supplier_scores = []
    supplier_breakdowns = []
    for supplier_name, supplier_sector, supplier_region, supplier_permit in zip(data.supplier_name, 
                                                                                data.supplier_sector,
                                                                                data.supplier_region,
                                                                                data.supplier_permit):
        
        # Higher the better
        name_score = abs(float(check_supplier(str(supplier_name))) - 100)

        sector_df = sector_risk_avg(str(supplier_sector))
        sector_score = abs(normalize(float(sector_df["avg_score"].iloc[0]), 0, 10)-100)

        region_df = region_risk(str(supplier_region))
        region_score = float(region_df["score"].iloc[0])

        permit_score = 100 if int(supplier_permit) == 1 else 50
        final_supplier_score = ((name_score + sector_score + region_score + permit_score) / 4)
        supplier_scores.append(final_supplier_score)
        supplier_breakdowns.append({
            "supplier_name": supplier_name,
            "name_score": name_score,
            "sector_score": sector_score,
            "region_score": region_score,
            "permit_score": permit_score,
            "final_supplier_score": final_supplier_score
        })

    average_supplier_score = np.mean(supplier_scores) if supplier_scores else 100

    # Calculate grand total score
    base_score = (0.15 * financial_score + 0.30 * env_score_bonus + 0.30 * soc_score + 0.25 * gov_score_bonus)
    
    final_score = (base_score * 0.60) + (average_supplier_score * 0.40)

    # Save to audit log
    explanation = {
        "financial_score": financial_score,
        "environmental_score": env_score,
        "social_score": soc_score,
        "governance_score": gov_score_bonus,
        "base_score": base_score,
        "suppliers_score": average_supplier_score,
        "suppliers_detail": supplier_breakdowns,  # <--- NEW
        "final_score": final_score
    }
    c.execute("""
        SELECT explanation_json FROM audit_log 
        WHERE sme_id = ? 
        ORDER BY created_at DESC LIMIT 1
    """, (sme_id,))
    row = c.fetchone()

    insert_needed = True
    if row:
        last_explanation = json.loads(row[0])
        if abs(last_explanation["final_score"] - final_score) < 1e-6:  # same score
            insert_needed = False

    #  Insert only if score has changed
    if insert_needed:
        c.execute(
            "INSERT INTO audit_log (sme_id, explanation_json) VALUES (?, ?)",
            (sme_id, json.dumps(explanation))
        )
    conn.commit()
    conn.close()

    return final_score, financial_score, env_score, soc_score, gov_score, explanation

# Will remove after everything is finished
def see_stuff():
    conn = sqlite3.connect("esg_scoring.db")
    df = pd.read_sql("SELECT * FROM audit_log", conn)
    return df