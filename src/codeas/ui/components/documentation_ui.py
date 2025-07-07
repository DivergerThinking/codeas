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

    edited_data = st.data_editor(
        doc_data,
        column_config={
            "Incl.": st.column_config.CheckboxColumn(width="small"),
            "Section": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
        key="doc_sections_editor",
    )

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
    total_output_tokens = 0
    total_input_cost = 0
    total_input_tokens = 0

    full_documentation = ""

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            output = None
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
                        if hasattr(output, 'cost') and isinstance(output.cost, dict) and 'total_cost' in output.cost:
                            total_cost += output.cost["total_cost"]
                        if hasattr(output, 'tokens') and isinstance(output.tokens, dict) and 'input_tokens' in output.tokens:
                            total_input_tokens += output.tokens["input_tokens"]
                        if hasattr(output, 'tokens') and isinstance(output.tokens, dict) and 'output_tokens' in output.tokens:
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
                        st.session_state.outputs[section] = output

                    if output and hasattr(output, 'cost') and isinstance(output.cost, dict) and 'input_cost' in output.cost:
                         total_input_cost += output.cost["input_cost"]
                    if output and hasattr(output, 'tokens') and isinstance(output.tokens, dict) and 'input_tokens' in output.tokens:
                         total_input_tokens += output.tokens["input_tokens"]

                display_section(section, generate=generate, preview=preview)

                if not preview and section in st.session_state.outputs:
                    current_output = st.session_state.outputs[section]
                    if hasattr(current_output, 'response') and isinstance(current_output.response, dict) and 'content' in current_output.response:
                        cleaned_content = clean_markdown_content(
                            current_output.response["content"]
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
    previous_output = state.read_output(f"{section}.json")
    output = type(
        "Output",
        (),
        {
            "response": {"content": previous_output.get("content", "")},
            "cost": previous_output.get("cost", {}),
            "tokens": previous_output.get("tokens", {}),
            "messages": previous_output.get(
                "messages",
                [{"content": "Context was not stored with previous output" if previous_output.get("messages") is None else ""}],
            ),
        },
    )()
    st.session_state.outputs[section] = output
    return output


def clean_markdown_content(content: str) -> str:
    if not isinstance(content, str):
        return ""
    content = content.strip()
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[11:-3].strip()
    return content


def _display_cost_info(output, generate, preview):
    if preview and hasattr(output, 'cost') and isinstance(output.cost, dict) and 'input_cost' in output.cost and \
       hasattr(output, 'tokens') and isinstance(output.tokens, dict) and 'input_tokens' in output.tokens:
        st.info(
            f"Input cost: ${output.cost['input_cost']:.4f} ({output.tokens['input_tokens']:,} tokens)"
        )
    elif generate and hasattr(output, 'cost') and isinstance(output.cost, dict) and 'total_cost' in output.cost and \
         hasattr(output, 'tokens') and isinstance(output.tokens, dict) and 'input_tokens' in output.tokens and 'output_tokens' in output.tokens:
         st.info(
            f"Total cost: ${output.cost['total_cost']:.4f} "
            f"(input tokens: {output.tokens['input_tokens']:,}, "
            f"output tokens: {output.tokens['output_tokens']:,})"
         )

def _display_valid_messages(messages, section):
    with st.expander("Messages", expanded=False):
        if all(isinstance(msg, dict) for msg in messages):
             st.json(messages)
        else:
             st.warning("Messages format unexpected.")
             st.write(messages)

    if isinstance(messages, list) and len(messages) > 0 and \
       isinstance(messages[0], dict) and 'content' in messages[0] and \
       not messages[0]["content"].strip():
         st.warning(f"No context found for {section.upper()}.")


def _display_messages(output, section):
    if hasattr(output, 'messages') and output.messages and isinstance(output.messages, list):
        _display_valid_messages(output.messages, section)
    elif hasattr(output, 'messages') and (output.messages is None or (isinstance(output.messages, list) and not output.messages)):
         st.info("No messages stored for this section.")

def _display_content(output, generate, section):
     if generate and hasattr(output, 'response') and isinstance(output.response, dict) and 'content' in output.response:
        content = output.response["content"]
        content = clean_markdown_content(content)
        st.code(content, language="markdown")
     elif generate:
        st.warning(f"Could not find content for {section.upper()} in output.")


def display_section(
    section: str,
    generate: bool = False,
    preview: bool = False,
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )

    output = st.session_state.outputs.get(section)

    with st.expander(expander_label, expanded=False):
        if output:
            _display_cost_info(output, generate, preview)
            _display_messages(output, section)
            _display_content(output, generate, section)


def add_download_button(selected_sections: list[str]):
    combined_content = "\n\n".join(
        [
            clean_markdown_content(
                 st.session_state.outputs[section].response["content"]
                 if section in st.session_state.outputs
                 and hasattr(st.session_state.outputs[section], 'response')
                 and isinstance(st.session_state.outputs[section].response, dict)
                 and "content" in st.session_state.outputs[section].response
                 else ""
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
        disabled=not combined_content.strip()
    )