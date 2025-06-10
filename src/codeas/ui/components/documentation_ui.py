import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section

# Define constants for repeated literals
INCL_COLUMN_LABEL = "Incl."
SECTION_COLUMN_LABEL = "Section"
MESSAGES_EXPANDER_LABEL = "Messages"
FULL_DOC_EXPANDER_LABEL = "Full Documentation"


def display():
    # Create a list of documentation sections from SECTION_CONFIG
    doc_sections = list(SECTION_CONFIG.keys())

    # Format the section names
    formatted_sections = [
        f"{' '.join(section.split('_')).upper()}" for section in doc_sections
    ]

    # Create a dictionary for the data editor
    doc_data = {
        INCL_COLUMN_LABEL: [True] * len(doc_sections),  # Default all to True
        SECTION_COLUMN_LABEL: formatted_sections,
    }

    # Display the data editor
    edited_data = st.data_editor(
        doc_data,
        column_config={
            INCL_COLUMN_LABEL: st.column_config.CheckboxColumn(width="small"),
            SECTION_COLUMN_LABEL: st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

    # Get the selected sections
    selected_sections = [
        section
        for section, incl in zip(doc_sections, edited_data[INCL_COLUMN_LABEL])
        if incl
    ]

    use_previous_outputs = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs"
    )

    generate_docs = st.button(
        "Generate documentation", type="primary", key="generate_docs"
    )
    preview_docs = st.button("Preview", key="preview_docs")

    if generate_docs or preview_docs:
         is_generate = generate_docs
         is_preview = preview_docs
         process_sections(
             selected_sections,
             generate=is_generate,
             preview=is_preview,
             use_previous=use_previous_outputs
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
    # Removed duplicate total_input_tokens initialization
    full_documentation = ""

    expander_title = f"Sections {'[Preview]' if preview else ''}"
    with st.expander(expander_title, expanded=not use_previous):
        # Separate logic for generate vs preview to reduce complexity
        if generate:
            for section in selected_sections:
                spinner_text = f"Generating {section}..."
                with st.spinner(spinner_text):
                    output = None
                    if use_previous:
                        try:
                            output = read_output(section)
                        except FileNotFoundError:
                            output = run_generation(section)
                    else:
                        output = run_generation(section)

                    if output:
                        total_cost += output.cost.get("total_cost", 0)
                        total_input_tokens += output.tokens.get("input_tokens", 0)
                        total_output_tokens += output.tokens.get("output_tokens", 0)

                    # Display section output (relies on session_state populated by run_generation/read_output)
                    display_section(section, generate=True, output=st.session_state.outputs.get(section))

                    # Build full documentation string
                    if section in st.session_state.outputs:
                        cleaned_content = clean_markdown_content(
                            st.session_state.outputs[section].response["content"]
                        )
                        full_documentation += f"\n\n{cleaned_content}"

        elif preview:
             for section in selected_sections:
                spinner_text = f"Previewing {section}..."
                with st.spinner(spinner_text):
                    output = None
                    if use_previous:
                        try:
                            output = read_output(section) # read_output populates session_state
                        except FileNotFoundError:
                            output = run_preview(section)
                    else:
                        output = run_preview(section)

                    if output:
                         total_input_cost += output.cost.get("input_cost", 0)
                         # Note: Original added input tokens in both generate and preview paths
                         total_input_tokens += output.tokens.get("input_tokens", 0)

                    # Display section output (pass the output obtained)
                    display_section(section, preview=True, output=output)


    # Display totals after the loop
    if generate:
        # Removed trailing backslash
        st.info(
            f"Total cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"
        )
        # This check was inside the loop in original, moved outside
        if not use_previous:
             usage_tracker.record_usage("generate_docs", total_cost)
    elif preview:
        st.info(
            f"Total input cost: ${total_input_cost:.4f} ({total_input_tokens:,} tokens)"
        )

    # Display full documentation if generated
    if full_documentation:
        with st.expander(FULL_DOC_EXPANDER_LABEL, expanded=True):
            # clean_markdown_content was called on the combined string in original, keep that
            full_documentation = clean_markdown_content(full_documentation)
            st.markdown(full_documentation)

    # Add download button if relevant outputs exist
    if generate or (
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        add_download_button(selected_sections)


def run_generation(section: str):
    # Run preview first to check context availability
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )

    if preview_output and preview_output.messages and preview_output.messages[0].get("content", "").strip():
        # If context exists, run full generation
        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        st.session_state.outputs[section] = output
        # State write_output expects a dict, not the raw output object
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
    # Create a simple object to mimic the structure expected by display/processing logic
    # Use a class or namedtuple for clarity instead of type()
    class Output:
        def __init__(self, content, cost, tokens, messages):
            self.response = {"content": content}
            self.cost = cost
            self.tokens = tokens
            self.messages = messages # Use stored messages

    output = Output(
        previous_output["content"],
        previous_output["cost"],
        previous_output["tokens"],
        previous_output.get(
            "messages",
            [{"content": "Context was not stored with previous output"}],
        ),
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
    output=None, # Accept the output object directly
):
    expander_label = f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"

    # Determine the output to display - prefer passed output, fallback to session state for generated
    output_to_display = output if output is not None else st.session_state.outputs.get(section)

    with st.expander(expander_label, expanded=False):
        if output_to_display:
            # Display cost info
            if preview:
                 st.info(
                     f"Input cost: ${output_to_display.cost.get('input_cost', 0):.4f} ({output_to_display.tokens.get('input_tokens', 0):,} tokens)"
                 )
            elif generate:
                 # Removed trailing backslash
                 st.info(
                     f"Total cost: ${output_to_display.cost.get('total_cost', 0):.4f} "
                     f"(input tokens: {output_to_display.tokens.get('input_tokens', 0):,}, "
                     f"output tokens: {output_to_display.tokens.get('output_tokens', 0):,})"
                 )

            # Display messages
            with st.expander(MESSAGES_EXPANDER_LABEL, expanded=False):
                st.json(output_to_display.messages)
            # Check for empty messages content
            if not output_to_display.messages or not output_to_display.messages[0].get("content", "").strip():
                 st.warning(f"No context found for {section.upper()}.")

            # Display content if generating
            if generate:
                content = output_to_display.response.get("content", "") # Use .get for safety
                content = clean_markdown_content(content)
                st.code(content, language="markdown")
        else:
             # Handle case where no output was available to display
             action = "generation" if generate else "preview"
             st.warning(f"No output available to display for {section.upper()}. {action.capitalize()} might have failed or found no context.")


def add_download_button(selected_sections: list[str]):
    # Filter for sections actually present in session_state.outputs
    available_outputs = [
        st.session_state.outputs[section]
        for section in selected_sections
        if section in st.session_state.outputs
    ]

    combined_content = "\n\n".join(
        [clean_markdown_content(output.response.get("content", "")) for output in available_outputs] # Use .get for safety
    )

    # Only show button if there is content to download
    if combined_content:
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
        )