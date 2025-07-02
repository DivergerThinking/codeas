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
LARGE_CONTEXT_TOKEN_THRESHOLD = 180000


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
    if any([entry.get("cost") for entry in st.session_state.chat_history]):
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
            context = retriever.retrieve(
                files_paths=state.repo.included_files_paths,
                files_tokens=state.repo.included_files_tokens,
                metadata=state.repo_metadata,
            )
            st.text_area("Context", context, height=300)

    if not any(files_missing_metadata):
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
    all_models = MODELS.keys()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox(
            "Model",
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
        template_label = f"[{entry['template']}]" if entry.get("template") else ""
        if entry["role"] == "user":
            with st.expander(f"USER {template_label}", icon="👤", expanded=False):
                st.text(entry["content"])
        else:
            model_label = f"[{entry['model']}] " if entry.get("model") else ""
            expander_title = f"ASSISTANT {model_label}{template_label}"
            expanded_state = True

            if entry.get("error") is not None:
                expander_title = f"🤖 ERROR [{entry.get('model', 'N/A')}] {template_label}"
                expanded_state = True
                with st.expander(expander_title, expanded=expanded_state, icon="🤖"):
                    st.error(f"Agent execution failed: {entry['error']}")
                    if entry.get("cost"):
                        st.write(f"💰 ${entry['cost']['total_cost']:.4f}")
            elif entry.get("content") is None:
                with st.expander(f"🤖 Running ASSISTANT {model_label}{template_label}", expanded=expanded_state, icon="🤖"):
                    with st.spinner("Running agent..."):
                        completion, cost, error = run_agent(entry["model"])
                        st.session_state.chat_history[i]["content"] = completion
                        st.session_state.chat_history[i]["cost"] = cost
                        st.session_state.chat_history[i]["error"] = error
                    st.rerun()
            else:
                with st.expander(expander_title, expanded=expanded_state, icon="🤖"):
                    st.markdown(entry["content"])
                    if entry.get("cost"):
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
    elif selected_templates:
        if st.session_state.input_reset:
            st.session_state.instructions = ""
        template = selected_templates[0]
        prompt_content = prompts.get(template, "")
        st.text_area(
            "Instructions", value=prompt_content, key="instructions", height=200
        )
    else:
        if st.session_state.input_reset:
            st.session_state.instructions = ""
        st.text_area("Instructions", key="instructions", height=200)


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


def _get_input_template_pairs():
    """Collects user inputs and their associated templates from session state."""
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    input_template_pairs = []

    if len(selected_templates) > 1:
        for i, template in enumerate(selected_templates):
            input_text = st.session_state.get(f"instructions{i+1}", "").strip()
            if input_text:
                input_template_pairs.append((input_text, template))
    else:
        input_text = st.session_state.get("instructions", "").strip()
        template = selected_templates[0] if selected_templates else ""
        if input_text:
            input_template_pairs.append((input_text, template))

    return input_template_pairs


def handle_send_button():
    """Handles the logic when the 'Send' button is clicked."""
    input_template_pairs = _get_input_template_pairs()

    if input_template_pairs:
        selected_models = get_selected_models()
        is_multiple_models = len(selected_models) > 1

        for user_input, template in input_template_pairs:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input, "template": template}
            )

            if selected_models:
                for model in selected_models:
                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "model": model,
                            "template": template,
                            "multiple_models": is_multiple_models,
                        }
                    )

        st.session_state.input_reset = True
        st.rerun()


def handle_preview_button():
    """Handles the logic when the 'Preview' button is clicked."""
    input_template_pairs = _get_input_template_pairs()
    selected_models = get_selected_models()

    for user_input, template in input_template_pairs:
        if not user_input:
            continue

        template_label = f"[{template}]" if template else ""
        for model in selected_models:
            with st.expander(
                f"🤖 PREVIEW [{model}] {template_label}", expanded=True
            ):
                with st.spinner("Previewing..."):
                    messages_for_preview = []
                    preview_error = None
                    cost = None

                    try:
                        llm_client = LLMClients(model=model)
                        messages_for_preview = get_history_messages(model)
                        messages_for_preview.append({"role": "user", "content": user_input})

                        total_tokens = tokencost.count_string_tokens(llm_client.extract_strings(messages_for_preview), model)
                        if total_tokens > LARGE_CONTEXT_TOKEN_THRESHOLD:
                             preview_error = f"Prompt ({total_tokens:,} tokens) exceeds the maximum recommended limit ({LARGE_CONTEXT_TOKEN_THRESHOLD:,} tokens) for model '{model}'. Skipping preview cost calculation."
                        else:
                             cost = llm_client.calculate_cost(messages_for_preview)

                    except Exception as e:
                         preview_error = str(e)
                         cost = None

                    st.json(messages_for_preview, expanded=False)

                    if preview_error:
                         st.error(f"Could not generate preview cost: {preview_error}")
                    elif cost:
                         st.write(
                             f"💰 ${cost['input_cost']:.4f} [input] ({cost['input_tokens']:,} tokens) "
                         )
                    else:
                        st.info("Cost calculation skipped (e.g., empty input, token limit exceeded)")


def run_agent(model):
    llm_client = LLMClients(model=model)
    messages = get_history_messages(model)

    total_tokens = tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
    if total_tokens > LARGE_CONTEXT_TOKEN_THRESHOLD:
         error_message = f"Prompt ({total_tokens:,} tokens) exceeds the maximum recommended limit ({LARGE_CONTEXT_TOKEN_THRESHOLD:,} tokens) for model '{model}'. Aborting agent execution."
         st.error(error_message)
         log_agent_execution(model, messages, None, error=error_message)
         return None, None, error_message

    if model in ["claude-3-5-sonnet", "claude-3-haiku"] and total_tokens > 10000:
        st.warning(
            "Anthropic API is limited to 80k tokens per minute. Using it with large context may result in errors."
        )

    completion = None
    cost = None
    error_message = None

    try:
        if model in ["o1-preview", "o1-mini"]:
            st.caption("Streaming is not supported for o1 models.")
            completion = llm_client.run(messages)
        else:
            completion = st.write_stream(llm_client.stream(messages))

        cost = llm_client.calculate_cost(messages, completion)
        log_agent_execution(model, messages, cost, error=None)

    except Exception as e:
        error_message = str(e)
        log_agent_execution(model, messages, None, error=error_message)
        st.error(f"An error occurred during agent execution: {error_message}")

    return completion, cost, error_message


def log_agent_execution(model, messages, cost, error=None):
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())

    prompt = messages[-1]["content"] if messages and messages[-1]["role"] == "user" else ""

    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]
    using_template = any(selected_templates)
    using_multiple_templates = len(selected_templates) > 1
    using_multiple_models = len(get_selected_models()) > 1

    usage_tracker.log_agent_execution(
        model=model,
        prompt=prompt,
        cost=cost,
        conversation_id=st.session_state.conversation_id,
        using_template=using_template,
        using_multiple_templates=using_multiple_templates,
        using_multiple_models=using_multiple_models,
        error=error
    )


def get_history_messages(model):
    retriever = ContextRetriever(**get_retriever_args())
    context = retriever.retrieve(
        files_paths=state.repo.included_files_paths,
        files_tokens=state.repo.included_files_tokens,
        metadata=state.repo_metadata,
    )
    messages = []
    if context:
        messages.append({"role": "user", "content": context})

    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            messages.append({"role": entry["role"], "content": entry["content"]})
        elif entry["role"] == "assistant" and entry.get("content") is not None:
            include_message = True
            if entry.get("multiple_models") is True:
                if entry.get("model") != model:
                    include_message = False

            if include_message:
                messages.append({"role": entry["role"], "content": entry["content"]})
    return messages


chat()