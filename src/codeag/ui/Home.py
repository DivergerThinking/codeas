import json
import os
from typing import Literal

import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.configs.agents_configs import AGENTS_CONFIGS
from codeag.configs.chains_configs import CHAINS_CONFIGS
from codeag.core.agent import Agent
from codeag.core.llms import LLMClient
from codeag.core.repo import Filters, Repo, RepoSelector
from codeag.ui.utils import search_dirs


def display_filters(key: Literal["files", "folders"]):
    col_include, col_exclude = st.columns(2)
    with col_include:
        st.text_input(
            "Include",
            value=", ".join(st.session_state.filters.include_files),
            key=f"include_{key}",
            on_change=lambda: update_filter(key, "include"),
            placeholder="*.py, src/*, etc.",
        )
    with col_exclude:
        st.text_input(
            "Exclude",
            value=",".join(st.session_state.filters.exclude_files),
            key=f"exclude_{key}",
            on_change=lambda: update_filter(key, "exclude"),
            placeholder="debug/*, *.ipynb, etc.",
        )


def update_filter(key: str, filter_type: Literal["include", "exclude"]):
    state_of_filters = st.session_state.get(f"{filter_type}_{key}")
    filters_list = state_of_filters.split(",") if state_of_filters else []
    filters_list = [filter_.strip() for filter_ in filters_list]
    setattr(st.session_state.filters, f"{filter_type}_{key}", filters_list)
    st.session_state.filters.export(st.session_state.repo_path)


def display_data_editor(key: str, data: dict):
    st.data_editor(
        data,
        key=key,
        use_container_width=True,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width="small"),
            "Path": st.column_config.TextColumn(width="large"),
        },
        disabled=True,
    )


if "llm_client" not in st.session_state:
    st.session_state.llm_client = LLMClient()


def chain_page():
    st.title("Codeas")

    st.subheader("Repo")
    repo_path = st_searchbox(search_dirs, placeholder=".", default=".")
    st.caption(os.path.abspath(repo_path))

    st.session_state.repo_path = repo_path

    if "filters" not in st.session_state:
        st.session_state.filters = Filters()
        st.session_state.filters.read_from_file(repo_path)

    # Load repository data
    repo = Repo(repo_path=repo_path)
    selector = RepoSelector(repo=repo)

    # Context section
    st.subheader("Context")
    display_filters("files")
    files_to_include = selector.filter_files(st.session_state.filters)
    files_data = {
        "Incl.": files_to_include,
        "Path": repo.files_paths,
        "Tokens": list(repo.files_tokens.values()),
    }
    # Sort by Incl. = True first, then by Path
    sorted_files_data = sorted(
        zip(files_data["Incl."], files_data["Path"], files_data["Tokens"]),
        key=lambda x: (not x[0], x[1]),
    )
    # Unzip the sorted data
    files_data["Incl."], files_data["Path"], files_data["Tokens"] = map(
        list, zip(*sorted_files_data)
    )
    display_data_editor("files_editor", files_data)

    # Add st.info() to show selected files / total files
    num_selected_files = sum(files_data["Incl."])
    total_files = len(files_data["Incl."])
    st.info(f"{num_selected_files} / {total_files} files selected")

    # Add st.info() to show tokens in selected files with comma delimiter
    st.session_state.selected_file_paths = [
        path for path, incl in zip(files_data["Path"], files_data["Incl."]) if incl
    ]

    selected_tokens = sum(
        token for incl, token in zip(files_data["Incl."], files_data["Tokens"]) if incl
    )
    st.warning(f"{selected_tokens:,} tokens in selected files")

    st.subheader("Chain")
    # Initialize session state for selected steps if not exists
    if "selected_steps" not in st.session_state:
        st.session_state.selected_steps = []

    # Available steps (agents)
    available_steps = list(AGENTS_CONFIGS.keys())
    available_chains = list(CHAINS_CONFIGS.keys())  # Available chains

    col1, col2 = st.columns([2, 2])
    with col1:
        selected_chain = st.selectbox(
            "Select a chain to add:", [""] + available_chains
        )  # Dropdown for chains
        if st.button("Add chain", key="add_chain"):
            if selected_chain:
                for step in CHAINS_CONFIGS[selected_chain]:
                    if step not in st.session_state.selected_steps:
                        st.session_state.selected_steps.append(step)
    with col2:
        selected_steps = st.multiselect(
            "Select steps to add to the chain:", available_steps
        )
        if st.button("Add Selected Steps"):
            for step in selected_steps:
                if step not in st.session_state.selected_steps:
                    st.session_state.selected_steps.append(step)

    # Display and manage the current chain
    for i, step in enumerate(st.session_state.selected_steps):
        col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
        with col1:
            st.write(f"{i+1}. {step}")
        with col2:
            if st.button("↑", key=f"up_{i}", disabled=i == 0):
                (
                    st.session_state.selected_steps[i],
                    st.session_state.selected_steps[i - 1],
                ) = (
                    st.session_state.selected_steps[i - 1],
                    st.session_state.selected_steps[i],
                )
                st.rerun()
        with col3:
            if st.button(
                "↓",
                key=f"down_{i}",
                disabled=i == len(st.session_state.selected_steps) - 1,
            ):
                (
                    st.session_state.selected_steps[i],
                    st.session_state.selected_steps[i + 1],
                ) = (
                    st.session_state.selected_steps[i + 1],
                    st.session_state.selected_steps[i],
                )
                st.rerun()
        with col4:
            if st.button("🗑", key=f"remove_{i}", type="primary"):
                st.session_state.selected_steps.pop(i)
                st.rerun()

    col1, col2, _ = st.columns([2, 2, 6])
    with col1:
        run_chain = st.button(
            "Run Chain",
            type="primary",
            disabled=len(st.session_state.selected_steps) == 0,
        )

    with col2:
        preview_chain = st.button(
            "Preview Chain", disabled=len(st.session_state.selected_steps) == 0
        )

    if run_chain:
        st.write("Running the chain...")
        for step in st.session_state.selected_steps:
            with st.spinner(f"Running {step}..."):
                agent = Agent(**AGENTS_CONFIGS[step])
                args = AGENTS_CONFIGS[step]["args"]
                parsed_args = {
                    key: st.session_state[value] for key, value in args.items()
                }
                output = agent.run(
                    llm_client=st.session_state.llm_client, **parsed_args
                )
                write_agent_output(output, step)
                display_agent_output(output, step)
        run_chain = False

    elif preview_chain:
        for step in st.session_state.selected_steps:
            with st.spinner(f"{step}"):
                agent = Agent(**AGENTS_CONFIGS[step])
                args = AGENTS_CONFIGS[step]["args"]
                parsed_args = {
                    key: st.session_state[value] for key, value in args.items()
                }
                preview = agent.preview(**parsed_args)
                display_agent_preview(preview, step)
        preview_chain = False


def write_agent_output(output, step: str):
    if not os.path.exists(f"{st.session_state.repo_path}/.codeas/outputs"):
        os.makedirs(f"{st.session_state.repo_path}/.codeas/outputs")
    with open(f"{st.session_state.repo_path}/.codeas/outputs/{step}.json", "w") as f:
        json.dump(output.model_dump(), f)


def display_agent_preview(preview, step: str):
    with st.expander(f"{step}", expanded=True):
        st.json(preview.model_dump(), expanded=False)


def display_agent_output(output, step: str):
    with st.expander(f"{step}", expanded=True):
        if AGENTS_CONFIGS[step]["output_func"] == "display_json":
            st.json(output.model_dump(), expanded=False)
        elif AGENTS_CONFIGS[step]["output_func"] == "display_text":
            st.markdown(output.response["content"])


if __name__ == "__main__":
    chain_page()
