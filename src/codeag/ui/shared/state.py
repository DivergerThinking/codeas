import logging

import streamlit as st
import streamlit_nested_layout  # needed to allow for nested expanders in the UI
from pydantic import BaseModel

from codeag.agents.orchestrator import Orchestrator
from codeag.agents.storage import Storage
from codeag.configs.agents_configs import AGENTS_CONFIGS
from codeag.core.repo import Repo
from codeag.core.retriever import Retriever

session_state = {}


class SteamlitState(BaseModel):
    def __init__(self, **data):
        super().__init__(**data)
        for field in self.model_fields:
            if field not in session_state:
                session_state[field] = getattr(self, field)

    def __getattribute__(self, name: str):
        # First, get the model_fields to avoid recursion
        model_fields = super().__getattribute__("model_fields")
        if name in model_fields:
            # For model fields, always prioritize session_state
            return session_state.get(name, model_fields[name].default)
        # For non-model fields, use the default behavior
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value) -> None:
        super().__setattr__(name, value)
        if name in self.model_fields:
            session_state[name] = value


class State(SteamlitState, arbitrary_types_allowed=True, extra="forbid"):
    repo_path: str = "."
    repo: Repo = None
    storage: Storage = None
    retriever: Retriever = None
    orchestrator: Orchestrator = None
    button_clicked: dict = {}
    selected_test_cases: dict = {}
    depth: int = 1
    feedback: dict = {}

    def model_post_init(self, __context):
        self.storage = Storage(repo_path=self.repo_path)
        self.retriever = Retriever(storage=self.storage)
        self.orchestrator = Orchestrator(
            agent_configs=AGENTS_CONFIGS, storage=self.storage, retriever=self.retriever
        )
        repo_filters = self.read_repo_filters()
        if repo_filters:
            self.repo = Repo(repo_path=self.repo_path, filters=repo_filters)
        else:
            self.repo = Repo(repo_path=self.repo_path)

    def read_repo_filters(self):
        try:
            return self.storage.read_json("state/filters.json")
        except FileNotFoundError:
            logging.warning("No repo filters found")

    def export_repo_state(self):
        self.storage.write_json("state/filters.json", self.repo.filters)
        self.storage.write_json(
            "state/incl_files_tokens.json", self.repo.incl_files_tokens
        )
        self.storage.write_json("state/incl_dir_tokens.json", self.repo.incl_dir_tokens)

    def update_repo_path(self, repo_path):
        self.repo_path = repo_path
        self.model_post_init(None)

    def clicked(self, key):
        self.button_clicked[key] = True

    def unclicked(self, key):
        self.button_clicked[key] = False

    def is_clicked(self, key):
        return self.button_clicked.get(key, False)

    def add_feedback(self, key):
        self.feedback[key] = st.session_state[key]


state = State()

# def set_state_once(key, value):
#     if key not in st.session_state:
#         st.session_state[key] = value


# def set_state(key, value):
#     st.session_state[key] = value


# def get_state(key, return_default=None):
#     return st.session_state.get(key, return_default)


# def set_common_state(repo_path, use_set_state_once=False):
#     set_func = set_state_once if use_set_state_once else set_state

#     set_func("repo_path", repo_path)
#     set_func("files_paths", parser.list_files(repo_path))
#     set_func(
#         "files_tokens",
#         parser.estimate_tokens_from_files(repo_path, get_state("files_paths")),
#     )
#     set_filter_settings(set_func)
#     filter_files_tokens(set_func)
#     set_func("commands", Commands(repo_path=repo_path))
#     set_func("clicked", {})
#     set_func("estimates", {})
#     set_func("outputs", {})
#     export_filter_settings()
#     set_func("selected_test_cases", {})


# def filter_files_tokens(set_func=set_state):
#     incl_files_tokens, excl_files_tokens = parser.filter_files(
#         get_state("files_tokens"), **get_state("filters")
#     )
#     set_func("incl_files_tokens", incl_files_tokens)
#     set_func("excl_files_tokens", excl_files_tokens)
#     export_filter_settings()
#     export_incl_files_tokens()


# def export_filter_settings():
#     settings_path = f"{get_state('repo_path')}/{SETTINGS_PATH}"
#     if not os.path.exists(settings_path):
#         os.makedirs(settings_path)
#     with open(os.path.join(settings_path, "filter_settings.json"), "w") as f:
#         f.write(json.dumps(get_state("filters")))


# def export_incl_files_tokens():
#     settings_path = f"{get_state('repo_path')}/{SETTINGS_PATH}"
#     if not os.path.exists(settings_path):
#         os.makedirs(settings_path)
#     with open(os.path.join(settings_path, "incl_files_tokens.json"), "w") as f:
#         f.write(json.dumps(get_state("incl_files_tokens")))


# def import_filter_settings(set_func):
#     settings_path = f"{get_state('repo_path')}/{SETTINGS_PATH}"
#     if not os.path.exists(settings_path):
#         os.makedirs(settings_path)
#     with open(os.path.join(settings_path, "filter_settings.json"), "r") as f:
#         set_func("filters", json.loads(f.read()))


# def set_filter_settings(set_func):
#     try:
#         import_filter_settings(set_func)
#     except FileNotFoundError:
#         logging.warning("Filter settings not found. Using default settings.")
#         set_func(
#             "filters",
#             {
#                 "exclude_dir": [],
#                 "include_dir": [],
#                 "exclude_files": [],
#                 "include_files": [],
#             },
#         )


# def init_state():
#     set_common_state(repo_path=".", use_set_state_once=True)


# def update_state(repo_path):
#     if repo_path is None:
#         repo_path = "."
#     set_common_state(repo_path=repo_path)
