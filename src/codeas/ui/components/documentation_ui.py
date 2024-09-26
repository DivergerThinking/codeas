import streamlit as st

from codeas.core.state import state
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section


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

    use_previous_outputs = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs"
    )
    if st.button("Generate documentation", type="primary", key="generate_docs"):
        if use_previous_outputs:
            process_sections(selected_sections, use_previous=use_previous_outputs)
        else:
            process_sections(selected_sections, generate=True)

    # Only show the preview button if no documentation has been generated
    if not any(section in st.session_state.outputs for section in selected_sections):
        if st.button("Preview", key="preview_docs"):
            process_sections(selected_sections, preview=True)


def process_sections(
    selected_sections: list[str],
    generate: bool = False,
    preview: bool = False,
    use_previous: bool = False,
):
    total_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_input_cost = 0
    full_documentation = ""

    with st.expander("Sections", expanded=False):
        for section in selected_sections:
            with st.spinner(
                f"{'Generating' if generate else 'Previewing' if preview else 'Displaying'} {section}..."
            ):
                if generate or preview:
                    output = generate_docs_section(
                        state.llm_client,
                        section,
                        state.repo,
                        state.repo_metadata,
                        preview=preview,
                    )
                    if generate:
                        st.session_state.outputs[section] = output
                        total_cost += output.cost["total_cost"]
                        total_input_tokens += output.tokens["input_tokens"]
                        total_output_tokens += output.tokens["output_tokens"]

                        # Write the output to a file
                        state.write_output(
                            {
                                "content": output.response["content"],
                                "cost": output.cost,
                                "tokens": output.tokens,
                            },
                            f"{section}.json",
                        )

                    if preview:
                        total_input_cost += output.cost["input_cost"]
                elif use_previous:
                    try:
                        previous_output = state.read_output(f"{section}.json")
                        output = type(
                            "Output",
                            (),
                            {
                                "response": {"content": previous_output["content"]},
                                "cost": previous_output["cost"],
                                "tokens": previous_output["tokens"],
                                "messages": [
                                    {"content": ""}
                                ],  # Placeholder for context
                            },
                        )
                        st.session_state.outputs[section] = output
                        total_cost += output.cost["total_cost"]
                        total_input_tokens += output.tokens["input_tokens"]
                        total_output_tokens += output.tokens["output_tokens"]
                    except FileNotFoundError:
                        st.warning(
                            f"No previous output found for {section}. Running generation..."
                        )
                        output = generate_docs_section(
                            state.llm_client,
                            section,
                            state.repo,
                            state.repo_metadata,
                            preview=False,
                        )
                        st.session_state.outputs[section] = output
                        total_cost += output.cost["total_cost"]
                        total_input_tokens += output.tokens["input_tokens"]
                        total_output_tokens += output.tokens["output_tokens"]

                        # Write the output to a file
                        state.write_output(
                            {
                                "content": output.response["content"],
                                "cost": output.cost,
                                "tokens": output.tokens,
                            },
                            f"{section}.json",
                        )
                display_section(section, preview)

                if not preview and section in st.session_state.outputs:
                    cleaned_content = clean_markdown_content(
                        st.session_state.outputs[section].response["content"]
                    )
                    full_documentation += f"\n\n{cleaned_content}"

    if generate:
        st.info(
            f"Total cumulated cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"
        )
    elif preview:
        st.info(f"Total cumulated input cost: ${total_input_cost:.4f}")

    with st.expander("Full Documentation", expanded=True):
        full_documentation = clean_markdown_content(full_documentation)
        st.markdown(full_documentation)

    if generate or (
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        add_download_button(selected_sections)


def clean_markdown_content(content: str) -> str:
    content = content.strip()
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[11:-3].strip()
    return content


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
                    state.repo,
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
                st.warning("Context is empty. Previous output may have been used.")

            if not preview:
                content = output.response["content"]
                content = clean_markdown_content(content)
                st.code(content, language="markdown")


def add_download_button(selected_sections: list[str]):
    combined_content = "\n\n".join(
        [
            clean_markdown_content(
                st.session_state.outputs[section].response["content"]
            )
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
