import streamlit as st

from codeag.ui.shared.components import display_button, display_steps, run_section
from codeag.ui.shared.state import get_state, init_state

init_state()


def display_documentation():
    st.write("## Documentation")
    with st.expander("Define sections"):
        display_define_sections()
    with st.expander("Generate sections"):
        display_generate_sections()
    with st.expander("Generate introduction"):
        display_generate_introduction()
    display_download_button()


def display_define_sections():
    display_steps(
        [
            "extract_file_descriptions",
            "extract_directory_descriptions",
            "define_documentation_sections",
        ]
    )
    display_button("Define Sections", "define_sections")

    if get_state("clicked").get("define_sections"):
        outputs = run_section("define_documentation_sections", "Defining sections...")
        display_sections_in_editor(outputs)


def display_generate_sections():
    display_steps(["generate_documentation_sections"])
    display_button("Generate sections", "generate_sections")

    if get_state("clicked").get("generate_sections"):
        outputs = run_section(
            "generate_documentation_sections", "Generating sections..."
        )
        display_sections(outputs)


def display_generate_introduction():
    display_steps(["generate_introduction"])
    display_button("Generate introduction", "generate_introduction")

    if get_state("clicked").get("generate_introduction"):
        outputs = run_section("generate_introduction", "Generating introduction...")
        display_introduction(outputs)


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


def display_download_button():
    docs = get_full_documentation()
    st.download_button(
        "Download documentation", docs, "documentation.md", type="primary"
    )


def get_full_documentation():
    full_documentation = ""

    intro = get_state("commands").read("generate_introduction")
    full_documentation += parse_json_to_markdown(intro["contents"])

    sections = get_state("commands").read("generate_documentation_sections")
    for content in sections["contents"].values():
        full_documentation += parse_json_to_markdown(content)

    return full_documentation


display_documentation()
