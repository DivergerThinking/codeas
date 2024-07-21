import streamlit as st

from codeag.core.agent import Agent
from codeag.core.commands import Commands
from codeag.utils import parser


def set_state_once(key, value):
    if key not in st.session_state:
        st.session_state[key] = value


def set_state(key, value):
    st.session_state[key] = value


def get_state(key, return_default=None):
    return st.session_state.get(key, return_default)


def set_common_state(repo_path, use_set_state_once=False):
    set_func = set_state_once if use_set_state_once else set_state

    set_func("repo_path", repo_path)
    set_func("files_paths", parser.list_files(repo_path))
    set_func(
        "files_tokens",
        parser.estimate_tokens_from_files(repo_path, get_state("files_paths")),
    )
    set_func(
        "filters",
        {
            "exclude_dir": [],
            "include_dir": [],
            "exclude_files": [],
            "include_files": [],
        },
    )

    incl_files_tokens, excl_files_tokens = parser.filter_files(
        get_state("files_tokens"), **get_state("filters")
    )
    set_func("incl_files_tokens", incl_files_tokens)
    set_func("excl_files_tokens", excl_files_tokens)
    set_func("commands", Commands(Agent(repo_path=repo_path)))
    set_func("clicked", {})
    set_func("estimates", {})
    set_func("outputs", {})


def init_state():
    set_common_state(repo_path=".", use_set_state_once=True)


def update_state(repo_path):
    if repo_path is None:
        repo_path = "."
    set_common_state(repo_path=repo_path)
