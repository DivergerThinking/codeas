import streamlit as st
import streamlit_nested_layout  # needed to allow for nested expanders in the UI
from pydantic import BaseModel

from codeag.agents.orchestrator import Orchestrator
from codeag.agents.storage import Storage
from codeag.configs.agents_configs import AGENTS_CONFIGS
from codeag.core._repo import Repo
from codeag.core.retriever import Retriever


class State(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
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
        self.repo = Repo(repo_path=self.repo_path, storage=self.storage)
        self.retriever = Retriever(storage=self.storage)
        self.orchestrator = Orchestrator(
            agent_configs=AGENTS_CONFIGS, storage=self.storage, retriever=self.retriever
        )

    def update(self, repo_path):
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
