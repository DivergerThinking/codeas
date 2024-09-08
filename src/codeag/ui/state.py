from pydantic import BaseModel

from codeag.core.llms import LLMClient
from codeag.core.repo import Filters


class State(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    repo_path: str = "."
    filters: Filters = Filters()
    files_info: dict = {}
    llm_client: LLMClient = LLMClient()


state = State()
