import json
import logging
import os

import streamlit as st
import streamlit_nested_layout  # needed to allow for nested expanders in the UI

from codeag.configs.storage_configs import SETTINGS_PATH
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
    set_filter_settings(set_func)
    filter_files_tokens(set_func)
    set_func("commands", Commands(repo_path=repo_path))
    set_func("clicked", {})
    set_func("estimates", {})
    set_func("outputs", {})
    export_filter_settings()
    set_func("selected_test_cases", {})


def filter_files_tokens(set_func=set_state):
    incl_files_tokens, excl_files_tokens = parser.filter_files(
        get_state("files_tokens"), **get_state("filters")
    )
    set_func("incl_files_tokens", incl_files_tokens)
    set_func("excl_files_tokens", excl_files_tokens)
    export_filter_settings()
    export_incl_files_tokens()


def export_filter_settings():
    settings_path = f"{get_state('repo_path')}/{SETTINGS_PATH}"
    if not os.path.exists(settings_path):
        os.makedirs(settings_path)
    with open(os.path.join(settings_path, "filter_settings.json"), "w") as f:
        f.write(json.dumps(get_state("filters")))


def export_incl_files_tokens():
    settings_path = f"{get_state('repo_path')}/{SETTINGS_PATH}"
    if not os.path.exists(settings_path):
        os.makedirs(settings_path)
    with open(os.path.join(settings_path, "incl_files_tokens.json"), "w") as f:
        f.write(json.dumps(get_state("incl_files_tokens")))


def import_filter_settings(set_func):
    settings_path = f"{get_state('repo_path')}/{SETTINGS_PATH}"
    if not os.path.exists(settings_path):
        os.makedirs(settings_path)
    with open(os.path.join(settings_path, "filter_settings.json"), "r") as f:
        set_func("filters", json.loads(f.read()))


def set_filter_settings(set_func):
    try:
        import_filter_settings(set_func)
    except FileNotFoundError:
        logging.warning("Filter settings not found. Using default settings.")
        set_func(
            "filters",
            {
                "exclude_dir": [],
                "include_dir": [],
                "exclude_files": [],
                "include_files": [],
            },
        )


def init_state():
    set_common_state(repo_path=".", use_set_state_once=True)


def update_state(repo_path):
    if repo_path is None:
        repo_path = "."
    set_common_state(repo_path=repo_path)
