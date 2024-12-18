import streamlit as st

from codeas.core.core import run_repo_agent
from codeas.core.state import state
from codeas.core.tools import handle_tool_calls
from codeas.ui.components import repo_ui
from codeas.ui.components.shared import find_overlapping_files

st.subheader("🤖 Repo Agent")


def chat_page():
    with st.sidebar:
        display_files()

    check_missing_embeddings()
    initialize_chat_history()
    display_chat_history()
    handle_user_input()


def display_files():
    state.load_page_filters()
    state.apply_filters()
    repo_ui.display_filters()
    title = f"{len(state.repo.included_files_paths)}/{len(state.repo.files_paths)} files included"
    st.dataframe({title: state.repo.included_files_paths}, use_container_width=True)


def check_missing_embeddings():
    _, files_missing_embeddings = find_overlapping_files()
    if any(files_missing_embeddings):
        st.warning(
            f"{len(files_missing_embeddings)} files missing embeddings. Generate missing embeddings."
        )


def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []


def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "content" in message and "tool_call_id" in message:
                display_tool_output(message)
            elif "content" in message:
                st.markdown(message["content"])
            elif "tool_calls" in message:
                st.write(message["tool_calls"])


def display_tool_output(message):
    with st.expander(message["tool_call_id"]):
        st.write(message["content"])


def handle_user_input():
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        prompt_assistant()


def prompt_assistant():
    with st.chat_message("assistant"):
        response = st.write_stream(run_repo_agent(st.session_state.messages))

    if isinstance(response, str):
        st.session_state.messages.append({"role": "assistant", "content": response})

    elif isinstance(response, list):
        tool_calls = response[0]
        st.session_state.messages.append(
            {"role": "assistant", "tool_calls": tool_calls}
        )
        tool_calls_messages = handle_tool_calls(tool_calls)

        for call_message in tool_calls_messages:
            st.session_state.messages.append(call_message)
            with st.chat_message("Tool"):
                display_tool_output(call_message)

        prompt_assistant()
    else:
        raise ValueError(f"Invalid response type: {type(response)}")


chat_page()
