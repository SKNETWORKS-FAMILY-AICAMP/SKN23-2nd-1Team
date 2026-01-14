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
from util.global_style import apply_global_style

apply_global_style("images/library_hero.jpg")

st.title("모델 성능")

col1, col2 = st.columns([5,5])
with col1: 
    with st.container(border=True):
        st.subheader("1. 주간 Steam Top 100")
        st.image("images/performance/top100.png")
    with st.container(border=True):
        st.subheader("2. 50개의 주요 게임 별 모델 학습")
        st.image("images/performance/top50.png")
     
with col2: 
    with st.container(border=True):
        st.subheader("3. 20개의 하위 모델 하이퍼파라미터")
        st.image("images/library_hero 3.jpg")
    with st.container(border=True):
        st.subheader("4. 5개의 하위 모델 SMOTE")
        st.image("images/library_hero 4.jpg")
