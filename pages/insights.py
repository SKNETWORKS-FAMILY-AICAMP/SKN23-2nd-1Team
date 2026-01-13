import streamlit as st
from pathlib import Path
import pandas as pd
import io
from util.global_style import apply_global_style

apply_global_style("images/library_hero 4.jpg")



st.markdown("""
<style>

</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([5,5])
with col1: 
    with st.container(border=True):
        st.subheader("내 리뷰 예측")
        st.write("*방금 작성한 내 STEAM 리뷰를 예측합니다.*")

        user_id = st.text_input("Steam ID를 입력하세요", placeholder="예: 7656119...")

        if user_id:
            if not user_id.isdigit():
                st.error("Steam ID는 숫자만 입력해주세요.")
            else:
                steam_id = int(user_id)
                st.success("정상 입력")
         
with col2:       
    with st.container(border=True):
        st.subheader("엑셀 업로드로 예측")
