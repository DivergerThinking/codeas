import os
from typing import Literal

import streamlit as st

from codeas.core.state import state


def display(demo: bool = False):
    display_repo_path(demo)
    display_files()


def display_repo_path(demo: bool = False):
    if demo is False:
        st.caption(os.path.abspath(state.repo_path))
    else:
        if state.repo_path == "./abstreet":
            st.markdown(
                "[github.com/a-b-street/abstreet](https://github.com/a-b-street/abstreet)"
            )
        elif state.repo_path == "../codeas":
            st.markdown(
                "[github.com/DivergerThinking/codeas](https://github.com/DivergerThinking/codeas)"
            )


def display_files():
    st.session_state.files_data = {
        "Incl.": state.repo.included,
        "Path": state.repo.files_paths,
        "Tokens": list(state.repo.files_tokens.values()),
    }
    num_selected_files, total_files, selected_tokens = get_selected_files_info()
    with st.expander(
        f"{num_selected_files}/{total_files} files selected | {selected_tokens:,} tokens"
    ):
        display_filters()
        display_files_editor()


def filter_files():
    include_patterns = [
        include.strip() for include in state.include.split(",") if include.strip()
    ]
    exclude_patterns = [
        exclude.strip() for exclude in state.exclude.split(",") if exclude.strip()
    ]
    state.repo.filter_files(include_patterns, exclude_patterns)
    st.session_state.files_data = {
        "Incl.": state.repo.included,
        "Path": state.repo.files_paths,
        "Tokens": list(state.repo.files_tokens.values()),
    }


def get_selected_files_info():
    num_selected_files = sum(st.session_state.files_data["Incl."])
    total_files = len(st.session_state.files_data["Incl."])
    selected_tokens = sum(
        token
        for incl, token in zip(
            st.session_state.files_data["Incl."], st.session_state.files_data["Tokens"]
        )
        if incl
    )
    return num_selected_files, total_files, selected_tokens


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
    filter_files()


def update_filter(filter_type: Literal["include", "exclude"]):
    input_key = f"{filter_type}_input"
    state_key = f"{filter_type}"

    if input_key in st.session_state:
        setattr(state, state_key, st.session_state[input_key])


def display_files_editor():
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
