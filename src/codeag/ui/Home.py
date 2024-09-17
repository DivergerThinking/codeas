import pyperclip
import streamlit as st
import streamlit_nested_layout

from codeag.ui.components.display_repo import display_repo
from codeag.ui.state import state
from codeag.use_cases.documentation import SECTION_CONFIG, generate_docs_section

if "outputs" not in st.session_state:
    st.session_state.outputs = {}


def home_page():
    st.title("Codeas")
    display_repo()
    display_metadata()
    display_tasks()


def display_metadata():
    st.subheader("Metadata")

    # Display number of files with generated metadata
    files_with_metadata = [
        f
        for f in st.session_state.selected_files_path
        if f in state.repo_metadata.files_usage
    ]
    files_missing_metadata = [
        f
        for f in st.session_state.selected_files_path
        if f not in state.repo_metadata.files_usage
    ]

    with st.expander("Metadata"):
        st.write("Files missing metadata")
        st.json(files_missing_metadata, expanded=False)

        if st.button("Generate Missing Metadata", type="primary"):
            with st.spinner("Generating missing metadata..."):
                state.repo_metadata.generate_missing_repo_metadata(
                    state.llm_client, files_missing_metadata
                )
                state.repo_metadata.export_metadata(state.repo_path)
            st.success("Missing metadata generated and exported successfully!")

        if st.button("Estimate cost", key="estimate_missing_metadata"):
            with st.spinner("Estimating cost..."):
                preview = state.repo_metadata.generate_missing_repo_metadata(
                    state.llm_client, files_missing_metadata, preview=True
                )
                input_cost = preview.cost["input_cost"]
                input_tokens = preview.tokens["input_tokens"]
                estimated_cost = input_cost * 3
                estimated_input_tokens = input_tokens * 2
                estimated_output_tokens = input_tokens // 3
                st.caption(
                    f"Estimated cost: ${estimated_cost:.4f} (input tokens: {estimated_input_tokens:,} + output tokens: {estimated_output_tokens:,})"
                )

        st.write("Metadata")
        st.json(state.repo_metadata.model_dump(), expanded=False)

        if st.button("Update metadata"):
            with st.spinner("Generating metadata..."):
                state.repo_metadata.generate_repo_metadata(
                    state.llm_client, st.session_state.selected_files_path
                )
                state.repo_metadata.export_metadata(state.repo_path)
            st.success("Metadata updated!")

        if st.button("Estimate cost", key="estimate_update_metadata"):
            with st.spinner("Estimating cost..."):
                preview = state.repo_metadata.generate_repo_metadata(
                    state.llm_client, st.session_state.selected_files_path, preview=True
                )
                input_cost = preview.cost["input_cost"]
                input_tokens = preview.tokens["input_tokens"]
                estimated_cost = input_cost * 3
                estimated_input_tokens = input_tokens * 2
                estimated_output_tokens = input_tokens // 3
                st.caption(
                    f"Estimated cost: ${estimated_cost:.4f} (input tokens: {estimated_input_tokens:,} + output tokens: {estimated_output_tokens:,})"
                )

        st.caption("This will re-generate metadata for all selected files")

    st.info(
        f"{len(files_with_metadata)}/{len(st.session_state.selected_files_path)} selected files have metadata"
    )


def display_tasks():
    st.subheader("Tasks")
    task_options = [
        "Generate documentation",
        "Generate testing",
        "Generate refactoring",
        "Generate deployments",
    ]
    selected_task = st.selectbox("Select a task", task_options)

    display_task(selected_task)


def display_task(task: str):
    if task == "Generate documentation":
        display_generate_documentation_task()


def display_generate_documentation_task():
    # Create a list of documentation sections from SECTION_CONFIG
    doc_sections = list(SECTION_CONFIG.keys())

    # Format the section names
    formatted_sections = [
        f"{' '.join(section.split('_')).upper()}" for section in doc_sections
    ]

    # Create a dictionary for the data editor
    doc_data = {
        "Incl.": [True] * len(doc_sections),  # Default all to True
        "Section": formatted_sections,
    }

    # Display the data editor
    edited_data = st.data_editor(
        doc_data,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width="small"),
            "Section": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

    # Get the selected sections
    selected_sections = [
        section for section, incl in zip(doc_sections, edited_data["Incl."]) if incl
    ]

    if st.button("Run", type="primary"):
        process_sections(selected_sections, generate=True)
    elif st.button("Preview"):
        process_sections(selected_sections, preview=True)
    else:
        process_sections(selected_sections)


def process_sections(
    selected_sections: list[str], generate: bool = False, preview: bool = False
):
    total_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_input_cost = 0  # New variable for cumulated input cost

    for section in selected_sections:
        with st.spinner(
            f"{'Generating' if generate else 'Previewing' if preview else 'Displaying'} {section}..."
        ):
            if generate or preview:
                output = generate_docs_section(
                    state.llm_client,
                    section,
                    st.session_state.selected_files_path,
                    state.repo_metadata,
                    preview=preview,
                )
                if generate:
                    st.session_state.outputs[section] = output
                    total_cost += output.cost["total_cost"]
                    total_input_tokens += output.tokens["input_tokens"]
                    total_output_tokens += output.tokens["output_tokens"]
                if preview:
                    total_input_cost += output.cost[
                        "input_cost"
                    ]  # Add input cost for preview

            display_section(section, preview)

    if generate:
        st.info(
            f"Total cumulated cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"
        )
    elif preview:
        st.info(f"Total cumulated input cost: ${total_input_cost:.4f}")

    if generate or (
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        add_download_button(selected_sections)


def display_section(section: str, preview: bool = False):
    output = st.session_state.outputs.get(section) if not preview else None

    if output or preview:
        expander_label = (
            f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
        )
        with st.expander(expander_label, expanded=True):
            if preview:
                output = generate_docs_section(
                    state.llm_client,
                    section,
                    st.session_state.selected_files_path,
                    state.repo_metadata,
                    preview=True,
                )
                st.info(
                    f"Input cost: ${output.cost['input_cost']:.4f} ({output.tokens['input_tokens']:,} tokens)"
                )
            else:
                st.info(
                    f"Total cost: ${output.cost['total_cost']:.4f} "
                    f"(input tokens: {output.tokens['input_tokens']:,}, "
                    f"output tokens: {output.tokens['output_tokens']:,})"
                )

            context_content = output.messages[0]["content"]
            if context_content.strip():
                with st.expander("Context", expanded=False):
                    st.code(context_content, language="markdown")
            else:
                st.warning("Context is empty.")

            if not preview:
                st.code(output.response["content"], language="markdown")


def add_download_button(selected_sections: list[str]):
    combined_content = "\n\n".join(
        [
            f"{st.session_state.outputs[section].response['content']}"
            for section in selected_sections
            if section in st.session_state.outputs
        ]
    )

    st.download_button(
        label="Download docs",
        data=combined_content,
        file_name="docs.md",
        mime="text/markdown",
        type="primary",
    )


if __name__ == "__main__":
    home_page()
