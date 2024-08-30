import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.ui.shared.components import display_agent, display_button, display_context
from codeag.ui.shared.state import state
from codeag.ui.utils import search_dirs


def display_home_page():
    st.markdown("## Repository")
    display_repo_path()
    display_context("docs", expanded=True)
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


def display_repo_path():
    with st.expander("Path", expanded=True):
        repo_path = st_searchbox(search_dirs, placeholder=".", default=".")

        display_button("Update", "update_files_tokens")
        if state.is_clicked("update_files_tokens"):
            state.update(repo_path)

        st.caption(os.path.abspath(state.repo_path))
        state.repo.export_attributes()


display_home_page()
