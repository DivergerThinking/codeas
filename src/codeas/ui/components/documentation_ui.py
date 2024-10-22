import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
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

    generate_docs = st.button(
        "Generate documentation", type="primary", key="generate_docs"
    )
    preview_docs = st.button("Preview", key="preview_docs")
    if generate_docs:
        process_sections(
            selected_sections, generate=True, use_previous=use_previous_outputs
        )
    if preview_docs:
        process_sections(
            selected_sections, preview=True, use_previous=use_previous_outputs
        )


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
    total_input_tokens = 0
    full_documentation = ""

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            with st.spinner(
                f"{'Generating' if generate else 'Previewing' if preview else 'Displaying'} {section}..."
            ):
                if generate:
                    if use_previous:
                        try:
                            output = read_output(section)
                        except FileNotFoundError:
                            output = run_generation(section)
                    else:
                        output = run_generation(section)
                    if output:
                        total_cost += output.cost["total_cost"]
                        total_input_tokens += output.tokens["input_tokens"]
                        total_output_tokens += output.tokens["output_tokens"]
                elif preview:
                    if use_previous:
                        try:
                            output = read_output(section)
                        except FileNotFoundError:
                            output = run_preview(section)
                    else:
                        output = run_preview(section)
                    if output:
                        total_input_cost += output.cost["input_cost"]
                        total_input_tokens += output.tokens["input_tokens"]

                display_section(section, generate, preview, use_previous)

                if not preview and section in st.session_state.outputs:
                    cleaned_content = clean_markdown_content(
                        st.session_state.outputs[section].response["content"]
                    )
                    full_documentation += f"\n\n{cleaned_content}"

    if generate:
        st.info(
            f"Total cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"
        )
        if not use_previous:
            usage_tracker.record_usage("generate_docs", total_cost)
    elif preview:
        st.info(
            f"Total input cost: ${total_input_cost:.4f} ({total_input_tokens:,} tokens)"
        )

    if full_documentation:
        with st.expander("Full Documentation", expanded=True):
            full_documentation = clean_markdown_content(full_documentation)
            st.markdown(full_documentation)

    if generate or (
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        add_download_button(selected_sections)


def run_generation(section: str):
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    if preview_output.messages and preview_output.messages[0]["content"].strip():
        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        st.session_state.outputs[section] = output
        state.write_output(
            {
                "content": output.response["content"],
                "cost": output.cost,
                "tokens": output.tokens,
                "messages": output.messages,
            },
            f"{section}.json",
        )
        return output
    else:
        st.warning(f"No context found for {section.upper()}. Skipping generation.")
        return None  # Return None if no generation occurred


def run_preview(section: str):
    return generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )


def read_output(section: str):
    previous_output = state.read_output(f"{section}.json")
    output = type(
        "Output",
        (),
        {
            "response": {"content": previous_output["content"]},
            "cost": previous_output["cost"],
            "tokens": previous_output["tokens"],
            "messages": previous_output.get(
                "messages",
                [{"content": "Context was not stored with previous output"}],
            ),  # Use stored messages if available
        },
    )
    st.session_state.outputs[section] = output
    return output


def clean_markdown_content(content: str) -> str:
    content = content.strip()
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[11:-3].strip()
    return content


def display_section(
    section: str,
    generate: bool = False,
    preview: bool = False,
    use_previous: bool = False,
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )
    with st.expander(expander_label, expanded=False):
        if preview:
            if use_previous:
                try:
                    output = read_output(section)
                except FileNotFoundError:
                    output = run_preview(section)
            else:
                output = run_preview(section)
            if output:
                st.info(
                    f"Input cost: ${output.cost['input_cost']:.4f} ({output.tokens['input_tokens']:,} tokens)"
                )
        elif generate:
            output = st.session_state.outputs.get(section)
            if output:
                st.info(
                    f"Total cost: ${output.cost['total_cost']:.4f} "
                    f"(input tokens: {output.tokens['input_tokens']:,}, "
                    f"output tokens: {output.tokens['output_tokens']:,})"
                )
        if output:
            with st.expander("Messages", expanded=False):
                st.json(output.messages)

            if not output.messages or not output.messages[0]["content"].strip():
                st.warning(f"No context found for {section.upper()}.")

        if generate:
            if output:
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
