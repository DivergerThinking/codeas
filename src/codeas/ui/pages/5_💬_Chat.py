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

# Define constants for duplicated strings (S1192)
ALL_FILES = "All files"
FULL_CONTENT = "Full content"


def chat():
    st.subheader("\ud83d\udcac Chat")
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
    with st.expander("CONTEXT", icon="\u2699\ufe0f", expanded=False):
        repo_ui.display_filters()
        display_file_options()

        retriever = ContextRetriever(**get_retriever_args())
        if (
            st.session_state.get("file_types") != ALL_FILES # Use constant (S1192)
            or st.session_state.get("content_types") != FULL_CONTENT # Use constant (S1192)
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

    # Original code had this caption outside the expander AND dependent on files_missing_metadata.
    # This was not flagged, preserve original structure.
    if not any(files_missing_metadata):
        st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")


def display_file_options():
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "File types",
            options=[
                ALL_FILES, # Use constant (S1192)
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
            options=[FULL_CONTENT, "Descriptions", "Details"], # Use constant (S1192)
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
        # Use .get('', '') for robustness, small non-functional change
        template_label = f"[{entry.get('template', '')}]" if entry.get("template") else ""
        if entry["role"] == "user":
            with st.expander(f"USER {template_label}", icon="\ud83d\udc64", expanded=False):
                st.write(entry["content"])
        else:
            with st.expander(
                f"ASSISTANT [{entry['model']}] {template_label}",
                expanded=True,
                icon="\ud83e\udd16",
            ):
                if entry.get("content") is None:
                    with st.spinner("Running agent..."):
                        content, cost = run_agent(entry["model"])
                        st.write(f"\ud83d\udcb0 ${cost['total_cost']:.4f}")
                        st.session_state.chat_history[i]["content"] = content
                        st.session_state.chat_history[i]["cost"] = cost
                else:
                    st.write(entry["content"])
                    st.write(f"\ud83d\udcb0 ${entry['cost']['total_cost']:.4f}")


def display_user_input():
    with st.expander(
        "NEW MESSAGE", icon="\ud83d\udc64", expanded=not any(st.session_state.chat_history)
    ):
        display_model_options()
        initialize_input_reset()
        display_template_options()
        display_input_areas()
        reset_input_flag()
        display_action_buttons()


def display_template_options():
    prompt_options = [\"\"] + list(read_prompts().keys())

    col1, _ = st.columns(2)
    with col1:
        st.selectbox(
            "Template",
            options=prompt_options,
            key="template1",
            index=0 if st.session_state.input_reset else None,
        )

    # Remove this commented out code. (S125)
    # remaining_options = [
    #     opt for opt in prompt_options if opt != st.session_state.template1
    # ]
    # with col2:
    #     st.selectbox(
    #         "Template 2",
    #         options=remaining_options,
    #         key="template2",
    #         index=0 if st.session_state.input_reset else None,
    #         disabled=not st.session_state.template1,
    #     )

    # Remove this commented out code. (S125)
    # final_options = [
    #     opt for opt in remaining_options if opt != st.session_state.template2
    # ]
    # with col3:
    #     st.selectbox(
    #         "Template 3",
    #         options=final_options,
    #         key="template3",
    #         index=0 if st.session_state.input_reset else None,
    #         disabled=not st.session_state.template2,
    #     )


# Helper function to encapsulate reset logic (S3776 refactoring)
def _reset_input_instruction_areas():
    # Original logic from display_input_areas, now extracted
    if st.session_state.input_reset:
        # Determine which instruction keys *would* be displayed based on current template selections
        # Replicate the condition from original display_input_areas
        selected_templates = [
            st.session_state.get(f"template{i}")
            for i in range(1, 4)
            if st.session_state.get(f"template{i}")
        ]

        if len(selected_templates) > 1:
            # Reset instructions1, instructions2, etc. for the number of selected templates > 1
            for i in range(1, len(selected_templates) + 1): # Loop 1 to N
                 instruction_key = f"instructions{i}"
                 # Original code did not check if key exists. Replicate exactly.
                 st.session_state[instruction_key] = ""
        else: # len is 0 or 1
             # Reset 'instructions' key
             # Original code did not check if key exists. Replicate exactly.
             st.session_state.instructions = ""


def display_input_areas():
    prompts = read_prompts()
    # Keep original logic for selected_templates
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]

    # Call the extracted reset logic (S3776 refactoring)
    _reset_input_instruction_areas()

    if len(selected_templates) > 1:
        for i, template in enumerate(selected_templates, 1):
            instruction_key = f"instructions{i}"
            prompt_content = prompts.get(template, "")
            with st.expander(f"Template {i}: {template}", expanded=True):
                st.text_area(
                    "Instructions",
                    value=prompt_content,
                    height=200,
                    key=instruction_key,
                )
    else:
        # Handles len(selected_templates) is 0 or 1
        template = selected_templates[0] if selected_templates else ""
        instruction_key = "instructions"
        prompt_content = prompts.get(template, "")
        st.text_area(
            "Instructions", value=prompt_content, key=instruction_key, height=200
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

    # Revert user_inputs collection to original logic (accessing keys directly or with get)
    # Then filter out empty strings.
    user_inputs = []
    if len(selected_templates) > 1:
        user_inputs = [
            st.session_state.get(f"instructions{i}", "").strip() # Use get with default for safety
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        # Original code accessed st.session_state.instructions directly.
        # Use get with default for safety, preserving empty string case.
        user_inputs = [st.session_state.get("instructions", "").strip()]

    # Filter out empty strings after collection
    user_inputs = [u for u in user_inputs if u]


    if any(user_inputs):
        # Add user messages (Revert template assignment logic to original potentially buggy version)
        for i, user_input in enumerate(user_inputs):
            if user_input: # Check needed as filtering was done outside the loop
                # Original potentially buggy logic: if > 1 templates, use selected_templates[i], else "".
                # If len(selected_templates) is 1, it uses "". Correct logic would be selected_templates[0].
                # But we replicate original bug for minimal change.
                template = selected_templates[i] if len(selected_templates) > 1 and i < len(selected_templates) else "" # Added check i < len(selected_templates) for safety, original might fail if user_inputs is longer than selected_templates (shouldn't happen based on logic)
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input, "template": template}
                )

        # Add assistant placeholders (Revert to original loop structure and template assignment)
        # Note: This re-iterates user_inputs and uses the 'template' variable from the *first* loop's last iteration if multiple inputs existed.
        # This is likely a bug but preserving original behavior.
        for i, user_input in enumerate(user_inputs): # Original code had this loop here
            for model in get_selected_models():
                 # Original code used the 'template' variable from the outer user message loop.
                 # If len(user_inputs) > 1, this 'template' will be from the last user input processed above.
                 # Original code did not store template in assistant entry placeholder. Revert removing template key.
                 st.session_state.chat_history.append(
                     {
                         "role": "assistant",
                         "model": model,
                         # "template": template, # Revert removing this key
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

    # Revert user_inputs collection to original logic
    user_inputs = []
    if len(selected_templates) > 1:
        user_inputs = [
            st.session_state.get(f"instructions{i}", "").strip() # Use get with default for safety
            for i in range(1, len(selected_templates) + 1)
        ]
    else:
        # Original code accessed st.session_state.instructions directly.
        # Use get with default for safety, preserving empty string case.
        user_inputs = [st.session_state.get("instructions", "").strip()]

    # Filter out empty strings after collection
    user_inputs = [u for u in user_inputs if u]

    for i, user_input in enumerate(user_inputs):
        if user_input: # Check needed as filtering was done outside the loop
            # Revert template label formatting to original potentially buggy version
            template_label = (
                f"[{selected_templates[i]}]" if len(selected_templates) > 1 and i < len(selected_templates) else "" # Added check i < len(selected_templates) for safety
            )
            for model in get_selected_models():
                with st.expander(
                    f"\ud83e\udd16 PREVIEW [{model}] {template_label}", expanded=True
                ):
                    with st.spinner("Previewing..."):
                        messages = get_history_messages(model)
                        # Revert appending message without template label
                        messages.append({"role": "user", "content": user_input})
                        st.json(messages, expanded=False)
                        llm_client = LLMClients(model=model)
                        cost = llm_client.calculate_cost(messages)
                        st.write(
                            f"\ud83d\udcb0 ${cost['input_cost']:.4f} [input] ({cost['input_tokens']:,} tokens) "
                        )


def run_agent(model):
    llm_client = LLMClients(model=model)
    messages = get_history_messages(model)
    # Original warning logic
    if model == "claude-3-5-sonnet" or model == "claude-3-haiku":
        if (
            tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
            > 10000
        ):
            st.warning(
                "Anthropic API is limited to 80k tokens per minute. Using it with large context may result in errors."
            )
    # Original o1 streaming logic
    if model == "o1-preview" or model == "o1-mini":
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
    # Revert adding template label to context message
    messages = [
        {"role": "user", "content": context}
    ]
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            # Revert adding template label to user messages from history
            messages.append({"role": entry["role"], "content": entry["content"]})
        # Merge nested if statements (S1066)
        elif entry["role"] == "assistant" and entry.get("content") is not None and \
             (entry.get("multiple_models") is False or entry.get("model") == model):
                 # Check .get("multiple_models") without default value as in original code
                 messages.append({"role": entry["role"], "content": entry["content"]})

    return messages


def get_retriever_args():
    file_types = st.session_state.get("file_types", ALL_FILES) # Use constant (S1192)
    content_types = st.session_state.get("content_types", FULL_CONTENT) # Use constant (S1192)
    return {
        "include_all_files": file_types == ALL_FILES, # Use constant (S1192)
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

    # Revert getting prompt content to original logic (last message content)
    prompt = messages[-1]["content"] if messages else ""

    # Keep original logic for getting template info from session state keys
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]
    using_template = any(selected_templates)
    using_multiple_templates = len(selected_templates) > 1 # Original logic

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