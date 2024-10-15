import streamlit as st

from codeas.configs.templates import TEMPLATES

# from codeas.core.state import state
from codeas.ui.components import metadata_ui, repo_ui


def chat():
    st.subheader("💬 Chat")
    repo_ui.display_repo_path()
    display_config_section()
    display_user_section()
    display_assistant_section()


def display_config_section():
    with st.expander("💻 CONFIGS", expanded=True):
        repo_ui.display_files()
        display_file_options()
        display_model_options()


def display_file_options():
    col1, col2 = st.columns(2)
    with col1:
        file_types = st.selectbox(
            "File types", options=["All", "Python", "Markdown", "Other"]
        )
    with col2:
        file_content = st.selectbox(
            "File content", options=["Full", "Descriptions", "Details"]
        )

    if file_types != "All" or file_content != "Full":
        metadata_ui.display()


def display_model_options():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox(
            "Model",
            options=["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"],
            key="model",
        )
    compare = st.toggle("Compare", value=False, key="compare")
    if compare:
        with col2:
            st.selectbox(
                "Model 2",
                options=["", "gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"],
                key="model2",
            )
        with col3:
            st.selectbox(
                "Model 3",
                options=["", "gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"],
                key="model3",
            )


def get_selected_models():
    models = [st.session_state.get("model")]
    if st.session_state.get("compare", False):
        models.extend([st.session_state.get("model2"), st.session_state.get("model3")])
    return [model for model in models if model]


def display_user_section():
    with st.expander("👤 USER", expanded=True):
        col1, _ = st.columns(2)
        with col1:
            prompt_options = [""] + list(TEMPLATES.keys())
            selected_prompt = st.selectbox("Templates", options=prompt_options)
        display_instructions(selected_prompt)
        if st.button("Run", type="primary"):
            run_assistant()


def display_assistant_section():
    for model in get_selected_models():
        if f"output_{model}" in st.session_state:
            with st.expander(f"🤖 ASSISTANT [{model}]", expanded=True):
                st.write(st.session_state[f"output_{model}"])


def display_instructions(selected_prompt):
    prompt_content = TEMPLATES.get(selected_prompt, "") if selected_prompt else ""
    st.text_area("Instructions", value=prompt_content, height=200, key="instructions")
    # TODO: Add logic to handle the prompt (e.g., send to AI, save to state, etc.)


def run_assistant():
    for model in get_selected_models():
        st.write(f"Running assistant for {model}...")
        # TODO: Replace this with actual API call or processing logic
        st.session_state[
            f"output_{model}"
        ] = f"Generated output for {model}. This is a placeholder."


chat()
