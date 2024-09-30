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
    demo: bool = True,
):
    st.subheader(pages[name]["name"])
    if demo:
        set_demo_state(name)
    repo_ui.display(demo)
    metadata_ui.display()
    pages[name]["ui"].display()


def set_demo_state(name: str):
    if name == "Documentation":
        codeas_state_all()
    elif name == "Deployment":
        codeas_state_all()
    elif name == "Testing":
        codeas_state()
    elif name == "Refactoring":
        codeas_state()


def codeas_state():
    state.update("../codeas")
    state.include = "*.py"
    state.exclude = "*configs*"


def codeas_state_all():
    state.update("../codeas")
    state.include = ""
    state.exclude = ""


def abstreet_state():
    state.update("../abstreet")
    state.include = ""
    state.exclude = "*.lock, *.txt, *.md, *osm, *data*, *geojson"
