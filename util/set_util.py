import streamlit as st
APP_NAME = "Steam Churn Radar"

def set_page(title: str):
    st.set_page_config(
        page_title=f"{title} | {APP_NAME}",
        page_icon="images/favicon.svg",
        layout="wide",
    )