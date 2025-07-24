import sys, os, base64
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from backend.user_utils import create_user, user_exists

# ─── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(page_title="Insurance Claim Login", page_icon="🔐", layout="centered")

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

# ─── CUSTOM STYLING ────────────────────────────────────────────
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
label, .stTextInput label, .stPasswordInput label {
    color: #ffffff !important;
    font-weight: 600;
}
input, textarea {
    background-color: #2c2c3c !important;
    color: white !important;
    border: 1px solid #555 !important;
    border-radius: 8px !important;
}
input:focus, textarea:focus {
    border: 1px solid #00c6ff !important;
    outline: none !important;
}
.stTextInput>div>input, .stPasswordInput>div>input {
    padding: 0.75rem;
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
</style>
""", unsafe_allow_html=True)

# ─── LOGIN FORM ────────────────────────────────────────────────
st.title("🛡️ Welcome To Secure Insurance Claim Portal")

mode = st.radio("Select Option", ["Login", "Register"], horizontal=True)
email = st.text_input("📧 Email")
password = st.text_input("🔑 Password", type="password")

if mode == "Register":
    confirm_password = st.text_input("✅ Confirm Password", type="password")

if st.button(f"{mode} Now"):
    if not email or not password:
        st.warning("Please enter both email and password.")
        st.stop()

    if mode == "Register":
        if password != confirm_password:
            st.error("Passwords do not match.")
            st.stop()
        if user_exists(email):
            st.error("User already exists. Please login.")
        else:
            create_user(email, password)
            st.success("User registered successfully! Please login.")
    else:
        if not user_exists(email):
            st.error("User not found. Please register.")
        else:
            stored_pwd = user_exists(email)
            if stored_pwd != password:
                st.error("Incorrect password.")
            else:
                st.session_state.user_email = email
                st.success("Login successful!")
                st.switch_page("pages/home.py")  # or "pages/final_app.py"
