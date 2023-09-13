from typing import Literal
from pydantic import BaseModel

class Entity(BaseModel):
    name: str
    label: Literal["class", "function", "method"]
    source_code: str
    docstring: str
    node: object