import streamlit as st
from pathlib import Path
import base64

def load_global_css():
    css = Path("styles/global.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def apply_global_style(bg_path: str):
    img_bytes = Path(bg_path).read_bytes()
    img_base64 = base64.b64encode(img_bytes).decode()

    css = f"""
    <style>
    .stApp {{
      background:
        linear-gradient(rgba(2,6,23,0.75), rgba(2,6,23,0.75)),
        url("data:image/jpg;base64,{img_base64}");
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)