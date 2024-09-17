import os
from typing import Literal

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.core.repo import Repo
from codeag.ui.state import state
from codeag.ui.utils import search_dirs


def display():
    st.subheader("Repo")
    display_repo_path()
    with st.expander("Files"):
        display_filters()
        display_files_editor()
    display_selected_files_info()


def display_repo_path():
    state.repo_path = st_searchbox(
        search_dirs, placeholder=state.repo_path, default=state.repo_path
    )
    st.caption(os.path.abspath(state.repo_path))


def display_filters():
    col_include, col_exclude = st.columns(2)
    with col_include:
        st.text_input(
            "Include",
            value=state.include,
            key="include_input",
            on_change=lambda: update_filter("include"),
            placeholder="*.py, src/*, etc.",
        )
    with col_exclude:
        st.text_input(
            "Exclude",
            value=state.exclude,
            key="exclude_input",
            on_change=lambda: update_filter("exclude"),
            placeholder="debug/*, *.ipynb, etc.",
        )


def update_filter(filter_type: Literal["include", "exclude"]):
    input_key = f"{filter_type}_input"
    state_key = f"{filter_type}"

    if input_key in st.session_state:
        setattr(state, state_key, st.session_state[input_key])


def display_files_editor():
    repo = Repo(repo_path=state.repo_path)
    include_patterns = [
        include.strip() for include in state.include.split(",") if include.strip()
    ]
    exclude_patterns = [
        exclude.strip() for exclude in state.exclude.split(",") if exclude.strip()
    ]
    incl_files = repo.filter_files(include_patterns, exclude_patterns)
    st.session_state.files_data = {
        "Incl.": incl_files,
        "Path": repo.files_paths,
        "Tokens": list(repo.files_tokens.values()),
    }
    sort_files_data()
    st.data_editor(
        st.session_state.files_data,
        use_container_width=True,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width=5),
            "Path": st.column_config.TextColumn(width="large"),
            "Tokens": st.column_config.NumberColumn(width=5),
        },
        disabled=True,
    )


def sort_files_data():
    # Sort by Incl. = True first, then by Path
    sorted_data = sorted(
        zip(
            st.session_state.files_data["Incl."],
            st.session_state.files_data["Path"],
            st.session_state.files_data["Tokens"],
        ),
        key=lambda x: (not x[0], x[1]),  # Sort by Incl. (True first) then by Path
    )
    # Unzip the sorted data back into separate lists
    (
        st.session_state.files_data["Incl."],
        st.session_state.files_data["Path"],
        st.session_state.files_data["Tokens"],
    ) = zip(*sorted_data)


def display_selected_files_info():
    num_selected_files = sum(st.session_state.files_data["Incl."])
    total_files = len(st.session_state.files_data["Incl."])
    selected_tokens = sum(
        token
        for incl, token in zip(
            st.session_state.files_data["Incl."], st.session_state.files_data["Tokens"]
        )
        if incl
    )
    st.info(
        f"{num_selected_files}/{total_files} files selected | {selected_tokens:,} tokens"
    )
    st.session_state.selected_files_path = [
        path
        for path, incl in zip(
            st.session_state.files_data["Path"], st.session_state.files_data["Incl."]
        )
        if incl
    ]
