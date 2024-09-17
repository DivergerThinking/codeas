import streamlit as st

from codeag.ui.state import state
from codeag.use_cases.documentation import SECTION_CONFIG, generate_docs_section


def display():
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
