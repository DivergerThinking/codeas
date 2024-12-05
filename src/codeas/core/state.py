import json
import os
from typing import Dict, List

from pydantic import BaseModel, Field

from codeas.core.client_azure import LLMClientAzure as LLMClient

# from codeas.core.metadata import RepoMetadata
from codeas.core.repo import Repo
from codeas.core.storage import Storage


class PageFilter(BaseModel):
    include: str = ""
    exclude: str = ""


class State(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    repo_path: str = os.path.abspath(".")
    llm_client: LLMClient = None
    repo: Repo = None
    page_filter: PageFilter = Field(default_factory=PageFilter)
    files_data: Dict[str, List] = Field(
        default_factory=lambda: {"Incl.": [], "Path": [], "Tokens": []}
    )
    storage: Storage = Storage()
    # repo_embeddings_map: dict[str, str] = {}

    def __init__(self, **data):
        super().__init__(**data)
        self.llm_client = LLMClient()
        self.load_page_filters()
        # self.load_repo_embeddings_map()
        self.repo = Repo(repo_path=self.repo_path)
        self.update_files_data()

    def update_files_data(self):
        self.files_data = {
            "Incl.": self.repo.included,
            "Path": self.repo.files_paths,
            "Tokens": list(self.repo.files_tokens.values()),
        }

    def write_output(self, output: dict, path: str):
        if not os.path.exists(f"{self.repo_path}/.codeas/outputs"):
            os.makedirs(f"{self.repo_path}/.codeas/outputs")
        with open(f"{self.repo_path}/.codeas/outputs/{path}", "w") as f:
            json.dump(output, f)

    def read_output(self, path: str):
        with open(f"{self.repo_path}/.codeas/outputs/{path}", "r") as f:
            return json.load(f)

    def update_page_filter(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.page_filter, key, value)
        self.save_page_filters()
        self.apply_filters()

    def apply_filters(self):
        include_patterns = [
            pattern.strip()
            for pattern in self.page_filter.include.split(",")
            if pattern.strip()
        ]
        exclude_patterns = [
            pattern.strip()
            for pattern in self.page_filter.exclude.split(",")
            if pattern.strip()
        ]
        self.repo.filter_files(include_patterns, exclude_patterns)
        self.update_files_data()

    def save_page_filters(self):
        page_filters_dir = os.path.join(self.repo_path, ".codeas")
        os.makedirs(page_filters_dir, exist_ok=True)
        with open(os.path.join(page_filters_dir, "filters.json"), "w") as f:
            json.dump(self.page_filter.model_dump(), f)

    def save_repo_embeddings_map(self):
        embeddings_map_dir = os.path.join(self.repo_path, ".codeas")
        os.makedirs(embeddings_map_dir, exist_ok=True)
        with open(
            os.path.join(embeddings_map_dir, "repo_embeddings_map.json"), "w"
        ) as f:
            json.dump(self.repo_embeddings_map, f)

    def load_page_filters(self):
        try:
            page_filters_path = os.path.join(self.repo_path, ".codeas", "filters.json")
            with open(page_filters_path, "r") as f:
                self.page_filter = PageFilter(**json.load(f))
        except FileNotFoundError:
            self.page_filter = PageFilter()

    # def load_repo_embeddings_map(self):
    #     try:
    #         embeddings_map_path = os.path.join(self.repo_path, ".codeas", "repo_embeddings_map.json")
    #         with open(embeddings_map_path, "r") as f:
    #             self.repo_embeddings_map = json.load(f)
    #     except FileNotFoundError:
    #         self.repo_embeddings_map = {}


state = State()
