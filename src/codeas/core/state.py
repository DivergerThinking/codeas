import json
import os

from pydantic import BaseModel

from codeas.core.llm import LLMClient
from codeas.core.metadata import RepoMetadata
from codeas.core.repo import Repo


class State(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    repo_path: str = "."
    include: str = ""
    exclude: str = ""
    llm_client: LLMClient = None
    repo: Repo = None
    repo_metadata: RepoMetadata = None

    def __init__(self, **data):
        super().__init__(**data)
        self.llm_client = LLMClient()
        self.repo = Repo(repo_path=self.repo_path)
        self.repo_metadata = RepoMetadata.load_metadata(self.repo_path)

    def update(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(repo_path=repo_path)
        self.repo_metadata = RepoMetadata.load_metadata(repo_path)

    def write_output(self, output: dict, path: str):
        if not os.path.exists(f"{self.repo_path}/.codeas/outputs"):
            os.makedirs(f"{self.repo_path}/.codeas/outputs")
        with open(f"{self.repo_path}/.codeas/outputs/{path}", "w") as f:
            json.dump(output, f)

    def read_output(self, path: str):
        with open(f"{self.repo_path}/.codeas/outputs/{path}", "r") as f:
            return json.load(f)


state = State()
