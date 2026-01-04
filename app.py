import streamlit as st
from pathlib import Path

# ================== 네비게이션 (사이드바) ==================

css = Path("css/global.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# ================== 네비게이션 (사이드바) ==================
pages = [
    st.Page("pages/main.py", title="홈"),
    st.Page("pages/predict.py", title="예측"),
    st.Page("pages/performance.py", title="모델 성능"),
    st.Page("pages/insights.py", title="데이터 인사이트"),
    st.Page("pages/action.py", title="비지니스 권장사항"),
    st.Page("util/common_util.py", title="공통유틸"),
]

st.navigation(pages, position="sidebar").run()
# ================== 로 고 ==================
# car_logo = "images/Car_value.png"
# st.logo(car_logo, size="large", icon_image= car_logo)
# ===========================================