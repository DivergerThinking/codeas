import streamlit as st

from codeag.configs.agents_configs import AGENTS_CONFIGS
from codeag.core.context import Context

# Initialize session state
if "steps" not in st.session_state:
    st.session_state.steps = []

if "files_paths" not in st.session_state:
    st.session_state.files_paths = []

if "generated_context" not in st.session_state:
    st.session_state.generated_context = {}


def display_context(context_config, preview: bool):
    if "context" in context_config and context_config["context"] != "files_content":
        display_generated_context(context_config, preview)
        display_retrieved_context(context_config)
    else:
        display_retrieved_context(context_config)


def display_generated_context(context_config, preview: bool):
    generator_name = context_config["context"]

    files_paths = get_files_to_generate(generator_name)
    if any(files_paths):
        generator_config = AGENTS_CONFIGS[generator_name]

        files_content = get_files_content(files_paths)
        context = Context(batch=True).retrieve(files_content)

        if preview:
            preview = preview_agent(generator_config, context)
            display_preview(preview)
            if st.button("Run", key=f"run_{generator_name}"):
                output = run_agent(generator_config, context)
                save_generated_context(generator_name, output)
                display_output(output)
        else:
            output = run_agent(generator_config, context)
            save_generated_context(generator_name, output)
            display_output(output)


def display_preview(preview):
    st.json(preview)


def display_output(output):
    st.json(output)


def display_retrieved_context(context_config):
    if "context" in context_config and context_config["context"] == "files_content":
        files_paths = get_files_content(st.session_state.files_paths)
        if any(files_paths):
            files_content = get_files_content(files_paths)
            context = Context(batch=True).retrieve(files_content)
            st.json(context)
        else:
            st.json(context_config)
    else:
        display_context_config(context_config)


def get_files_to_generate():
    ...


def save_generated_context(agent_name, output):
    st.session_state.generated_context[agent_name] = output


def get_preview(agent_config):
    return agent_config


def get_output(agent_config):
    return agent_config


def preview_agent(agent_config, context):
    ...


def run_agent(agent_config, context):
    ...


def get_files_content(files_paths):
    ...


def home_page():
    st.title("Codeas (Dummy Version)")
    display_task_selector()
    display_workflow()
    display_run_tasks()


def display_task_selector():
    st.subheader("Tasks")
    available_steps = list(AGENTS_CONFIGS.keys())

    col, _ = st.columns(2)
    with col:
        selected_agent = st.selectbox(
            "Select instructions to add:", [""] + available_steps
        )
        if st.button("Add") and selected_agent:
            add_step_to_workflow(selected_agent)


def add_step_to_workflow(selected_agent):
    if selected_agent not in [step["name"] for step in st.session_state.steps]:
        st.session_state.steps.append({"type": "agent", "name": selected_agent})
    st.rerun()


def display_workflow():
    for i, step in enumerate(st.session_state.steps):
        col_step, col_remove = st.columns([11, 1])
        with col_step:
            display_step(step, i)
        with col_remove:
            if st.button("🗑", key=f"remove_{i}", type="primary"):
                st.session_state.steps.pop(i)
                st.rerun()


def display_step(step, index):
    step_types = {
        "agent": display_agent_step,
        "preview": display_preview_step,
        "output": display_output_step,
        "context": display_context_step,
    }
    step_types[step["type"]](step["name"], index)


def display_agent_step(agent_name, index):
    with st.expander(f"{agent_name}", expanded=True):
        display_agent_config(agent_name)
        col_run, col_preview, _ = st.columns([1, 2, 6])
        with col_run:
            if st.button("Run", key=f"run_{agent_name}_{index}", type="primary"):
                update_workflow(agent_name, "output")
        with col_preview:
            if st.button("Preview", key=f"preview_{agent_name}_{index}"):
                update_workflow(agent_name, "preview")


def update_workflow(agent_name, step_type):
    # Remove existing context, preview, and output steps for this agent
    st.session_state.steps = [
        step
        for step in st.session_state.steps
        if not (
            step["name"] == agent_name
            and step["type"] in ["context", "preview", "output"]
        )
    ]

    # Capture current configuration
    agent_config = {
        "model": st.session_state.get(f"{agent_name}_model"),
        "instructions": st.session_state.get(f"{agent_name}_instructions"),
    }

    # Capture context-related configurations
    context_config = {
        "context_generator": st.session_state.get(f"{agent_name}_context_generator"),
        "batch": st.session_state.get(f"{agent_name}_batch"),
        "auto_select": st.session_state.get(f"{agent_name}_auto_select"),
        "use_previous_outputs": st.session_state.get(
            f"{agent_name}_use_previous_outputs"
        ),
    }

    # Add a separate context step
    st.session_state.steps.append(
        {"type": "context", "name": agent_name, "context_config": context_config}
    )

    # Add the preview or output step
    st.session_state.steps.append(
        {"type": step_type, "name": agent_name, "config": agent_config}
    )

    st.rerun()


def display_context_step(agent_name, _):
    context_step = next(
        step
        for step in st.session_state.steps
        if step["name"] == agent_name and step["type"] == "context"
    )
    # Find the corresponding preview or output step
    result_step = next(
        (
            step
            for step in st.session_state.steps
            if step["name"] == agent_name and step["type"] in ["preview", "output"]
        ),
        None,
    )

    is_preview = result_step["type"] == "preview" if result_step else False

    with st.expander(f"[Context] {agent_name}", expanded=True):
        display_context(context_step["context_config"], preview=is_preview)


def display_preview_step(agent_name, _):
    step = next(
        step
        for step in st.session_state.steps
        if step["name"] == agent_name and step["type"] == "preview"
    )
    with st.expander(f"[Preview] {agent_name}", expanded=True):
        preview_output = get_preview(step["config"])
        st.json(preview_output)


def display_output_step(agent_name, _):
    step = next(
        step
        for step in st.session_state.steps
        if step["name"] == agent_name and step["type"] == "output"
    )
    with st.expander(f"[Output] {agent_name}", expanded=True):
        output = get_output(step["config"])
        st.json(output)


def display_agent_config(agent_name):
    agent_config = AGENTS_CONFIGS[agent_name]

    col_context, col_model = st.columns([2, 2])
    with col_context:
        context_options = [None, "extract_files_description", "extract_files_detail"]
        st.selectbox(
            "Context Generator",
            options=context_options,
            index=context_options.index(agent_config.get("context_generator", None)),
            key=f"{agent_name}_context_generator",
            format_func=lambda x: "None" if x is None else x,
        )

        col_batch, col_auto = st.columns([1, 1])
        with col_batch:
            st.toggle(
                "Batch",
                value=agent_config.get("batch", False),
                key=f"{agent_name}_batch",
            )
        with col_auto:
            st.toggle(
                "Auto select",
                value=agent_config.get("auto_select", False),
                key=f"{agent_name}_auto_select",
            )

    with col_model:
        model_options = ["gpt-4o-2024-08-06", "gpt-4o-mini"]
        st.selectbox(
            "Model",
            options=model_options,
            index=model_options.index(agent_config["model"]),
            key=f"{agent_name}_model",
        )
        st.toggle(
            "Use previous outputs",
            value=agent_config.get("use_previous_outputs", False),
            key=f"{agent_name}_use_previous_outputs",
        )

    with st.expander("Instructions", expanded=False):
        st.text_area(
            "prompt",
            agent_config["instructions"],
            height=300,
            key=f"{agent_name}_instructions",
        )


def display_context_config(context_config):
    with st.expander("Context Configuration", expanded=False):
        st.json(context_config)


def display_run_tasks():
    if st.button(
        "Run tasks", type="primary", disabled=len(st.session_state.steps) == 0
    ):
        run_tasks()


def run_tasks():
    for step in st.session_state.steps:
        if step["type"] == "agent":
            update_workflow(step["name"], "output")
    st.rerun()


if __name__ == "__main__":
    home_page()
