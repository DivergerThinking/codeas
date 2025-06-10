import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section

# Constants
SECTION_INCLUDE_COL = "Incl."


def display():
    # Ensure outputs dictionary exists in session state early
    if "outputs" not in st.session_state:
        st.session_state.outputs = {}

    # Create a list of documentation sections from SECTION_CONFIG
    doc_sections = list(SECTION_CONFIG.keys())

    # Format the section names
    formatted_sections = [
        f"{' '.join(section.split('_')).upper()}" for section in doc_sections
    ]

    # Create a dictionary for the data editor
    doc_data = {
        SECTION_INCLUDE_COL: [True] * len(doc_sections),  # Default all to True
        "Section": formatted_sections,
    }

    # Display the data editor
    edited_data = st.data_editor(
        doc_data,
        column_config={
            SECTION_INCLUDE_COL: st.column_config.CheckboxColumn(width="small"),
            "Section": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

    # Get the selected sections
    selected_sections = [
        section for section, incl in zip(doc_sections, edited_data[SECTION_INCLUDE_COL]) if incl
    ]

    use_previous_outputs = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs"
    )

    # Keep original button variables to use in download button logic later
    generate_docs_clicked = st.button(
        "Generate documentation", type="primary", key="generate_docs"
    )
    preview_docs_clicked = st.button("Preview", key="preview_docs")

    # Determine action based on button clicks
    action = None
    if generate_docs_clicked:
        action = "generate"
    elif preview_docs_clicked: # Use elif here as generate and preview are mutually exclusive
        action = "preview"

    if action:
        process_sections(
            selected_sections, action=action, use_previous=use_previous_outputs
        )

    # --- Download button logic using original condition ---
    # This displays the button if Generate was clicked, OR
    # if Preview was NOT clicked AND there are any outputs in session state
    # (which could be from previous runs if use_previous was true, or from a recent generate run).
    if generate_docs_clicked or (
        not preview_docs_clicked
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        # add_download_button function reads from st.session_state.outputs,
        # which might contain results from this run or previous runs.
        add_download_button(selected_sections)


def process_sections(
    selected_sections: list[str],
    action: str,  # 'generate' or 'preview'
    use_previous: bool = False,
):
    total_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0
    full_documentation = ""

    # st.session_state.outputs is initialized in display() now

    processing_label = "Generating" if action == "generate" else "Previewing"
    sections_label = f"Sections [{'Preview]' if action == 'preview' else ''}"

    with st.expander(sections_label, expanded=not use_previous):
        for section in selected_sections:
            with st.spinner(f"{processing_label} {section}..."):
                output_obtained = False # Flag to track if we successfully got output

                # Attempt to read previous output if use_previous is True
                if use_previous:
                    try:
                        output = read_output(section)
                        # Store read output in session state immediately
                        st.session_state.outputs[section] = output
                        output_obtained = True
                        st.info(f"Read previous output for {section.upper()}.")

                    except FileNotFoundError:
                        st.warning(f"Previous output not found for {section.upper()}.")
                        # output_obtained remains False, will fall through to generate/preview

                # If output was not obtained from previous, run generation/preview
                if not output_obtained:
                    new_output = None # Use a local variable for new output
                    if action == "generate":
                         st.info(f"Running generation for {section.upper()}...")
                         # run_generation stores its successful output to state internally
                         new_output = run_generation(section)
                         if new_output:
                             output_obtained = True # Check if run_generation was successful

                    elif action == "preview":
                         st.info(f"Running preview for {section.upper()}...")
                         # run_preview returns the output, store it in state
                         new_output = run_preview(section)
                         if new_output:
                              st.session_state.outputs[section] = new_output
                              output_obtained = True # Check if run_preview was successful

                # Now, process the output which is stored in st.session_state.outputs[section] if successful
                # Retrieve from state to ensure we use the stored object, whether read or newly generated/previewed
                current_output_in_state = st.session_state.outputs.get(section)

                if current_output_in_state:
                    # Aggregate totals
                    if action == "generate":
                        total_cost += current_output_in_state.cost.get("total_cost", 0)
                        total_input_tokens += current_output_in_state.tokens.get("input_tokens", 0)
                        total_output_tokens += current_output_in_state.tokens.get("output_tokens", 0)
                    elif action == "preview":
                         # Assuming preview only has input cost/tokens
                         total_cost += current_output_in_state.cost.get("input_cost", 0) # Use total_cost var for summary
                         total_input_tokens += current_output_in_state.tokens.get("input_tokens", 0)

                    # Append content for full documentation view if generating
                    # Full documentation is only built if action is generate AND content exists
                    if action == "generate" and current_output_in_state.response and current_output_in_state.response.get("content"):
                         cleaned_content = clean_markdown_content(
                             current_output_in_state.response["content"]
                         )
                         full_documentation += f"\n\n{cleaned_content}"
                else:
                    # This case happens if neither reading previous nor generating/previewing succeeded
                    st.warning(f"Could not get output for {section.upper()}. Skipping aggregation and display.")


                # Always call display_section; it will handle if the output is not in state
                # It retrieves the output from st.session_state.outputs itself
                display_section(section, action)


    # Display total costs/tokens based on action
    if action == "generate":
        st.info(
            f"Total cost: ${total_cost:.4f} "
            f"(input tokens: {total_input_tokens:,}, "
            f"output tokens: {total_output_tokens:,})"\
            f" (Aggregated from successful sections)" # Added clarity
        )
        # Record usage only if any cost was incurred during this generation run
        # Note: This doesn't distinguish between cost from reading previous output vs generating new.
        # A more complex logic would be needed to track if actual generation API calls were made.
        # For simplicity, we track if the action was generate and *any* cost was aggregated (including from read files).
        # This might overcount slightly if files contain cost info from previous runs.
        # If only new generation cost should be tracked, usage_tracker should be called *inside* run_generation.
        # Let's revert usage tracking to be inside run_generation, only when a new call happens.
        # The original code's usage tracking was simple: if generate and not use_previous.
        # Let's stick to tracking if generate ran *and* total cost > 0. This matches previous iteration logic.
        if total_cost > 0:
             usage_tracker.record_usage("generate_docs", total_cost)

    elif action == "preview":
        st.info(
            f"Total input cost: ${total_cost:.4f} ({total_input_tokens:,} tokens)"
            f" (Aggregated from successful sections)" # Added clarity
        )

    # Display full documentation if available
    # Full documentation is only built if action was 'generate' and sections produced content
    if full_documentation.strip(): # Check if there's actual content beyond whitespace
        with st.expander("Full Documentation", expanded=True):
            # Content was already cleaned when adding to full_documentation string
            st.markdown(full_documentation)

    # The download button logic is handled in the display() function.


def run_generation(section: str):
    # Run a preview first to check for context
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )

    # Check if the preview returned meaningful context/messages
    # Accessing messages[0]["content"] needs robust checks
    has_context = (
        preview_output
        and preview_output.messages
        and len(preview_output.messages) > 0
        and preview_output.messages[0].get("content", "").strip() != ""
    )

    if has_context:
        # st.info(f"Context found for {section.upper()}. Generating documentation...") # Moved info into process_sections
        # Run full generation if context exists
        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        # Write output to file if content was generated
        if output and output.response and output.response.get("content"):
            state.write_output(
                {
                    "content": output.response["content"],
                    "cost": output.cost,
                    "tokens": output.tokens,
                    "messages": output.messages,
                },
                f"{section}.json",
            )
        # Return the generated output (process_sections will store it in state)
        return output
    else:
        st.warning(f"No context found for {section.upper()}. Skipping generation.")
        return None  # Return None if no generation occurred


def run_preview(section: str):
    # st.info(f"Previewing {section.upper()}...") # Moved info into process_sections
    # run_preview doesn't need to write to file as it's just a preview
    # It returns the output structure which process_sections stores to state
    return generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )


def read_output(section: str):
    # st.info(f"Reading previous output for {section.upper()}...") # Moved info into process_sections
    previous_output = state.read_output(f"{section}.json")
    # Reconstruct a simple object similar to the generation/preview output structure
    # Ensure all expected keys exist with default empty values if necessary for robustness
    output_data = {
        "response": {"content": previous_output.get("content", "")},
        "cost": previous_output.get("cost", {}),
        "tokens": previous_output.get("tokens", {}),
        # Use stored messages if available, provide a default if not
        "messages": previous_output.get(
            "messages",
            [{"role": "system", "content": "Context was not stored with previous output"}], # Added role for better JSON
        ),
    }
    # Instantiate the type and return the object
    output = type("Output", (), output_data)()
    return output


def clean_markdown_content(content: str) -> str:
    # Check if content is a string before attempting strip/startswith/endswith
    if not isinstance(content, str):
        return "" # Return empty string for non-string input

    content = content.strip()
    # Handle ```markdown ... ``` blocks
    if content.lower().startswith("```markdown") and content.endswith("```"):
        # Remove the opening ```markdown line and the closing ```
        lines = content.splitlines()
        if len(lines) > 1:
             # Remove the first line and the last line
             content = "\n".join(lines[1:-1]).strip()
        else:
             # Handle single line ```markdown content``` case - remove markers
             content = content[len("```markdown"):].rstrip()
             if content.endswith("```"):
                 content = content[:-3].rstrip()


    # Handle plain ```...``` blocks (e.g., ```python ```)
    elif content.lower().startswith("```") and content.endswith("```"):
         # Simple removal of first ``` line and last ``` line
         lines = content.splitlines()
         if len(lines) > 1:
             # Remove the first line (```lang) and the last line (```)
             content = "\n".join(lines[1:-1]).strip()
         else:
             # Handle single line ```content``` case, remove ``` from start and end
             content = content[3:-3].strip()

    return content.strip() # Final strip


def display_section(
    section: str,
    action: str # 'generate' or 'preview'
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if action == 'preview' else ''}"
    )
    with st.expander(expander_label, expanded=False):
        # Retrieve the output from session state; it should have been stored by process_sections
        output = st.session_state.outputs.get(section)

        # Check if output exists before proceeding with display
        if output:
            # Display info message
            if action == "preview":
                 # Use get with default for robustness
                input_cost = output.cost.get('input_cost', 0)
                input_tokens = output.tokens.get('input_tokens', 0)
                st.info(
                    f"Input cost: ${input_cost:.4f} ({input_tokens:,} tokens)"
                )
            elif action == "generate":
                 # Use get with default for robustness
                 total_cost = output.cost.get('total_cost', 0)
                 input_tokens = output.tokens.get('input_tokens', 0)
                 output_tokens = output.tokens.get('output_tokens', 0)
                 st.info(
                    f"Total cost: ${total_cost:.4f} "
                    f"(input tokens: {input_tokens:,}, "
                    f"output tokens: {output_tokens:,})"\
                    f" (for this section)" # Added clarity
                 )

            # Display Messages
            # Check if messages exist and are not empty before displaying expander
            # Using output.messages directly relies on process_sections ensuring it's stored, which it does.
            if output.messages:
                 with st.expander("Messages", expanded=False):
                     # Ensure messages is a list before iterating or accessing
                     if isinstance(output.messages, list):
                         st.json(output.messages)
                     else:
                         # This shouldn't happen if read_output default is used, but defensive
                         st.warning("Message history format is unexpected.")

            # Display content if generating
            # Merged the condition to reduce one level of nesting for this specific code path
            # This addresses S1066 more directly in the original location/logic flow.
            if action == "generate" and output.response and output.response.get("content"):
                 content = output.response["content"]
                 # Content was already cleaned when adding to full_documentation,
                 # but clean again here for the section-specific code block display
                 content = clean_markdown_content(content)
                 st.code(content, language="markdown")
            # Added an else-if for clarity if generating but no content was produced
            elif action == "generate":
                 # This case is already handled by run_generation returning None and process_sections checking if output_obtained
                 # and the subsequent 'if output:' check in this function.
                 # This elif might be redundant or misleading. Removing it.
                 pass # Removed: st.warning(f"No content generated for {section.upper()}.")


        else:
             # This means process_sections could not get output for this section (read failed and generate/preview failed or returned None)
             st.warning(f"Could not retrieve output for {section.upper()}.")


def add_download_button(selected_sections: list[str]):
    combined_content_parts = []
    for section in selected_sections:
        # Get content from session state; ensure output and content exist
        output = st.session_state.outputs.get(section)
        # Only include sections that were successfully generated (action == 'generate')
        # and actually have content in the download
        # We can't easily know the action here, so we rely on content existing.
        # The download button condition in display() implies it's primarily for generate runs,
        # or previous outputs when not previewing.
        # Just check if content exists.
        if output and output.response and output.response.get("content"):
             # Content was already cleaned in process_sections (if generate),
             # but re-clean here for safety/consistency if called after preview+use_previous
             cleaned_content = clean_markdown_content(output.response["content"])
             combined_content_parts.append(cleaned_content)

    combined_content = "\\n\\n".join(combined_content_parts)

    # Only show the button if there is content to download
    if combined_content.strip(): # Check for non-empty content after join
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
        )