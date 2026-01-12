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
/* =========================
   Steam Topbar Install Button (Tuned)
   ========================= */

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button,
div[data-testid="stButton"] button,
div[data-testid="stDownloadButton"] button,
div[data-testid="stFormSubmitButton"] button,
button[kind="primary"],
button[kind="secondary"] {

  /* 형태 */
  border-radius: 2px !important;
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 12px !important;

  /* 🔹 기본 색상 = 이전 hover 색 */
  background: #3a4554 !important;
  border: 1px solid #4b5868 !important;
  color: #e6edf5 !important;

  font-size: 14px !important;
  font-weight: 600 !important;
  letter-spacing: 0.2px !important;

  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.08) !important;

  transition:
    background 120ms ease,
    border-color 120ms ease,
    transform 80ms ease !important;
}

/* 🔹 Hover = 기본보다 살짝 더 연하게 */
.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover,
div[data-testid="stButton"] button:hover,
div[data-testid="stDownloadButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover {

  background: #465366 !important;
  border-color: #5a687b !important;
}

/* 🔹 Active = 눌림 */
.stButton > button:active,
.stDownloadButton > button:active,
.stFormSubmitButton > button:active,
button[kind="primary"]:active,
button[kind="secondary"]:active {

  transform: translateY(1px) !important;
  background: #2f3845 !important;
  border-color: #3b4654 !important;
}

/* Disabled */
.stButton > button:disabled,
.stDownloadButton > button:disabled {
  opacity: 0.55 !important;
  cursor: not-allowed !important;
}

/* 전체 앱 배경 */
.stApp {
    background:
        linear-gradient(
            rgba(2, 6, 23, 0.85),
            rgba(2, 6, 23, 0.85)
        ),
        url("https://images.unsplash.com/photo-1542751371-adc38448a05e");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

/* 기본 흰 배경 제거 */
[data-testid="stAppViewContainer"] {
    background: transparent;
}

/* 섹션별 배경도 투명 */
[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="stToolbar"] {
    background: transparent;
}
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