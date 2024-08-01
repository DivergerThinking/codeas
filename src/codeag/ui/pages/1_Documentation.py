import streamlit as st

from codeag.ui.shared.components import clicked, display_command
from codeag.ui.shared.state import get_state, init_state

init_state()


def display_documentation():
    st.write("## Documentation")
    display_section("Define sections", display_define_sections_content)
    display_section("Generate sections", display_generate_sections_content)
    display_section("Generate introduction", display_generate_introduction_content)


def display_section(title, content_func):
    with st.expander(title, expanded=True):
        content_func()


def display_define_sections_content():
    display_steps(
        [
            "extract_file_descriptions",
            "extract_directory_descriptions",
            "define_documentation_sections",
        ]
    )
    display_button("Define Sections", "define_sections")

    if get_state("clicked").get("define_sections"):
        outputs = run_command("define_documentation_sections", "Defining sections...")
        display_sections_in_editor(outputs)


def display_generate_sections_content():
    display_steps(["generate_documentation_sections"])
    display_button("Generate sections", "generate_sections")

    if get_state("clicked").get("generate_sections"):
        outputs = run_command(
            "generate_documentation_sections", "Generating sections..."
        )
        display_sections(outputs)


def display_generate_introduction_content():
    display_steps(["generate_introduction"])
    display_button("Generate introduction", "generate_introduction")

    if get_state("clicked").get("generate_introduction"):
        outputs = run_command("generate_introduction", "Generating introduction...")
        display_introduction(outputs)


def display_steps(steps):
    with st.expander("Steps"):
        for step in steps:
            display_command(step)


def display_button(label, key):
    st.button(
        label,
        type="primary",
        key=key,
        on_click=lambda: clicked(key),
    )


def run_command(command_name, spinner_text):
    with st.spinner(spinner_text):
        if get_state("commands").exists_output(command_name):
            outputs = get_state("commands").read(command_name)
            st.info("Using stored outputs.")
        else:
            outputs = get_state("commands").run(command_name)
            get_state("commands").write(command_name, outputs)
        return outputs


def display_sections_in_editor(outputs):
    sections = list(outputs["contents"].keys())
    paths = list(outputs["contents"].values())
    incl = [True] * len(sections)
    data = {
        "incl": incl,
        "sections": sections,
        "paths": paths,
    }
    st.data_editor(data)


def display_sections(outputs):
    with st.expander("Sections", expanded=True):
        for section, content in outputs["contents"].items():
            with st.expander(section):
                st.markdown(parse_json_to_markdown(content))


def display_introduction(outputs):
    with st.expander("Introduction"):
        st.markdown(parse_json_to_markdown(outputs["contents"]))


def parse_json_to_markdown(json_output):
    markdown = ""
    for key, content in json_output.items():
        if "h1" in key:
            markdown += f"## {content}\n\n"
        elif "h2" in key:
            markdown += f"### {content}\n\n"
        elif "h3" in key:
            markdown += f"#### {content}\n"
        elif "h4" in key:
            markdown += f"##### {content}\n"
        elif "p" in key:
            markdown += f"{content}\n\n"
    return markdown


display_documentation()
