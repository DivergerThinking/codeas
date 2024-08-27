import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.ui.shared.components import display_agent, display_button
from codeag.ui.shared.state import state
from codeag.ui.utils import search_dirs


def display_home_page():
    st.markdown("## Repository")
    display_repo_path()
    display_extract_files_info()
    display_extract_folders_info()


def display_repo_path():
    with st.expander("Path", expanded=True):
        repo_path = st_searchbox(search_dirs, placeholder=".", default=".")

        display_button("Update", "update_files_tokens")
        if state.is_clicked("update_files_tokens"):
            state.update_repo_path(repo_path)

        st.caption(os.path.abspath(state.repo_path))
        state.export_repo_state()


def display_extract_files_info():
    with st.expander("Files Info", expanded=True):
        display_files()
        display_agent("extract_files_info", "Extract Files Info", display_json)


def display_extract_folders_info():
    with st.expander("Folders Info", expanded=True):
        display_dirs()
        display_agent("extract_folders_info", "Extract Folders Info", display_json)


def display_json(output):
    st.json(output, expanded=False)


def display_files():
    n_files = "{:,}".format(len(state.repo.incl_files_tokens))
    n_tokens = "{:,}".format(sum(state.repo.incl_files_tokens.values()))
    with st.expander(f"{n_files} files | {n_tokens} tokens"):
        display_data("files")


def display_dirs():
    n_folders = "{:,}".format(len(state.repo.incl_dir_tokens))
    with st.expander(f"{n_folders} folders"):
        st.slider("depth", 1, 10, 3, key="dir_depth", on_change=update_repo_dir)
        display_data("dir")


def update_repo_dir():
    state.repo.dir_depth = st.session_state["dir_depth"]
    state.repo.filter_dirs()


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
    incl_data = {
        "incl.": [True] * len(state.repo.incl_dir_tokens),
        "paths": list(state.repo.incl_dir_tokens.keys()),
        "n_files": list(state.repo.incl_dir_nfiles.values()),
        "n_tokens": list(state.repo.incl_dir_tokens.values()),
    }
    excl_data = {
        "incl.": [False] * len(state.repo.excl_dir_tokens),
        "paths": list(state.repo.excl_dir_tokens.keys()),
        "n_files": list(state.repo.excl_dir_nfiles.values()),
        "n_tokens": list(state.repo.excl_dir_tokens.values()),
    }
    return incl_data, excl_data


def get_files_data():
    incl_data = {
        "incl.": [True] * len(state.repo.incl_files_tokens),
        "paths": list(state.repo.incl_files_tokens.keys()),
        "n_tokens": list(state.repo.incl_files_tokens.values()),
    }
    excl_data = {
        "incl.": [False] * len(state.repo.excl_files_tokens),
        "paths": list(state.repo.excl_files_tokens.keys()),
        "n_tokens": list(state.repo.excl_files_tokens.values()),
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
                options=state.repo.filters[f"exclude_{key}"],
                default=state.repo.filters[f"exclude_{key}"],
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
                options=state.repo.filters.get(f"include_{key}", []),
                default=state.repo.filters.get(f"include_{key}", []),
                on_change=lambda: update_filter_list(key, "include"),
                key=f"include_{key}_list",
            )


def update_filters_from_data_editor(key: str, data: dict):
    updated_data = st.session_state[key]
    filters = state.repo.filters

    if key.startswith("incl_data"):
        filter_key = "exclude_dir" if "dir" in key else "exclude_files"
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", True) is False:
                item_to_exclude = data["paths"][row_nr]
                if item_to_exclude not in filters.get(filter_key, []):
                    filters.get(filter_key).append(item_to_exclude)
                    state.repo.apply_filters()
                    state.export_repo_state()
    elif key.startswith("excl_data"):
        filter_key = "exclude_dir" if "dir" in key else "exclude_files"
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", False) is True:
                item_to_include = data["paths"][row_nr]
                if item_to_include in filters.get(filter_key, []):
                    filters.get(filter_key).remove(item_to_include)
                    state.repo.apply_filters()
                    state.export_repo_state()


def update_filter(key, filter_type):
    current_filters = state.repo.filters[f"{filter_type}_{key}"]
    new_filter = st.session_state.get(f"{filter_type}_{key}")
    if new_filter and new_filter not in current_filters:
        current_filters.append(new_filter)
        state.repo.apply_filters()
        state.export_repo_state()


def update_filter_list(key, filter_type):
    state.repo.filters.update(
        {f"{filter_type}_{key}": st.session_state[f"{filter_type}_{key}_list"]}
    )
    state.repo.apply_filters()
    state.export_repo_state()


display_home_page()
