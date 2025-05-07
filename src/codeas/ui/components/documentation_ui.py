import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section
import json # Import json for reading output


# Define constants
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


def _get_section_output(section: str, generate: bool, preview: bool, use_previous: bool):
    """Helper to get output for a section, either by reading previous or running."""
    output = None
    task_func = run_generation if generate else run_preview
    read_func = read_output

    if use_previous:
        try:
            output = read_func(section)
            # Special handling: if previous output is empty/invalid for the current task, force a run
            if output and not output.response.get("content", "").strip():
                 st.warning(f"Previous output for {section.upper()} is empty. Forcing a new run.")
                 output = task_func(section) # This run updates state/file if it's run_generation
        except FileNotFoundError:
            # File not found, run the task
            output = task_func(section) # This run updates state/file if it's run_generation
    else:
        # Not using previous, always run
        output = task_func(section) # This run updates state/file if it's run_generation

    # If run_preview was called and it's not handled internally, update state
    # run_generation updates state internally. read_output updates state internally.
    # run_preview just returns output but doesn't update state.
    # So if task_func was run_preview AND output is not None, update state.
    if not generate and output is not None: # If it was preview
         st.session_state.outputs[section] = output # Update state manually for preview runs

    return output


def process_sections(
    selected_sections: list[str],
    generate: bool = False,
    preview: bool = False,
    use_previous: bool = False,
):
    total_generate_cost = 0
    total_generate_input_tokens = 0
    total_generate_output_tokens = 0
    total_preview_input_cost = 0
    total_preview_input_tokens = 0
    full_documentation = ""

    # Extract nested conditional expression
    action_verb = 'Generating' if generate else ('Previewing' if preview else 'Displaying')

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            with st.spinner(f"{action_verb} {section}..."):
                output = _get_section_output(section, generate, preview, use_previous)

                # Accumulate costs/tokens
                if output:
                    if generate:
                        if "cost" in output and "total_cost" in output.cost:
                            total_generate_cost += output.cost["total_cost"]
                        if "tokens" in output:
                            if "input_tokens" in output.tokens:
                                total_generate_input_tokens += output.tokens["input_tokens"]
                            if "output_tokens" in output.tokens:
                                total_generate_output_tokens += output.tokens["output_tokens"]
                    elif preview:
                        if "cost" in output and "input_cost" in output.cost:
                            total_preview_input_cost += output.cost["input_cost"]
                        if "tokens" in output and "input_tokens" in output.tokens:
                            total_preview_input_tokens += output.tokens["input_tokens"]


                # Display the section details using the retrieved output
                display_section(section, generate, preview, output)

                # Aggregate full documentation content if generating and output exists
                if generate and output and section in st.session_state.outputs:
                    # Content is cleaned in display_section, but aggregation uses session_state directly.
                    # Clean here before appending to ensure consistency.
                    cleaned_content = clean_markdown_content(st.session_state.outputs[section].response["content"])
                    full_documentation += f"\n\n{cleaned_content}"


    # Display summaries outside the loop
    if generate:
        st.info(
            f"Total cost: ${total_generate_cost:.4f} "
            f"(input tokens: {total_generate_input_tokens:,}, "
            f"output tokens: {total_generate_output_tokens:,})"\n        )
        if not use_previous:
             usage_tracker.record_usage("generate_docs", total_generate_cost)
    elif preview:
        st.info(
            f"Total input cost: ${total_preview_input_cost:.4f} ({total_preview_input_tokens:,} tokens)"\n        )

    # Display full documentation if aggregated
    if full_documentation:
         with st.expander("Full Documentation", expanded=True):
            # full_documentation already contains cleaned content from aggregation step
            st.markdown(full_documentation)

    # Add download button based on conditions
    if generate or (\n        not preview\n        and any(section in st.session_state.outputs for section in selected_sections)\n    ):
        add_download_button(selected_sections)


def run_generation(section: str):
    # This function remains largely the same, it handles preview check before full run
    # and updates session state and writes output if successful.
    preview_output = generate_docs_section(
        state.llm_client,\n        section,\n        state.repo,\n        state.repo_metadata,\n        preview=True,\n    )
    if preview_output.messages and preview_output.messages[0]["content"].strip():
        output = generate_docs_section(
            state.llm_client,\n            section,\n            state.repo,\n            state.repo_metadata,\n            preview=False,\n        )
        st.session_state.outputs[section] = output
        state.write_output(
            {\n                "content": output.response["content"],\n                "cost": output.cost,\n                "tokens": output.tokens,\n                "messages": output.messages,\n            },\n            f"{section}.json",
        )
        return output
    else:
        st.warning(f"No context found for {section.upper()}. Skipping generation.")
        return None  # Return None if no generation occurred


def run_preview(section: str):
    # This function remains the same. It does not update state or write files.
    return generate_docs_section(
        state.llm_client,\n        section,\n        state.repo,\n        state.repo_metadata,\n        preview=True,\n    )


def read_output(section: str):
    # This function remains the same. It reads from file and updates session state.
    previous_output_data = state.read_output(f"{section}.json")
    # Construct a simple object similar to the expected Output structure
    class Output:
        def __init__(self, data):
            self.response = {"content": data.get("content", "")}
            self.cost = data.get("cost", {})
            self.tokens = data.get("tokens", {})
            self.messages = data.get(
                "messages",
                [{"content": "Context was not stored with previous output"}],
            ) # Use stored messages if available

    output = Output(previous_output_data)
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
    output = None, # Accept output object directly
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )
    with st.expander(expander_label, expanded=False):
        # Removed duplicate logic for reading/running output. Assumes output is passed.
        if output: # Check if output was provided
            if preview:
                # Display preview cost using provided output
                if "cost" in output and "input_cost" in output.cost and "tokens" in output and "input_tokens" in output.tokens:
                     st.info(
                        f"Input cost: ${output.cost['input_cost']:.4f} ({output.tokens['input_tokens']:,} tokens)"
                     )
            elif generate:
                 # Display generation cost using provided output
                if "cost" in output and "total_cost" in output.cost and "tokens" in output and "input_tokens" in output.tokens and "output_tokens" in output.tokens:
                    st.info(
                        f"Total cost: ${output.cost['total_cost']:.4f} "
                        f"(input tokens: {output.tokens['input_tokens']:,}, "
                        f"output tokens: {output.tokens['output_tokens']:,})"\n                    )

            # Display messages expander if output is available
            with st.expander("Messages", expanded=False):
                 # Handle case where messages might not exist or be empty list
                 if output.messages:
                    st.json(output.messages)
                 else:
                     st.info("No messages available.") # Or st.write, depending on desired UI

            # Merge S1066: Check for empty/blank content *only if* output and messages exist.
            # If output exists and (no messages OR first message content is blank)
            if output and (not output.messages or not output.messages[0].get("content", "").strip()):
                 st.warning(f"No context found for {section.upper()}.\n")


            # Display content as code block if generating AND output is available
            if generate:
                 if output and output.response and "content" in output.response:
                     content = output.response["content"]
                     content = clean_markdown_content(content)
                     st.code(content, language="markdown")


def add_download_button(selected_sections: list[str]):
    # This function remains the same, relies on session state being populated.
    combined_content = "\n\n".join(
        [\n            clean_markdown_content(\n                st.session_state.outputs[section].response["content"]\n            )\n            for section in selected_sections\n            if section in st.session_state.outputs
        ]\n    )

    if combined_content.strip(): # Only show download button if there's content
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
        )
    else:
        st.info("Generate some content first to enable download.") # Optional: provide feedback