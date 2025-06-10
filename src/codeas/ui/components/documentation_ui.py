import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section

# Define constants for repeated literals
INCL_COLUMN_NAME = "Incl."

def display():
    # Create a list of documentation sections from SECTION_CONFIG
    doc_sections = list(SECTION_CONFIG.keys())

    # Format the section names
    formatted_sections = [
        f"{' '.join(section.split('_')).upper()}" for section in doc_sections
    ]

    # Create a dictionary for the data editor
    doc_data = {
        INCL_COLUMN_NAME: [True] * len(doc_sections),  # Default all to True
        "Section": formatted_sections,
    }

    # Display the data editor
    edited_data = st.data_editor(
        doc_data,
        column_config={
            INCL_COLUMN_NAME: st.column_config.CheckboxColumn(width="small"),
            "Section": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

    # Get the selected sections
    selected_sections = [
        section for section, incl in zip(doc_sections, edited_data[INCL_COLUMN_NAME]) if incl
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
    # Removed duplicate initialization of total_input_tokens
    full_documentation = ""

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            with st.spinner(
                f"{'Generating' if generate else 'Previewing' if preview else 'Displaying'} {section}..."
            ):
                output = None # Initialize output for the current section

                # Attempt to read previous output if requested
                if use_previous:
                    try:
                        output = read_output(section) # read_output saves to state
                    except FileNotFoundError:
                        # If previous not found, proceed to generate/preview if applicable
                        pass # output remains None

                # If output was not read (or not using previous), run generate/preview
                if output is None:
                    if generate:
                        output = run_generation(section) # run_generation saves to state
                    elif preview:
                        output = run_preview(section) # run_preview does NOT save to state

                # Process output if obtained
                if output:
                    if generate:
                        total_cost += output.cost.get("total_cost", 0)
                        total_input_tokens += output.tokens.get("input_tokens", 0)
                        total_output_tokens += output.tokens.get("output_tokens", 0)
                    elif preview:
                        total_input_cost += output.cost.get("input_cost", 0)
                        total_input_tokens += output.tokens.get("input_tokens", 0)

                # Display section using the obtained output
                display_section(section, generate, preview, use_previous, section_output=output)

                # Accumulate full documentation (only if not preview and output is in session_state)
                # Accumulation logic relies on output being stored in session_state.
                # run_generation and read_output store output in state. run_preview does not.
                # This means accumulation primarily happens for 'generate' actions or when using previous results.
                # Use .get() for content access for robustness when reading from session_state
                if not preview and section in st.session_state.outputs:
                     section_output_state = st.session_state.outputs[section]
                     content_to_clean = section_output_state.response.get("content", "")
                     cleaned_content = clean_markdown_content(content_to_clean)
                     full_documentation += f"\n\n{cleaned_content}"


    # Display total costs after processing all sections
    if generate:
        st.info(
            f"Total cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"
        )
        # Record usage only if generation was actually performed (not just preview) and not using previous
        if total_cost > 0 and not use_previous:
             usage_tracker.record_usage("generate_docs", total_cost)
    elif preview:
        st.info(
            f"Total input cost: ${total_input_cost:.4f} ({total_input_tokens:,} tokens)"
        )

    # Display full documentation
    if full_documentation.strip():
        with st.expander("Full Documentation", expanded=True):
            final_documentation = clean_markdown_content(full_documentation)
            st.markdown(final_documentation)


    # Add download button only if generate ran or using previous outputs with content
    # Check if there is any output content in state for the selected sections
    if generate or (\
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
         # Calculate content to download based on session_state
         # Use .get() for content access for robustness
        downloadable_content = "\\n\\n".join(\
            [
                clean_markdown_content(\
                    st.session_state.outputs[section].response.get("content", "")\
                )\
                for section in selected_sections\
                if section in st.session_state.outputs
            ]\
        )
        # Only call add_download_button if there's content after cleaning
        if downloadable_content.strip():
            add_download_button(downloadable_content)


def run_generation(section: str):
    # Run a preview first to check if there's context
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    # Check if the preview indicates context was found (e.g., by having messages with content)
    # Assuming messages list indicates whether context was found and has content
    if preview_output and preview_output.messages and preview_output.messages[0].get("content", "").strip():
        # If context exists, run the full generation
        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        # Store the output in session state and write to file
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
        # If no context found based on preview, show warning and return None
        st.warning(f"No context found for {section.upper()}. Skipping generation.")
        # Clean up if a previous run existed in state but new generation failed
        if section in st.session_state.outputs:
             del st.session_state.outputs[section]
        return None


def run_preview(section: str):
    # run_preview should not save to state or write files
    return generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )


def read_output(section: str):
    # Reads previous output and stores it in session state
    previous_output_data = state.read_output(f"{section}.json")
    # Reconstruct an object similar to the output from generate_docs_section
    # Use a class for structure
    class SectionOutput:
        def __init__(self, content, cost, tokens, messages):
            self.response = {"content": content}
            self.cost = cost
            self.tokens = tokens
            self.messages = messages

    # Use .get() with default empty structures for robustness when reading file
    output = SectionOutput(
        content=previous_output_data.get("content", ""),
        cost=previous_output_data.get("cost", {}),
        tokens=previous_output_data.get("tokens", {}),
        messages=previous_output_data.get(
            "messages",
            []
        ),
    )
    st.session_state.outputs[section] = output # Store in session state
    return output


def clean_markdown_content(content: str) -> str:
    if not isinstance(content, str):
        return ""
    content = content.strip()
    # Revert to original simple markdown code block stripping logic
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[11:-3].strip()
    return content


# Modified display_section to accept the output object
def display_section(
    section: str,
    generate: bool = False,
    preview: bool = False,
    use_previous: bool = False,
    section_output=None # Accept the output object retrieved earlier
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )
    # Use a unique key for each expander within the loop (necessary for dynamic elements)
    expander_key = f"section_expander_{section}_{generate}_{preview}_{use_previous}"

    with st.expander(expander_label, expanded=False, key=expander_key):
        # Display cost info if output is available
        if section_output:
            if preview:
                # Use .get with default 0 for robustness, assuming cost/tokens are dicts
                st.info(
                    f"Input cost: ${section_output.cost.get('input_cost', 0):.4f} ({section_output.tokens.get('input_tokens', 0):,} tokens)"
                )
            elif generate: # This covers newly generated or loaded previous generated output
                 # Use .get with default 0 for robustness, assuming cost/tokens are dicts
                st.info(
                    f"Total cost: ${section_output.cost.get('total_cost', 0):.4f} "
                    f"(input tokens: {section_output.tokens.get('input_tokens', 0):,}, "
                    f"output tokens: {section_output.tokens.get('output_tokens', 0):,})",
                )

            # Display messages if available and not empty
            if section_output.messages:
                 with st.expander("Messages", expanded=False):
                    # Use try-except for json display robustness
                    try:
                        st.json(section_output.messages)
                    except Exception:
                        st.text(str(section_output.messages)) # Fallback to text

            # Display warning if context was not found or content is empty
            # Merged the 'if generate:' and 'if output:' conditions (Issue S1066)
            # Check if messages list is empty/None OR if the first message content is empty/missing
            first_message_content = section_output.messages[0].get("content", "") if section_output.messages else ""
            if generate and section_output and (not section_output.messages or not first_message_content.strip()):
                 st.warning(f"No context found for {section.upper()}{' from previous run' if use_previous else ''}.")


            # Display code content if generating and output content is available
            # Merged the 'if generate:' and 'if output:' conditions (Issue S1066)
            if generate and section_output:
                # Use .get() for content access for robustness
                content = section_output.response.get("content", "")
                cleaned_content = clean_markdown_content(content)
                if cleaned_content.strip(): # Only display if content is not empty after cleaning
                    st.code(cleaned_content, language="markdown")


# Modified add_download_button to accept the combined content
def add_download_button(combined_content: str):
    # The combined_content is now passed in, calculated in process_sections
    # Display the button only if there is content to download
    if combined_content.strip():
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
            key="download_docs_button"
        )