import os
from typing import Literal

import streamlit as st

from codeas.core.state import state


def display():
    display_repo_path()
    display_files()


def display_repo_path():
    st.markdown(f"**Repo**: {os.path.abspath(state.repo_path)}")


def display_files():
    display_filters()
    num_selected_files, total_files, selected_tokens = get_selected_files_info()
    with st.expander(
        f"{num_selected_files}/{total_files} files selected | {selected_tokens:,} tokens"
    ):
        display_files_editor()


def get_selected_files_info():
    num_selected_files = sum(state.files_data["Incl."])
    total_files = len(state.files_data["Incl."])
    selected_tokens = sum(
        token
        for incl, token in zip(state.files_data["Incl."], state.files_data["Tokens"])
        if incl
    )
    return num_selected_files, total_files, selected_tokens


def display_filters():
    col_include, col_exclude = st.columns(2)
    page_filter = state.get_page_filter()
    with col_include:
        st.text_input(
            "Include",
            value=page_filter.include,
            key="include_input",
            on_change=lambda: update_filter("include"),
            placeholder="Example: *.py, src/*, etc.",
        )
    with col_exclude:
        st.text_input(
            "Exclude",
            value=page_filter.exclude,
            key="exclude_input",
            on_change=lambda: update_filter("exclude"),
            placeholder="Example: debug/*, *.ipynb, etc.",
        )


def update_filter(filter_type: Literal["include", "exclude"]):
    input_key = f"{filter_type}_input"
    update_args = {filter_type: st.session_state[input_key]}
    state.update_page_filter(**update_args)


def display_files_editor():
    sort_files_data()
    st.data_editor(
        state.files_data,
        use_container_width=True,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width=5),
            "Path": st.column_config.TextColumn(width="large"),
            "Tokens": st.column_config.NumberColumn(width=5),
        },
        disabled=True,
        height=300,
    )


def display_metadata_editor(files_metadata):
    sort_files_metadata(files_metadata)
    st.data_editor(
        files_metadata,
        use_container_width=True,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width=5),
            "Path": st.column_config.TextColumn(width="large"),
            "Tokens": st.column_config.NumberColumn(width=5),
        },
        disabled=True,
        height=300,
    )


def sort_files_data():
    sorted_data = sorted(
        zip(
            state.files_data["Incl."],
            state.files_data["Path"],
            state.files_data["Tokens"],
        ),
        key=lambda x: (not x[0], x[1]),
    )
    (
        state.files_data["Incl."],
        state.files_data["Path"],
        state.files_data["Tokens"],
    ) = zip(*sorted_data)


def sort_files_metadata(files_metadata):
    sorted_data = sorted(
        zip(
            files_metadata["Incl."],
            files_metadata["Path"],
            files_metadata["Tokens"],
        ),
        key=lambda x: (not x[0], x[1]),
    )
    (
        files_metadata["Incl."],
        files_metadata["Path"],
        files_metadata["Tokens"],
    ) = zip(*sorted_data)
