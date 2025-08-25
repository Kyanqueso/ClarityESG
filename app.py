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

st.markdown(
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" crossorigin="anonymous">',
             unsafe_allow_html=True
        )
st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" crossorigin="anonymous">',
    unsafe_allow_html=True
)
st.html("""
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', sans-serif;
            color: #fff;
            margin: 0;
            padding: 0;
        }

        .container {
            max-width: 900px;
            margin: 60px auto;
            text-align: center;
        }

        .container h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        }

        .container h4 {
            font-weight: 400;
            margin-bottom: 50px;
        }

        .card-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 30px;
        }
        a.card {
            cursor: pointer;
            text-decoration: none;
            color: white  
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            width: 220px;
            transition: all 0.3s ease;
            cursor: pointer;
            text-align: center;
            box-shadow: 0px 8px 20px rgba(0,0,0,0.3);
        }
        .card-form {
            background: linear-gradient(135deg, #ff7e5f, #feb47b);
        }

        .card-analyze {
            background: linear-gradient(135deg, #6a11cb, #2575fc);
        }

        .card-stats {
            background: linear-gradient(135deg, #43cea2, #185a9d);
        }

        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0px 12px 30px rgba(0,0,0,0.5);
            filter: brightness(1.1);
        }

        .card i {
            font-size: 3rem;
            margin-bottom: 15px;
            color: #fff;
        }

        .card h5 {
            font-size: 1.2rem;
            margin-bottom: 0;
            font-weight: 600;
        }

        hr {
            border-top: 2px solid rgba(255,255,255,0.5);
            width: 50%;
            margin: 30px auto;
        }
        </style>

        <div class="container">
            <h1>Welcome to ClarityESG!</h1>
            <h4>Select an Action</h4>
            <hr>

            <div class="card-container">
                <a href="/sme_form" class="card card-form">
                    <i class="fas fa-plus-circle"></i>
                    <h5>Input SME</h5>
                </a>
                <a href="/sme_analysis" class="card card-analyze">
                    <i class="fas fa-chart-line"></i>
                    <h5>Analyze SMEs</h5>
                </a>
                <a href="/statistics" class="card card-stats">
                    <i class="fas fa-chart-pie"></i>
                    <h5>Statistics</h5>
                </a>
            </div>
        </div>
    """)