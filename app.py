import streamlit as st
from pathlib import Path


##
# Date        Description    Authur
# 2026-01-02  최초생성       created by 양창일
# 2026-01-11  로딩로고 추가   modified by 양창일
##


st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="images/favicon.svg", 
)

# ================== css 선언 ==================
css = Path("styles/global.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# 전역 스피너 HTML
# SPINNER_URL = "https://store.fastly.steamstatic.com/public/images/applications/store/steam_spinner.png?v=8669e97b288da32670e77181618c3dfb"
# SPINNER_HTML = f"""
# <div class="loading-overlay">
#   <div class="loading-backdrop"></div>
#   <img class="loading-spinner" src="{SPINNER_URL}" />
# </div>
# """

# # 세션키 초기화
# if "loading" not in st.session_state:
#     st.session_state["loading"] = False

# # 전역 overlay 렌더 (레이아웃 안 밀림)
# ph = st.empty()
# if st.session_state["loading"]:
#     ph.markdown(SPINNER_HTML, unsafe_allow_html=True)
# else:
#     ph.empty()
# ================== 네비게이션 (사이드바) ==================

pages = [
        st.Page("pages/home.py", title="Overview"),
        st.Page("pages/predict.py", title="Prediction"),
        st.Page("pages/performance.py", title="Model Performance"),
        st.Page("pages/insights.py", title="Insights"),
        st.Page("pages/action.py", title="Recommendations")
]


st.navigation(pages, position="sidebar").run()

# ================== 로 고 ==================
steam_logo = "images/steam_logo_white.svg"
st.logo(steam_logo, size="large", icon_image=steam_logo)
# ===========================================