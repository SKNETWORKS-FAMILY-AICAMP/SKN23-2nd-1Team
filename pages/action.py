from util.global_style import apply_global_style
import streamlit as st
from util.set_util import set_page
set_page("Recommendations")

apply_global_style("images/library_hero 2.jpg")


st.title("비지니스 권장사항")

col1, col2, col3 = st.columns([5,5,5])
with col1: 
    with st.container(border=True):
        st.image("images/recommendations/recommendations1.png")
        st.image("images/recommendations/recommendations2.png")
        st.image("images/recommendations/recommendations3.png")
        st.image("images/recommendations/recommendations4.png")
        
with col2: 
    with st.container(border=True):
        st.image("images/recommendations/recommendations5.png")
        st.image("images/recommendations/recommendations6.png")
        st.image("images/recommendations/recommendations7.png")
        st.image("images/recommendations/recommendations8.png")
        
with col3: 
    with st.container(border=True):
        st.image("images/recommendations/recommendations9.png")
        st.image("images/recommendations/recommendations10.png")
        st.image("images/recommendations/recommendations11.png")
        st.image("images/recommendations/recommendations12.png")

        