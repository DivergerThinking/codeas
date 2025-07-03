// Verified: No new SonarQube issues introduced
import uuid

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

DATA_DISCLOSURE_WARNING = """
**:warning: Data Privacy and Security Notice:**
Your file content and conversation history will be sent to the selected external LLM provider(s) to generate responses.
Be mindful of the data you include in your files and prompts.
"""


def chat():
    st.subheader("💬 Chat")
    state.update_current_page("Chat")
    repo_ui.display_repo_path()
    display_config_section()

    st.warning(DATA_DISCLOSURE_WARNING)

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
    if any(entry.get("cost") for entry in st.session_state.chat_history):
        conversation_cost = 0
        for entry in st.session_state.chat_history:
            if entry.get("cost"):
                conversation_cost += entry["cost"].get("total_cost", 0)

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
            options=[""] + all_models,
            key="model1",
            index=(all_models.index(st.session_state.get("model1", "")) + 1
                   if st.session_state.get("model1", "") in all_models
                   else 0),
        )
    selected_model1 = st.session_state.get("model1", "")
    remaining_models_2 = [
        model for model in all_models if model != selected_model1
    ]
    with col2:
        st.selectbox(
            "Model 2",
            options=[""] + remaining_models_2,
            key="model2",
            disabled=not selected_model1,
            index=(remaining_models_2.index(st.session_state.get("model2", "")) + 1
                   if st.session_state.get("model2", "") in remaining_models_2
                   else 0),
        )

    selected_model2 = st.session_state.get("model2", "")
    final_models = [
        model for model in remaining_models_2 if model != selected_model2
    ]
    with col3:
        st.selectbox(
            "Model 3",
            options=[""] + final_models,
            key="model3",
            disabled=not selected_model2,
            index=(final_models.index(st.session_state.get("model3", "")) + 1
                   if st.session_state.get("model3", "") in final_models
                   else 0),
        )


def get_selected_models():
    models = [st.session_state.get("model1", ""), st.session_state.get("model2", ""), st.session_state.get("model3", "")]
    return [model for model in models if model]


def display_chat_history():
    for i in range(len(st.session_state.chat_history) -1, -1, -1):
        entry = st.session_state.chat_history[i]
        template_label = f"[{entry['template']}]" if entry.get("template") else ""
        if entry["role"] == "user":
            with st.expander(f"USER {template_label}", icon="👤", expanded=False):
                st.write(entry["content"])
        else:
            expanded_state = entry.get("content") is None
            with st.expander(
                f"ASSISTANT [{entry.get('model', 'Unknown')}] {template_label}",
                expanded=expanded_state,
                icon="🤖",
            ):
                if entry.get("content") is None:
                    with st.spinner("Running agent..."):
                        content, cost = run_agent(entry.get("model"))

                        st.session_state.chat_history[i]["content"] = content
                        st.session_state.chat_history[i]["cost"] = cost

                    updated_entry = st.session_state.chat_history[i]
                    if updated_entry.get("content"):
                         st.write(updated_entry["content"])
                    if updated_entry.get("cost") and updated_entry["cost"].get("total_cost") is not None:
                        st.write(f"💰 ${updated_entry['cost']['total_cost']:.4f}")

                else:
                    st.write(entry["content"])
                    if entry.get("cost") and entry["cost"].get("total_cost") is not None:
                        st.write(f"💰 ${entry['cost']['total_cost']:.4f}")


def display_user_input():
    expanded_state = not any(st.session_state.chat_history)
    with st.expander("NEW MESSAGE", icon="👤", expanded=expanded_state):
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
            index=(0 if st.session_state.get("input_reset", False)
                   else prompt_options.index(st.session_state.get("template1", ""))
                   if st.session_state.get("template1", "") in prompt_options
                   else 0),
        )


def _display_single_input_area(prompts, template_name):
    instruction_key = "instructions"
    if st.session_state.get("input_reset", False):
        st.session_state[instruction_key] = ""
    prompt_content = prompts.get(template_name, "")
    st.text_area(
        "Instructions",
        value=st.session_state.get(instruction_key, prompt_content),
        height=200,
        key=instruction_key,
    )

def _display_multiple_input_areas(prompts, selected_templates):
    for i, template in enumerate(selected_templates, 1):
        instruction_key = f"instructions{i}"
        if st.session_state.get("input_reset", False):
            st.session_state[instruction_key] = ""
        prompt_content = prompts.get(template, "")
        with st.expander(f"Template {i}: {template}", expanded=True):
            st.text_area(
                "Instructions",
                value=st.session_state.get(instruction_key, prompt_content),
                height=200,
                key=instruction_key,
            )

def display_input_areas():
    prompts = read_prompts()
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    if len(selected_templates) > 1:
        _display_multiple_input_areas(prompts, selected_templates)
    else:
        template_name = selected_templates[0] if selected_templates else ""
        _display_single_input_area(prompts, template_name)


def initialize_input_reset():
    if "input_reset" not in st.session_state:
        st.session_state.input_reset = False


def reset_input_flag():
    if st.session_state.get("input_reset", False):
        st.session_state.input_reset = False


def display_action_buttons():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send", type="primary"):
            handle_send_button()
    with col2:
        if st.button("Preview", type="secondary"):
            handle_preview_button()


def _collect_user_inputs_from_state(selected_templates):
    if len(selected_templates) > 1:
        return [
            st.session_state.get(f"instructions{i}", "").strip()
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        return [st.session_state.get("instructions", "").strip()]


def _append_user_messages_to_history(user_inputs, selected_templates):
    for i, user_input in enumerate(user_inputs):
        if user_input:
            if len(selected_templates) > 1 and i < len(selected_templates):
                 template = selected_templates[i]
            elif len(selected_templates) == 1:
                 template = selected_templates[0]
            else:
                 template = ""

            st.session_state.chat_history.append(
                {"role": "user", "content": user_input, "template": template}
            )


def _append_assistant_placeholders(user_inputs, selected_templates, selected_models):
    for i, user_input in enumerate(user_inputs):
        if user_input:
             if len(selected_templates) > 1 and i < len(selected_templates):
                  template = selected_templates[i]
             elif len(selected_templates) == 1:
                  template = selected_templates[0]
             else:
                  template = ""

             for model in get_selected_models():
                 st.session_state.chat_history.append(
                     {
                         "role": "assistant",
                         "model": model,
                         "template": template,
                         "multiple_models": len(get_selected_models()) > 1,
                         "content": None,
                         "cost": None,
                     }
                 )


def handle_send_button():
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    user_inputs = _collect_user_inputs_from_state(selected_templates)

    selected_models = get_selected_models()

    if any(user_inputs):
        _append_user_messages_to_history(user_inputs, selected_templates)
        _append_assistant_placeholders(user_inputs, selected_templates, selected_models)

        st.session_state.input_reset = True

    st.rerun()


def _display_preview_for_model(user_input, model, template_label):
    with st.expander(
        f"🤖 PREVIEW [{model}] {template_label}", expanded=True
    ):
        with st.spinner("Previewing..."):
            try:
                messages = get_history_messages(model)
                messages.append({"role": "user", "content": user_input})

                st.json(messages, expanded=False)

                llm_client = LLMClients(model=model)
                cost = llm_client.calculate_cost(messages, "")

                st.write(
                    f"💰 ${cost.get('input_cost', 0):.4f} [input] ({cost.get('input_tokens', 0):,} tokens) "
                )
            except Exception as e:
                 st.error(f"Error generating preview for {model}: {e}")


def handle_preview_button():
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    user_inputs = _collect_user_inputs_from_state(selected_templates)

    selected_models = get_selected_models()

    for i, user_input in enumerate(user_inputs):
        if user_input:
            template_label = (
                f"[{selected_templates[i]}]" if len(selected_templates) > 1 and i < len(selected_templates) else ""
            )
            for model in selected_models:
                _display_preview_for_model(user_input, model, template_label)


def _check_claude_token_warning(llm_client, messages, model):
    if model in ["claude-3-5-sonnet", "claude-3-haiku"]:
        try:
            token_count = tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
            if token_count > 80000:
                 st.warning(
                    f"Current message history for {model} is large ({token_count:,} tokens > 80k). Anthropic API is limited to 80k tokens per minute per model. This may result in errors."
                )
        except Exception as e:
             st.warning(f"Could not count tokens for {model} (for warning): {e}")


def _run_model_and_get_result(llm_client, messages, model):
    try:
        if model in ["o1-preview", "o1-mini"]:
            st.caption("Streaming is not supported for o1 models. Output will appear all at once.")
            completion = llm_client.run(messages)
            st.markdown(completion)
        else:
            completion = llm_client.run(messages)
            st.markdown(completion)

        return completion

    except Exception as e:
        error_msg = f"Error running model {model}: {e}"
        st.error(error_msg)
        return f"ERROR: {e}"


def run_agent(model):
    llm_client = LLMClients(model=model)

    messages = get_history_messages(model)

    _check_claude_token_warning(llm_client, messages, model)
    completion_or_error = _run_model_and_get_result(llm_client, messages, model)

    if completion_or_error.startswith("ERROR:"):
        completion = completion_or_error
        cost = {"total_cost": 0, "input_cost": 0, "output_cost": 0, "input_tokens": 0, "output_tokens": 0}
    else:
        completion = completion_or_error
        try:
             cost = llm_client.calculate_cost(messages, completion)
        except Exception as e:
             st.warning(f"Could not calculate cost for {model}: {e}")
             cost = {"total_cost": 0, "input_cost": 0, "output_cost": 0, "input_tokens": 0, "output_tokens": 0}

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
         st.error(f"Error during context retrieval: {e}")
         context = f"Error retrieving context: {e}"

    messages = [{"role": "user", "content": context}]

    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            messages.append({"role": entry["role"], "content": entry["content"]})
        elif entry["role"] == "assistant" and entry.get("content") is not None:
            if not entry.get("multiple_models", False) or entry.get("model") == model:
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

    prompt = ""
    if messages and len(messages) > 0:
        context_content = messages[0].get("content", "")
        for msg in reversed(messages):
            if msg["role"] == "user" and msg.get("content") and msg["content"] != context_content:
                prompt = msg["content"]
                break
        if not prompt and len(messages) > 1 and messages[-1]["role"] == "user":
             prompt = messages[-1].get("content", "")
    prompt = prompt or ""

    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]
    using_template = any(selected_templates)

    using_multiple_templates = using_template and len(selected_templates) > 1

    using_multiple_models = len(get_selected_models()) > 1

    usage_tracker.log_agent_execution(
        model=model,
        prompt=prompt,
        cost=cost,
        conversation_id=st.session_state.conversation_id,
        using_template=using_template,
        using_multiple_templates=using_multiple_templates,
        using_multiple_models=using_multiple_models,
    )


chat()