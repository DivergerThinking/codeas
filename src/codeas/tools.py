import inspect
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validate_call
from rich.console import Console

from codeas.codebase import Codebase
from codeas.repomap import RepoMap
from codeas.utils import File

load_dotenv()

console = Console()


class ListFileParams(BaseModel):
    dir_path: str = Field(..., description="relative directory path")


@validate_call
def list_files(params: ListFileParams):
    """list all of the files in a given directory"""
    cb = Codebase(base_dir=params.dir_path)
    return cb.get_modules_paths()


class DelegateParams(BaseModel):
    request: str = Field(..., description="the search request for the assistant")


@validate_call
def ask_assistant_to_search(params: DelegateParams):
    """asks an assistant to search for specific parts of a codebase"""
    ...


class ReturnAnswerParams(BaseModel):
    answer: str = Field(..., description="answer to return")


def return_answer(params: ReturnAnswerParams):
    """returns the final answer to the user"""
    return params.answer


class ReadFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    line_start: int = Field(1, description="start line to read")
    line_end: int = Field(-1, description="end line to read")
    structure_only: bool = Field(
        False, description="if True, uses only the code structure of the file"
    )


def view_file(params: ReadFileParams):
    """view the content of a file"""
    # we are simply changing the function naming here for agent prompting purposes
    return read_file(params)


def add_file(params: ReadFileParams):
    """adds a new file to the context"""
    # we are simply changing the function naming here for agent prompting purposes
    return read_file(params)


@validate_call
def read_file(params: ReadFileParams):
    """reads the content of a file"""
    try:
        console.print("\n")
        console.rule("Function", style="blue")
        console.print(f"Reading file: {params.path}\n")

        file_ = _read_file(
            params.path, params.line_start, params.line_end, params.structure_only
        )

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


def _read_file(path, line_start=1, line_end=-1, structure_only=False):
    if structure_only:
        rm = RepoMap()
        content = rm.get_file_structure(path)
    else:
        with open(path) as f:
            lines = f.readlines()
            content = "".join(lines[line_start - 1 : line_end])

    return File(
        path=path,
        content=content,
        line_start=line_start,
        line_end=len(lines) if line_end == -1 else line_end,
    )


class ReadElementParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    function_name: str = Field(None, description="function name if given")
    class_name: str = Field(None, description="class name if given")


@validate_call
def read_file_element(params: ReadElementParams):
    """reads given element from a file. At least one of 'function_name' or a 'class_name' must be given. For methods, both should be given"""
    try:
        console.print("\n")
        console.rule("Function", style="blue")

        if params.function_name and params.class_name:
            return read_method(params.path, params.function_name, params.class_name)
        elif params.function_name:
            return read_function(params.path, params.function_name)
        elif params.class_name:
            return read_class(params.path, params.class_name)

        console.rule(style="blue")

    except Exception as e:
        msg = f"ERROR: Unexpected error: {e}. Please review request"
        console.print(msg)
        return msg


def read_function(path: str, name: str):
    """reads a given function from a file"""
    console.print(f"Reading function '{name}' from '{path}'\n")

    functions = _read_function(path, name)

    if any(functions):
        console.print(f"Successfully read function: {name}")
    else:
        console.print(f"Function '{name}' not found")

    return functions


def _read_function(path: str, name: str):
    cb = Codebase()
    return cb.get_functions(path, name)


def read_class(path: str, name: str):
    """reads a given class from a file"""
    console.print(f"Reading class '{name}' from '{path}'\n")

    classes = _read_class(path, name)

    if any(classes):
        console.print(f"Successfully read class: {name}")
    else:
        console.print(f"Class '{name}' not found")

    console.rule(style="blue")

    return classes


def _read_class(path: str, name: str):
    cb = Codebase()
    return cb.get_classes(path, name)


def read_method(path: str, name: str, class_name: str):
    """reads a given method from a file"""
    console.print(f"Reading method '{class_name}{name}' from '{path}'\n")

    functions = _read_method(path, name)

    if any(functions):
        console.print(f"Successfully read function '{class_name}{name}'")
    else:
        console.print(f"Method '{class_name}{name}' not found")

    console.rule(style="blue")

    return functions


def _read_method(path: str, name: str, class_name: str):
    cb = Codebase()
    return cb.get_methods(path, name, class_name)


class CreateFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    content: str = Field(..., description="file content")


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


class ModifyFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    new_content: str = Field(..., description="new content for the modified file")
    line_start: int = Field(1, description="start line to modify content from")
    line_end: int = Field(-1, description="end line to modify content until")


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
