from typing import Literal

import streamlit as st
import streamlit_nested_layout  # noqa

from codeas.core.state import state
from codeas.ui.components import (
    deployment_ui,
    documentation_ui,
    metadata_ui,
    refactoring_ui,
    repo_ui,
    testing_ui,
)

pages = {
    "Documentation": {"name": "📚 Documentation", "ui": documentation_ui},
    "Deployment": {"name": "🚀 Deployment", "ui": deployment_ui},
    "Testing": {"name": "🧪 Testing", "ui": testing_ui},
    "Refactoring": {"name": "🔄 Refactoring", "ui": refactoring_ui},
}


def display(
    name: Literal["Documentation", "Deployment", "Testing", "Refactoring"],
):
    st.subheader(pages[name]["name"])
    state.update_current_page(name)
    repo_ui.display_repo_path()
    with st.expander("CONTEXT", icon="⚙️", expanded=True):
        repo_ui.display_filters()
        num_selected_files, _, selected_tokens = repo_ui.get_selected_files_info()
        st.caption(f"{num_selected_files:,} files | {selected_tokens:,} tokens")
        repo_ui.display_files_editor()
        metadata_ui.display()
    pages[name]["ui"].display()
