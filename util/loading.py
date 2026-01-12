import streamlit as st
from contextlib import contextmanager

@contextmanager
def loading_on():
    st.session_state["loading"] = True
    try:
        yield
    finally:
        st.session_state["loading"] = False
