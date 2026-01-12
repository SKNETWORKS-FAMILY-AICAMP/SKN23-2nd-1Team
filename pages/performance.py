import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import pandas as pd
import json
import ast
import util.review_api as ra
from util.loading import loading_on
import io
from util.global_style import load_global_css


st.markdown("""
<style>

</style>
""", unsafe_allow_html=True)

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
            
with st.container(border=True):
    st.subheader("엑셀 업로드로 예측")

    _, col1, col2, col3 = st.columns([5, 3, 2.45, 2.5])
    with col1:
        st.download_button(
            "템플릿 다운로드",
            data=Path("data/template.xlsx").read_bytes(),
            file_name="template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        uploaded = None
        with st.popover("엑셀 업로드"):
            uploaded = st.file_uploader(
                "파일 선택",
                type=["xlsx"],
                label_visibility="collapsed",
            )

    # 업로드 전: 빈 테이블 + 다운로드 비활성화
    if uploaded is None:
        st.dataframe(pd.DataFrame(), use_container_width=True, height=500)

        with col3:
            st.button("엑셀 다운로드", disabled=True, use_container_width=True)
    else:

        # 업로드 후
        df = pd.read_excel(uploaded)
        st.dataframe(df, use_container_width=True, height=500)

        # DataFrame → Excel bytes
        def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="data")
            return buffer.getvalue()

        excel_bytes = df_to_excel_bytes(df)

        with col3:
            st.download_button(
                "엑셀 다운로드",
                data=excel_bytes,
                file_name="result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )