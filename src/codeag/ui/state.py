from pydantic import BaseModel

from codeag.core.llm import LLMClient
from codeag.core.metadata import RepoMetadata
from codeag.core.repo import Repo


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


state = State()
