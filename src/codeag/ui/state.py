from pydantic import BaseModel


class State(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    repo_path: str = "."
    include: str = ""
    exclude: str = ""
    files_description: dict = {}
    files_detail: dict = {}


state = State()
