from typing import Literal

import streamlit as st
import streamlit_nested_layout  # noqa

from codeas.core.state import state
from codeas.ui.components import (
    architecture_ui,
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
    "Architecture": {"name": "🏛️ Architecture", "ui": architecture_ui},
}


def display(
    name: Literal[
        "Documentation", "Deployment", "Testing", "Refactoring", "Architecture"
    ],
):
    st.subheader(pages[name]["name"])
    state.update_current_page(name)
    repo_ui.display()
    metadata_ui.display()
    pages[name]["ui"].display()
