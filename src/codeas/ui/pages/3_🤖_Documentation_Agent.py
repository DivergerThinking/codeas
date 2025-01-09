import streamlit as st

from codeas.core.core import handle_tool_calls, run_documentation_agent
from codeas.core.prompts import DOCUMENTATION_AGENT_PROMPT
from codeas.ui.components.shared import (
    check_missing_embeddings,
    display_chat_history,
    display_files,
    display_tool_output,
    initialize_chat_history,
)

st.subheader("🤖 Documentation Agent")


def chat_page():
    with st.sidebar:
        display_files()
    check_missing_embeddings()
    initialize_chat_history(DOCUMENTATION_AGENT_PROMPT)
    display_chat_history()
    handle_user_input()


def handle_user_input():
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        prompt_assistant()


def prompt_assistant():
    with st.chat_message("assistant"):
        response = st.write_stream(run_documentation_agent(st.session_state.messages))

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
