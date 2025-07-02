import uuid
import traceback

import streamlit as st
import streamlit_nested_layout  # noqa
import tokencost

from codeas.core.clients import MODELS, LLMClients
from codeas.core.retriever import ContextRetriever
from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.ui.components import metadata_ui, repo_ui
from codeas.ui.utils import read_prompts

ALL_FILES = "All files"
FULL_CONTENT = "Full content"


def chat():
    st.subheader("💬 Chat")
    state.update_current_page("Chat")
    repo_ui.display_repo_path()
    display_config_section()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    display_chat_history()
    display_user_input()
    display_clear_history_button()
    display_conversation_costs()


def display_clear_history_button():
    if st.button("Clear history"):
        st.session_state.chat_history = []
        if "conversation_id" in st.session_state:
            del st.session_state.conversation_id
        st.rerun()


def display_conversation_costs():
    if st.session_state.get("chat_history") and any(entry.get("cost") for entry in st.session_state.chat_history):
        conversation_cost = 0
        for entry in st.session_state.chat_history:
            if entry.get("cost"):
                conversation_cost += entry["cost"]["total_cost"]
        st.info(f"Conversation cost: ${conversation_cost:.4f}")


def display_config_section():
    with st.expander("CONTEXT", icon="⚙️", expanded=False):
        repo_ui.display_filters()
        display_file_options()

        retriever = ContextRetriever(**get_retriever_args())
        if (
            st.session_state.get("file_types") != ALL_FILES
            or st.session_state.get("content_types") != FULL_CONTENT
        ):
            files_missing_metadata = metadata_ui.display()
            if not any(files_missing_metadata):
                files_metadata = retriever.retrieve_files_data(
                    files_paths=state.repo.included_files_paths,
                    metadata=state.repo_metadata,
                )
                num_selected_files = sum(files_metadata["Incl."])
                selected_tokens = sum(
                    token
                    for incl, token in zip(
                        files_metadata["Incl."], files_metadata["Tokens"]
                    )
                    if incl
                )
                st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")
                repo_ui.display_metadata_editor(files_metadata)
        else:
            files_missing_metadata = []
            num_selected_files, _, selected_tokens = repo_ui.get_selected_files_info()
            st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")
            repo_ui.display_files_editor()

        if not any(files_missing_metadata) and st.button("Show context"):
            try:
                context = retriever.retrieve(
                    files_paths=state.repo.included_files_paths,
                    files_tokens=state.repo.included_files_tokens,
                    metadata=state.repo_metadata,
                )
                st.text_area("Context", context, height=300)
            except Exception as e:
                st.error(f"Error retrieving context: {e}")

    if not any(files_missing_metadata):
        if not (st.session_state.get("file_types") != ALL_FILES or st.session_state.get("content_types") != FULL_CONTENT):
             num_selected_files, _, selected_tokens = repo_ui.get_selected_files_info()

        st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")


def display_file_options():
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "File types",
            options=[
                ALL_FILES,
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
            options=[FULL_CONTENT, "Descriptions", "Details"],
            key="content_types",
        )


def display_model_options():
    all_models = list(MODELS.keys())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox(
            "Model",
            options=all_models,
            key="model1",
            index=0 if "model1" not in st.session_state or st.session_state.model1 not in all_models else all_models.index(st.session_state.model1)
        )

    remaining_models = [
        model for model in all_models if model != st.session_state.get("model1")
    ]
    with col2:
        st.selectbox(
            "Model 2",
            options=[""] + remaining_models,
            key="model2",
            disabled=not st.session_state.get("model1"),
            index=0 if "model2" not in st.session_state or st.session_state.get("model2") not in ([""] + remaining_models) else ([""] + remaining_models).index(st.session_state.get("model2"))
        )

    final_models = [
        model for model in remaining_models if model != st.session_state.get("model2")
    ]
    with col3:
        st.selectbox(
            "Model 3",
            options=[""] + final_models,
            key="model3",
            disabled=not st.session_state.get("model2"),
            index=0 if "model3" not in st.session_state or st.session_state.get("model3") not in ([""] + final_models) else ([""] + final_models).index(st.session_state.get("model3"))
        )


def get_selected_models():
    models = [
        st.session_state.get("model1"),
        st.session_state.get("model2"),
        st.session_state.get("model3")
    ]
    return [model for model in models if model]


def display_chat_history():
    for i, entry in enumerate(st.session_state.chat_history):
        template_label = f"[{entry['template']}]" if entry.get("template") else ""
        if entry["role"] == "user":
            with st.expander(f"USER {template_label}", icon="👤", expanded=False):
                st.write(entry["content"])
        else:
            with st.expander(
                f"ASSISTANT [{entry['model']}] {template_label}",
                expanded=True,
                icon="🤖",
            ):
                if entry.get("content") is None:
                    try:
                        with st.spinner("Running agent..."):
                            content, cost = run_agent(entry["model"])
                            st.write(f"💰 ${cost['total_cost']:.4f}")
                            st.session_state.chat_history[i]["content"] = content
                            st.session_state.chat_history[i]["cost"] = cost
                    except Exception as e:
                        st.error(f"Error running agent {entry['model']}: {e}")
                        st.session_state.chat_history[i]["content"] = f"Error: {e}"
                        st.session_state.chat_history[i]["cost"] = {"total_cost": 0}
                else:
                    st.write(entry["content"])
                    if entry.get('cost'):
                         st.write(f"💰 ${entry['cost']['total_cost']:.4f}")


def display_user_input():
    with st.expander(
        "NEW MESSAGE", icon="👤", expanded=not any(st.session_state.chat_history)
    ):
        display_model_options()
        initialize_input_reset()
        display_template_options()
        display_input_areas()
        reset_input_flag()
        display_action_buttons()


def display_template_options():
    prompt_options = [""] + list(read_prompts().keys())

    col1, _ = st.columns(2)
    with col1:
        st.selectbox(
            "Template",
            options=prompt_options,
            key="template1",
            index=0 if st.session_state.input_reset else None,
        )


def display_input_areas():
    prompts = read_prompts()
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    if len(selected_templates) > 1:
        for i, template in enumerate(selected_templates, 1):
            instruction_key = f"instructions{i}"
            if st.session_state.input_reset:
                st.session_state[instruction_key] = ""
            prompt_content = prompts.get(template, "")
            with st.expander(f"Template {i}: {template}", expanded=True):
                st.text_area(
                    "Instructions",
                    value=prompt_content,
                    height=200,
                    key=instruction_key,
                )
    else:
        if st.session_state.input_reset:
            st.session_state.instructions = ""
        template = selected_templates[0] if selected_templates else ""
        prompt_content = prompts.get(template, "")
        st.text_area(
            "Instructions", value=prompt_content, key="instructions", height=200
        )


def initialize_input_reset():
    # used to empty user input and templates after user sends a message
    if "input_reset" not in st.session_state:
        st.session_state.input_reset = False


def reset_input_flag():
    # used to empty user input and templates after user sends a message
    if st.session_state.input_reset:
        st.session_state.input_reset = False


def display_action_buttons():
    if st.button("Send", type="primary"):
        handle_send_button()

    if st.button("Preview", type="secondary"):
        handle_preview_button()


def handle_send_button():
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    if len(selected_templates) > 1:
        user_inputs_raw = [
            st.session_state.get(f"instructions{i}", "").strip()
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        user_inputs_raw = [st.session_state.get("instructions", "").strip()]

    valid_inputs = [(i, user_input) for i, user_input in enumerate(user_inputs_raw) if user_input]

    if valid_inputs:
        for i, user_input in valid_inputs:
            template = selected_templates[i] if len(selected_templates) > 1 and i < len(selected_templates) else ""
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input, "template": template}
            )

        for i, user_input in valid_inputs:
            template = selected_templates[i] if len(selected_templates) > 1 and i < len(selected_templates) else ""
            for model in get_selected_models():
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "model": model,
                        "template": template,
                        "multiple_models": len(get_selected_models()) > 1,
                        "content": None,
                        "cost": None
                    }
                )
        st.session_state.input_reset = True
    st.rerun()

def _display_preview_for_input_model(user_input, model, template_label):
    """Helper function to display a single preview section."""
    with st.expander(
        f"🤖 PREVIEW [{model}] {template_label}", expanded=True
    ):
        with st.spinner("Previewing..."):
            messages = get_history_messages(model)
            messages.append({"role": "user", "content": user_input})
            st.json(messages, expanded=False)
            try:
                llm_client = LLMClients(model=model)
                cost = llm_client.calculate_cost(messages)
                st.write(
                    f"💰 ${cost['input_cost']:.4f} [input] ({cost['input_tokens']:,} tokens) "
                )
            except Exception as e:
                 st.warning(f"Could not calculate cost for preview: {e}")


def handle_preview_button():
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    if len(selected_templates) > 1:
        user_inputs_raw = [
            st.session_state.get(f"instructions{i}", "").strip()
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        user_inputs_raw = [st.session_state.get("instructions", "").strip()]

    valid_inputs = [(i, user_input) for i, user_input in enumerate(user_inputs_raw) if user_input]

    for i, user_input in valid_inputs:
        template_label = (
            f"[{selected_templates[i]}]" if len(selected_templates) > 1 and i < len(selected_templates) else ""
        )
        for model in get_selected_models():
           _display_preview_for_input_model(user_input, model, template_label)


def run_agent(model):
    llm_client = LLMClients(model=model)
    messages = get_history_messages(model)

    if model in ["claude-3-5-sonnet", "claude-3-haiku"]:
        current_tokens = tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
        if current_tokens > 10000:
            st.warning(
                "Context size is large for Anthropic models. May exceed rate limits or token limits."
            )

    completion = None
    cost = {"total_cost": 0, "input_tokens": 0, "output_tokens": 0, "input_cost": 0, "output_cost": 0}

    try:
        if model in ["o1-preview", "o1-mini"]:
            st.caption("Streaming is not supported for o1 models.")
            completion = llm_client.run(messages)
            st.markdown(completion)
        else:
            completion = st.write_stream(llm_client.stream(messages))

        cost = llm_client.calculate_cost(messages, completion)

    except Exception as e:
        st.error(f"Error during LLM interaction ({model}): {e}")
        completion = f"Error: Failed to get response from {model}. {e}"

    log_agent_execution(model, messages, cost)
    return completion, cost


def get_history_messages(model):
    retriever = ContextRetriever(**get_retriever_args())
    try:
        context = retriever.retrieve(
            files_paths=state.repo.included_files_paths,
            files_tokens=state.repo.included_files_tokens,
            metadata=state.repo_metadata,
        )
    except Exception as e:
        st.error(f"Error retrieving context for agent: {e}")
        context = f"Error including context: {e}\n"

    messages = [{"role": "user", "content": context}]

    for entry in st.session_state.get("chat_history", []):
        if entry.get("role") == "user":
            if entry.get("content"):
                 messages.append({"role": entry["role"], "content": entry["content"]})
        elif entry.get("role") == "assistant" and entry.get("content") is not None:
            if entry.get("multiple_models", False) is False or entry.get("model") == model:
                messages.append({"role": entry["role"], "content": entry["content"]})

    return messages


def get_retriever_args():
    file_types = st.session_state.get("file_types", ALL_FILES)
    content_types = st.session_state.get("content_types", FULL_CONTENT)
    return {
        "include_all_files": file_types == ALL_FILES,
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


def log_agent_execution(model, messages, cost):
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())

    prompt = messages[-1].get("content", "") if messages else ""

    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]
    using_template = any(selected_templates)
    using_multiple_templates = len(selected_templates) > 1
    using_multiple_models = len(get_selected_models()) > 1
    cost_to_log = cost if cost is not None else {"total_cost": 0, "input_tokens": 0, "output_tokens": 0, "input_cost": 0, "output_cost": 0}

    usage_tracker.log_agent_execution(
        model=model,
        prompt=prompt,
        cost=cost_to_log,
        conversation_id=st.session_state.get("conversation_id"),
        using_template=using_template,
        using_multiple_templates=using_multiple_templates,
        using_multiple_models=using_multiple_models,
    )


chat()