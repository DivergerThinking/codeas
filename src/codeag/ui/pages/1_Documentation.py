import streamlit as st

from codeag.ui.shared.components import display_command
from codeag.ui.shared.state import init_state

init_state()


def display_documentation():
    st.write("## Documentation")
    display_command("extract_file_descriptions")


display_documentation()
