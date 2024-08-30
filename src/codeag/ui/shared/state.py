import logging
from typing import Dict, List

import streamlit as st
import streamlit_nested_layout  # needed to allow for nested expanders in the UI
from pydantic import BaseModel

from codeag.agents.orchestrator import Orchestrator
from codeag.agents.storage import Storage
from codeag.configs.agents_configs import AGENTS_CONFIGS
from codeag.core.repo import Repo
from codeag.core.retriever import Retriever


class SteamlitState(BaseModel):
    def __init__(self, **data):
        super().__init__(**data)
        for field in self.model_fields:
            if field not in st.session_state:
                st.session_state[field] = getattr(self, field)

    def __getattribute__(self, name: str):
        # First, get the model_fields to avoid recursion
        model_fields = super().__getattribute__("model_fields")
        if name in model_fields:
            # For model fields, always prioritize session_state
            return st.session_state.get(name, model_fields[name].default)
        # For non-model fields, use the default behavior
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value) -> None:
        super().__setattr__(name, value)
        if name in self.model_fields:
            st.session_state[name] = value


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

    def init(self):
        self.storage = Storage(repo_path=self.repo_path)
        self.repo = Repo(repo_path=self.repo_path, storage=self.storage)
        self.retriever = Retriever(storage=self.storage)
        self.orchestrator = Orchestrator(
            agent_configs=AGENTS_CONFIGS, storage=self.storage, retriever=self.retriever
        )

    def update(self, repo_path):
        self.repo_path = repo_path
        self.init()

    def clicked(self, key):
        self.button_clicked[key] = True

    def unclicked(self, key):
        self.button_clicked[key] = False

    def is_clicked(self, key):
        return self.button_clicked.get(key, False)

    def add_feedback(self, key):
        self.feedback[key] = st.session_state[key]


state = State()
state.init()
