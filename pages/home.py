import streamlit as st
from util.set_util import set_page

set_page("Overview")
st.markdown("""

<div class="hero">
  <!-- PC title -->
  <div class="title pc-title">STEAM 게임 이탈 예측 서비스</div>

  <!-- Mobile title (forced line break) -->
  <div class="title mobile-title">
    <span class="line1">STEAM 게임 이탈</span><br/>
    <span class="line2">예측 서비스</span>
  </div>

  <!-- Subtitle (same effect as title) -->
  <div class="subtitle">
    AI 기반 리뷰 · 플레이 데이터 분석을 통해 게임별 유저 이탈 가능성을 사전에 예측하고
    운영 전략 수립을 지원합니다.
  </div>
</div>
""", unsafe_allow_html=True)
