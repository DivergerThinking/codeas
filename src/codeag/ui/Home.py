import logging
import os

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.core.agent import Agent
from codeag.core.commands import Commands
from codeag.utils import parser

if "commands" not in st.session_state:
    st.session_state.commands = Commands(agent=Agent(repo_path="."))
if "estimates" not in st.session_state:
    st.session_state.estimates = {}
if "outputs" not in st.session_state:
    st.session_state.outputs = {}


def list_dir(path: str):
    # search function that returns the directories with starting path "path"
    if "/" in path:
        base_dir, start_next_dir = os.path.split(path)
        try:
            return [
                os.path.join(base_dir, d)
                for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d))
                and d.startswith(start_next_dir)
            ]
        except Exception:
            return []
    elif path == "." or path == "..":
        return [
            os.path.join(path, d)
            for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d))
        ]


st.markdown("## Repository")

base_path = os.path.abspath(".")
current_dir_name = os.path.basename(base_path)
repo_path = st_searchbox(list_dir, label="Path", placeholder=".")
if repo_path:
    st.caption(os.path.abspath(repo_path))
else:
    st.caption(base_path)
    repo_path = os.path.abspath(".")

clicked_parse = st.button("Parse", type="primary")


def display_paths(repo_path, folder_only):
    paths = parser.get_repository_paths(
        repo_path,
        exclude_dir=[".*"],
        folder_only=folder_only,  # , check_readibility=True
    )
    logging.error(f"Found {len(paths)} paths")
    if any(paths):
        data = {"incl.": [True] * len(paths), "paths": paths}
        return st.data_editor(
            data,
            column_config={
                "incl.": st.column_config.CheckboxColumn(width="small"),
                "paths": st.column_config.TextColumn(width="large"),
            },
            key=str(folder_only),
        )


if clicked_parse:
    st.write("repo", repo_path)
    with st.expander("Directories"):
        dir_paths = display_paths(repo_path, folder_only=True)
    with st.expander("Files"):
        file_paths = display_paths(repo_path, folder_only=False)


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


# st.markdown("### Extract codebase information")
# display_command("extract_file_descriptions")
# display_command("extract_directory_descriptions")

# st.markdown("### Generate documentation")
# display_command("define_documentation_sections")
# display_command("identify_sections_context")
# display_command("generate_documentation_sections")
# display_command("generate_introduction")
