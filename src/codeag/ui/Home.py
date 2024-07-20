import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.core.agent import Agent
from codeag.core.commands import Commands
from codeag.ui.utils import search_dirs
from codeag.utils import parser

if "commands" not in st.session_state:
    st.session_state.commands = Commands(agent=Agent(repo_path="."))
if "estimates" not in st.session_state:
    st.session_state.estimates = {}
if "outputs" not in st.session_state:
    st.session_state.outputs = {}
if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = {}
if "db" not in st.session_state:
    st.session_state.db = {}


def set_state_once(key, value):
    if key not in st.session_state:
        st.session_state[key] = value


def set_state(key, value):
    st.session_state[key] = value


def get_state(key):
    return st.session_state.get(key)


def display_home_page():
    st.markdown("## Repository")

    with st.expander("", expanded=True):
        display_repo_path()

        if get_state("files_tokens") is None:
            set_files_tokens()
        if get_state("incl_files_tokens") is None:
            filter_files_tokens()

        display_tokens_count()
        st.divider()
        display_dirs()
        display_files()


def display_repo_path():
    set_state_once("repo_path", ".")

    repo_path = st_searchbox(search_dirs, label="Path", placeholder=".")
    if repo_path:
        set_state("repo_path", repo_path)

    st.caption(os.path.abspath(get_state("repo_path")))
    st.button("Update", key="update_files_tokens", on_click=update_files_tokens)
    st.divider()


def update_files_tokens():
    set_files_tokens()
    filter_files_tokens()


def set_files_tokens():
    repo_path = get_state("repo_path")
    files_paths = parser.list_files(repo_path)
    files_tokens = parser.estimate_tokens_from_files(repo_path, files_paths)
    set_state("files_tokens", files_tokens)


def filter_files_tokens():
    files_tokens = get_state("files_tokens")
    incl_files_tokens, excl_files_tokens = parser.filter_files(
        files_tokens, **get_filters()
    )
    set_state("incl_files_tokens", incl_files_tokens)
    set_state("excl_files_tokens", excl_files_tokens)


def display_tokens_count():
    incl_files_tokens = get_state("incl_files_tokens")
    st.write("**Tokens**:", "{:,}".format(sum(incl_files_tokens.values())))
    st.write("**N Files**:", "{:,}".format(len(incl_files_tokens)))


def display_dirs():
    st.write("**Directories**:")

    depth = st.slider("Depth of tree", 1, 10, 1)
    set_state("depth", depth)

    incl_data, excl_data = get_dirs_data()
    incl_data = display_data_editor(incl_data, key="incl_data_dir")
    excl_data = display_data_editor(excl_data, key="excl_data_dir")
    if any(excl_data["incl."]):
        st.warning(
            "Filter is already applied on these directories or no tokens are found. Check filters and tokens count."
        )

    display_dir_filters()

    display_tokens_count()

    st.divider()


def display_files():
    st.write("**Files**:")
    incl_data, excl_data = get_files_data()
    incl_data = display_data_editor(incl_data, key="incl_data_files")
    excl_data = display_data_editor(excl_data, key="excl_data_files")
    if any(excl_data["incl."]):
        st.warning(
            "Filter is already applied on those files or no tokens are found. Check filters or tokens count."
        )

    display_file_filters()

    display_tokens_count()


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
        if key == "incl_data_dir":
            st.write("No directories are included.")
        elif key == "excl_data_dir":
            st.write("No directories are excluded.")
        elif key == "incl_data_files":
            st.write("No files are included.")
        elif key == "excl_data_files":
            st.write("No files are excluded.")


def update_filters_from_data_editor(key: str, data: dict):
    if key == "incl_data_dir":
        updated_data = st.session_state.incl_data_dir
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", True) is False:
                dir_to_exclude = data["paths"][row_nr]
                filters = get_filters()
                if dir_to_exclude not in filters.get("exclude_dir", []):
                    filters.get("exclude_dir").append(dir_to_exclude)
                    filter_files_tokens()
    elif key == "excl_data_dir":
        updated_data = st.session_state.excl_data_dir
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", False) is True:
                dir_to_include = data["paths"][row_nr]
                filters = get_filters()
                if dir_to_include in filters.get("exclude_dir", []):
                    filters.get("exclude_dir").remove(dir_to_include)
                    filter_files_tokens()
    elif key == "incl_data_files":
        updated_data = st.session_state.incl_data_files
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", True) is False:
                file_to_exclude = data["paths"][row_nr]
                filters = get_filters()
                if file_to_exclude not in filters.get("exclude_files", []):
                    filters.get("exclude_files").append(file_to_exclude)
                    filter_files_tokens()
    elif key == "excl_data_files":
        updated_data = st.session_state.excl_data_files
        for row_nr, edited_values in updated_data["edited_rows"].items():
            if edited_values.get("incl.", False) is True:
                file_to_include = data["paths"][row_nr]
                filters = get_filters()
                if file_to_include in filters.get("exclude_files", []):
                    filters.get("exclude_files").remove(file_to_include)
                    filter_files_tokens()


def display_dir_filters():
    display_filters(key="dir")


def display_file_filters():
    display_filters(key="files")


def display_filters(key: str):
    with st.expander("Filters"):
        col_exclude, col_include = st.columns(2)
        with col_exclude:
            st.text_input(
                "Exclude",
                key=f"exclude_{key}",
                on_change=lambda: update_filter(key, "exclude"),
            )
            st.multiselect(
                "Filters",
                options=get_filters().get(f"exclude_{key}", []),
                default=get_filters().get(f"exclude_{key}", []),
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
                options=get_filters().get(f"include_{key}", []),
                default=get_filters().get(f"include_{key}", []),
                on_change=lambda: update_filter_list(key, "include"),
                key=f"include_{key}_list",
            )


def update_filter(key, filter_type):
    current_filters = get_filters()[f"{filter_type}_{key}"]
    new_filter = st.session_state.get(f"{filter_type}_{key}")
    if new_filter and new_filter not in current_filters:
        current_filters.append(new_filter)
        filter_files_tokens()


def update_filter_list(key, filter_type):
    get_filters().update(
        {f"{filter_type}_{key}": st.session_state[f"{filter_type}_{key}_list"]}
    )
    filter_files_tokens()


def get_filters():
    if get_state("filters") is None:
        set_filters()
    return get_state("filters")


def set_filters():
    set_state(
        "filters",
        {
            "exclude_dir": [],
            "include_dir": [],
            "exclude_files": [],
            "include_files": [],
        },
    )


def display_command(command_name: str):
    label = command_name.replace("_", " ").title()
    with st.expander(label):
        st.write("**Estimates**:")

        if command_name not in st.session_state.estimates:
            estimates = st.session_state.commands.estimate(command_name)
            st.session_state.estimates[command_name] = estimates

        tokens, in_tokens, out_tokens, cost, messages = (
            st.session_state.estimates[command_name]["tokens"],
            st.session_state.estimates[command_name]["in_tokens"],
            st.session_state.estimates[command_name]["out_tokens"],
            st.session_state.estimates[command_name]["cost"],
            st.session_state.estimates[command_name]["messages"],
        )
        st.write(f"tokens: {tokens:,} (in: {in_tokens:,} | out: {out_tokens:,})")
        st.write(f"cost: ${cost}")
        if st.session_state.commands.COMMAND_ARGS[command_name].multiple_requests:
            st.write(f"messages [n = {len(messages)}]:")
        else:
            st.write("messages:")
        st.json(messages, expanded=False)

        run_func = st.button(label, type="primary")

        if run_func:
            with st.spinner(f"Running '{command_name}'..."):
                outputs = st.session_state.commands.run(command_name)
                st.session_state.commands.write(command_name, outputs)

        if command_name not in st.session_state.outputs:
            outputs = st.session_state.commands.read(command_name)
            if outputs:
                st.session_state.outputs[command_name] = outputs

        if command_name in st.session_state.outputs:
            st.write("**Output**:")
            cost, tokens, in_tokens, out_tokens, contents = (
                st.session_state.outputs[command_name]["cost"],
                st.session_state.outputs[command_name]["tokens"],
                st.session_state.outputs[command_name]["in_tokens"],
                st.session_state.outputs[command_name]["out_tokens"],
                st.session_state.outputs[command_name]["contents"],
            )
            st.write(f"tokens: {tokens:,} (in: {in_tokens:,} | out: {out_tokens:,})")
            st.write(f"cost: {cost}")
            if st.session_state.commands.COMMAND_ARGS[command_name].multiple_requests:
                st.write(f"responses [n = {len(contents)}]:")
            else:
                st.write("response:")
            if isinstance(contents, str):
                st.write(contents)
            else:
                st.json(contents, expanded=False)


display_home_page()

# st.markdown("### Extract codebase information")
# display_command("extract_file_descriptions")
# display_command("extract_directory_descriptions")

# st.markdown("### Generate documentation")
# display_command("define_documentation_sections")
# display_command("identify_sections_context")
# display_command("generate_documentation_sections")
# display_command("generate_introduction")
