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
    total_gen_cost = 0
    total_gen_input_tokens = 0
    total_gen_output_tokens = 0
    total_preview_input_cost = 0
    total_preview_input_tokens = 0
    full_documentation = ""

    with st.expander(
        f"Sections {'[Preview]' if preview else ''}", expanded=not use_previous
    ):
        for section in selected_sections:
            with st.spinner(
                f"{'Generating' if generate else 'Previewing' if preview else 'Displaying'} {section}..."
            ):
                section_output = None

                if generate:
                    if use_previous:
                        try:
                            section_output = read_output(section)
                        except FileNotFoundError:
                            section_output = run_generation(section)
                    else:
                        section_output = run_generation(section)

                    if section_output:
                        total_gen_cost += section_output.cost.get("total_cost", 0)
                        total_gen_input_tokens += section_output.tokens.get("input_tokens", 0)
                        total_gen_output_tokens += section_output.tokens.get("output_tokens", 0)

                elif preview:
                    if use_previous:
                        try:
                            section_output = read_output(section)
                        except FileNotFoundError:
                            section_output = run_preview(section)
                    else:
                        section_output = run_preview(section)

                    if section_output:
                        total_preview_input_cost += section_output.cost.get("input_cost", 0)
                        total_preview_input_tokens += section_output.tokens.get("input_tokens", 0)

                display_section(
                    section,
                    section_output,
                    generate=generate,
                    preview=preview,
                )

                if not preview and section in st.session_state.outputs:
                    output_obj = st.session_state.outputs.get(section)
                    if output_obj and output_obj.response and "content" in output_obj.response:
                        cleaned_content = clean_markdown_content(
                            output_obj.response["content"]
                        )
                        full_documentation += f"\n\n{cleaned_content}"

    if generate:
        st.info(
            f"Total generation cost: ${total_gen_cost:.4f} "
            f"(input tokens: {total_gen_input_tokens:,}, "
            f"output tokens: {total_gen_output_tokens:,})"
        )
        if not use_previous and total_gen_cost > 0:
             usage_tracker.record_usage("generate_docs", total_gen_cost)

    elif preview:
        st.info(
            f"Total preview input cost: ${total_preview_input_cost:.4f} ({total_preview_input_tokens:,} tokens)"
        )

    if full_documentation.strip():
        with st.expander("Full Documentation", expanded=True):
            st.markdown(full_documentation)

    if generate or (
        not preview
        and any(section in st.session_state.outputs for section in selected_sections)
    ):
        add_download_button(selected_sections)


def _display_cost_info(output: object | None, generate: bool, preview: bool):
    if output:
        if preview:
            input_cost = output.cost.get('input_cost', 0)
            input_tokens = output.tokens.get('input_tokens', 0)
            st.info(
                f"Input cost: ${input_cost:.4f} ({input_tokens:,} tokens)"
            )
        elif generate:
            total_cost = output.cost.get('total_cost', 0)
            input_tokens = output.tokens.get('input_tokens', 0)
            output_tokens = output.tokens.get('output_tokens', 0)
            st.info(
                f"Section cost: ${total_cost:.4f} "
                f"(input tokens: {input_tokens:,}, "
                f"output tokens: {output_tokens:,})",
                help="Cost/tokens for this specific section generation."
            )


def _display_messages_and_warnings(output: object | None, section: str):
    if output:
        if output.messages:
             with st.expander("Messages", expanded=False):
                 st.json(output.messages)

        if not output.messages or (output.messages and len(output.messages) > 0 and "content" in output.messages[0] and not output.messages[0]["content"].strip()):
             st.warning(f"No context found or empty context message for {section.upper()}.")


def _display_generated_content(output: object | None):
    if output:
        if output.response and "content" in output.response:
            content = output.response["content"]
            content = clean_markdown_content(content)
            st.code(content, language="markdown")
        else:
             st.warning("No generated content available for display for this section.")


def display_section(
    section: str,
    output: object | None,
    generate: bool = False,
    preview: bool = False,
):
    expander_label = (
        f"{section.replace('_', ' ').upper()}{' [Preview]' if preview else ''}"
    )

    with st.expander(expander_label, expanded=False):
        _display_cost_info(output, generate, preview)
        _display_messages_and_warnings(output, section)

        if generate:
            _display_generated_content(output)


def run_generation(section: str):
    preview_output = generate_docs_section(
        state.llm_client,
        section,
        state.repo,
        state.repo_metadata,
        preview=True,
    )
    if preview_output and hasattr(preview_output, 'messages') and preview_output.messages and len(preview_output.messages) > 0 and "content" in preview_output.messages[0] and preview_output.messages[0]["content"].strip():
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

    output_data = {
        "response": {"content": previous_output.get("content", "")},
        "cost": previous_output.get("cost", {"total_cost": 0, "input_cost": 0}),
        "tokens": previous_output.get("tokens", {"input_tokens": 0, "output_tokens": 0}),
        "messages": previous_output.get(
            "messages",
            [{"role": "system", "content": "Context was not stored with previous output"}],
        ),
    }

    class OutputObject:
        def __init__(self, data):
            self.response = data["response"]
            self.cost = data["cost"]
            self.tokens = data["tokens"]
            self.messages = data["messages"]
        def __getattr__(self, name):
            if name in self.__dict__:
                return self.__dict__[name]
            return None


    output = OutputObject(output_data)

    st.session_state.outputs[section] = output

    return output


def clean_markdown_content(content: str) -> str:
    content = content.strip()
    if content.startswith("```markdown") and content.endswith("```"):
        content = content[11:-3].strip()
    return content


def add_download_button(selected_sections: list[str]):
    combined_content_parts = []
    for section in selected_sections:
        output_obj = st.session_state.outputs.get(section)
        if output_obj and hasattr(output_obj, 'response') and output_obj.response and "content" in output_obj.response:
             combined_content_parts.append(clean_markdown_content(output_obj.response["content"]))

    combined_content = "\n\n".join(combined_content_parts)

    if combined_content.strip():
        st.download_button(
            label="Download docs",
            data=combined_content,
            file_name="docs.md",
            mime="text/markdown",
            type="primary",
        )