import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section

# Define constants for repeated strings
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


def _get_output_for_section(section: str, generate: bool, preview: bool, use_previous: bool):
    """Helper to get or generate/preview output for a single section."""
    output = None
    action_func = None

    if generate:
        action_func = run_generation
    elif preview:
        action_func = run_preview

    if action_func:
        if use_previous:
            try:
                output = read_output(section)
                # If read_output returns None (e.g. file not found or empty/invalid), try to run action
                if output is None:
                     output = action_func(section)
            except FileNotFoundError:
                output = action_func(section)
        else:
            output = action_func(section)

    # Ensure output is None if generation/preview was skipped or failed (e.g. no context)
    # Check if output is valid and has content if generation/preview was attempted
    if output is not None and (generate or preview) and not (output.response and output.response.get("content")):
         output = None # Explicitly set to None if content is missing

    return output


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
    full_documentation = "" # Accumulate content here as in original

    expander_label = f"Sections {'[Preview]' if preview else ''}"
    with st.expander(expander_label, expanded=not use_previous):
        for section in selected_sections:
            action_text = 'Generating' if generate else ('Previewing' if preview else 'Displaying')
            spinner_text = f"{action_text} {section}..."
            with st.spinner(spinner_text):
                output = _get_output_for_section(section, generate, preview, use_previous)

                if output:
                    if generate:
                        total_cost += output.cost.get("total_cost", 0)
                        total_input_tokens += output.tokens.get("input_tokens", 0)
                        total_output_tokens += output.tokens.get("output_tokens", 0)
                    elif preview:
                        total_input_cost += output.cost.get("input_cost", 0)
                        total_input_tokens += output.tokens.get("input_tokens", 0)

                # Pass output to display_section
                display_section(section, output, generate, preview, use_previous)

                # Accumulate full documentation inside the loop if not previewing and section in session state outputs
                if not preview and section in st.session_state.get("outputs", {}):
                    # Check if output exists and has response/content as in original logic
                    output_in_state = st.session_state["outputs"].get(section)
                    if output_in_state and output_in_state.response and output_in_state.response.get("content") is not None:
                         cleaned_content = clean_markdown_content(output_in_state.response["content"])
                         # Append content even if cleaned content is empty, matching original behavior
                         full_documentation += f"\n\n{cleaned_content}"


    if generate:
        st.info(
            f"Total cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"\
        )
        # Only record usage if generation actually happened (total_cost > 0) and not using previous
        if not use_previous and total_cost > 0:
             usage_tracker.record_usage("generate_docs", total_cost)

    elif preview:
        st.info(
            f"Total input cost: ${total_input_cost:.4f} ({total_input_tokens:,} tokens)"
        )

    # Display full documentation based on original condition
    if full_documentation:
        with st.expander("Full Documentation", expanded=True):
            # Content was already cleaned when accumulated
            st.markdown(full_documentation) # Reverted back to original display logic without strip


    # Add download button based on the original condition logic
    # Show button if generating OR (not preview and any selected section has output in state)
    if generate or (not preview and any(section in st.session_state.get("outputs", {}) for section in selected_sections)):
         add_download_button(selected_sections)


def run_generation(section: str):
    # Run preview first to check context
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )

    # Check if preview had context (messages or content)
    if preview_output and preview_output.messages and preview_output.messages[0].get("content", "").strip():
        # If context exists, run full generation
        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        # Store output in session state and write to file
        if "outputs" not in st.session_state:
             st.session_state.outputs = {}
        st.session_state.outputs[section] = output
        state.write_output(
            {
                "content": output.response.get("content", ""),
                "cost": output.cost,
                "tokens": output.tokens,
                "messages": output.messages,
            },
            f"{section}.json",
        )
        return output
    else:
        # No context found, skip generation
        st.warning(f"No context found for {section.upper()}. Skipping generation.")
        return None  # Return None if no generation occurred


def run_preview(section: str):
    # Simply run preview
    return generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )


def read_output(section: str):
    """Reads output from file and returns an object similar to the generation output."""
    try:
        previous_output = state.read_output(f"{section}.json")
        if not previous_output:
             return None # Return None if file exists but is empty/invalid JSON

        # Construct a simple object with necessary attributes
        output = type(
            "Output",
            (),
            {
                "response": {"content": previous_output.get("content", "")},
                "cost": previous_output.get("cost", {}),
                "tokens": previous_output.get("tokens", {}),
                "messages": previous_output.get(
                    "messages",
                    [{"content": "Context was not stored with previous output"}],
                ),
            },
        )() # Instantiate the temporary class

        # Store in session state
        if "outputs" not in st.session_state:
             st.session_state.outputs = {}
        st.session_state.outputs[section] = output

        return output
    except FileNotFoundError:
        # This exception is handled by the caller (_get_output_for_section)
        raise
    except Exception as e:
        st.error(f"Error reading previous output for {section}: {e}")
        return None


def clean_markdown_content(content: str) -> str:
    """Cleans markdown content by stripping triple backticks if present."""
    if not isinstance(content, str):
        return ""

    content = content.strip()
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[11:-3].strip()
    return content


def display_section(
    section: str,
    output: object, # Pass the retrieved/generated output object
    generate: bool = False,
    preview: bool = False,
    use_previous: bool = False, # Keep for context, but logic is in output
):
    """Displays the details for a single section."""
    expander_label = f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    with st.expander(expander_label, expanded=False):
        # Display cost/token info based on whether output exists and mode
        if output:
            if preview:
                input_cost = output.cost.get("input_cost", 0)
                input_tokens = output.tokens.get("input_tokens", 0)
                st.info(
                    f"Input cost: ${input_cost:.4f} ({input_tokens:,} tokens)"
                )
            elif generate:
                total_cost = output.cost.get("total_cost", 0)
                input_tokens = output.tokens.get("input_tokens", 0)
                output_tokens = output.tokens.get("output_tokens", 0)
                st.info(
                    f"Total cost: ${total_cost:.4f} "
                    f"(input tokens: {input_tokens:,}, "
                    f"output tokens: {output_tokens:,})"\
                )

            # Display messages if available
            if output.messages:
                with st.expander("Messages", expanded=False):
                    st.json(output.messages)
            # Merged condition logic: if output exists but has no messages OR first message has no content
            elif not output.messages or not output.messages[0].get("content", "").strip():
                st.warning(f"No context found for {section.upper()}.")


        # Display code content if generating and output exists and has content
        # Reverted check before st.code call to match original behavior
        if generate and output and output.response and output.response.get("content") is not None:
            content = clean_markdown_content(output.response["content"])
            st.code(content, language="markdown")


def add_download_button(selected_sections: list[str]):
    """Adds a download button for the combined documentation."""
    # Original logic: join cleaned content for selected sections that are in session state outputs
    combined_content = "\n\n".join(
        [
            clean_markdown_content(
                st.session_state.get("outputs", {}).get(section, {}).get("response", {}).get("content", "") # Handle nested gets gracefully
            )
            for section in selected_sections
            # Reverted condition slightly to match original more closely while keeping safety
            if section in st.session_state.get("outputs", {}) and st.session_state["outputs"].get(section) is not None
        ]
    )

    # Original code always displayed the button regardless of content, but used combined_content as data.
    st.download_button(
        label="Download docs",
        data=combined_content, # Pass potentially empty string
        file_name="docs.md",
        mime="text/markdown",
        type="primary",
    )