import streamlit as st

from codeag.configs.agents_configs import AGENTS_CONFIGS

st.title("Configs")

context_options = ["file_content", "file_info", "folder_info", "agent_output"]

# Initialize session state for new contexts
if "new_contexts" not in st.session_state:
    st.session_state.new_contexts = {agent_name: [] for agent_name in AGENTS_CONFIGS}

for agent_name, agent_config in AGENTS_CONFIGS.items():
    with st.expander(agent_name):
        agent_config["system_prompt"] = st.text_area(
            "System Prompt",
            agent_config["system_prompt"],
            key=f"{agent_name}_system_prompt",
            height=200,  # Increased height
        )
        agent_config["instructions"] = st.text_area(
            "Instructions",
            agent_config["instructions"],
            key=f"{agent_name}_instructions",
            height=200,  # Increased height
        )
        agent_config["model"] = st.text_input(
            "Model", agent_config["model"], key=f"{agent_name}_model"
        )

        for n, (context_key, context_value) in enumerate(
            agent_config["context"].items()
        ):
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                agent_config["context"][context_key] = st.selectbox(
                    f"Context {n+1}",
                    options=context_options,
                    index=context_options.index(context_value)
                    if context_value in context_options
                    else 0,
                    key=f"{agent_name}_{context_key}",
                )
            with col2:
                if agent_config["context"][context_key] == "file_content":
                    agent_config["auto_select_files"] = st.selectbox(
                        "Auto-select",
                        options=[True, False],
                        key=f"{agent_name}_{context_key}_auto_select_files",
                    )
                elif agent_config["context"][context_key] == "agent_output":
                    st.selectbox(
                        "Agent name",
                        options=AGENTS_CONFIGS.keys(),
                        key=f"{agent_name}_{context_key}_agent_name",
                    )
            with col3:
                agent_config["batch"] = st.selectbox(
                    "Batch",
                    options=[True, False],
                    key=f"{agent_name}_{context_key}_batch",
                )

        # Add new contexts from session state
        for i, new_context in enumerate(st.session_state.new_contexts[agent_name]):
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.selectbox(
                    f"New Context {i+1}",
                    options=context_options,
                    key=f"{agent_name}_new_context_{i}",
                )
            with col2:
                st.selectbox(
                    "Auto-select",
                    options=[True, False],
                    key=f"{agent_name}_new_context_{i}_auto_select_files",
                )
            with col3:
                st.selectbox(
                    "Batch",
                    options=[True, False],
                    key=f"{agent_name}_new_context_{i}_batch",
                )

        # Button to add new context
        if st.button("Add context", key=f"{agent_name}_add_context"):
            st.session_state.new_contexts[agent_name].append("")
