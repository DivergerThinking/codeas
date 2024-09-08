import os
from typing import Literal

import pyperclip
import streamlit as st
from streamlit_searchbox import st_searchbox

from codeag.configs.agents_configs import AGENTS_CONFIGS
from codeag.core.agent import Agent
from codeag.core.context import Context
from codeag.core.llms import LLMClient
from codeag.core.repo import Filters, Repo, RepoSelector
from codeag.ui.utils import search_dirs

if "filters" not in st.session_state:
    st.session_state.filters = Filters()

if "files_description" not in st.session_state:
    st.session_state.files_description = {}

if "llm_client" not in st.session_state:
    st.session_state.llm_client = LLMClient()


def display_filters(key: Literal["files", "folders"]):
    col_include, col_exclude = st.columns(2)
    with col_include:
        include_value = getattr(st.session_state.filters, f"include_{key}", [])
        include_value = ", ".join(include_value)
        st.text_input(
            "Include",
            value=include_value,
            key=f"include_{key}_input",
            on_change=lambda: update_filter(key, "include"),
            placeholder="*.py, src/*, etc.",
        )
    with col_exclude:
        exclude_value = getattr(st.session_state.filters, f"exclude_{key}", [])
        exclude_value = ", ".join(exclude_value)
        st.text_input(
            "Exclude",
            value=exclude_value,
            key=f"exclude_{key}_input",
            on_change=lambda: update_filter(key, "exclude"),
            placeholder="debug/*, *.ipynb, etc.",
        )


def update_filter(key: str, filter_type: Literal["include", "exclude"]):
    input_key = f"{filter_type}_{key}_input"
    state_key = f"{filter_type}_{key}"

    if input_key in st.session_state:
        input_value = st.session_state[input_key]
        filters_list = [
            filter_.strip() for filter_ in input_value.split(",") if filter_.strip()
        ]
        setattr(st.session_state.filters, state_key, filters_list)


def display_data_editor(key: str, data: dict):
    st.data_editor(
        data,
        key=key,
        use_container_width=True,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width=10),
            "Path": st.column_config.TextColumn(width="large"),
            "Tokens": st.column_config.NumberColumn(width=10),
        },
        disabled=True,
    )


def chain_page():
    st.title("Codeas")
    st.subheader("Repo")
    repo_path = st_searchbox(search_dirs, placeholder=".", default=".")
    st.caption(os.path.abspath(repo_path))

    st.session_state.repo_path = repo_path

    # Load repository data
    repo = Repo(repo_path=repo_path)
    selector = RepoSelector(repo=repo)

    # Context section
    display_filters("files")
    files_to_include = selector.filter_files(st.session_state.filters)
    files_data = {
        "Incl.": files_to_include,
        "Path": repo.files_paths,
        "Tokens": list(repo.files_tokens.values()),
    }
    # Sort by Incl. = True first, then by Path
    sorted_files_data = sorted(
        zip(files_data["Incl."], files_data["Path"], files_data["Tokens"]),
        key=lambda x: (not x[0], x[1]),
    )
    # Unzip the sorted data
    files_data["Incl."], files_data["Path"], files_data["Tokens"] = map(
        list, zip(*sorted_files_data)
    )
    display_data_editor("files_editor", files_data)

    # Add st.info() to show selected files / total files
    num_selected_files = sum(files_data["Incl."])
    total_files = len(files_data["Incl."])
    selected_tokens = sum(
        token for incl, token in zip(files_data["Incl."], files_data["Tokens"]) if incl
    )
    st.info(
        f"{num_selected_files} / {total_files} files selected | {selected_tokens:,} tokens"
    )

    st.session_state.selected_files_path = [
        path for path, incl in zip(files_data["Path"], files_data["Incl."]) if incl
    ]

    st.subheader("Tasks")
    if "steps" not in st.session_state:
        st.session_state.steps = []

    available_steps = list(AGENTS_CONFIGS.keys())

    col, _ = st.columns(2)
    with col:
        selected_agent = st.selectbox(
            "Select instructions to add:", [""] + available_steps
        )
        if st.button("Add"):
            if selected_agent:
                if selected_agent not in [
                    step["name"] for step in st.session_state.steps
                ]:
                    st.session_state.steps.append(
                        {"type": "agent", "name": selected_agent}
                    )
                st.rerun()

    # Display steps below the select box
    for i, step in enumerate(st.session_state.steps):
        col_step, col_remove = st.columns([11, 1])
        with col_step:
            if step["type"] == "output_with_spinner":
                display_output_step_with_spinner(step["name"])
            elif step["type"] == "preview_with_spinner":
                display_preview_step_with_spinner(step["name"])
            else:
                display_step(step, i)
        with col_remove:
            if st.button("🗑", key=f"remove_{i}", type="primary"):
                st.session_state.steps.pop(i)
                st.rerun()

    # Add "Run tasks" button and "Sequential" toggle
    st.divider()
    if st.button(
        "Run tasks", type="primary", disabled=len(st.session_state.steps) == 0
    ):
        run_tasks()


def run_tasks():
    for step in st.session_state.steps:
        if step["type"] == "agent":
            agent_name = step["name"]
            run_agent_callback(agent_name)
    # Rerun once after all tasks are completed
    st.rerun()


def display_step(step, index):
    if step["type"] == "agent":
        display_agent_step(step["name"], index)
    elif step["type"] == "preview":
        display_preview_step(step["name"], step["preview"])
    elif step["type"] == "output":
        display_output_step(step["name"], step["output"])


def display_agent_step(agent_name, index):
    with st.expander(
        f"{agent_name}", expanded=True if agent_name == "custom" else False
    ):
        buttons_disabled = display_agent_config(agent_name)
        col_run, col_preview, _ = st.columns([1, 2, 6])
        with col_run:
            if st.button(
                "Run",
                key=f"run_{agent_name}_{index}",
                type="primary",
                disabled=buttons_disabled,
                on_click=lambda: run_agent_callback(agent_name),
            ):
                st.rerun()
        with col_preview:
            if st.button(
                "Preview",
                key=f"preview_{agent_name}_{index}",
                disabled=buttons_disabled,
                on_click=lambda: preview_agent_callback(agent_name),
            ):
                st.rerun()


def run_agent_callback(agent_name):
    remove_agent_steps(agent_name)
    add_output_step_with_spinner(agent_name)


def preview_agent_callback(agent_name):
    remove_agent_steps(agent_name)
    add_preview_step_with_spinner(agent_name)
    # Clear the previous preview state
    if f"preview_{agent_name}" in st.session_state:
        del st.session_state[f"preview_{agent_name}"]
    if f"preview_{agent_name}_complete" in st.session_state:
        del st.session_state[f"preview_{agent_name}_complete"]


def remove_agent_steps(agent_name):
    st.session_state.steps = [
        step
        for step in st.session_state.steps
        if not (
            step["name"] == agent_name
            and step["type"]
            in ["preview", "output", "preview_with_spinner", "output_with_spinner"]
        )
    ]


def add_output_step_with_spinner(agent_name):
    st.session_state.steps.append(
        {
            "type": "output_with_spinner",
            "name": agent_name,
        }
    )


def add_preview_step_with_spinner(agent_name):
    st.session_state.steps.append(
        {
            "type": "preview_with_spinner",
            "name": agent_name,
        }
    )


def display_output_step(agent_name, output):
    with st.expander(f"[Output] {agent_name}", expanded=True):
        with st.expander("Context", expanded=True):
            display_context(get_context(**AGENTS_CONFIGS[agent_name]))

        total_tokens = output.tokens["input_tokens"] + output.tokens["output_tokens"]
        st.info(
            f"Cost: $**{output.cost['total_cost']:.4f}** (**{output.cost['input_cost']:.4f}** + **{output.cost['output_cost']:.4f}**) | "
            f"Tokens: **{total_tokens:,}** (**{output.tokens['input_tokens']:,}** + **{output.tokens['output_tokens']:,}**)"
        )

        display_output(output)


def display_output_step_with_spinner(agent_name):
    with st.expander(f"[Output] {agent_name}", expanded=True):
        # Generate files description if needed
        if (
            agent_name != "extract_files_description"
            and AGENTS_CONFIGS[agent_name].get("context") == "files_description"
        ):
            if not generate_files_description(st.session_state.selected_files_path):
                st.stop()

        with st.expander("Context", expanded=True):
            display_context(get_context(**AGENTS_CONFIGS[agent_name]))

        with st.spinner(f"Running {agent_name}..."):
            output = run_agent(agent_name)

        total_tokens = output.tokens["input_tokens"] + output.tokens["output_tokens"]
        st.info(
            f"Cost: $**{output.cost['total_cost']:.4f}** (**{output.cost['input_cost']:.4f}** + **{output.cost['output_cost']:.4f}**) | "
            f"Tokens: **{total_tokens:,}** (**{output.tokens['input_tokens']:,}** + **{output.tokens['output_tokens']:,}**)"
        )

        display_output(output)

        # Update the step to remove the spinner for future renders
        for step in st.session_state.steps:
            if step["type"] == "output_with_spinner" and step["name"] == agent_name:
                step["type"] = "output"
                step["output"] = output
                break


def display_preview_step(agent_name, preview):
    with st.expander(f"[Preview] {agent_name}", expanded=True):
        with st.expander("Context", expanded=True):
            display_context(get_context(**AGENTS_CONFIGS[agent_name]))

        st.info(
            f"Input cost: **${preview.cost['input_cost']:.4f}** | "
            f"Input tokens: **{preview.tokens['input_tokens']:,}**"
        )

        st.write("Messages:")
        st.json(preview.messages, expanded=False)


def display_preview_step_with_spinner(agent_name):
    with st.expander(f"[Preview] {agent_name}", expanded=True):
        context_type = AGENTS_CONFIGS[agent_name].get("context")
        if context_type in ["files_description", "files_detail"] and agent_name not in [
            "extract_files_description",
            "extract_files_detail",
        ]:
            if not ensure_context_data(
                context_type, st.session_state.selected_files_path
            ):
                return

        with st.expander("Context", expanded=True):
            display_context(get_context(**AGENTS_CONFIGS[agent_name]))

        # Remove the check for existing preview and always generate a new one
        with st.spinner(f"Previewing {agent_name}..."):
            preview = preview_agent(agent_name)
            st.session_state[f"preview_{agent_name}"] = preview
            st.session_state[f"preview_{agent_name}_complete"] = True

        st.info(
            f"Input cost: **${preview.cost['input_cost']:.4f}** | "
            f"Input tokens: **{preview.tokens['input_tokens']:,}**"
        )

        st.write("Messages:")
        st.json(preview.messages, expanded=False)

        # Update the step to remove the spinner for future renders
        update_step_type(agent_name, "preview", preview)


def remove_preview_step(agent_name):
    st.session_state.steps = [
        step
        for step in st.session_state.steps
        if not (step["type"] == "preview" and step["name"] == agent_name)
    ]


def remove_output_step(agent_name):
    st.session_state.steps = [
        step
        for step in st.session_state.steps
        if not (step["type"] == "output" and step["name"] == agent_name)
    ]


def run_agent(agent_name: str):
    agent = Agent(**AGENTS_CONFIGS[agent_name])
    context = get_context(**AGENTS_CONFIGS[agent_name])
    return agent.run(llm_client=st.session_state.llm_client, context=context)


def preview_agent(agent_name: str):
    agent = Agent(**AGENTS_CONFIGS[agent_name])
    context = get_context(**AGENTS_CONFIGS[agent_name])
    return agent.preview(context)


def display_context(context):
    st.json(context, expanded=False)


def display_preview(preview):
    st.json(preview.model_dump(), expanded=False)


def display_output(output):
    with st.expander("Output", expanded=True):
        if "content" in output.response:
            container = st.container()
            if container.button("Copy", key=f"copy_single_output_{id(output)}"):
                pyperclip.copy(output.response["content"])
                container.success("Copied to clipboard!")
            container.markdown(output.response["content"])
        else:
            for key, value in output.response.items():
                with st.expander(f"{key}", expanded=True):
                    container = st.container()
                    if container.button("Copy", key=f"copy_{key}_{id(output)}"):
                        pyperclip.copy(value["content"])
                        container.success("Copied to clipboard!")
                    container.markdown(value["content"])


def ensure_context_data(
    context_type: Literal["files_description", "files_detail"], files_path: list[str]
):
    if context_type == "files_description":
        return generate_files_description(files_path)
    elif context_type == "files_detail":
        return generate_files_details(files_path)
    return True


def get_context(
    context: Literal["files_content", "files_description", "files_detail", None],
    batch: bool = False,
    auto_select: bool = False,
    use_previous_outputs: bool = False,
    **_,
):
    files_content = None
    if context is not None:
        files_path = (
            auto_select_files() if auto_select else st.session_state.selected_files_path
        )

        if context in ["files_description", "files_detail"]:
            if not ensure_context_data(context, files_path):
                st.stop()

        if context == "files_content":
            files_content = get_files_content(files_path, info_only=False)
        elif context == "files_description":
            files_content = get_files_content(files_path, info_only=True)
        elif context == "files_detail":
            files_content = get_files_content(files_path, compressed=True)

    agents_output = get_previous_outputs() if use_previous_outputs else {}
    ctx = Context(batch=batch)
    return ctx.retrieve(files_content=files_content, agents_output=agents_output)


def auto_select_files():
    return []


def get_previous_outputs():
    outputs = {}
    for step in st.session_state.steps:
        if step["type"] == "output" and "output" in step:
            output = step["output"]
            agent_name = step["name"]
            if "content" in output.response:
                outputs[agent_name] = output.response["content"]
            elif isinstance(output.response, dict):
                st.error("Adding batch outputs is not implemented yet.")
                return {}
    return outputs


def get_files_content(
    files_path: list[str], info_only: bool = False, compressed: bool = False
):
    files_content = {}
    for file_path in files_path:
        if info_only:
            files_content[file_path] = st.session_state.files_description[file_path]
        elif compressed:
            files_content[file_path] = st.session_state.files_detail[file_path]
        else:
            files_content[file_path] = read_file(file_path)
    return files_content


def generate_files_description(files_path: list[str]):
    files_to_generate = [
        file_path
        for file_path in files_path
        if file_path not in st.session_state.files_description
    ]
    if files_to_generate:
        # Preview the agent to get input tokens and cost
        preview = preview_agent("extract_files_description")

        st.warning(
            f"Files description needs to be generated for {len(files_to_generate)} files."
        )
        st.info(
            f"Input cost: **${preview.cost['input_cost']:.4f}** | "
            f"Input tokens: **{preview.tokens['input_tokens']:,}**"
        )

        if "files_description_generated" not in st.session_state:
            st.session_state.files_description_generated = False

        if not st.session_state.files_description_generated:
            if st.button("Generate Files Description"):
                with st.spinner("Generating files description..."):
                    output = run_agent("extract_files_description")
                for file_path, response in output.response.items():
                    st.session_state.files_description[file_path] = response["content"]
                st.session_state.files_description_generated = True

                # Display the generated description immediately
                st.success("Files description generated successfully!")

                total_tokens = (
                    output.tokens["input_tokens"] + output.tokens["output_tokens"]
                )
                st.info(
                    f"Cost: $**{output.cost['total_cost']:.4f}** (**{output.cost['input_cost']:.4f}** + **{output.cost['output_cost']:.4f}**) | "
                    f"Tokens: **{total_tokens:,}** (**{output.tokens['input_tokens']:,}** + **{output.tokens['output_tokens']:,}**)"
                )

                st.write("Files Description:")
                st.json(st.session_state.files_description, expanded=False)

                # Use a button to trigger the rerun
                if st.button("Continue"):
                    st.rerun()
            return False  # Return False instead of st.stop()
        else:
            st.write("Generated Files Description:")
            st.json(st.session_state.files_description, expanded=False)
    return True


def generate_files_details(files_path: list[str]):
    if "files_detail" not in st.session_state:
        st.session_state.files_detail = {}

    files_to_detail = [
        file_path
        for file_path in files_path
        if file_path not in st.session_state.files_detail
    ]
    if files_to_detail:
        # Preview the agent to get input tokens and cost
        preview = preview_agent("extract_files_detail")

        st.warning(
            f"Detailed content needs to be generated for {len(files_to_detail)} files."
        )
        st.info(
            f"Input cost: **${preview.cost['input_cost']:.4f}** | "
            f"Input tokens: **{preview.tokens['input_tokens']:,}**"
        )

        if "files_detail_generated" not in st.session_state:
            st.session_state.files_detail_generated = False

        if not st.session_state.files_detail_generated:
            if st.button("Generate Files Detail"):
                with st.spinner("Generating files detail..."):
                    output = run_agent("extract_files_detail")
                for file_path, response in output.response.items():
                    st.session_state.files_detail[file_path] = response["content"]
                st.session_state.files_detail_generated = True

                # Display the generated detailed content immediately
                st.success("Files detail generated successfully!")

                total_tokens = (
                    output.tokens["input_tokens"] + output.tokens["output_tokens"]
                )
                st.info(
                    f"Cost: $**{output.cost['total_cost']:.4f}** (**{output.cost['input_cost']:.4f}** + **{output.cost['output_cost']:.4f}**) | "
                    f"Tokens: **{total_tokens:,}** (**{output.tokens['input_tokens']:,}** + **{output.tokens['output_tokens']:,}**)"
                )

                st.write("Files Detail:")
                st.json(st.session_state.files_detail, expanded=False)

                # Use a button to trigger the rerun
                if st.button("Continue"):
                    st.rerun()
            return False
        else:
            st.write("Generated Files Detail:")
            st.json(st.session_state.files_detail, expanded=False)
    return True


def read_file(file_path: str):
    with open(f"{st.session_state.repo_path}/{file_path}", "r") as f:
        return f.read()


def display_agent_config(agent_name: str):
    agent_config = AGENTS_CONFIGS[agent_name]

    col_context, col_model = st.columns([2, 2])
    with col_context:
        context_options = ["files_content", "files_description", "files_detail"]
        selected_context = st.selectbox(
            "Context",
            options=context_options,
            index=context_options.index(agent_config.get("context", "files_content")),
            key=f"{agent_name}_context",
        )
        agent_config["context"] = selected_context

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
        agent_config["model"] = st.selectbox(
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

    is_custom = agent_name == "custom"
    instructions_expanded = is_custom or agent_config["instructions"].strip() == ""

    if is_custom:
        instructions = st.text_area(
            "Instructions",
            agent_config["instructions"],
            height=200,
            key=f"{agent_name}_instructions",
        )
    else:
        with st.expander("Instructions", expanded=instructions_expanded):
            instructions = st.text_area(
                "prompt",
                agent_config["instructions"],
                height=300,
                key=f"{agent_name}_instructions",
            )

    # Disable buttons if instructions are empty
    buttons_disabled = instructions.strip() == ""

    return buttons_disabled


def update_step_type(agent_name, new_type, data):
    # Remove any existing preview or output steps for this agent
    st.session_state.steps = [
        step
        for step in st.session_state.steps
        if not (
            step["name"] == agent_name
            and step["type"]
            in ["preview", "output", "preview_with_spinner", "output_with_spinner"]
        )
    ]

    # Add the new step
    st.session_state.steps.append(
        {"type": new_type, "name": agent_name, new_type: data}
    )


if __name__ == "__main__":
    chain_page()
