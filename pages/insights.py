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

with st.container(border=True):
    col1, col2 = st.columns([5,5])
    