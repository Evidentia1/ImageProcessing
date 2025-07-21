import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from backend.user_utils import create_user, user_exists

st.set_page_config(page_title="Insurance Claim Login", page_icon="🔐", layout="centered")
st.title("🔐 Welcome to Insurance Claim App")

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
                st.switch_page("pages/final_app.py")
