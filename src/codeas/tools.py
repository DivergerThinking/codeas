import inspect
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validate_call
from rich.console import Console

from codeas.codebase import Codebase
from codeas.repomap import RepoMap

load_dotenv()


class RepoMapParams(BaseModel):
    max_map_tokens: int = Field(
        1024, description="maximum number of tokens to use in the repo map"
    )


class ReadFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    line_start: int = Field(1, description="start line to read")
    line_end: int = Field(-1, description="end line to read")


class CreateFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    content: str = Field(..., description="file content")


class ModifyFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    new_content: str = Field(..., description="new content for the modified file")
    line_start: int = Field(1, description="start line to modify content from")
    line_end: int = Field(-1, description="end line to modify content until")


class File(BaseModel):
    path: str
    content: str
    line_start: int
    line_end: int


@validate_call
def add_repo_map(params: RepoMapParams):
    """get the repository map"""
    try:
        console = Console()
        console.print("\n")
        console.rule("Function", style="blue")
        console.print("Adding repo map\n")

        cb = Codebase()
        paths = cb.get_modules_paths()
        rm = RepoMap(params.max_map_tokens)
        rmap = rm.get_repo_map([], paths)

        console.print("Successfully added repo map")
        console.rule(style="blue")
        return rmap

    except Exception as e:
        msg = f"ERROR: Unexpected error: {e}. Please review request"
        console.print(msg)
        return msg


@validate_call
def read_file(params: ReadFileParams):
    """reads the content of a file"""
    try:
        console = Console()
        console.print("\n")
        console.rule("Function", style="blue")
        console.print(f"Reading file: {params.path}\n")

        file_ = _read_file(params.path, params.line_start, params.line_end)

        console.print(f"Successfully read file: {params.path}")
        console.rule(style="blue")

        return file_

    except FileNotFoundError:
        msg = "ERROR: File not found. Please specify the exact file path, including file name."
        console.print(msg)
        return msg

    except Exception as e:
        msg = f"ERROR: Unexpected error: {e}. Please review request"
        console.print(msg)
        return msg


def _read_file(path, line_start, line_end):
    with open(path) as f:
        content = "".join(f.readlines()[line_start - 1 : line_end])

    return File(
        path=path,
        content=content,
        line_start=line_start,
        line_end=line_end,
    )


@validate_call
def create_file(params: CreateFileParams):
    """creates a new file with the given content"""
    try:
        console = Console()
        console.print("\n")
        console.rule("Function", style="blue")
        console.print(f"Writing file: {params.path}\n")

        _write_file(params.path, params.content)

        console.print(f"Successfully wrote file: {params.path}")
        console.rule(style="blue")

    except Exception as e:
        msg = f"ERROR: Unexpected error: {e}. Please review request"
        console.print(msg)
        return msg


def _write_file(path, content):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, "w") as f:
        f.write(content)


@validate_call
def modify_file(params: ModifyFileParams):
    """modifies the content of a file"""
    try:
        console = Console()
        console.print("\n")
        console.rule("Function", style="blue")
        console.print(f"Modifying file: {params.path}\n")

        _modify_file(
            params.path, params.new_content, params.line_start, params.line_end
        )

        console.print(f"Successfully modified file: {params.path}")
        console.rule(style="blue")

    except Exception as e:
        msg = f"ERROR: Unexpected error: {e}. Please review request"
        console.print(msg)
        return msg


def _modify_file(path, new_content, line_start, line_end):
    with open(path, "r") as f:
        lines = f.readlines()

    lines[line_start - 1 : line_end] = new_content

    with open(path, "w") as f:
        f.writelines(lines)


def get_function_schema(function):
    signature = inspect.signature(function)
    first_parameter = next(iter(signature.parameters.values()), None)
    if first_parameter is not None and issubclass(
        first_parameter.annotation, BaseModel
    ):
        schema = first_parameter.annotation.model_json_schema()
        schema.pop("title", None)
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)
        return schema
    else:
        return {}


def get_schemas(functions: list):
    if functions is not None:
        schemas = []
        for function in functions:
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": function.__name__,
                        "description": function.__doc__,
                        "parameters": get_function_schema(function),
                    },
                }
            )
        return schemas
