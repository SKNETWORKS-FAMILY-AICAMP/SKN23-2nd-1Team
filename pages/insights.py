import streamlit as st
from pathlib import Path
import pandas as pd
import io
from util.global_style import apply_global_style
from util.set_util import set_page
set_page("Insights")

apply_global_style("images/library_hero 4.jpg")

st.markdown("""
<style>

</style>
""", unsafe_allow_html=True)
st.title("인사이트")

with st.container(border=True):
    st.image('images/insights/insight1.png')
    st.write("긍정적 감정 + 짧은 플레이 타임 → 이탈 신호가 가장 강하게 관측됨")
    st.write("부정적 감정 + 긴 플레이 타임 → 이탈 신호가 상대적으로 약하게 관측됨")

col1, col2 = st.columns([5,5])
with col1:
    with st.container(border=True):
        st.image('images/insights/insight3.png')
        st.write("플레이 집중도가 높을 수록 → 이탈 신호가 낮게 관측됨")
with col2:
    with st.container(border=True):
        st.image('images/insights/insight4.png')
        st.write("리뷰를 수정한 여부는 충성도의 지표 → 이탈 신호가 약하게 관측됨")
