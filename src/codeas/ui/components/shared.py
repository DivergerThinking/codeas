import streamlit as st

from codeas.core.state import state
from codeas.ui.components import repo_ui


def find_overlapping_files():
    selected_repo_files = state.repo.get_file_paths()
    files_with_embeddings = state.storage.fetch_files_in_chromadb(state.repo_path)
    files_overlapping = [
        filepath
        for filepath in selected_repo_files
        if filepath in files_with_embeddings
    ]
    files_missing_embeddings = [
        filepath
        for filepath in selected_repo_files
        if filepath not in files_with_embeddings
    ]
    additional_files_with_embeddings = [
        filepath
        for filepath in files_with_embeddings
        if filepath not in selected_repo_files
    ]
    return files_overlapping, files_missing_embeddings, additional_files_with_embeddings


def display_files():
    state.load_page_filters()
    state.apply_filters()
    repo_ui.display_filters()
    title = f"{len(state.repo.included_files_paths)}/{len(state.repo.files_paths)} files included"
    st.dataframe({title: state.repo.included_files_paths}, use_container_width=True)


def check_missing_embeddings():
    (
        _,
        files_missing_embeddings,
        additional_files_with_embeddings,
    ) = find_overlapping_files()
    if any(files_missing_embeddings):
        st.warning(
            f"{len(files_missing_embeddings)} files missing embeddings. Generate missing embeddings."
        )
    if any(additional_files_with_embeddings):
        st.error(
            f"{len(additional_files_with_embeddings)} files with embeddings not found in selected files. Update collection."
        )


def initialize_chat_history(system_prompt: str):
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]


def display_chat_history():
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            if "content" in message and "tool_call_id" in message:
                display_tool_output(message)
            elif "content" in message:
                st.markdown(message["content"])
            elif "tool_calls" in message:
                st.write(message["tool_calls"])


def display_tool_output(message):
    with st.expander(message["tool_call_id"]):
        st.code(message["content"])
