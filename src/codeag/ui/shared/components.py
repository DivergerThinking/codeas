import logging

import streamlit as st

from codeag.ui.shared.state import state


def display_button(label, key, type="primary"):
    st.button(
        label,
        type=type,
        key=key,
        on_click=lambda: state.clicked(key),
    )


def display_chain(chain_name, label, steps, output_func):
    display_button(label, chain_name)
    # display_input_cost("extract_files_info")
    if state.is_clicked(chain_name):
        for step in steps:
            with st.spinner(f"Running {step}..."):
                state.unclicked(step)
                state.orchestrator.run(step)

    display_button("Preview", f"preview_{chain_name}", "secondary")
    if state.is_clicked(f"preview_{chain_name}"):
        with st.expander("Preview", expanded=True):
            for i, step in enumerate(steps):
                st.markdown(f"**Step {i+1}:** {step}")
                try:
                    preview = state.orchestrator.preview(step)
                    st.json(preview, expanded=False)
                except Exception as e:
                    st.warning(f"Can't preview '{step}' until previous steps are run.")
                    logging.error(e)
    with st.expander("Output"):
        output_func()
        # display_output_cost("extract_files_info")


def display_agent(agent_name, label, output_func):
    display_button(label, agent_name)
    # display_input_cost("extract_files_info")
    if state.is_clicked(agent_name):
        with st.spinner(f"Running {agent_name}..."):
            state.unclicked(agent_name)
            state.orchestrator.run(agent_name)

    display_button("Preview", f"preview_{agent_name}", "secondary")
    if state.is_clicked(f"preview_{agent_name}"):
        preview = state.orchestrator.preview(agent_name)
        with st.expander("Preview", expanded=True):
            st.json(preview, expanded=False)

    with st.expander("Output"):
        if not state.orchestrator.exist_output(agent_name):
            st.error("No output found.")
        else:
            output = state.orchestrator.read_output(agent_name)
            output_func(output)
            # display_output_cost("extract_files_info")


def display_files(category: str, expanded: bool = False):
    n_files = "{:,}".format(len(state.repo.incl_files_tokens[category]))
    n_tokens = "{:,}".format(sum(state.repo.incl_files_tokens[category].values()))
    with st.expander(f"{n_files} files | {n_tokens} tokens", expanded=expanded):
        display_data("files", category)


def display_folders(category: str, expanded: bool = False):
    n_folders = "{:,}".format(len(state.repo.incl_dir_tokens[category]))
    with st.expander(f"{n_folders} folders", expanded=expanded):
        st.slider(
            "depth",
            1,
            10,
            3,
            key=f"dir_depth_{category}",
            on_change=lambda: update_repo_dir(category),
        )
        display_data("dir", category)


def update_repo_dir(category: str):
    state.repo.dir_depth = st.session_state[f"dir_depth_{category}"]
    state.repo.filter_dirs(category)


# Update the display_data function to accept the category parameter
def display_data(data_type, category: str):
    incl_data, excl_data = get_data(data_type, category)
    incl_data = display_data_editor(incl_data, key=f"incl_data_{data_type}_{category}")
    excl_data = display_data_editor(excl_data, key=f"excl_data_{data_type}_{category}")
    if any(excl_data["incl."]):
        st.warning(
            f"Filter is already applied on these {data_type} or no tokens are found. Check filters and tokens count."
        )

    display_filters(data_type, category)


# Update the get_data function to use the category
def get_data(data_type, category: str):
    if data_type == "dir":
        return get_dirs_data(category)
    elif data_type == "files":
        return get_files_data(category)
    else:
        raise ValueError("Invalid data_type. Must be 'dir' or 'files'.")


# Update get_dirs_data and get_files_data to use the category
def get_dirs_data(category: str):
    incl_data = {
        "incl.": [True] * len(state.repo.incl_dir_tokens[category]),
        "paths": list(state.repo.incl_dir_tokens[category].keys()),
        "n_files": list(state.repo.incl_dir_nfiles[category].values()),
        "n_tokens": list(state.repo.incl_dir_tokens[category].values()),
    }
    excl_data = {
        "incl.": [False] * len(state.repo.excl_dir_tokens[category]),
        "paths": list(state.repo.excl_dir_tokens[category].keys()),
        "n_files": list(state.repo.excl_dir_nfiles[category].values()),
        "n_tokens": list(state.repo.excl_dir_tokens[category].values()),
    }
    return incl_data, excl_data


def get_files_data(category: str):
    incl_data = {
        "incl.": [True] * len(state.repo.incl_files_tokens[category]),
        "paths": list(state.repo.incl_files_tokens[category].keys()),
        "n_tokens": list(state.repo.incl_files_tokens[category].values()),
    }
    excl_data = {
        "incl.": [False] * len(state.repo.excl_files_tokens[category]),
        "paths": list(state.repo.excl_files_tokens[category].keys()),
        "n_tokens": list(state.repo.excl_files_tokens[category].values()),
    }
    return incl_data, excl_data


# Update the display_filters function to use the category
def display_filters(key: str, category: str):
    with st.expander("Filters", expanded=True):
        col_exclude, col_include = st.columns(2)
        with col_exclude:
            st.text_input(
                "Exclude",
                key=f"exclude_{key}_{category}",
                on_change=lambda: update_filter(key, "exclude", category),
            )
            st.multiselect(
                "Filters",
                options=state.repo.filters[category][f"exclude_{key}"],
                default=state.repo.filters[category][f"exclude_{key}"],
                on_change=lambda: update_filter_list(key, "exclude", category),
                key=f"exclude_{key}_list_{category}",
            )
        with col_include:
            st.text_input(
                "Include only",
                key=f"include_{key}_{category}",
                on_change=lambda: update_filter(key, "include", category),
            )
            st.multiselect(
                "Filters",
                options=state.repo.filters[category].get(f"include_{key}", []),
                default=state.repo.filters[category].get(f"include_{key}", []),
                on_change=lambda: update_filter_list(key, "include", category),
                key=f"include_{key}_list_{category}",
            )


# Update the update_filter and update_filter_list functions to use the category
def update_filter(key, filter_type, category: str):
    current_filters = state.repo.filters[category][f"{filter_type}_{key}"]
    new_filter = st.session_state.get(f"{filter_type}_{key}_{category}")
    if new_filter and new_filter not in current_filters:
        current_filters.append(new_filter)
        state.repo.apply_filters(category)


def update_filter_list(key, filter_type, category: str):
    state.repo.filters[category].update(
        {
            f"{filter_type}_{key}": st.session_state[
                f"{filter_type}_{key}_list_{category}"
            ]
        }
    )
    state.repo.apply_filters(category)


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


def update_filters_from_data_editor(key: str, data: dict):
    updated_data = st.session_state[key]
    category = key.split("_")[-1]  # Extract category from the key
    filters = state.repo.filters[category]

    if key.startswith("incl_data"):
        filter_key = "exclude_dir" if "dir" in key else "exclude_files"
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", True) is False:
                item_to_exclude = data["paths"][row_nr]
                if item_to_exclude not in filters[filter_key]:
                    filters[filter_key].append(item_to_exclude)
                    state.repo.apply_filters(category)
    elif key.startswith("excl_data"):
        filter_key = "exclude_dir" if "dir" in key else "exclude_files"
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", False) is True:
                item_to_include = data["paths"][row_nr]
                if item_to_include in filters[filter_key]:
                    filters[filter_key].remove(item_to_include)
                    state.repo.apply_filters(category)
