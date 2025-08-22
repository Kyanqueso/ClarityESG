import fitz
import sqlite3
import requests
import pandas as pd
import time, random
import io, base64, os
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup
from pyvis.network import Network

# Load API Key 
env_path = Path("C:/Users/admin/Desktop/VS CODE PROJECTS/Microfund-AI/.env")
load_dotenv(dotenv_path=env_path)
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found. Please check your .env file.")

client = OpenAI(api_key=api_key)

# ==========================
def encode_image(pil_image):
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def run_gpt_ocr(base64_img, ext="jpeg"):
    """Send an image (base64) to GPT-4o for OCR and interpretation."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all visible text from the image with exact formatting, including numbers, tables, special characters, "
                            "and structured data such as ESG metrics, financial figures, business KPIs, charts, and labels; if graphs or dashboards are present, interpret "
                            "and summarize key business insights, ESG indicators, and financial or operational risks for audit and reporting; if no text exists, describe "
                            "the layout, document type, visual elements, and any business context or branding relevant to SME ESG lender analysis and automated due diligence."},
                {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{base64_img}"}}
            ]
        }],
        temperature=0,
        max_tokens=2048,
    )
    return response.choices[0].message.content

def get_text_from_file(file_obj, file_type=None):
    """
    Extract text from PDF or image using GPT-4o Vision.
    
    Args:
        file_obj: file-like object or raw bytes
        file_type: MIME type string (e.g. 'application/pdf', 'image/jpeg')
    
    Returns:
        dict with keys:
            - "pages": list of dicts { "page_num": int, "text": str }
    """
    results = []

    if not file_type and hasattr(file_obj, "type"):
        file_type = file_obj.type

    # Handle PDFs
    if file_type and "pdf" in file_type:
        if hasattr(file_obj, "read"):
            pdf_bytes = file_obj.read()
        else:
            pdf_bytes = file_obj  # already bytes

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            base64_img = encode_image(img)
            text = run_gpt_ocr(base64_img)
            results.append({"page_num": i+1, "text": text})

    # Handle Images
    else:
        if hasattr(file_obj, "read"):
            img = Image.open(file_obj)
        elif isinstance(file_obj, bytes):
            img = Image.open(io.BytesIO(file_obj))
        else:
            img = Image.open(str(file_obj))  # fallback path

        ext = file_type.split("/")[-1] if file_type else "jpeg"
        base64_img = encode_image(img)
        text = run_gpt_ocr(base64_img, ext=ext)
        results.append({"page_num": 1, "text": text})

    return {"pages": results}

def generate_summary(prompt):
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are going to analyze a utility bill of a Filipino SME."},
            {"role": "user", "content": prompt}
        ],
        temperature = 0,
        max_tokens= 1024
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content
#===================================================================

# Supply chain mapping
def supply_chain_map(sme_id, sme_risk_score, output_file="supply_chain.html", db_path="esg_scoring.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get SME
    c.execute("SELECT sme_id, business_name FROM sme WHERE sme_id = ?", (sme_id,))
    smes = c.fetchone()

    if smes is None:
        conn.close()
        raise ValueError(f"No SME found with sme_id={sme_id}")

    sme_id_val, business_name = smes

    # Get suppliers
    c.execute("SELECT supplier_id, sme_id, supplier_name FROM supplier WHERE sme_id = ?", (sme_id,))
    suppliers = c.fetchall()
    conn.close()

    net = Network(height="512px", width="100%", bgcolor="#222222", font_color="white")

    # Add SME node
    net.add_node(f"SME_{sme_id_val}", label=f"{business_name} ({sme_risk_score})", color="blue", title=f"SME: {business_name}, {str(sme_risk_score)}")
    
    # Add supplier nodes + edges
    for supplier_id, supplier_sme_id, supplier_name in suppliers:
        net.add_node(f"SUP_{supplier_id}", label=supplier_name, color="red", title=f"Supplier: {supplier_name}")
        net.add_edge(f"SME_{sme_id_val}", f"SUP_{supplier_id}")
    
    net.save_graph(output_file)
    return output_file

# Web Scrape Methods
def philgeps_blacklist():
    url = "https://onlineblacklistingportal.gppb.gov.ph/obp-backend/cbr/cbr_public/?category=BLACKLISTED_ENTITIES"
    data = requests.get(url).json()

    df = pd.DataFrame(data)

    cleaned_df = df[["category", "blacklisted_entity", "project", "offenses", 
                    "saction_imposed", "start_date", "end_date"]]
    
    cleaned_df = cleaned_df.rename(columns={"blacklisted_entity": "BUSINESS_NAME", "offenses":"RISK_TAG"})
    cleaned_df["RISK_TAG"] = cleaned_df["RISK_TAG"].astype(str)
    return cleaned_df

def sec_suspended(): 
    session = requests.Session()

    base_url = "https://checkwithsec.sec.gov.ph"
    suspended_url = f"{base_url}/check-with-sec/suspended"

    headers = {
        "User-Agent": "Mozilla/5.0"
    } #"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9"

    response = session.get(suspended_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "_csrf"})["value"]
    
    post_headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": suspended_url,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
    }

    all_companies = []
    page = 1
    max_pages = 115

    while page <= max_pages:
        payload = {
            "_csrf" : csrf_token,
            "user_input" : "",
            "page" : page
        }

        try:
            post_response = session.post(suspended_url, headers=post_headers,
                                         data=payload, timeout=20)
            post_response.raise_for_status()
            json_data = post_response.json()
        except Exception as e:
            print(f"⚠️ Error on page {page}: {e}, retrying...")
            time.sleep(10)   # wait longer
            continue         # retry same page

        if json_data.get("status") != "success":
            print(f"⚠️ Server error on page {page}: {json_data.get('response')}")
            time.sleep(10)
            continue

        companies = json_data["response"]["data"]
        if not companies:
            break

        all_companies.extend(companies)
        print(f"✅ Page {page} scraped, got {len(companies)} records")

        page += 1
        time.sleep(random.uniform(2, 5))  # slow down to avoid SEC crash
    
    return pd.DataFrame(all_companies)