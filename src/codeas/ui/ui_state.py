import streamlit as st


def init_ui_state():
    if "outputs" not in st.session_state:
        st.session_state.outputs = {}
