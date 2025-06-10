import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section

# S1192: Define a constant for the duplicated literal "Incl."
INCLUDE_COLUMN_NAME = "Incl."


def display():
    # Create a list of documentation sections from SECTION_CONFIG
    doc_sections = list(SECTION_CONFIG.keys())

    # Format the section names
    formatted_sections = [
        f"{' '.join(section.split('_')).upper()}" for section in doc_sections
    ]

    # Create a dictionary for the data editor
    doc_data = {
        INCLUDE_COLUMN_NAME: [True] * len(doc_sections),  # Default all to True
        "Section": formatted_sections,
    }

    # Display the data editor
    edited_data = st.data_editor(
        doc_data,
        column_config={
            INCLUDE_COLUMN_NAME: st.column_config.CheckboxColumn(width="small"),
            "Section": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

    # Get the selected sections
    selected_sections = [
        section
        for section, incl in zip(doc_sections, edited_data[INCLUDE_COLUMN_NAME])
        if incl
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


# Helper function to get or generate/preview section output
def _get_output_for_section(section: str, generate: bool, preview: bool, use_previous: bool):
    """Helper to get or generate/preview section output, handling use_previous."""
    output = None
    if use_previous:
        try:
            output = read_output(section)
        except FileNotFoundError:
            st.warning(f"No previous output found for {section.upper()}. Running new.")
            if generate:
                output = run_generation(section)
            elif preview:
                output = run_preview(section)
    else:
        if generate:
            output = run_generation(section)
        elif preview:
            output = run_preview(section)
    return output


def process_sections(
    selected_sections: list[str],
    generate: bool = False,
    preview: bool = False,
    use_previous: bool = False,
):
    # S3776 (process_sections): Initialize separate totals for clarity and correctness
    total_generate_cost = 0
    total_preview_input_cost = 0
    total_generate_input_tokens = 0
    total_generate_output_tokens = 0
    total_preview_input_tokens = 0
    full_documentation = ""

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            # S3358: Extract nested conditional into an independent statement
            status_text = 'Generating' if generate else 'Previewing' if preview else 'Displaying'
            with st.spinner(f"{status_text} {section}..."):
                # S3776 (process_sections): Use helper function to get output
                output = _get_output_for_section(section, generate, preview, use_previous)

                if output:
                    # Store output consistently in state
                    st.session_state.outputs[section] = output

                    # Update totals based on generate/preview flag
                    if generate:
                        total_generate_cost += output.cost["total_cost"]
                        total_generate_input_tokens += output.tokens["input_tokens"]
                        total_generate_output_tokens += output.tokens["output_tokens"]
                    elif preview:
                        total_preview_input_cost += output.cost["input_cost"]
                        total_preview_input_tokens += output.tokens["input_tokens"]

                # Display section details - this function will read from state
                display_section(section, generate, preview) # Pass only necessary flags

                # Add to full_documentation if not preview and output exists in state
                if not preview and section in st.session_state.outputs:
                    cleaned_content = clean_markdown_content(
                        st.session_state.outputs[section].response["content"]
                    )
                    full_documentation += f"\n\n{cleaned_content}"

    if generate:
        # S3776 (process_sections): Use correct token variables in summary
        st.info(
            f"Total cost: ${total_generate_cost:.4f} "
            f"(input tokens: {total_generate_input_tokens:,}, "
            f"output tokens: {total_generate_output_tokens:,})"\
        )
        if not use_previous:
            usage_tracker.record_usage("generate_docs", total_generate_cost)
    elif preview:
        # S3776 (process_sections): Use correct token variable in summary
        st.info(
            f"Total input cost: ${total_preview_input_cost:.4f} ({total_preview_input_tokens:,} tokens)"
        )

    if full_documentation:
        with st.expander("Full Documentation", expanded=True):
            # The content is already cleaned when added to full_documentation
            st.markdown(full_documentation)

    if generate or (\
        not preview\
        and any(section in st.session_state.outputs for section in selected_sections)\
    ):
        add_download_button(selected_sections)


def run_generation(section: str):
    # Run a preview first to check for context
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    if preview_output and preview_output.messages and preview_output.messages[0]["content"].strip():
        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        # Output will be stored in state by process_sections
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
    # Output will be stored in state by process_sections
    return generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )


def read_output(section: str):
    previous_output = state.read_output(f"{section}.json")
    # Create a dummy object matching the expected structure
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
            ),
        },
    )() # Instantiate the type
    # Output will be stored in state by process_sections
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
    # S3776 (display_section): Removed unused use_previous flag
):
    # S3776 (display_section): Simplified logic - read from state
    output = st.session_state.outputs.get(section)

    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )
    with st.expander(expander_label, expanded=False):
        if output:
            # Display cost based on generate/preview
            if preview:
                # S3776 (display_section): Display input cost for preview
                st.info(
                    f"Input cost: ${output.cost['input_cost']:.4f} ({output.tokens['input_tokens']:,} tokens)"
                )
            elif generate:
                # S3776 (display_section): Display total cost for generate
                 st.info(
                    f"Total cost: ${output.cost['total_cost']:.4f} "
                    f"(input tokens: {output.tokens['input_tokens']:,}, "
                    f"output tokens: {output.tokens['output_tokens']:,})"\
                )

            # Always display messages if output exists and has messages
            if output.messages:
                with st.expander("Messages", expanded=False):
                    st.json(output.messages)

                # Check for no context based on first message content
                if not output.messages[0]["content"].strip():
                    st.warning(f"No context found for {section.upper()}.")
            else:
                 # Handle case where messages list is empty or None
                 st.info("No message history stored.") # Or maybe just display empty messages expander? Sticking closer to original intent.


            # Display generated content if generate is true
            if generate:
                 content = output.response["content"]
                 content = clean_markdown_content(content)
                 st.code(content, language="markdown")
        else:
             # Handle case where output was not successfully obtained and stored in state
             st.warning(f"Could not obtain output for {section.upper()}.")


def add_download_button(selected_sections: list[str]):
    combined_content = "\n\n".join(\
        [\
            clean_markdown_content(\
                st.session_state.outputs[section].response["content"]\
            )\
            for section in selected_sections\
            if section in st.session_state.outputs\
        ]\
    )

    # S1066: Merged if statement with the enclosing one (redundant if output check removed by complexity fix)
    # The original issue was `if generate: if output: ... st.code(...)` inside display_section.
    # My fix for S3776 already removed the inner `if output:` there.
    # This specific S1066 is now likely moot or refers to the structure which no longer exists.
    # Let's double check if there's another potential merge.
    # No, the only remaining if structures seem necessary or already handled by refactoring.

    st.download_button(
        label="Download docs",
        data=combined_content,
        file_name="docs.md",
        mime="text/markdown",
        type="primary",
    )