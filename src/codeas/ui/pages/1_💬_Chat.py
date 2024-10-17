import streamlit as st
import streamlit_nested_layout  # noqa

from codeas.configs.templates import TEMPLATES
from codeas.core.clients import MODELS, LLMClients
from codeas.core.retriever import ContextRetriever
from codeas.core.state import state
from codeas.ui.components import metadata_ui, repo_ui


def chat():
    st.subheader("💬 Chat")
    repo_ui.display_repo_path()
    display_config_section()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    display_chat_history()
    display_user_input()
    display_clear_history_button()


def display_clear_history_button():
    if st.button("Clear history"):
        st.session_state.chat_history = []
        st.rerun()


def display_config_section():
    with st.popover("SETTINGS", icon="⚙️", use_container_width=True):
        repo_ui.display_files()
        display_file_options()


def display_file_options():
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "File types",
            options=[
                "All files",
                "Code files",
                "Testing files",
                "Config files",
                "Deployment files",
                "Security files",
                "UI files",
                "API files",
            ],
            key="file_types",
        )
    with col2:
        st.selectbox(
            "Content types",
            options=["Full content", "Descriptions", "Details"],
            key="content_types",
        )

    if (
        st.session_state.get("file_types") != "All files"
        or st.session_state.get("content_types") != "Full content"
    ):
        metadata_ui.display()


def display_model_options():
    all_models = MODELS.keys()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox(
            "Model 1",
            options=all_models,
            key="model1",
        )

    remaining_models = [
        model for model in all_models if model != st.session_state.model1
    ]
    with col2:
        st.selectbox(
            "Model 2",
            options=[""] + remaining_models,
            key="model2",
            disabled=not st.session_state.model1,
        )

    final_models = [
        model for model in remaining_models if model != st.session_state.model2
    ]
    with col3:
        st.selectbox(
            "Model 3",
            options=[""] + final_models,
            key="model3",
            disabled=not st.session_state.model2,
        )


def get_selected_models():
    models = [st.session_state.model1, st.session_state.model2, st.session_state.model3]
    return [model for model in models if model]


def display_chat_history():
    for i, entry in enumerate(st.session_state.chat_history):
        if entry["role"] == "user":
            with st.expander("USER", icon="👤", expanded=True):
                st.write(entry["content"])
        else:
            model_name = entry.get("model", "")
            with st.expander(
                f"ASSISTANT {'[' + model_name + ']' if model_name else ''}",
                expanded=True,
                icon="🤖",
            ):
                if entry.get("content") is None:
                    agent_output = run_agent(entry["model"])
                    st.session_state.chat_history[i]["content"] = agent_output
                else:
                    st.write(entry["content"])


def display_user_input():
    with st.expander(
        "NEW MESSAGE", icon="👤", expanded=not any(st.session_state.chat_history)
    ):
        display_model_options()
        initialize_input_reset()
        display_template_selector()
        display_input_area()
        reset_input_flag()
        display_action_buttons()


def display_template_selector():
    col1, _ = st.columns(2)
    with col1:
        prompt_options = [""] + list(TEMPLATES.keys())
        st.selectbox(
            "Templates",
            options=prompt_options,
            key="template_selector",
            index=0 if st.session_state.input_reset else None,
        )


def initialize_input_reset():
    if "input_reset" not in st.session_state:
        st.session_state.input_reset = False


def reset_input_flag():
    if st.session_state.input_reset:
        st.session_state.input_reset = False


def display_input_area():
    selected_prompt = st.session_state.get("template_selector")
    if st.session_state.input_reset:
        st.session_state.instructions = ""
    prompt_content = TEMPLATES.get(selected_prompt, "") if selected_prompt else ""
    st.text_area("Instructions", value=prompt_content, height=200, key="instructions")


def display_action_buttons():
    if st.button("Send", type="primary"):
        handle_send_button()

    if st.button("Preview", type="secondary"):
        handle_preview_button()


def handle_send_button():
    user_input = st.session_state.instructions.strip()
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        for model in get_selected_models():
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": None,
                    "model": model,
                    "multiple_models": len(get_selected_models()) > 1,
                }
            )
        st.session_state.input_reset = True
    st.rerun()


def handle_preview_button():
    user_input = st.session_state.instructions.strip()
    if user_input:
        for model in get_selected_models():
            with st.expander(f"🤖 PREVIEW [{model}]", expanded=True):
                with st.spinner("Previewing..."):
                    messages = get_history_messages(model)
                    messages.append({"role": "user", "content": user_input})
                    st.json(messages, expanded=False)


def run_agent(model):
    llm_client = LLMClients(model=model)
    messages = get_history_messages(model)
    return st.write_stream(llm_client.stream(messages))


def get_history_messages(model):
    retriever = ContextRetriever(**get_retriever_args())
    context = retriever.retrieve(
        files_paths=state.repo.included_files_paths,
        files_tokens=state.repo.included_files_tokens,
        metadata=state.repo_metadata,
    )
    messages = [{"role": "user", "content": context}]
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            messages.append({"role": entry["role"], "content": entry["content"]})
        elif entry["role"] == "assistant" and entry["content"] is not None:
            if entry.get("multiple_models") is False or entry.get("model") == model:
                messages.append({"role": entry["role"], "content": entry["content"]})
    return messages


def display_preview(agent_preview):
    st.info(
        f"Input cost: ${agent_preview.cost['input_cost']:.4f} ({agent_preview.tokens['input_tokens']:,} input tokens)"
    )
    st.write("Messages:")
    st.json(agent_preview.messages, expanded=False)


def get_retriever_args():
    file_types = st.session_state.get("file_types", "All files")
    content_types = st.session_state.get("content_types", "Full content")
    return {
        "include_all_files": file_types == "All files",
        "include_code_files": file_types == "Code files",
        "include_testing_files": file_types == "Testing files",
        "include_config_files": file_types == "Config files",
        "include_deployment_files": file_types == "Deployment files",
        "include_security_files": file_types == "Security files",
        "include_ui_files": file_types == "UI files",
        "include_api_files": file_types == "API files",
        "use_descriptions": content_types == "Descriptions",
        "use_details": content_types == "Details",
    }


chat()
