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

        # Initialize variables that need to be set in branches
        files_missing_metadata = []
        num_selected_files = 0
        selected_tokens = 0
        files_metadata = None # Needed for metadata editor


        is_specific_selection = (
            st.session_state.get("file_types") != "All files"
            or st.session_state.get("content_types") != "Full content"
        )

        # Handle the case where specific selections are made (original line 75)
        if is_specific_selection:
            # Display metadata UI - this must run if specific selection is true (original line 79)
            # This call displays the metadata UI and returns files with missing metadata
            files_missing_metadata = metadata_ui.display()

            # The data retrieval and count calculation (original lines 81-90)
            # only needs to run if specific selection AND no missing metadata.
            # This block was originally inside the nested if at line 80.
            # Merging the conditions for *this block* leads to the following structure:
            if not any(files_missing_metadata): # This condition was the original line 80
                # This specific block of code was originally guarded by the nested if
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
            # else: if is_specific_selection AND any(files_missing_metadata), files_metadata remains None, counts remain 0.

        # Handle the case where "All files" and "Full content" are selected (original lines 95-97)
        else: # not is_specific_selection
            files_missing_metadata = [] # No missing metadata in this mode (original line 95)
            num_selected_files, _, selected_tokens = repo_ui.get_selected_files_info() # Original line 96
            # files_metadata remains None.


        # Now handle displaying the appropriate editor based on the state determined above
        # Display metadata editor if specific selection AND no missing metadata (original line 94 was inside the nested if block)
        # This condition is 'is_specific_selection' AND 'not any(files_missing_metadata)' AND 'files_metadata is not None'
        # files_metadata is only set if the merged condition block above runs, so just checking if files_metadata is set is sufficient here
        if files_metadata is not None: # Equivalent to: is_specific_selection and not any(files_missing_metadata)
             repo_ui.display_metadata_editor(files_metadata)
        # Display files editor if not specific selection (original line 97)
        elif not is_specific_selection:
             repo_ui.display_files_editor()
        # If is_specific_selection and there *is* missing metadata, neither editor is displayed here, matching original behavior.


        # Display caption and "Show context" button if no missing metadata.
        # This logic applies across both branches where this condition holds.
        # (Original lines 91, 96, 107 for caption, and 98-105 for button)
        # Consolidate the caption display just before the "Show context" button logic.
        if not any(files_missing_metadata):
            # Caption display (consolidated, was original lines 91, 96, 107)
            # num_selected_files and selected_tokens are guaranteed to be set if !any(files_missing_metadata)
            st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")

            # "Show context" button logic (original lines 98-105)
            # This button's original condition was 'if not any(files_missing_metadata):'
            if st.button("Show context"):
                context = retriever.retrieve(
                    files_paths=state.repo.included_files_paths,
                    files_tokens=state.repo.included_files_tokens,
                    metadata=state.repo_metadata,
                )
                st.text_area("Context", context, height=300)

    # Removed the redundant caption outside the expander (original lines 106-107).


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
            # Restored original index logic
            index=0 if st.session_state.input_reset else None,
            disabled=not st.session_state.model2,
        )


def get_selected_models():
    models = [st.session_state.model1, st.session_state.model2, st.session_state.model3]
    return [model for model in models if model]


def display_chat_history():
    for i, entry in enumerate(st.session_state.chat_history):
        template_label = f"[{entry['template']}]" if entry.get("template") else ""
        if entry["role"] == "user":
            with st.expander(f"USER {template_label}", icon="\ud83d\udc64", expanded=False):
                st.write(entry["content"])
        else:
            with st.expander(
                f"ASSISTANT [{entry['model']}] {template_label}",
                expanded=True,
                icon="\ud83e\udd16",
            ):
                # Restored original logic for handling content generation/display
                if entry.get("content") is None:
                    with st.spinner("Running agent..."):
                        # Assuming run_agent correctly populates content and cost
                        # This logic depends on handle_send_button NOT adding content/cost
                        # placeholders, which aligns with the original code structure.
                        content, cost = run_agent(entry["model"])
                        st.session_state.chat_history[i]["content"] = content
                        st.session_state.chat_history[i]["cost"] = cost
                        # Need to re-run to display the content immediately after generating
                        # This was missing in original, but essential for UX if not streaming from display_chat_history
                        # However, display_chat_history calls write_stream if not o1 model,
                        # so the content will appear without needing rerun. Cost is added after.
                        # Sticking to minimal changes, no added rerun here.
                    # The cost display needs to be outside the spinner or after content is set
                    # Original code displays cost *after* write_stream or run.
                    # Let's match that.
                    st.write(f"\ud83d\udcb0 ${st.session_state.chat_history[i]['cost']['total_cost']:.4f}")

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
    prompt_options = [""] + list(read_prompts().keys())

    col1, _ = st.columns(2)
    with col1:
        st.selectbox(
            "Template",
            options=prompt_options,
            key="template1",
            index=0 if st.session_state.input_reset else None,
        )

    # The following template selectboxes were commented out in the original code
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
        # Restored original logic for adding messages to history sequentially
        multiple_models_selected = len(get_selected_models()) > 1
        for i, user_input in enumerate(user_inputs):
            if user_input:
                template = selected_templates[i] if len(selected_templates) > 1 else ""
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input, "template": template}
                )
                # Add assistant entries as placeholders *after* the user message
                for model in get_selected_models():
                     st.session_state.chat_history.append(
                         {
                             "role": "assistant",
                             "model": model,
                             "template": template,
                             "multiple_models": multiple_models_selected,
                             # Content and cost are NOT added here, matching original behavior.
                             # They are added later by run_agent when called by display_chat_history.
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

    for i, user_input in enumerate(user_inputs):
        if user_input:
            template_label = (
                f"[{selected_templates[i]}]" if len(selected_templates) > 1 else ""
            )
            for model in get_selected_models():
                with st.expander(
                    f"\ud83e\udd16 PREVIEW [{model}] {template_label}", expanded=True
                ):
                    with st.spinner("Previewing..."):
                        # Get history messages *before* adding the current user input for preview
                        messages = get_history_messages(model)
                        # Add the current user input for this specific preview
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

    if model == "claude-3-5-sonnet" or model == "claude-3-haiku":
        if (
            tokencost.count_string_tokens(llm_client.extract_strings(messages), model)
            > 10000
        ):
            st.warning(
                "Anthropic API is limited to 80k tokens per minute. Using it with large context may result in errors."
            )
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
    messages = [{"role": "user", "content": context}]

    # Reconstruct history relevant to this model run from the session state history
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
             # Append user messages from history
            messages.append({"role": entry["role"], "content": entry["content"]})
        elif entry["role"] == "assistant" and entry.get("content") is not None:
            # Append assistant messages from history *only if* they match the current model
            # or are from single-model runs (multiple_models=False indicates single run)
             if entry.get("multiple_models") is False or entry.get("model") == model:
                 messages.append({"role": entry["role"], "content": entry["content"]})
    return messages


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


def log_agent_execution(model, messages, cost):
    # Get or create a conversation ID
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    # Get the content of the last message (assumed to be the user prompt for logging)
    # This relies on the structure of messages built by get_history_messages
    prompt = messages[-1]["content"] if messages else ""

    # Get template information and multi-model flag from the current session state,
    # as these reflect the user's input settings when the prompt was sent.
    # Note: This assumes the template and multiple model selections in session state
    # are still correct at the time the agent runs, which might not be true if the
    # user changes selections while agents are running. A more robust logging
    # might store these settings with the user message entry in chat_history.
    # However, sticking to minimal changes from original, use current state.
    selected_templates = [
        st.session_state.get(f"template{i}")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}")
    ]
    using_template = any(selected_templates)
    using_multiple_templates = len(selected_templates) > 1

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