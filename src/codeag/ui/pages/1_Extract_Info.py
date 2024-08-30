import streamlit as st

from codeag.ui.shared.components import display_agent, display_files, display_folders


def display_extract_info():
    st.write("## Extract Info")
    with st.expander("CONTEXT", expanded=True):
        display_files("info", expanded=True)
        display_folders("info", expanded=True)
    display_extract_files_info()
    display_extract_folders_info()


def display_extract_files_info():
    with st.expander("Files Info", expanded=True):
        display_agent("extract_files_info", "Extract Files Info", display_json)


def display_extract_folders_info():
    with st.expander("Folders Info", expanded=True):
        display_agent("extract_folders_info", "Extract Folders Info", display_json)


def display_json(output):
    st.json(output, expanded=False)


display_extract_info()
