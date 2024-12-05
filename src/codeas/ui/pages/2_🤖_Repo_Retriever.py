import streamlit as st

from codeas.core.state import state
from codeas.ui.components import repo_ui
from codeas.ui.components.shared import find_overlapping_files

st.subheader("🤖 Repo Retriever")


def display_files():
    state.load_page_filters()
    state.apply_filters()
    repo_ui.display_filters()
    title = f"{len(state.repo.included_files_paths)}/{len(state.repo.files_paths)} files included"
    st.dataframe({title: state.repo.included_files_paths}, use_container_width=True)
    _, files_missing_embeddings = find_overlapping_files()
    if any(files_missing_embeddings):
        st.warning(
            f"{len(files_missing_embeddings)} files missing embeddings. Generate missing embeddings."
        )


def chat_page():
    with st.sidebar:
        display_files()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = st.write_stream(response_generator())
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


def response_generator():
    yield "Hello, how can I help you today?"


chat_page()
