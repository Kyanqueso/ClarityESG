import os
import io
import json
import re
import sqlite3
import textwrap
import tempfile
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

DB_PATH = "esg_scoring.db"  
OPENAI_MODEL = "gpt-4.1"
env_path = Path("C:/Users/admin/Desktop/VS CODE PROJECTS/Microfund-AI/.env")
load_dotenv(dotenv_path=env_path)
load_dotenv()  

# Get json and date created
def load_latest_explanation(sme_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    row = conn.execute("""
        SELECT explanation_json, created_at 
        FROM audit_log 
        WHERE sme_id=? 
        ORDER BY created_at DESC, id DESC LIMIT 1
    """, (sme_id,)).fetchone()
    conn.close()
    if not row:
        return None, None
    exp = json.loads(row[0])
    created_at = row[1]
    return exp, created_at

# Get all sme data
def load_sme_record(sme_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM sme WHERE sme_id=?", conn, params=(sme_id,))
    conn.close()
    if df.empty:
        return None
    return df.iloc[0].to_dict()

# Bar chart for component scores
def save_scores_chart(explanation) -> str:
    comps = ["Financial", "Environmental", "Social", "Governance", "Suppliers"]
    vals = [
        explanation["financial_score"],
        explanation["environmental_score"],
        explanation["social_score"],
        explanation["governance_score"],
        explanation["suppliers_score"],
    ]

    colors = ["#fd7e14", "#5cb85c", "#f0ad4e", "#5bc0de","#6f42c1"]
    plt.figure(figsize=(6, 4))
    plt.bar(comps, vals, color=colors)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.title("ESG Component Scores")
    plt.ylim(0, 100)
    plt.ylabel("Score")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.tight_layout()
    plt.savefig(tmp.name, dpi=180, bbox_inches="tight")
    plt.close()
    return tmp.name

# Build small graph: SME -> suppliers, with edge weight mapped to supplier score
def save_supply_chain_graph(sme_info, explanation) -> str:
    
    G = nx.DiGraph()
    sme_label = sme_info.get("business_name", f"SME {sme_info.get('sme_id','')}")

    G.add_node(sme_label)

    suppliers = explanation.get("suppliers_detail", [])
    for s in suppliers:
        sup_name = str(s.get("supplier_name", "Supplier"))
        G.add_node(sup_name)
        # weight = supplier final score (higher = better)
        G.add_edge(sme_label, sup_name, weight=s.get("final_supplier_score", 0.0))

    # layout & draw
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(6, 4))
    nx.draw_networkx_nodes(G, pos, node_size=1000)
    nx.draw_networkx_labels(G, pos, font_size=8)
    nx.draw_networkx_edges(G, pos, arrows=True)

    # annotate edges with weights
    edge_labels = {(u, v): f"{d.get('weight',0):.1f}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

    plt.title("Supply Chain Map (edge label = supplier score)")
    plt.axis("off")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.tight_layout()
    plt.savefig(tmp.name, dpi=180, bbox_inches="tight")
    plt.close()
    return tmp.name

# Generates Risk analysis
def draft_risk_analysis(explanation, sme_info):
    
    client = OpenAI()

    # Construct concise, structured prompt
    prompt = f"""
        You are an ESG analyst. Write a concise, decision-oriented risk analysis (maximum of 250 words) for the SME below.
        Focus on strengths, weaknesses, and immediate mitigations. Avoid fluff; be specific.

        SME:
        - Name: {sme_info.get('business_name', 'N/A')}
        - Industry: {sme_info.get('industry_sector', 'N/A')}
        - Region: {sme_info.get('region', 'N/A')}
        - Years in operation: {sme_info.get('years_in_operation', 'N/A')}
        - Employees: {sme_info.get('number_of_employees', 'N/A')}

        Scores:
        - Financial: {explanation['financial_score']:.1f}
        - Environmental: {explanation['environmental_score']:.1f}
        - Social: {explanation['social_score']:.1f}
        - Governance: {explanation['governance_score']:.1f}
        - Suppliers: {explanation['suppliers_score']:.1f}
        - Final ESG: {explanation['final_score']:.1f}

        Top suppliers (name: score):
        {json.dumps([{ 'name': s.get('supplier_name','?'), 'score': s.get('final_supplier_score',0) } for s in explanation.get('suppliers_detail', [])], indent=2)}

        Structure your response like this:

        ### Basic Info of SME
        ### Financial Score
        ### Environmental Score
        ### Social Score
        ### Governance Score
        ### Suppliers, Supplier Score, and Final ESG rating
        ### Short conclusion
        """

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.4,
        messages=[
            {"role": "system", "content": "You are a senior ESG analyst."},
            {"role": "user", "content": prompt}
        ],
    )
    return resp.choices[0].message.content.strip()

def build_pdf(sme_info, explanation, scored_at, scores_chart_path, sc_graph_path) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.2*cm, bottomMargin=1.2*cm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="H2", fontSize=14, leading=18, spaceAfter=8))
    styles.add(ParagraphStyle(name="Mono", fontName="Courier", fontSize=8, leading=10))

    story = []

    # Cover
    story.append(Paragraph("ESG Audit Report", styles["Title"]))
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles["Normal"]))
    story.append(Spacer(1, 12))

    # SME Info
    story.append(Paragraph("SME Information", styles["H2"]))
    sme_table_data = [
        ["Business Name", str(sme_info.get("business_name", ""))],
        ["SME ID", str(sme_info.get("sme_id", ""))],
        ["Industry Sector", str(sme_info.get("industry_sector", ""))],
        ["Region", str(sme_info.get("region", ""))],
        ["Employees", str(sme_info.get("number_of_employees", ""))],
        ["Years in Operation", str(sme_info.get("years_in_operation", ""))],
        ["Scored At", str(scored_at or "N/A")],
    ]
    t = Table(sme_table_data, colWidths=[4*cm, 11*cm])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Scores + Final
    story.append(Paragraph("ESG Scores", styles["H2"]))
    story.append(Paragraph(f"Final ESG Score: <b>{explanation['final_score']:.2f}</b>", styles["Normal"]))
    story.append(Spacer(1, 6))
    story.append(Image(scores_chart_path, width=15*cm, height=9*cm))
    story.append(Spacer(1, 12))

    # Supply Chain Map
    story.append(Paragraph("Supply Chain Map", styles["H2"]))
    story.append(Image(sc_graph_path, width=15*cm, height=9*cm))
    story.append(Spacer(1, 12))

    # Suppliers table
    suppliers = explanation.get("suppliers_detail", [])
    if suppliers:
        story.append(Paragraph("Supplier Breakdown", styles["H2"]))
        header = ["Supplier", "Name Score", "Sector Score", "Region Score", "Permit Score", "Total Score"]
        rows = [
            [
                str(s.get("supplier_name","")),
                f"{s.get('name_score',0):.1f}",
                f"{s.get('sector_score',0):.1f}",
                f"{s.get('region_score',0):.1f}",
                f"{s.get('permit_score',0):.1f}",
                f"{s.get('final_supplier_score',0):.1f}",
            ] for s in suppliers
        ]
        stbl = Table([header] + rows, colWidths=[5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 3*cm])
        stbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(stbl)
        story.append(PageBreak())

    # Risk Analysis (GPT)
    story.append(Paragraph("Risk Analysis", styles["H2"]))
    narrative = draft_risk_analysis(explanation, sme_info)
    render_risk_analysis_to_pdf(story, narrative)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def render_risk_analysis_to_pdf(story, narrative):
    styles = getSampleStyleSheet()
    for line in narrative.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Handle headers like "### Section"
        if line.startswith("###"):
            title = line.replace("###", "").strip()
            story.append(Spacer(1, 12))
            story.append(Paragraph(title, styles["Heading3"]))
            story.append(Spacer(1, 6))
            continue

        # Convert markdown-style **bold** to <b> for reportlab
        line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)

        wrapped = textwrap.fill(line, width=100)
        story.append(Paragraph(wrapped, styles["Normal"]))
        story.append(Spacer(1, 4))