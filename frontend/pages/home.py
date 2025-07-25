import os, base64, io
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
from PIL import Image, ExifTags

from backend.firebase_config import db
from backend.hash_utils import compute_sha256, check_duplicate_hash
from backend.claim_agent import claim_agent

load_dotenv()
DATA_DIR = "frontend/data"
os.makedirs(DATA_DIR, exist_ok=True)

# ─── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(page_title="Claim Portal", layout="centered")

# ─── LOGO & BRANDING ───────────────────────────────────────────
logo_path = "../frontend/lloyds_logo.png"
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(f"""
<div style="display: flex; align-items: center; gap: 20px; margin-bottom: 30px;">
    <img src="data:image/png;base64,{logo_b64}" alt="Logo" width="70" style="border-radius: 12px;">
    <div>
        <h1 style="margin: 0; padding: 0;">Evidentia</h1>
        <p style="margin: 0; font-size: 16px; color: #ccc;">AI-powered insurance intelligence</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── PAGE STYLES ───────────────────────────────────────────────
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #1e1e2f, #34314c);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #1e1e2f, #34314c);
}
h1 {
    text-align: center;
    color: white;
}
h4, h5, .stTextInput>div>input, .stTextArea>div>textarea {
    font-family: 'Segoe UI', sans-serif;
}
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.06);
    padding: 2.2rem;
    border-radius: 1rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.15);
    margin-top: 20px;
}
.stButton > button {
    background: linear-gradient(to right, #00c6ff, #0072ff);
    color: white;
    font-weight: bold;
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
    margin-top: 25px;
    transition: 0.3s ease-in-out;
}
.stButton > button:hover {
    background: linear-gradient(to right, #0072ff, #00c6ff);
    transform: scale(1.03);
}
.verdict-box {
    padding: 1.5rem;
    margin-top: 2rem;
    border-left: 8px solid;
    border-radius: 12px;
    backdrop-filter: blur(8px);
}
.pdf-btn {
    background: linear-gradient(to right, #ff758c, #ff7eb3);
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
    color: white !important;
    font-weight: bold;
    display: inline-block;
    text-decoration: none;
    margin-top: 1rem;
}
.pdf-btn:hover {
    background: linear-gradient(to right, #ff7eb3, #ff758c);
}
</style>
""", unsafe_allow_html=True)

# ─── HEADER ────────────────────────────────────────────────────
st.title("💠 Smart Claim Processing")
st.markdown("<h5 style='text-align:center;'>Fast • Transparent • AI-Powered</h5>", unsafe_allow_html=True)

# ─── GPS EXIF HELPER ───────────────────────────────────────────
def get_gps_from_exif(pil_image):
    try:
        raw = pil_image._getexif() or {}
        gps = raw.get(next(k for k, v in ExifTags.TAGS.items() if v == "GPSInfo"), None)
        if not gps:
            return None, None

        def _dms2deg(dms, ref):
            d = dms[0][0] / dms[0][1]
            m = dms[1][0] / dms[1][1]
            s = dms[2][0] / dms[2][1]
            val = d + m / 60 + s / 3600
            return -val if ref in ("S", "W") else val

        lat = _dms2deg(gps[2], gps[1])
        lng = _dms2deg(gps[4], gps[3])
        return round(lat, 6), round(lng, 6)
    except Exception:
        return None, None

# ─── FORM UI ───────────────────────────────────────────────────
with st.form("claim_form"):
    st.subheader("📋 Claim Information")
    col1, col2 = st.columns(2)
    with col1:
        user_email = st.text_input("📧 Email")
        policy_number = st.text_input("🔢 Policy Number")
        policy_date = st.date_input("📅 Policy Start Date")
    with col2:
        dol = st.date_input("📆 Date of Loss")
        threshold = st.number_input("📏 EXIF↔DOL Gap Limit (days)", 0, 30, 10)

    claim_text = st.text_area("📝 What happened? (Brief description)", height=130)

    st.markdown("---")
    st.subheader("📸 Upload Evidence")
    image_file = st.file_uploader("Upload JPG / PNG", type=["jpg", "jpeg", "png"])

    exif_lat = exif_lng = None
    if image_file:
        img_bytes = image_file.getvalue()
        image = Image.open(io.BytesIO(img_bytes))
        lat, lng = get_gps_from_exif(image)
        exif_lat, exif_lng = lat, lng

        # ⬇️ Show Image Preview
        st.markdown("#### 🖼️ Image Preview:")
        st.image(image, width=300, caption="Preview of uploaded evidence")

        if lat and lng:
            st.success(f"📍 Found GPS Coordinates in EXIF: **{lat}, {lng}**")

    st.markdown("---")
    st.subheader("🌪️ Event Validation")
    natural_calamity = st.checkbox("Claim involves storm/flood/natural event?")
    storm_location = None
    if natural_calamity and not (exif_lat and exif_lng):
        storm_location = st.text_input("📍 Location (city / ZIP)")

    submitted = st.form_submit_button("🚀 Submit Claim")

# ─── FORM SUBMISSION LOGIC ─────────────────────────────────────
if submitted:
    print("✅ Submit button clicked.")

    if not (user_email and claim_text and policy_number and image_file):
        st.error("⚠️ Please complete all required fields.")
        st.stop()

    fname = f"{user_email.replace('@','_')}_{datetime.now():%Y%m%d%H%M%S}.jpg"
    path = os.path.join(DATA_DIR, fname)
    with open(path, "wb") as f:
        f.write(image_file.getbuffer())

    # 🔒 Removed Firebase hash checking
    # h = compute_sha256(path)
    # if check_duplicate_hash(h):
    #     st.error("🚩 This image was already submitted.")
    #     st.stop()
    # db.collection("image_hashes").add({"hash": h, "ts": datetime.now()})

    init_state = {
        "file_path": path,
        "user_text": claim_text,
        "policy_data": {
            "policy_number": policy_number,
            "policy_date": str(policy_date),
            "dol": str(dol),
            "threshold": int(threshold),
            "location": storm_location,  # for weather check
        },
        "natural_calamity": natural_calamity,
        "storm_location": storm_location,
        "exif_lat": exif_lat,
        "exif_lng": exif_lng,
    }

    with st.spinner("🧠 AI is analyzing your claim..."):
        print("🚀 Invoking claim_agent with:", init_state)
        try:
            result = claim_agent.invoke(init_state)
            print("✅ claim_agent returned result")
        except Exception as e:
            print("❌ claim_agent crashed:", e)
            st.error(f"Backend error: {e}")
            st.stop()

    if result.get("debug"):
        with st.expander("🛠️ Debug Logs"):
            for l in result["debug"]:
                st.write("•", l)

    verdict = result.get("final_decision", "flag").lower()
    vmap = {
        "approve": ("#00c851", "#003b2e"),
        "reject": ("#ff4444", "#2a0000"),
        "flag": ("#ffbb33", "#3a2b00")
    }

    verdict_type = "flag"
    if verdict.startswith("approve"):
        verdict_type = "approve"
    elif verdict.startswith("reject"):
        verdict_type = "reject"

    color, bg_color = vmap[verdict_type]

    st.markdown(f"""
    <div class="verdict-box" style="border-color:{color}; background:{bg_color};">
        <h4>🎯 Final Verdict:</h4>
        <p style="font-size:22px;font-weight:bold;color:{color};">{result['final_decision'].upper()}</p>
    </div>
    """, unsafe_allow_html=True)

    pdf_path = result.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<a class="pdf-btn" href="data:application/pdf;base64,{b64}" download="claim_report.pdf" target="_blank">📄 Download Claim Report</a>',
            unsafe_allow_html=True
        )
    else:
        st.info("📭 No PDF report generated.")
