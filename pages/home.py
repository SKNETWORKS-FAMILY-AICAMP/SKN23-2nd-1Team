import streamlit as st
from util.set_util import set_page

set_page("Overview")
st.markdown("""
<style>
/* =========================
   HERO LAYOUT
========================= */
.hero{
  display:flex;
  flex-direction:column;
  justify-content:center;
  align-items:center;
  height:55vh;
  gap:14px;
  text-align:center;
  font-family:"Segoe UI","Noto Sans KR",sans-serif;
  padding:0 18px;
}

/* =========================
   TITLE (PC / Mobile switch)
   - No typing, no cursor
   - Smooth fade + slight rise
========================= */
.title{
  font-weight:800;
  color:#e5e4dc;
  margin:0;
  opacity:0;
  transform: translateY(6px);
  animation: fadeUp 0.9s ease-out forwards;
}

.pc-title{ display:block; font-size:48px; white-space:nowrap; }
.mobile-title{ display:none; font-size:32px; white-space:normal; line-height:1.15; }

.mobile-title .line1,
.mobile-title .line2{
  display:inline-block;
}

/* =========================
   SUBTITLE
   - Same effect as title (fadeUp)
   - Delayed after title
========================= */
.subtitle{
  font-size:18px;
  color:#b8c6d9;
  max-width:900px;
  line-height:1.55;

  opacity:0;
  transform: translateY(6px);
  animation: fadeUp 0.9s ease-out forwards;
  animation-delay: 0.35s;
}

/* PC에서는 한 줄로 유지하고 싶으면 주석 해제
.subtitle{ white-space:nowrap; }
*/

/* =========================
   ANIMATION
========================= */
@keyframes fadeUp{
  to{
    opacity:1;
    transform: translateY(0);
  }
}

/* =========================
   MOBILE
========================= */
@media (max-width: 768px){
  .hero{
    height:48vh;
    padding:0 16px;
    gap:12px;
  }

  .pc-title{ display:none; }
  .mobile-title{ display:block; }

  .subtitle{
    font-size:15px;
    max-width:100%;
  }
}
</style>

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
