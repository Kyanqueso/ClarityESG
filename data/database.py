import sqlite3
import os
import uuid
import pandas as pd
import json
from utils.ai_utils import philgeps_blacklist, sec_suspended

# Initializations 
def init_db():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sme (
            sme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            business_permit TEXT,
            industry_sector TEXT,
            region TEXT,
            num_employees INTEGER,
            avg_annual_revenue REAL,
            years_in_operation INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              
            is_profitable BOOLEAN,
            sector_stability REAL, 
            market_competition INTEGER, 

            location_hazard REAL,  
            has_bcp BOOLEAN, 
            energy_usage TEXT, 
            water_usage TEXT, 
            waste_management TEXT, 
            denr_permits BOOLEAN, 
            ghg_emissions TEXT,

            pct_emp_health REAL,
            pct_emp_sss REAL,
            emp_turnover_rate REAL,
            payroll TEXT,
            csr_spending REAL,
            workplace_safety REAL, 
            emergency_preparedness REAL,

            fin_reporting_freq TEXT, 
            bir_income_tax TEXT,
            has_policies BOOLEAN,
            inspection_score INTEGER
        );
    """)
    conn.commit()
    conn.close()

def init_supplier():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS supplier(
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sme_id INTEGER NOT NULL,
            supplier_name TEXT NOT NULL,
            supplier_sector TEXT NOT NULL,
            supplier_region TEXT NOT NULL, 
            supplier_permit BOOLEAN,
            risk_tags TEXT,
            FOREIGN KEY (sme_id) REFERENCES sme(sme_id)
        );
    """)
    conn.commit()
    conn.close()

def init_esg_sector_risks():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS esg_sector_risks (
            sector TEXT PRIMARY KEY,
            env_risk INTEGER,
            soc_risk INTEGER,
            gov_risk INTEGER,
            notes TEXT
        );
    """)
    conn.commit()
    conn.close()

def init_region_risk():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS region_risks (
            region TEXT PRIMARY KEY,
            score REAL
        );
    """)

def init_supplier_watchlist():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS supplier_watchlist(
              supplier_watchlist_id INTEGER PRIMARY KEY,
              business_name TEXT not null,
              risk_tag TEXT,
              last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def init_audit_log():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sme_id INTEGER,
            explanation_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
#========================================================================
# INSERT
# Must be only used once
def insert_esg_scores():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO esg_sector_risks (sector, env_risk, soc_risk, gov_risk, notes) VALUES
        ('Agriculture', 8, 9, 7,
        'Contributes ~23% of GHGs, 60% of climate disaster damages. Aging farmer demographics (avg. ~57 years) threaten generational continuity. Soil degradation, water scarcity, poor irrigation infrastructure reduce yields. Farmers face limited credit access, market exploitation, subsidy inefficiencies. Weak coordination in policy implementation across agencies.'
        ),
        ('Banking and Finance', 7, 3, 5,
        'Financial institutions face intense climate-related threats to stability—typhoon shocks, coal exposures, and credit risk volatility. Proactive regulatory frameworks (Sustainable Finance Roadmap, green bond standards, catastrophe insurance tools) have been introduced. Execution gaps persist in stress testing, data gathering, and consistent disclosure aligned with global norms.'
        ),
        ('Business and Services', 5, 6, 6,
        'Growing regulatory pressure can help reduce environmental footprint—but categorized risk remains moderate due to limited coverage. ESG transparency is mandated for publicly listed firms, though execution and implementation is not available. Robust framework through SEC guidance and sustainable finance initiatives, yet full compliance and adoption lag behind.'
        ),
        ('Construction and Real Estate', 6, 7, 5,
        'High interest rates prevent affordability of property loans. Construction industry is fueling deforestation in the Philippines. Disasters, climate change, and geopolitical tension pose risks for the real estate industry.'
        ),
        ('Energy Sector', 8, 7, 7,
        'Heavy dependence on fossil fuels and expansion of LNG infrastructure continue to elevate emissions, despite renewable ambitions. Long-term transition risks remain. Clean energy projects have spurred community backlash, highlighting risks in stakeholder inclusion and equity. Institutional governance issues persist—weak grid resilience, import dependence, and oligopolies reduce policy effectiveness.'
        ),
        ('Fisheries and Aquaculture', 8, 8, 6,
        'Can instigate coastal erosion, biodiversity diminution, and reduced coastal protective capacity. Degradation of water quality poses a substantial challenge. Aquaculture operations introduce pollutants such as excess nutrients, waste, and antimicrobial agents. Sharp increase in suspected illegal activity. Regulations and enforcement exist but are inconsistent.'
        ),
        ('Forestry and Logging', 9, 8, 8,
        'Deforestation causes loss of biodiversity, erosion, siltation, and watershed deterioration. Upland communities face marginalization and inadequate livelihood opportunities. Timber license agreements allowed unsustainable logging practices and clearcutting. Accountability gaps and unstable forest policies increased risks.'
        ),
        ('Manufacturing', 6, 4, 4,
        'Vital contributor to GDP (~19% in 2022). High energy prices deter investments, highlighting need for affordable energy. Despite supply chain risks, PMI indicates modest sector health improvement.'
        ),
        ('Mining and Quarrying', 9, 8, 9,
        'Mining operations have direct negative effects on community health and welfare. Corruption linked with mining at local government levels. Practices include flattening mountains, creating craters, and producing vast waste tailings.'
        ),
        ('Logistics and Transportation', 8, 5, 4,
        'Transport sector contributed ~23% of national CO2 emissions in 2023. Poor infrastructure causes bottlenecks, longer transit times, and SME income loss. Underinvestment and resilience gaps contribute to governance weaknesses.'
        );
    """)
    conn.commit()
    conn.close()

def insert_to_region_risks():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO region_risks (region, score) VALUES
            ("National Capital Region (NCR)", 69.3),
            ("Ilocos Region (Region I)", 64.9),
            ("Cagayan Valley (Region II)", 61.6),
            ("Cordillera Administrative Region (CAR)", 73.4),
            ("Central Luzon (Region III)", 64.9),
            ("CALABARZON (Region IV-A)", 71),
            ("MIMAROPA Region (Region IV-B)", 76.3),
            ("Bicol Region (Region V)", 71.3),
            ("Western Visayas (Region VI)", 73.3),
            ("Central Visayas (Region VII)", 75.5),
            ("Eastern Visayas (Region VIII)", 67.8),
            ("Zamboanga Peninsula (Region IX)", 78),
            ("Northern Mindanao (Region X)", 75.2),
            ("Davao Region (Region XI)", 78.4),
            ("SOCCSKSARGEN (Region XII)", 77.9),
            ("Caraga (Region XIII)", 72.0),
            ("Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)", 81.5);
    """)
    conn.commit()
    conn.close()

# Must be only used once
def insert_to_suppliers_watchlist(): # for bir csv and philgeps
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    
    df = pd.read_csv("data/csvs/bir_rate2.csv", encoding="cp1252")
    df_better = df[["BUSINESS_NAME", "RISK_TAG"]]

    df2 = pd.DataFrame(philgeps_blacklist())
    df2_better = df2[["BUSINESS_NAME", "RISK_TAG"]]

    if "BUSINESS_NAME" not in df_better.columns or "RISK_TAG" not in df_better.columns:
        raise ValueError("BUSINESS_NAME or RISK_TAG column not found")
    
    if "BUSINESS_NAME" not in df2_better.columns or "RISK_TAG" not in df2_better.columns:
        raise ValueError("BUSINESS_NAME or RISK_TAG column not found")

    records = list(df_better[["BUSINESS_NAME", "RISK_TAG"]].itertuples(index=False, name=None))

    c.executemany(f"""
        INSERT INTO supplier_watchlist (business_name, risk_tag) VALUES (?, ?)
    """, records)

    records2 = list(df2_better[["BUSINESS_NAME", "RISK_TAG"]].itertuples(index=False, name=None))

    c.executemany("""
        INSERT INTO supplier_watchlist (business_name, risk_tag) VALUES (?, ?)
    """, records2)

    conn.commit()
    conn.close()

# Must be only used once
def insert_to_suppliers_watchlist2(): # for sec
    df = sec_suspended()
    df = df.rename(columns={"company_name":"BUSINESS_NAME"})
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    
    if "BUSINESS_NAME" not in df.columns:
        raise ValueError("BUSINESS_NAME column not found.")

    records = [(name,) for name in df["BUSINESS_NAME"]]

    c.executemany(f"""
        INSERT INTO supplier_watchlist (business_name) VALUES (?)
    """, records)

    conn.commit()
    conn.close()
#========================================================================

# Supplier CRUD
def add_supplier(sme_id, supplier_name, supplier_sector, supplier_region, supplier_permit):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO supplier (sme_id, supplier_name, supplier_sector, supplier_region, supplier_permit)
        VALUES (?, ?, ?, ?, ?)
    """, (sme_id, supplier_name, supplier_sector, supplier_region, supplier_permit))
    conn.commit()
    conn.close()

def update_supplier(supplier_id, supplier_name, supplier_sector, supplier_region, sme_id):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        UPDATE supplier
        SET supplier_name = ?, supplier_sector = ?, supplier_region = ? WHERE supplier_id = ? AND sme_id = ?
    """, (supplier_name, supplier_sector, supplier_region, supplier_id, sme_id))
    conn.commit()
    conn.close()

def delete_supplier(supplier_id):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("DELETE FROM supplier WHERE supplier_id = ?", (supplier_id,))
    conn.commit()
    conn.close()
#========================================================================

# Local Storage (Will change to google cloud on deployment!!!)
def save_to_uploads(uploaded_file, sme_id, subfolder="data/uploads"):
    if uploaded_file is None:
        return None
    else:
        folder_path = os.path.join(subfolder, f"SME_{sme_id}")
        os.makedirs(folder_path, exist_ok=True)

        file_ext = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        save_path = os.path.join(folder_path, unique_filename)

        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return os.path.relpath(save_path)

def update_sme_files(sme_id, business_permit, payroll, bir_income_tax):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("""
        UPDATE sme
        SET business_permit = ?, payroll = ?, bir_income_tax = ?
        WHERE sme_id = ?
    """, (business_permit, payroll, bir_income_tax, sme_id))
    conn.commit()
    conn.close()
#========================================================================

# == TEMPORARY STUFF ==
def temp_insert_sme(sme_data):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO sme (
            business_name, industry_sector, region, num_employees, avg_annual_revenue, years_in_operation, is_profitable, 
            sector_stability, market_competition, location_hazard, has_bcp, energy_usage, water_usage, waste_management,
            denr_permits, ghg_emissions, pct_emp_health, pct_emp_sss, emp_turnover_rate, csr_spending, workplace_safety,
            emergency_preparedness, fin_reporting_freq, has_policies, inspection_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sme_data["business_name"],
        sme_data["industry_sector"],
        sme_data["region"],
        sme_data["num_employees"],
        sme_data["avg_annual_revenue"],       
        sme_data["years_in_operation"],
        sme_data["is_profitable"],
        sme_data["sector_stability"],              
        sme_data["market_competition"],
        sme_data["location_hazard"],
        sme_data["has_bcp"],
        sme_data["energy_usage"],
        sme_data["water_usage"],  
        sme_data["waste_management"],
        sme_data["denr_permits"],
        sme_data["ghg_emissions"],
        sme_data["pct_emp_health"],       
        sme_data["pct_emp_sss"],       
        sme_data["emp_turnover_rate"],     
        sme_data["csr_spending"],
        sme_data["workplace_score"],
        sme_data["emergency_score"],
        sme_data["fin_reporting_freq"],
        sme_data["has_policies"],
        sme_data["inspection_result"]
    ))
    sme_id = c.lastrowid
    conn.commit()
    conn.close()
    return sme_id

# Getters
def search_name(business_name):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("SELECT sme_id, business_name, industry_sector, region, created_at FROM sme WHERE business_name LIKE ? ORDER BY business_name", (f"%{business_name}%",))
    s_name = c.fetchall()
    conn.close()
    return s_name

def get_all_smes():
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("SELECT sme_id, business_name, industry_sector, region, created_at FROM sme ORDER BY sme_id ASC")
    data = c.fetchall()
    conn.close()
    return data

def get_id(sme_id):
    conn = sqlite3.connect("esg_scoring.db")

    # Get sme detail
    df1 = pd.read_sql("""
        SELECT sme_id, business_name, industry_sector, region, created_at
        FROM sme
        WHERE sme_id = ?
    """, conn, params=(sme_id,))

    # Get suppliers 
    df2 = pd.read_sql("""
        SELECT supplier_id, supplier_name, supplier_sector, supplier_region, supplier_permit, sme_id
        FROM supplier
        WHERE sme_id = ?
    """, conn, params=(sme_id,))
    conn.close()

    return df1,df2

def get_audit_score(sme_id):
    conn = sqlite3.connect("esg_scoring.db")
    df = pd.read_sql("SELECT * FROM audit_log WHERE sme_id = ?", conn, params=(sme_id,))
    df['final_score'] = df['explanation_json'].apply(lambda x: json.loads(x)['final_score'])
    return df

def display_sme_data(sme_id):
    conn = sqlite3.connect("esg_scoring.db")
    df = pd.read_sql("SELECT * FROM sme where sme_id = ?", conn, params=(sme_id,))
    conn.close()

    # Rename labels
    FIELD_LABELS = {
        "sme_id": "SME ID",
        "business_name": "Business Name",
        "business_permit": "Business Permit File",
        "industry_sector": "Industry Sector",
        "region": "Region",
        "num_employees": "Number of Employees",
        "avg_annual_revenue": "Average Annual Revenue",
        "years_in_operation": "Years in Operation",
        "created_at": "Created At",

        # Financial
        "is_profitable": "Is SME Profitable?",
        "sector_stability": "Sector Stability Score",
        "market_competition": "Market Competition Score",

        # Environment
        "location_hazard": "Location Hazard Score",
        "has_bcp": "Has Business Continuity Plan?",
        "energy_usage": "Energy Usage",
        "water_usage": "Water Usage",
        "waste_management": "Waste Management",
        "denr_permits": "DENR Permits",
        "ghg_emissions": "Greenhouse Gas Emissions",

        # Social
        "pct_emp_health": "Percentage of Employees with Health Benefits",
        "pct_emp_sss": "Percentage of Employees with SSS",
        "emp_turnover_rate": "Employee Turnover Rate",
        "payroll": "Payroll File",
        "csr_spending": "CSR Spending",
        "workplace_safety": "Workplace Safety",
        "emergency_preparedness": "Emergency Preparedness",

        # Governance
        "fin_reporting_freq": "Financial Reporting Frequency",
        "bir_income_tax": "BIR Income Tax File",
        "has_policies": "Has Policies",
        "inspection_score": "Inspection Score"
    }

    df_transformed = df.T.reset_index()
    df_transformed.columns = ["Field", "Value"]
    df_transformed["Field"] = df_transformed["Field"].replace(FIELD_LABELS)
    return df_transformed

# delete sme
def delete_sme(sme_id):
    conn = sqlite3.connect("esg_scoring.db")
    c = conn.cursor()
    c.execute("DELETE FROM supplier WHERE sme_id = ?", (sme_id,))
    c.execute("DELETE FROM sme WHERE sme_id = ?", (sme_id,))
    conn.commit()
    conn.close()