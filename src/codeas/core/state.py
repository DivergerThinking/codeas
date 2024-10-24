import json
import os
from typing import Dict, List

from pydantic import BaseModel, Field

from codeas.core.llm import LLMClient
from codeas.core.metadata import RepoMetadata
from codeas.core.repo import Repo


class PageFilter(BaseModel):
    include: str = ""
    exclude: str = ""


class State(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    current_page: str = ""
    repo_path: str = "."
    llm_client: LLMClient = None
    repo: Repo = None
    repo_metadata: RepoMetadata = None
    page_filters: Dict[str, PageFilter] = Field(default_factory=dict)
    files_data: Dict[str, List] = Field(
        default_factory=lambda: {"Incl.": [], "Path": [], "Tokens": []}
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.llm_client = LLMClient()
        self.load_page_filters()
        self.repo = Repo(repo_path=self.repo_path)
        self.repo_metadata = RepoMetadata.load_metadata(self.repo_path)
        self.update_files_data()

    def update_repo_path(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(repo_path=repo_path)
        self.repo_metadata = RepoMetadata.load_metadata(repo_path)
        self.load_page_filters()
        self.update_files_data()

    def update_current_page(self, page_name: str):
        self.current_page = page_name
        self.load_page_filters()
        self.apply_filters()

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

    def get_page_filter(self) -> PageFilter:
        if self.current_page not in self.page_filters:
            self.page_filters[self.current_page] = PageFilter()
        return self.page_filters[self.current_page]

    def update_page_filter(self, **kwargs):
        page_filter = self.get_page_filter()
        for key, value in kwargs.items():
            setattr(page_filter, key, value)
        self.save_page_filters()
        self.apply_filters()

    def apply_filters(self):
        page_filter = self.get_page_filter()
        include_patterns = [
            pattern.strip()
            for pattern in page_filter.include.split(",")
            if pattern.strip()
        ]
        exclude_patterns = [
            pattern.strip()
            for pattern in page_filter.exclude.split(",")
            if pattern.strip()
        ]
        self.repo.filter_files(include_patterns, exclude_patterns)
        self.update_files_data()

    def save_page_filters(self):
        page_filters_dict = {
            name: state.model_dump() for name, state in self.page_filters.items()
        }
        page_filters_dir = os.path.join(self.repo_path, ".codeas")
        os.makedirs(page_filters_dir, exist_ok=True)
        with open(os.path.join(page_filters_dir, "filters.json"), "w") as f:
            json.dump(page_filters_dict, f)

    def load_page_filters(self):
        try:
            page_filters_path = os.path.join(self.repo_path, ".codeas", "filters.json")
            with open(page_filters_path, "r") as f:
                page_filters_dict = json.load(f)
            self.page_filters = {
                name: PageFilter(**state) for name, state in page_filters_dict.items()
            }
        except FileNotFoundError:
            self.page_filters = {}


state = State()
