import uuid
import logging
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
ANTHROPIC_MODELS_WARNING = ["claude-3-5-sonnet", "claude-3-haiku"]
O1_MODELS_NO_STREAM = ["o1-preview", "o1-mini"]
ANTHROPIC_WARNING_TOKEN_THRESHOLD = 10000
MAX_INPUT_LENGTH = 10000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    if any([entry.get("cost") for entry in st.session_state.get("chat_history", [])]):
        conversation_cost = 0
        for entry in st.session_state.chat_history:
            cost_info = entry.get("cost")
            if cost_info and "total_cost" in cost_info:
                conversation_cost += cost_info["total_cost"]
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
                num_selected_files = sum(files_metadata.get("Incl.", []))
                selected_tokens = sum(
                    token
                    for incl, token in zip(
                        files_metadata.get("Incl.", []), files_metadata.get("Tokens", [])
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

        if not any(files_missing_metadata):
            if st.button("Show context"):
                context = retriever.retrieve(
                    files_paths=state.repo.included_files_paths,
                    files_tokens=state.repo.included_files_tokens,
                    metadata=state.repo_metadata,
                )
                st.text_area("Context", context, height=300)


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
        )

    selected_model1 = st.session_state.get("model1")
    remaining_models = [
        model for model in all_models if model != selected_model1
    ]
    with col2:
        st.selectbox(
            "Model 2",
            options=[""] + remaining_models,
            key="model2",
            disabled=not selected_model1,
        )

    selected_model2 = st.session_state.get("model2")
    final_models = [
        model for model in remaining_models if model != selected_model2
    ]
    with col3:
        st.selectbox(
            "Model 3",
            options=[""] + final_models,
            key="model3",
            disabled=not selected_model2,
        )


def get_selected_models():
    models = [
        st.session_state.get("model1", ""),
        st.session_state.get("model2", ""),
        st.session_state.get("model3", "")
    ]
    return [model for model in models if model]


def display_chat_history():
    for i, entry in enumerate(st.session_state.get("chat_history", [])):
        template = entry.get("template")
        template_label = f"[{template}]" if template else ""
        role = entry.get("role")
        content = entry.get("content")
        model = entry.get("model", "Unknown Model")

        if role == "user":
            with st.expander(f"USER {template_label}", icon="👤", expanded=False):
                if content is not None:
                    st.write(content)
        elif role == "assistant":
            cost = entry.get("cost")

            label = f"ASSISTANT [{model}]"
            if template:
                label += f" [{template}]"

            with st.expander(
                label,
                expanded=True,
                icon="🤖",
            ):
                if content is None:
                    with st.spinner("Running agent..."):
                        try:
                            completion, calculated_cost = run_agent(model)
                            st.write(completion)
                            if calculated_cost and "total_cost" in calculated_cost:
                                st.write(f"💰 ${calculated_cost['total_cost']:.4f}")
                            st.session_state.chat_history[i]["content"] = completion
                            st.session_state.chat_history[i]["cost"] = calculated_cost
                        except Exception as e:
                            logger.error(f"Error running agent: {e}", exc_info=True)
                            st.error("An error occurred while running the agent. Please try again.")
                            st.session_state.chat_history[i]["content"] = "Error processing message."
                            st.session_state.chat_history[i]["cost"] = {"total_cost": 0}
                else:
                    st.write(content)
                    if cost and "total_cost" in cost:
                         st.write(f"💰 ${cost['total_cost']:.4f}")
                    else:
                         st.caption("Cost information not available.")


def display_user_input():
    is_history_empty = not st.session_state.get("chat_history")
    with st.expander(
        "NEW MESSAGE", icon="👤", expanded=is_history_empty
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
            index=0 if st.session_state.get("input_reset", False) else None,
        )


def display_input_areas():
    prompts = read_prompts()
    selected_templates = [
        st.session_state.get(f"template{i}", "")
        for i in range(1, 4)
    ]
    active_templates = [t for t in selected_templates if t]

    if not active_templates:
        active_templates = [""]

    if len(active_templates) <= 1:
        template = active_templates[0]
        input_key = "instructions"
        # used to empty user input and templates after user sends a message
        if st.session_state.get("input_reset", False):
            st.session_state[input_key] = ""
        prompt_content = prompts.get(template, "") if template else ""
        st.text_area(
            "Instructions",
            value=st.session_state.get(input_key, prompt_content),
            key=input_key,
            height=200,
        )
    else:
        for i, template in enumerate(active_templates, 1):
            instruction_key = f"instructions{i}"
            # used to empty user input and templates after user sends a message
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


def initialize_input_reset():
    # used to empty user input and templates after user sends a message
    if "input_reset" not in st.session_state:
        st.session_state.input_reset = False


def reset_input_flag():
    # used to empty user input and templates after user sends a message
    if st.session_state.get("input_reset", False):
        st.session_state.input_reset = False


def display_action_buttons():
    if st.button("Send", type="primary"):
        handle_send_button()

    if st.button("Preview", type="secondary"):
        handle_preview_button()


def handle_send_button():
    selected_templates = [
        st.session_state.get(f"template{i}", "")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}", "")
    ]

    if not selected_templates:
         selected_templates = [""]

    input_template_pairs = []
    input_too_long = False
    if len(selected_templates) > 1:
        for i, template in enumerate(selected_templates, 1):
             input_key = f"instructions{i}"
             user_input = st.session_state.get(input_key, "").strip()
             if user_input:
                 if len(user_input) > MAX_INPUT_LENGTH:
                      input_too_long = True
                      st.warning(f"Input for Template {i} exceeds the maximum length of {MAX_INPUT_LENGTH} characters.")
                      break
                 input_template_pairs.append((user_input, template))
    else:
        template = selected_templates[0]
        input_key = "instructions"
        user_input = st.session_state.get(input_key, "").strip()
        if user_input:
            if len(user_input) > MAX_INPUT_LENGTH:
                 input_too_long = True
                 st.warning(f"Input exceeds the maximum length of {MAX_INPUT_LENGTH} characters.")
            else:
                 input_template_pairs.append((user_input, template))

    if input_template_pairs and not input_too_long:
        for user_input, template in input_template_pairs:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input, "template": template}
            )
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
        st.session_state.input_reset = True
    st.rerun()


def handle_preview_button():
    selected_templates = [
        st.session_state.get(f"template{i}", "")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}", "")
    ]

    if not selected_templates:
         selected_templates = [""]

    input_template_pairs = []
    input_too_long = False
    if len(selected_templates) > 1:
         for i, template in enumerate(selected_templates, 1):
             input_key = f"instructions{i}"
             user_input = st.session_state.get(input_key, "").strip()
             if user_input:
                 if len(user_input) > MAX_INPUT_LENGTH:
                      input_too_long = True
                      st.warning(f"Input for Template {i} exceeds the maximum length of {MAX_INPUT_LENGTH} characters. Cannot preview.")
                      break
                 input_template_pairs.append((user_input, template))
    else:
        template = selected_templates[0]
        input_key = "instructions"
        user_input = st.session_state.get(input_key, "").strip()
        if user_input:
            if len(user_input) > MAX_INPUT_LENGTH:
                 input_too_long = True
                 st.warning(f"Input exceeds the maximum length of {MAX_INPUT_LENGTH} characters. Cannot preview.")
            else:
                 input_template_pairs.append((user_input, template))

    for user_input, template in input_template_pairs:
        template_label = f"[{template}]" if template else ""
        for model in get_selected_models():
            with st.expander(
                f"🤖 PREVIEW [{model}] {template_label}", expanded=True
            ):
                with st.spinner("Previewing..."):
                    messages = get_history_messages(model)
                    messages.append({"role": "user", "content": user_input})
                    st.json(messages, expanded=False)
                    llm_client = LLMClients(model=model)
                    cost = llm_client.calculate_cost(messages)
                    input_cost = cost.get("input_cost", 0) if cost else 0
                    input_tokens = cost.get("input_tokens", 0) if cost else 0
                    st.write(
                        f"💰 ${input_cost:.4f} [input] ({input_tokens:,} tokens) "
                    )


def _issue_anthropic_warning(model, messages, llm_client):
    if model in ANTHROPIC_MODELS_WARNING:
        if tokencost.count_string_tokens(llm_client.extract_strings(messages), model) > ANTHROPIC_WARNING_TOKEN_THRESHOLD:
            st.warning(
                "Anthropic API is limited to 80k tokens per minute. Using it with large context may result in errors."
            )


def _handle_o1_models(llm_client, messages):
    st.caption("Streaming is not supported for o1 models.")
    completion = llm_client.run(messages)
    st.text(completion)
    return completion


def _handle_streaming_models(llm_client, messages):
    completion = st.write_stream(llm_client.stream(messages))
    return completion


def run_agent(model):
    llm_client = LLMClients(model=model)
    messages = get_history_messages(model)

    _issue_anthropic_warning(model, messages, llm_client)

    if model in O1_MODELS_NO_STREAM:
        completion = _handle_o1_models(llm_client, messages)
    else:
        completion = _handle_streaming_models(llm_client, messages)

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

    for entry in st.session_state.get("chat_history", []):
        role = entry.get("role")
        content = entry.get("content")
        entry_model = entry.get("model")
        multiple_models = entry.get("multiple_models", False)

        if role == "user" and content is not None:
            messages.append({"role": role, "content": content})
        elif role == "assistant" and content is not None:
             if not multiple_models or entry_model == model:
                 messages.append({"role": role, "content": content})

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

    # Log the prompt sent to the agent.
    # The last message in the 'messages' list sent to run_agent is the user's input + context.
    prompt_content_sent_to_agent = messages[-1]["content"] if messages else ""

    # Log template information based on the state of the input fields when 'Send' was clicked.
    selected_templates = [
        st.session_state.get(f"template{i}", "")
        for i in range(1, 4)
        if st.session_state.get(f"template{i}", "")
    ]
    using_template = any(selected_templates)
    using_multiple_templates = len(selected_templates) > 1

    # Check if multiple models are being used for this turn
    using_multiple_models = len(get_selected_models()) > 1

    # Log the agent execution using the UsageTracker
    usage_tracker.log_agent_execution(
        model=model,
        prompt=prompt_content_sent_to_agent,
        cost_details=cost,
        total_cost=cost.get("total_cost", 0) if cost else 0,
        conversation_id=st.session_state.conversation_id,
        using_template=using_template,
        using_multiple_templates=using_multiple_templates,
        using_multiple_models=using_multiple_models,
    )


chat()