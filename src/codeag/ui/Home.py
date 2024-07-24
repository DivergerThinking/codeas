import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.ui.shared.state import (
    filter_files_tokens,
    get_state,
    init_state,
    set_state,
    update_state,
)
from codeag.ui.utils import search_dirs
from codeag.utils import parser

init_state()


def display_home_page():
    st.markdown("## Repository")

    with st.expander("Path", expanded=True):
        display_repo_path()

    with st.expander("Files", expanded=True):
        display_files()

    with st.expander("Directories", expanded=True):
        display_dirs()


def display_repo_path():
    repo_path = st_searchbox(search_dirs, placeholder=".")
    st.button(
        "Update", key="update_files_tokens", on_click=lambda: update_state(repo_path)
    )
    st.caption(os.path.abspath(get_state("repo_path")))


def display_dirs():
    depth = st.slider("Depth of tree", 1, 10, 1)
    set_state("depth", depth)
    st.write("**Tokens**:", "{:,}".format(sum(get_state("incl_files_tokens").values())))
    display_data("dir")


def display_files():
    st.write("**Included files**:", "{:,}".format(len(get_state("incl_files_tokens"))))
    st.write("**Tokens**:", "{:,}".format(sum(get_state("incl_files_tokens").values())))
    display_data("files")


def display_data(data_type):
    incl_data, excl_data = get_data(data_type)
    incl_data = display_data_editor(incl_data, key=f"incl_data_{data_type}")
    excl_data = display_data_editor(excl_data, key=f"excl_data_{data_type}")
    if any(excl_data["incl."]):
        st.warning(
            f"Filter is already applied on these {data_type} or no tokens are found. Check filters and tokens count."
        )

    display_filters(data_type)


def get_data(data_type):
    if data_type == "dir":
        return get_dirs_data()
    elif data_type == "files":
        return get_files_data()
    else:
        raise ValueError("Invalid data_type. Must be 'dir' or 'files'.")


def get_dirs_data():
    incl_paths, incl_n_files, incl_n_tokens = parser.extract_folders_up_to_level(
        get_state("repo_path"), get_state("incl_files_tokens"), get_state("depth")
    )
    excl_paths, excl_n_files, excl_n_tokens = parser.extract_folders_up_to_level(
        get_state("repo_path"), get_state("excl_files_tokens"), get_state("depth")
    )
    incl_data = {
        "incl.": [True] * len(incl_paths),
        "paths": incl_paths,
        "n_files": incl_n_files,
        "n_tokens": incl_n_tokens,
    }
    excl_data = {
        "incl.": [False] * len(excl_paths),
        "paths": excl_paths,
        "n_files": excl_n_files,
        "n_tokens": excl_n_tokens,
    }
    return incl_data, excl_data


def get_files_data():
    incl_data = {
        "incl.": [True] * len(get_state("incl_files_tokens")),
        "paths": list(get_state("incl_files_tokens").keys()),
        "n_tokens": list(get_state("incl_files_tokens").values()),
    }
    excl_data = {
        "incl.": [False] * len(get_state("excl_files_tokens")),
        "paths": list(get_state("excl_files_tokens").keys()),
        "n_tokens": list(get_state("excl_files_tokens").values()),
    }
    return incl_data, excl_data


def display_data_editor(data, key, disable_checks: bool = False):
    if any(data["paths"]):
        return st.data_editor(
            data,
            use_container_width=True,
            column_config={
                "incl.": st.column_config.CheckboxColumn(
                    width="small", disabled=disable_checks
                ),
                "paths": st.column_config.TextColumn(width="large"),
            },
            key=key,
            on_change=lambda: update_filters_from_data_editor(key, data),
        )
    else:
        display_no_data_message(key)


def display_no_data_message(key):
    messages = {
        "incl_data_dir": "No directories are included.",
        "excl_data_dir": "No directories are excluded.",
        "incl_data_files": "No files are included.",
        "excl_data_files": "No files are excluded.",
    }
    st.write(messages.get(key, "No data available."))


def display_filters(key: str):
    with st.expander("Filters", expanded=True):
        col_exclude, col_include = st.columns(2)
        with col_exclude:
            st.text_input(
                "Exclude",
                key=f"exclude_{key}",
                on_change=lambda: update_filter(key, "exclude"),
            )
            st.multiselect(
                "Filters",
                options=get_state("filters")[f"exclude_{key}"],
                default=get_state("filters")[f"exclude_{key}"],
                on_change=lambda: update_filter_list(key, "exclude"),
                key=f"exclude_{key}_list",
            )
        with col_include:
            st.text_input(
                "Include only",
                key=f"include_{key}",
                on_change=lambda: update_filter(key, "include"),
            )
            st.multiselect(
                "Filters",
                options=get_state("filters").get(f"include_{key}", []),
                default=get_state("filters").get(f"include_{key}", []),
                on_change=lambda: update_filter_list(key, "include"),
                key=f"include_{key}_list",
            )


def update_filters_from_data_editor(key: str, data: dict):
    updated_data = st.session_state[key]
    filters = get_state("filters")

    if key.startswith("incl_data"):
        filter_key = "exclude_dir" if "dir" in key else "exclude_files"
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", True) is False:
                item_to_exclude = data["paths"][row_nr]
                if item_to_exclude not in filters.get(filter_key, []):
                    filters.get(filter_key).append(item_to_exclude)
                    filter_files_tokens()
    elif key.startswith("excl_data"):
        filter_key = "exclude_dir" if "dir" in key else "exclude_files"
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", False) is True:
                item_to_include = data["paths"][row_nr]
                if item_to_include in filters.get(filter_key, []):
                    filters.get(filter_key).remove(item_to_include)
                    filter_files_tokens()


def update_filter(key, filter_type):
    current_filters = get_state("filters")[f"{filter_type}_{key}"]
    new_filter = st.session_state.get(f"{filter_type}_{key}")
    if new_filter and new_filter not in current_filters:
        current_filters.append(new_filter)
        filter_files_tokens()


def update_filter_list(key, filter_type):
    get_state("filters").update(
        {f"{filter_type}_{key}": st.session_state[f"{filter_type}_{key}_list"]}
    )
    filter_files_tokens()


display_home_page()
