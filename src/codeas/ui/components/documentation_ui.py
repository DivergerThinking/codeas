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
    total_generate_cost = 0
    total_generate_input_tokens = 0
    total_generate_output_tokens = 0
    total_preview_input_cost = 0
    total_preview_input_tokens = 0

    if 'outputs' not in st.session_state:
        st.session_state.outputs = {}

    full_documentation = ""

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            output = None
            with st.spinner(
                f"{'Generating' if generate else 'Previewing' if preview else 'Displaying'} {section.replace('_', ' ').upper()}..."
            ):
                if generate:
                    if use_previous:
                        try:
                            output = read_output(section)
                        except FileNotFoundError:
                             try:
                                output = run_generation(section)
                             except Exception as e:
                                 st.error(f"Error generating {section.replace('_', ' ').upper()}: {e}")
                                 output = None
                                 st.session_state.outputs.pop(section, None)
                    else:
                        try:
                            output = run_generation(section)
                        except Exception as e:
                             st.error(f"Error generating {section.replace('_', ' ').upper()}: {e}")
                             output = None
                             st.session_state.outputs.pop(section, None)


                    if output and hasattr(output, 'cost') and hasattr(output, 'tokens'):
                         total_generate_cost += output.cost.get("total_cost", 0)
                         total_generate_input_tokens += output.tokens.get("input_tokens", 0)
                         total_generate_output_tokens += output.tokens.get("output_tokens", 0)

                elif preview:
                    if use_previous:
                        try:
                            output = read_output(section)
                            if output and hasattr(output, 'cost') and hasattr(output, 'tokens'):
                                total_preview_input_cost += output.cost.get("input_cost", 0)
                                total_preview_input_tokens += output.tokens.get("input_tokens", 0)
                        except FileNotFoundError:
                            try:
                                output = run_preview(section)
                                if output:
                                    st.session_state.outputs[section] = output
                                if output and hasattr(output, 'cost') and hasattr(output, 'tokens'):
                                    total_preview_input_cost += output.cost.get("input_cost", 0)
                                    total_preview_input_tokens += output.tokens.get("input_tokens", 0)
                            except Exception as e:
                                st.error(f"Error previewing {section.replace('_', ' ').upper()}: {e}")
                                output = None
                                st.session_state.outputs.pop(section, None)

                    else:
                        try:
                            output = run_preview(section)
                            if output:
                                st.session_state.outputs[section] = output
                            if output and hasattr(output, 'cost') and hasattr(output, 'tokens'):
                                total_preview_input_cost += output.cost.get("input_cost", 0)
                                total_preview_input_tokens += output.tokens.get("input_tokens", 0)
                        except Exception as e:
                            st.error(f"Error previewing {section.replace('_', ' ').upper()}: {e}")
                            output = None
                            st.session_state.outputs.pop(section, None)


            display_section(section, generate, preview)

            if generate and section in st.session_state.outputs:
                output_for_doc = st.session_state.outputs[section]
                content_for_doc = getattr(getattr(output_for_doc, 'response', None), 'content', None)
                if content_for_doc:
                     cleaned_content = clean_markdown_content(content_for_doc)
                     full_documentation += f"\n\n{cleaned_content}"


    if generate:
        st.info(
            f"Total cost: ${total_generate_cost:.4f} "
            f"(input tokens: {total_generate_input_tokens:,}, "
            f"output tokens: {total_generate_output_tokens:,})"
        )
        if not use_previous:
            if total_generate_cost > 0:
                 usage_tracker.record_usage("generate_docs", total_generate_cost)
            else:
                 st.warning("No generation cost recorded as all sections failed or were skipped.")

    elif preview:
        st.info(
            f"Total input cost: ${total_preview_input_cost:.4f} ({total_preview_input_tokens:,} tokens)"
        )


    if full_documentation.strip():
        with st.expander("Full Documentation", expanded=True):
            st.markdown(full_documentation)
    elif generate:
         st.info("No full documentation could be compiled.")


    if full_documentation.strip():
        add_download_button(selected_sections)


def run_generation(section: str):
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    has_context = preview_output and \
                  hasattr(preview_output, 'messages') and \
                  isinstance(preview_output.messages, list) and \
                  len(preview_output.messages) > 0 and \
                  preview_output.messages[0].get("content") is not None and \
                  preview_output.messages[0]["content"].strip() != ""

    if has_context:
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
                "content": getattr(getattr(output, 'response', None), 'content', None),
                "cost": getattr(output, 'cost', {}),
                "tokens": getattr(output, 'tokens', {}),
                "messages": getattr(output, 'messages', []),
            },
            f"{section}.json",
        )
        return output
    else:
        st.warning(f"No context found for {section.upper()}. Skipping generation.")
        st.session_state.outputs.pop(section, None)
        return None


def run_preview(section: str):
    output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    if output:
        return output
    else:
         st.warning(f"Preview generation returned no output for {section.upper()}.")
         return None


def read_output(section: str):
    previous_output = state.read_output(f"{section}.json")

    if not previous_output:
        st.warning(f"Previous output file found but was empty or invalid for {section.upper()}.")
        raise FileNotFoundError(f"Invalid or empty previous output for {section}")

    output = type(
        "Output",
        (),
        {
            "response": {"content": previous_output.get("content", "")},
            "cost": previous_output.get("cost", {}),
            "tokens": previous_output.get("tokens", {}),
            "messages": previous_output.get(
                "messages",
                [{"content": "Context was not stored with previous output"}] if previous_output.get("content") else []
            ),
        },
    )()
    st.session_state.outputs[section] = output
    return output


def clean_markdown_content(content: str) -> str:
    if content is None:
        return ""
    content_str = str(content).strip()
    if content_str.startswith("```markdown") and content_str.endswith("```"):
        content_str = content_str[11:-3].strip()
    return content_str


def _display_section_costs(output, generate, preview):
    if output and hasattr(output, 'cost') and hasattr(output, 'tokens'):
        if preview:
             st.info(
                f"Input cost: ${output.cost.get('input_cost', 0):.4f} ({output.tokens.get('input_tokens', 0):,} tokens)"
             )
        elif generate:
            st.info(
                f"Total cost: ${output.cost.get('total_cost', 0):.4f} "
                f"(input tokens: {output.tokens.get('input_tokens', 0):,}, "
                f"output tokens: {output.tokens.get('output_tokens', 0):,})"
            )

def _display_section_messages(output, section_name):
    if output and hasattr(output, 'messages') and isinstance(output.messages, list):
        messages = output.messages
        if messages:
            with st.expander("Messages", expanded=False):
                try:
                    st.json(messages)
                except Exception:
                     st.warning("Could not display messages.")

        if not messages or (len(messages) > 0 and messages[0].get("content") is not None and not messages[0]["content"].strip()):
             st.warning(f"No context found for {section_name.upper()}.")


def _display_section_content(output, generate):
    if generate and output and hasattr(output, 'response') and isinstance(output.response, dict) and output.response.get('content') is not None:
        content = output.response['content']
        if content:
            cleaned_content = clean_markdown_content(content)
            if cleaned_content.strip():
                 st.code(cleaned_content, language="markdown")
            else:
                 st.info("Generated content was empty after cleanup.")


def display_section(
    section: str,
    generate: bool = False,
    preview: bool = False,
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )
    with st.expander(expander_label, expanded=False):
        output = st.session_state.outputs.get(section)

        if output is None:
             if generate or preview:
                  st.info(f"No output available for {section.replace('_', ' ').upper()}.")
             return

        _display_section_costs(output, generate, preview)
        _display_section_messages(output, section)
        _display_section_content(output, generate)


def add_download_button(selected_sections: list[str]):
    section_contents = []
    for section in selected_sections:
        output = st.session_state.outputs.get(section)
        if output and hasattr(output, 'response') and isinstance(output.response, dict):
            content = output.response.get('content')
            if content is not None:
                 cleaned = clean_markdown_content(content)
                 if cleaned.strip():
                     section_contents.append(cleaned)

    combined_content = "\n\n".join(section_contents)

    if combined_content.strip():
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
        )