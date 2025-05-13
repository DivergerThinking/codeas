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

# Define constants for duplicated literals
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
    if any([entry.get("cost") for entry in st.session_state.chat_history]):
        conversation_cost = 0
        for entry in st.session_state.chat_history:
            if entry.get("cost"):
                conversation_cost += entry["cost"]["total_cost"]
        st.info(f"Conversation cost: ${conversation_cost:.4f}")


def display_config_section():
    files_missing_metadata = []
    num_selected_files = 0
    selected_tokens = 0
    retriever = ContextRetriever(**get_retriever_args())

    with st.expander("CONTEXT", icon="⚙️", expanded=False):
        repo_ui.display_filters()
        display_file_options()

        # Main logic branch based on file/content types
        if (
            st.session_state.get("file_types") != ALL_FILES
            or st.session_state.get("content_types") != FULL_CONTENT
        ):
            # Branch for non-All Files or non-Full Content (requires metadata display)
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
                repo_ui.display_metadata_editor(files_metadata)
        else:
            # Branch for All Files and Full Content (uses file editor, no metadata issues)
            files_missing_metadata = [] # Ensure this is empty in this branch
            num_selected_files, _, selected_tokens = repo_ui.get_selected_files_info()
            repo_ui.display_files_editor()

        # Consolidate logic that depends on whether files are missing metadata
        # This addresses the S1066 issue on original line 80
        if not any(files_missing_metadata):
            st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")
            if st.button("Show context"):
                context = retriever.retrieve(
                    files_paths=state.repo.included_files_paths,
                    files_tokens=state.repo.included_files_tokens,
                    metadata=state.repo_metadata,
                )
                st.text_area("Context", context, height=300)

    # Removed redundant caption display outside expander as per original code


def display_file_options():
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "File types",
            options=[
                ALL_FILES, # Use constant
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
            options=[FULL_CONTENT, "Descriptions", "Details"], # Use constant
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


def display_assistant_entry(entry, i):
    """Helper to display a single assistant chat entry."""
    template_label = f"[{entry['template']}]" if entry.get("template") else ""
    with st.expander(
        f"ASSISTANT [{entry['model']}] {template_label}",
        expanded=True,
        icon="🤖",
    ):
        if entry.get("content") is None:
            with st.spinner("Running agent..."):
                content, cost = run_agent(entry["model"])
                st.write(f"💰 ${cost['total_cost']:.4f}")
                st.session_state.chat_history[i]["content"] = content
                st.session_state.chat_history[i]["cost"] = cost
        else:
            st.write(entry["content"])
            st.write(f"💰 ${entry['cost']['total_cost']:.4f}")


def display_user_entry(entry):
    """Helper to display a single user chat entry."""
    template_label = f"[{entry['template']}]" if entry.get("template") else ""
    with st.expander(f"USER {template_label}", icon="👤", expanded=False):
        st.write(entry["content"])


def display_chat_history():
    # Refactored to reduce cognitive complexity (S3776)
    for i, entry in enumerate(st.session_state.chat_history):
        if entry["role"] == "user":
            display_user_entry(entry)
        else:  # role == "assistant"
            display_assistant_entry(entry, i)


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

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "Template",
            options=prompt_options,
            key="template1",
            index=0 if st.session_state.input_reset else None,
        )

    # Commented out template options removed as per S125


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
        user_inputs = [
            st.session_state.get(f"instructions{i}").strip()
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        user_inputs = [st.session_state.instructions.strip()]

    if any(user_inputs):
        for user_input in user_inputs:
            if user_input:
                 st.session_state.chat_history.append(
                    {"role": "user", "content": user_input}
                 )
        for model in get_selected_models():
             st.session_state.chat_history.append(
                 {
                     "role": "assistant",
                     "model": model,
                     "content": None,
                     "cost": None,
                 }
             )
        st.session_state.input_reset = True
    st.rerun()


def handle_preview_button():
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    if len(selected_templates) > 1:
        user_inputs = [
            st.session_state.get(f"""instructions{i}""").strip()
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        user_inputs = [st.session_state.instructions.strip()]

    for i, user_input in enumerate(user_inputs):
        if user_input:
            template_label = (
                f"[{selected_templates[i]}]" if len(selected_templates) > 1 else ""
            )
            for model in get_selected_models():
                with st.expander(
                    f"🤖 PREVIEW [{model}] {template_label}", expanded=True
                ):
                    with st.spinner("Previewing...👀"):
                        messages = get_history_messages(model)
                        messages.append({"role": "user", "content": user_input})
                        st.json(messages, expanded=False)
                        llm_client = LLMClients(model=model)
                        cost = llm_client.calculate_cost(messages)
                        st.write(
                            f"💰 ${cost['input_cost']:.4f} [input] ({cost['input_tokens']:,} tokens) "
                        )


def run_agent(model):
    llm_client = LLMClients(model=model)
    messages = get_history_messages(model)
    if model in ["claude-3-5-sonnet", "claude-3-haiku"]:
        if (
            tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
            > 10000
        ):
            st.warning(
                "Anthropic API is limited to 80k tokens per minute. Using it with large context may result in errors."
            )
    if model in ["o1-preview", "o1-mini"]:
        st.caption("Streaming is not supported for o1 models.")
        completion = llm_client.run(messages)
        st.markdown(completion)
    else:
        completion = st.write_stream(llm_client.stream(messages))
    cost = llm_client.calculate_cost(messages, completion)
    log_agent_execution(model, messages, cost)
    return completion, cost


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
        elif entry["role"] == "assistant" and entry.get("content") is not None:
            # Restore original logic for including assistant messages
            # This handles the case where 'multiple_models' might be missing
            if entry.get("multiple_models") is False or entry.get("model") == model:
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
    # Get or create a conversation ID
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    # Get the content of the last message - Keep original logic (last entry)
    prompt = messages[-1]["content"] if messages else ""

    # Get template information
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]
    using_template = any(selected_templates)
    using_multiple_templates = len(selected_templates) > 1
    # Check if multiple models are being used
    using_multiple_models = len(get_selected_models()) > 1
    # Log the agent execution using the UsageTracker
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