import streamlit as st
import pandas as pd
from util.global_style import apply_global_style
from util.set_util import set_page
set_page("Performance")
apply_global_style("images/library_hero.jpg")

st.title("모델 성능")
with st.container(border=True):
    st.subheader("50개의 주요 게임 별 모델 학습")
    st.image("images/performance/top50.png")
        
# col1, col2 = st.columns([5,5])
# with col1: 
#     with st.container(border=True):
#         st.subheader("1. 주간 Steam Top 100")
#         st.image("images/performance/top100.png")
#     with st.container(border=True):
#         st.subheader("2. 50개의 주요 게임 별 모델 학습")
#         st.image("images/performance/top50.png")
     
# with col2: 
#     with st.container(border=True):
#         st.subheader("3. 20개의 하위 모델 하이퍼파라미터")
#         st.image("images/library_hero 3.jpg")
#     with st.container(border=True):
#         st.subheader("4. 5개의 하위 모델 SMOTE")
#         st.image("images/library_hero 4.jpg")



with st.container(border=True):
    st.subheader("첫 번째 학습, 50개 모델")
    df_first = pd.read_csv('data/learning_first.csv')
    styled_view_first = df_first.style.set_properties(**{
        "background-color": "#1b2838",   # Steam 다크 블루
        "color": "#c7d5e0"               # Steam 글자색
    })
    st.dataframe(styled_view_first, use_container_width=True, hide_index=True)
    
with st.container(border=True):
    st.subheader("두 번째 학습, 20개의 하위 모델 하이퍼파라미터")
    df_seocond = pd.read_csv('data/learning_second.csv')
    styled_view_second = df_seocond.style.set_properties(**{
        "background-color": "#1b2838",   # Steam 다크 블루
        "color": "#c7d5e0"               # Steam 글자색
    })
    st.dataframe(styled_view_second, use_container_width=True, hide_index=True)
    
with st.container(border=True):
    st.subheader("세 번째 학습, 5개의 하위 모델 SMOTE")
    df_thrid = pd.read_csv('data/learning_third.csv')
    styled_view_third = df_thrid.style.set_properties(**{
        "background-color": "#1b2838",   # Steam 다크 블루
        "color": "#c7d5e0"               # Steam 글자색
    })
    st.dataframe(styled_view_third, use_container_width=True, hide_index=True)