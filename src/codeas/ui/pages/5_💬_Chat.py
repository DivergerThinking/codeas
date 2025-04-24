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

# Define constants for duplicated literals (S1192)
ALL_FILES_OPTION = "All files"
FULL_CONTENT_OPTION = "Full content"


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
        # Use constants (S1192)
        if (
            st.session_state.get("file_types") != ALL_FILES_OPTION
            or st.session_state.get("content_types") != FULL_CONTENT_OPTION
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

        # Merge nested if statements (S1066)
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
                ALL_FILES_OPTION,  # Use constant (S1192)
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
            options=[FULL_CONTENT_OPTION, "Descriptions", "Details"],  # Use constant (S1192)
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
                st.write(entry["content"])
        else:
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


def display_user_input():
    with st.expander(
        "NEW MESSAGE", icon="👤", expanded=not any(st.session_state.chat_history)
    ):
        display_model_options()
        initialize_input_reset()
        display_template_options()
        display_input_areas() # Refactored function
        reset_input_flag()
        display_action_buttons()


# Refactored display_input_areas for S3776 to reduce complexity
def _display_single_input_area(prompts, template, instruction_key="instructions"):
    """Helper to display a single text area for instructions."""
    prompt_content = prompts.get(template, "")
    # Use value from session state if it exists, otherwise use prompt content
    initial_value = st.session_state.get(instruction_key, prompt_content)
    st.text_area(
        "Instructions",
        value=initial_value,
        key=instruction_key,
        height=200,
    )

def _display_multiple_input_areas(prompts, selected_templates):
    """Helper to display multiple text areas within expanders."""
    for i, template in enumerate(selected_templates, 1):
        instruction_key = f"instructions{i}"
        prompt_content = prompts.get(template, "")
        # Use value from session state if it exists, otherwise use prompt content
        initial_value = st.session_state.get(instruction_key, prompt_content)
        with st.expander(f"Template {i}: {template}", expanded=True):
            st.text_area(
                "Instructions",
                value=initial_value,
                height=200,
                key=instruction_key,
            )

def display_input_areas():
    """Displays input areas based on selected templates."""
    prompts = read_prompts()
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    # Handle input reset for all potential keys upfront
    if st.session_state.input_reset:
        st.session_state["instructions"] = ""
        for i in range(1, 4):
             st.session_state[f"instructions{i}"] = ""

    # Branch based on the number of selected templates
    if not selected_templates:
        # Case: No templates selected, display default single input area
        _display_single_input_area(prompts, "") # Pass empty template name
    elif len(selected_templates) == 1:
        # Case: Single template selected, display single input area with template content
        _display_single_input_area(prompts, selected_templates[0])
    else: # Case: Multiple templates selected
        # Display multiple input areas within expanders
        _display_multiple_input_areas(prompts, selected_templates)


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
    # Removed commented out code block (S125)


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

    # Filter valid user inputs with their original index (S1066 fix)
    valid_user_inputs_indexed = [(i, user_input) for i, user_input in enumerate(user_inputs) if user_input]

    if valid_user_inputs_indexed:
        # Append user messages first
        for i, user_input in valid_user_inputs_indexed:
            # Determine template associated with this user input based on its original index
            template = selected_templates[i] if len(selected_templates) > i else ""
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input, "template": template}
            )
        # Then append assistant placeholders for each model/input combo
        for i, user_input in valid_user_inputs_indexed: # Iterate through valid inputs again
             # Determine template associated with this user input based on its original index
             template = selected_templates[i] if len(selected_templates) > i else ""
             for model in get_selected_models():
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "model": model,
                        "template": template, # Use the determined template
                        "multiple_models": len(get_selected_models()) > 1,
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
            st.session_state.get(f"instructions{i}").strip()
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        user_inputs = [st.session_state.instructions.strip()]

    # Filter valid user inputs with their original index (S1066 fix)
    valid_user_inputs_indexed = [(i, user_input) for i, user_input in enumerate(user_inputs) if user_input]

    for i, user_input in valid_user_inputs_indexed:
        # Determine template label based on its original index
        template_label = (
            f"[{selected_templates[i]}]" if len(selected_templates) > i else ""
        )
        for model in get_selected_models():
            with st.expander(
                f"🤖 PREVIEW [{model}] {template_label}\n", expanded=True
            ):
                with st.spinner("Previewing...\n"):
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
    # Use 'in' operator for slightly cleaner conditions
    if model in ["claude-3-5-sonnet", "claude-3-haiku"]:
        if (
            tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
            > 10000
        ):
            st.warning(
                "Anthropic API is limited to 80k tokens per minute. Using it with large context may result in errors.\n"
            )
    # Use 'in' operator for slightly cleaner conditions
    if model in ["o1-preview", "o1-mini"]:
        st.caption("Streaming is not supported for o1 models.\n")
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
    # Initialize messages with context user message
    messages = [{"role": "user", "content": context}]

    # Add chat history messages
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            messages.append({"role": entry["role"], "content": entry["content"]})
        # Add assistant messages only if content exists AND (it's a single model conversation OR the model matches)
        elif entry["role"] == "assistant" and entry.get("content") is not None:
            # Use default False for 'multiple_models' if not present
            if entry.get("multiple_models", False) is False or entry.get("model") == model:
                 messages.append({"role": entry["role"], "content": entry["content"]})
    return messages


def get_retriever_args():
    # Use constants (S1192)
    file_types = st.session_state.get("file_types", ALL_FILES_OPTION)
    content_types = st.session_state.get("content_types", FULL_CONTENT_OPTION)
    return {
        "include_all_files": file_types == ALL_FILES_OPTION, # Use constant (S1192)
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
    # Get the content of the last user message (assuming it's the one triggering this agent run)
    prompt = messages[-1]["content"] if messages else ""

    # Get template information from session state (preserving original logic)
    selected_templates_from_state = [
         st.session_state.get(f"template{i}")
         for i in range(1, 4)
         if st.session_state.get(f"template{i}")
     ]
    using_template = any(selected_templates_from_state)
    using_multiple_templates = len(selected_templates_from_state) > 1

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