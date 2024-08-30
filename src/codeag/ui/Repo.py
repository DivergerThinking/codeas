import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.ui.shared.components import display_button
from codeag.ui.shared.state import state
from codeag.ui.utils import search_dirs


def display_home_page():
    st.markdown("## Repository")
    display_repo_path()


def display_repo_path():
    with st.expander("Path", expanded=True):
        repo_path = st_searchbox(search_dirs, placeholder=".", default=".")

        display_button("Update", "update_files_tokens")
        if state.is_clicked("update_files_tokens"):
            state.update_repo_path(repo_path)

        st.caption(os.path.abspath(state.repo_path))
        state.repo.export_attributes()


display_home_page()
