import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Explicit region groupings — avoids fragile iloc index slicing
LUZON_REGIONS = [
    "National Capital Region (NCR)",
    "Ilocos Region (Region I)",
    "Cagayan Valley (Region II)",
    "Cordillera Administrative Region (CAR)",
    "Central Luzon (Region III)",
    "CALABARZON (Region IV-A)",
    "MIMAROPA Region (Region IV-B)",
    "Bicol Region (Region V)",
]

VISAYAS_REGIONS = [
    "Western Visayas (Region VI)",
    "Central Visayas (Region VII)",
    "Eastern Visayas (Region VIII)",
]

MINDANAO_REGIONS = [
    "Zamboanga Peninsula (Region IX)",
    "Northern Mindanao (Region X)",
    "Davao Region (Region XI)",
    "SOCCSKSARGEN (Region XII)",
    "Caraga (Region XIII)",
    "Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)",
]


def sector_risk_avg():
    conn = sqlite3.connect("esg_scoring.db")
    df = pd.read_sql("SELECT * FROM esg_sector_risks", conn)
    conn.close()
    df["avg_score"] = (df["env_risk"] + df["soc_risk"] + df["gov_risk"]) / 3
    return df

def region_risk():
    conn = sqlite3.connect("esg_scoring.db")
    df = pd.read_sql("SELECT * FROM region_risks", conn)
    conn.close()
    return df

# UI
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

if st.button("Back to Home"):
    st.switch_page("app.py")

st.header("Statistics of Sectors and Regions of the Philippines")
st.text("Last Updated: August 25, 2025")
st.markdown("<br>", unsafe_allow_html=True)

sector_df = sector_risk_avg()

region_df = region_risk()
luzon_df = region_df[region_df["region"].isin(LUZON_REGIONS)]
visayas_df = region_df[region_df["region"].isin(VISAYAS_REGIONS)]
mindanao_df = region_df[region_df["region"].isin(MINDANAO_REGIONS)]

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("Current PH Sector risk scores (Lower the Better):")

st.table(sector_df[["sector", "env_risk", "soc_risk", "gov_risk"]])
st.markdown("<br>", unsafe_allow_html=True)

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#111", "figure.facecolor": "#111"})
sns.barplot(x="sector", y="avg_score", data=sector_df, color="#967311")
plt.xlabel("SECTOR", color="white")
plt.ylabel("AVERAGE SCORE", color='white')
plt.xticks(rotation=90, color='white')
plt.yticks(color='white')

st.pyplot(plt)
st.markdown("<br>", unsafe_allow_html=True)
plt.clf()

st.subheader("Luzon Region Scores (Higher the Better):")
st.table(luzon_df)
st.markdown("<br>", unsafe_allow_html=True)

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#111", "figure.facecolor": "#111"})
sns.barplot(x="region", y="score", data=luzon_df, color="green")
plt.xlabel("REGION", color="white")
plt.ylabel("SCORE", color='white')
plt.xticks(rotation=90, color='white')
plt.yticks(color='white')

st.pyplot(plt)
st.markdown("<br>", unsafe_allow_html=True)
plt.clf()

st.subheader("Visayas Region Scores (Higher the Better):")
st.table(visayas_df)
st.markdown("<br>", unsafe_allow_html=True)

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#111", "figure.facecolor": "#111"})
sns.barplot(x="region", y="score", data=visayas_df, color="blue")
plt.xlabel("REGION", color="white")
plt.ylabel("SCORE", color='white')
plt.xticks(rotation=90, color='white')
plt.yticks(color='white')

st.pyplot(plt)
st.markdown("<br>", unsafe_allow_html=True)
plt.clf()

st.subheader("Mindanao Region Scores (Higher the Better):")
st.table(mindanao_df)
st.markdown("<br>", unsafe_allow_html=True)

sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#111", "figure.facecolor": "#111"})
sns.barplot(x="region", y="score", data=mindanao_df, color="#b37125")
plt.xlabel("REGION", color="white")
plt.ylabel("SCORE", color='white')
plt.xticks(rotation=90, color='white')
plt.yticks(color='white')

st.pyplot(plt)
st.markdown("<br>", unsafe_allow_html=True)
plt.clf()
