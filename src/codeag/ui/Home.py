import streamlit as st
import streamlit_nested_layout

from codeag.ui.components import (
    docs_ui,
    metadata_ui,
    refactoring_ui,
    repo_ui,
    testing_ui,
)

if "outputs" not in st.session_state:
    st.session_state.outputs = {}


def home_page():
    st.title("Codeas")
    repo_ui.display()
    metadata_ui.display()
    display_tasks()


def display_tasks():
    st.subheader("Tasks")
    task_options = [
        "Generate documentation",
        "Generate testing",
        "Generate refactoring",
        "Generate deployments",
    ]
    selected_task = st.selectbox("Select a task", [""] + task_options)

    display_task(selected_task)


def display_task(task: str):
    if task == "Generate documentation":
        docs_ui.display()
    elif task == "Generate testing":
        testing_ui.display()
    elif task == "Generate refactoring":
        refactoring_ui.display()


if __name__ == "__main__":
    home_page()
