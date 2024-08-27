import streamlit as st

from codeag.ui.shared.components import display_agent, display_chain
from codeag.ui.shared.state import state


def display_documentation():
    st.write("## Documentation")
    display_define_sections()
    display_generate_documentation()
    # display_generate_sections()
    # display_generate_introduction()
    # display_final_documentation()


def display_define_sections():
    with st.expander("Define sections", expanded=True):
        display_agent(
            "define_documentation_sections",
            "Define Sections",
            display_sections_in_editor,
        )


def display_generate_documentation():
    with st.expander("Generate documentation", expanded=True):
        with st.expander("Steps"):
            display_generate_sections()
            display_generate_introduction()
        display_chain(
            "generate_documentation",
            "Generate Documentation",
            ["generate_documentation_sections", "generate_introduction"],
            display_final_documentation,
        )


def display_generate_sections():
    with st.expander("Generate sections", expanded=True):
        display_agent(
            "generate_documentation_sections", "Generate Sections", display_sections
        )


def display_generate_introduction():
    with st.expander("Generate introduction", expanded=True):
        display_agent(
            "generate_introduction", "Generate Introduction", display_introduction
        )


def display_sections_in_editor(output):
    sections = list(output["responses"]["content"].keys())
    paths = list(output["responses"]["content"].values())
    incl = [True] * len(sections)
    data = {
        "incl": incl,
        "sections": sections,
        "paths": paths,
    }
    st.data_editor(data, use_container_width=True)
    display_user_feedback("define_documentation_sections")


def display_user_feedback(agent_name: str):
    st.text_area(
        "User feedback",
        key=f"feedback_{agent_name}",
        on_change=lambda: state.add_feedback(f"feedback_{agent_name}"),
    )
    st.button(
        "Enter",
        key=f"ask_{agent_name}",
        type="primary",
        on_click=lambda: update_output(agent_name),
    )


def display_section_user_feedback(agent_name: str, section: str):
    st.text_area(
        "User feedback",
        key=f"feedback_{agent_name}_{section}",
        on_change=lambda: state.add_feedback(f"feedback_{agent_name}_{section}"),
    )
    st.button(
        "Enter",
        key=f"ask_{agent_name}_{section}",
        type="primary",
        on_click=lambda: update_section_output(agent_name, section),
    )


def update_output(agent_name):
    with st.spinner("Updating output..."):
        state.orchestrator.ask(agent_name, state.feedback[f"feedback_{agent_name}"])
    state.unclicked(f"ask_{agent_name}")


def update_section_output(agent_name, section: str):
    with st.spinner("Updating output..."):
        state.orchestrator.ask(
            agent_name, state.feedback[f"feedback_{agent_name}_{section}"], section
        )
    state.unclicked(f"ask_{agent_name}_{section}")


def display_sections(output):
    for section, responses in output["responses"].items():
        with st.expander(section):
            st.markdown(state.retriever.parse_json_to_markdown(responses["content"]))
            display_section_user_feedback("generate_documentation_sections", section)


def display_introduction(output):
    st.markdown(state.retriever.parse_json_to_markdown(output["responses"]["content"]))


def display_final_documentation():
    # with st.expander("Final documentation", expanded=True):
    docs = get_full_documentation()

    st.download_button("Download", docs, "documentation.md", type="primary")
    if docs == "":
        st.info("No generated documentation.")
    else:
        st.markdown(docs)


def get_full_documentation():
    full_documentation = ""
    try:
        full_documentation += state.retriever.get_introduction_markdown()
    except FileNotFoundError:
        pass
    try:
        full_documentation += state.retriever.get_sections_markdown()
    except FileNotFoundError:
        pass
    return full_documentation


display_documentation()
