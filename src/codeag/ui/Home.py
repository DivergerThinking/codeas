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

    if st.button("Run"):
        generate_sections(selected_sections)
    else:
        display_sections(selected_sections)


def generate_sections(selected_sections: list[str]):
    for section in selected_sections:
        with st.spinner(f"Generating {section}..."):
            st.session_state.outputs[section] = generate_docs_section(
                state.llm_client,
                section,
                st.session_state.selected_files_path,
                state.repo_metadata,
            )
            display_section(section)


def display_sections(selected_sections: list[str]):
    for section in selected_sections:
        if section in st.session_state.outputs:
            display_section(section)


def display_section(section: str):
    with st.expander(section.replace("_", " ").upper(), expanded=True):
        st.markdown(st.session_state.outputs[section].response["content"])


if __name__ == "__main__":
    home_page()
