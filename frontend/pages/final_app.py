# frontend/pages/final_app.py
import os, base64, io
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
from PIL import Image, ExifTags
# 3rd-party helpers
from backend.firebase_config import db
from backend.hash_utils import compute_sha256, check_duplicate_hash
from backend.claim_agent   import claim_agent

load_dotenv()
DATA_DIR = "frontend/data"
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Insurance Claim App", layout="centered")
st.title("🏚️ Insurance Claim Processing")

# ─────────────────────────────────────────────────────────────
def get_gps_from_exif(pil_image):
    try:
        raw = pil_image._getexif() or {}
        gps  = raw.get(next(k for k,v in ExifTags.TAGS.items() if v=="GPSInfo"), None)
        if not gps: return None, None
        def _dms2deg(dms, ref):
            d = dms[0][0]/dms[0][1]
            m = dms[1][0]/dms[1][1]
            s = dms[2][0]/dms[2][1]
            val = d + m/60 + s/3600
            return -val if ref in ("S","W") else val
        lat = _dms2deg(gps[2], gps[1])
        lng = _dms2deg(gps[4], gps[3])
        return round(lat,6), round(lng,6)
    except Exception:
        return None, None
# ─────────────────────────────────────────────────────────────

with st.form("claim_form"):
    st.header("📋 Claim Details")
    user_email  = st.text_input("📧 Email")
    policy_date = st.date_input("📅 Policy Start")
    dol         = st.date_input("📆 Date of Loss (DOL)")
    threshold   = st.number_input("⏱️ Allowed EXIF↔DOL gap (days)", 0, 30, 10)
    claim_text  = st.text_area("📝 Describe the incident", height=140)

    st.header("📸 Evidence")
    image_file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])

    exif_lat = exif_lng = None
    if image_file:
        # read in-memory for EXIF sniff
        img_bytes = image_file.getvalue()
        lat, lng  = get_gps_from_exif(Image.open(io.BytesIO(img_bytes)))
        exif_lat, exif_lng = lat, lng
        if lat and lng:
            st.success(f"📍 GPS found in EXIF: {lat}, {lng}")

    st.header("🌪️ Natural Calamity")
    natural_calamity = st.checkbox("Claim caused by storm / flood / other event?")
    storm_location   = None
    if natural_calamity and not (exif_lat and exif_lng):
        storm_location = st.text_input("📍 Enter city / ZIP (EXIF GPS not found)")

    submitted = st.form_submit_button("🚀 Submit Claim")

# ─────────────────────────────────────────────────────────────
if submitted:
    if not (user_email and claim_text and image_file):
        st.error("⚠️ Please fill all mandatory fields.")
        st.stop()

    # Save to disk
    fname = f"{user_email.replace('@','_')}_{datetime.now():%Y%m%d%H%M%S}.jpg"
    path  = os.path.join(DATA_DIR, fname)
    with open(path,"wb") as f: f.write(image_file.getbuffer())

    # duplicate check
    h = compute_sha256(path)
    if check_duplicate_hash(h):
        st.error("🚩 Duplicate image detected.")
        st.stop()
    db.collection("image_hashes").add({"hash":h,"ts":datetime.now()})

    init_state = {
        "file_path": path,
        "user_text": claim_text,
        "policy_data": {
            "policy_date": str(policy_date),
            "dol": str(dol),
            "threshold": int(threshold)
        },
        "natural_calamity": natural_calamity,
        "storm_location": storm_location,
        "exif_lat": exif_lat,
        "exif_lng": exif_lng,
    }

    with st.spinner("🔎 Running AI checks ..."):
        result = claim_agent.invoke(init_state)

    # ── Debug
    if result.get("debug"):
        st.subheader("🪵 Debug Log")
        for l in result["debug"]: st.write("•", l)

    # ── Verdict
    verdict = result.get("final_decision","flag")
    cmap = {"approve":"#16a34a","reject":"#dc2626","flag":"#ca8a04"}
    st.markdown(f"""
    <div style="background:#111;padding:18px;border-left:6px solid {cmap.get(verdict,'#ca8a04')}">
    <b style="font-size:18px">Final Verdict:</b><br>{verdict.capitalize()}
    </div>""", unsafe_allow_html=True)

    # ── Warnings
    if result.get("is_ai_image"):
        st.error("Image identified as AI-generated ➜ claim rejected.")
    if natural_calamity and result.get("storm_verification") is False:
        st.warning("Weather data could not confirm severe conditions for that date/location.")

    # ── PDF
    pdf_path = result.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path,"rb") as f: b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="claim_report.pdf">📥 Download PDF</a>', unsafe_allow_html=True)
    else:
        st.info("No PDF generated.")
