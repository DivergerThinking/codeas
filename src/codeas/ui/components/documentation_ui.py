import streamlit as st

from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker
from codeas.use_cases.documentation import SECTION_CONFIG, generate_docs_section


def display():
    doc_sections = list(SECTION_CONFIG.keys())

    formatted_sections = [
        f"{' '.join(section.split('_')).upper()}" for section in doc_sections
    ]

    doc_data = {
        "Incl.": [True] * len(doc_sections),
        "Section": formatted_sections,
    }

    st.data_editor(
        doc_data,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width="small"),
            "Section": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

    selected_sections = [
        section for section, incl in zip(doc_sections, st.session_state["doc_sections_editor"]["Incl."]) if incl
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
                output = None
                if generate:
                    if use_previous:
                        try:
                            output = read_output(section)
                        except FileNotFoundError:
                            output = run_generation(section)
                    else:
                        output = run_generation(section)
                    if output:
                        if hasattr(output, 'cost') and isinstance(output.cost, dict) and 'total_cost' in output.cost:
                             total_cost += output.cost["total_cost"]
                        if hasattr(output, 'tokens') and isinstance(output.tokens, dict):
                            if 'input_tokens' in output.tokens:
                                total_input_tokens += output.tokens["input_tokens"]
                            if 'output_tokens' in output.tokens:
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
                        if hasattr(output, 'cost') and isinstance(output.cost, dict) and 'input_cost' in output.cost:
                            total_input_cost += output.cost["input_cost"]
                        if hasattr(output, 'tokens') and isinstance(output.tokens, dict) and 'input_tokens' in output.tokens:
                             total_input_tokens += output.tokens["input_tokens"]

                display_section(section, generate, preview, section_output=output)

                if not preview and section in st.session_state.outputs and \
                   hasattr(st.session_state.outputs[section], 'response') and \
                   isinstance(st.session_state.outputs[section].response, dict) and \
                   'content' in st.session_state.outputs[section].response:
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

    if generate and full_documentation.strip():
        with st.expander("Full Documentation", expanded=True):
            full_documentation = clean_markdown_content(full_documentation)
            st.markdown(full_documentation)
    elif generate and not full_documentation.strip() and selected_sections:
         st.info("No documentation generated for the selected sections.")


    if generate or (
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        add_download_button(selected_sections)
    elif not generate and not preview and selected_sections:
         st.info("Select 'Generate documentation' to create content or 'Preview' to see context.")


def run_generation(section: str):
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    if preview_output and hasattr(preview_output, 'messages') and isinstance(preview_output.messages, list) and \
       len(preview_output.messages) > 0 and isinstance(preview_output.messages[0], dict) and \
       preview_output.messages[0].get("content", "").strip():

        output = generate_docs_section(
            state.llm_client,
            section,
            state.repo,
            state.repo_metadata,
            preview=False,
        )
        st.session_state.outputs[section] = output
        if hasattr(output, 'response') and hasattr(output.response, 'content') and \
           hasattr(output, 'cost') and hasattr(output, 'tokens') and hasattr(output, 'messages'):
            try:
                state.write_output(
                    {
                        "content": output.response["content"],
                        "cost": output.cost,
                        "tokens": output.tokens,
                        "messages": output.messages,
                    },
                    f"{section}.json",
                )
            except Exception as e:
                 st.error(f"Error writing output for {section.upper()}: {e}")
            return output
        else:
             st.warning(f"Generated output for {section.upper()} is missing expected attributes (response, cost, tokens, messages). Not writing to file.")
             return output
    else:
        st.warning(f"No context found or preview failed for {section.upper()}. Skipping generation.")
        return None


def run_preview(section: str):
    return generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )


def read_output(section: str):
    try:
        previous_output = state.read_output(f"{section}.json")
        if not isinstance(previous_output, dict):
             st.error(f"Previous output for {section} is not a dictionary.")
             raise FileNotFoundError(f"Invalid data format for {section}.json")

        if "content" not in previous_output or "cost" not in previous_output or "tokens" not in previous_output:
             st.error(f"Previous output for {section} is missing required keys.")
             raise FileNotFoundError(f"Missing data in {section}.json")

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
        )()
        st.session_state.outputs[section] = output
        return output
    except FileNotFoundError:
         raise
    except Exception as e:
         st.error(f"Error reading previous output for {section}: {e}")
         raise


def clean_markdown_content(content: str) -> str:
    if not isinstance(content, str):
        return ""
    content = content.strip()
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[len("```markdown"):-len("```")].strip()
    return content


def _display_section_cost(output, generate: bool, preview: bool):
    if preview:
        input_cost = output.cost.get('input_cost') if hasattr(output, 'cost') and isinstance(output.cost, dict) else None
        input_tokens = output.tokens.get('input_tokens') if hasattr(output, 'tokens') and isinstance(output.tokens, dict) else None
        if input_cost is not None and input_tokens is not None:
             st.info(
                 f"Input cost: ${input_cost:.4f} ({input_tokens:,} tokens)"
             )
        else:
             st.info("Input cost information not available.")
    elif generate:
        total_cost = output.cost.get('total_cost') if hasattr(output, 'cost') and isinstance(output.cost, dict) else None
        input_tokens = output.tokens.get('input_tokens') if hasattr(output, 'tokens') and isinstance(output.tokens, dict) else None
        output_tokens = output.tokens.get('output_tokens') if hasattr(output, 'tokens') and isinstance(output.tokens, dict) else None
        if total_cost is not None and input_tokens is not None and output_tokens is not None:
             st.info(
                 f"Total cost: ${total_cost:.4f} "
                 f"(input tokens: {input_tokens:,}, "
                 f"output tokens: {output_tokens:,})")
        else:
             st.info("Total cost information not available.")


def _display_section_messages_and_context(output, section: str):
    with st.expander("Messages", expanded=False):
        messages = getattr(output, 'messages', None)
        if messages and isinstance(messages, list):
            st.json(messages)
        else:
            st.info("No messages available.")

    messages = getattr(output, 'messages', None)
    first_message_content = ""
    if messages and isinstance(messages, list) and len(messages) > 0 and isinstance(messages[0], dict):
         first_message_content = messages[0].get("content", "")

    if not messages or not first_message_content.strip():
        st.warning(f"No context or meaningful response found for {section.upper()}.")


def _display_section_content(output, generate: bool):
    if generate and hasattr(output, 'response') and isinstance(output.response, dict) and 'content' in output.response:
        content = output.response["content"]
        content = clean_markdown_content(content)
        st.code(content, language="markdown")
    elif generate:
         st.info("Generated content is not available in the expected format.")


def display_section(
    section: str,
    generate: bool = False,
    preview: bool = False,
    section_output=None,
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )

    output = section_output

    with st.expander(expander_label, expanded=False):
        if output:
            _display_section_cost(output, generate, preview)
            _display_section_messages_and_context(output, section)
            _display_section_content(output, generate)
        else:
            st.info(f"No output available for {section.upper()}.")


def add_download_button(selected_sections: list[str]):
    combined_content = "\n\n".join(
        [
            clean_markdown_content(
                st.session_state.outputs[section].response["content"]
            )
            for section in selected_sections
            if section in st.session_state.outputs and \
               hasattr(st.session_state.outputs[section], 'response') and \
               isinstance(st.session_state.outputs[section].response, dict) and \
               'content' in st.session_state.outputs[section].response
        ]
    )

    if combined_content.strip():
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
        )
    else:
        st.info("Generate some documentation to enable the download button.")