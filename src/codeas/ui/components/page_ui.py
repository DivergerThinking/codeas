import os
import pickle
from typing import Literal

import streamlit as st
import streamlit_nested_layout  # noqa

from codeas.core.metadata import RepoMetadata
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
    if name == "Documentation" or name == "Deployment":
        load_or_create_repo_state("./abstreet", "abstreet")
    elif name == "Testing" or name == "Refactoring":
        load_or_create_repo_state("../codeas", "codeas")


def load_or_create_repo_state(repo_path: str, repo_name: str):
    state_file = f".codeas/{repo_name}_repo_state.pkl"
    if repo_name == "abstreet":
        state.include = ""
        state.exclude = "*.lock, *.txt, *.md, *osm, *data*, *geojson"
    elif repo_name == "codeas":
        state.include = "*.py"
        state.exclude = "*configs*"
    if os.path.exists(state_file):
        state.repo_path = repo_path
        with open(state_file, "rb") as f:
            state.repo = pickle.load(f)
        state.repo_metadata = RepoMetadata.load_metadata(repo_path)
    else:
        state.update(repo_path)
        include_patterns = [
            include.strip() for include in state.include.split(",") if include.strip()
        ]
        exclude_patterns = [
            exclude.strip() for exclude in state.exclude.split(",") if exclude.strip()
        ]
        state.repo.filter_files(
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        with open(state_file, "wb") as f:
            pickle.dump(state.repo, f)
