import inspect
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validate_call

from codeas.codebase import Codebase
from codeas.utils import File

load_dotenv()


class ListFileParams(BaseModel):
    dir_path: str = Field(..., description="relative directory path")


@validate_call
def list_files(params: ListFileParams):
    """list all of the files in a given directory"""
    codebase = Codebase(base_dir=params.dir_path)
    return codebase.get_modules_paths()


class ReturnAnswerParams(BaseModel):
    answer: str = Field(..., description="answer to return")


@validate_call
def return_answer(params: ReturnAnswerParams):
    """returns the final answer to the user"""
    return params.answer


class ReadDirParams(BaseModel):
    path: str = Field(..., description="relative directory path")
    structure_only: bool = Field(
        False,
        description="if True, uses only the code structure of files in the directory",
    )


@validate_call
def add_files_in_dir(params: ReadDirParams):
    """adds all files in a given directory to the context"""
    files = []
    codebase = Codebase(base_dir=params.path)
    for file_path in codebase.get_modules_paths():
        params = ReadFileParams(path=file_path, structure_only=params.structure_only)
        file_ = read_file(params)
        files.append(file_)
    return files


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
    if params.structure_only:
        codebase = Codebase()
        content = codebase.get_file_structure(params.path)
    else:
        with open(params.path) as f:
            lines = f.readlines()
            content = "".join(lines[params.line_start - 1 : params.line_end])
            params.line_end = len(lines) if params.line_end == -1 else params.line_end
    return File(
        path=params.path,
        content=content,
        line_start=params.line_start,
        line_end=params.line_end,
    )


class ReadElementParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    function_name: str = Field(None, description="function name if given")
    class_name: str = Field(None, description="class name if given")


def add_file_element(params: ReadElementParams):
    """adds a file element to the context"""
    # we are simply changing the function naming here for agent prompting purposes
    return read_file_element(params)


@validate_call
def read_file_element(params: ReadElementParams):
    """reads given element from a file. At least one of 'function_name' or a 'class_name' must be given. For methods, both should be given"""
    if params.function_name and params.class_name:
        return read_method(params.path, params.function_name, params.class_name)
    elif params.function_name:
        return read_function(params.path, params.function_name)
    elif params.class_name:
        return read_class(params.path, params.class_name)


def read_function(path: str, name: str):
    """reads a given function from a file"""
    codebase = Codebase()
    return codebase.get_functions(path, name)


def read_class(path: str, name: str):
    """reads a given class from a file"""
    codebase = Codebase()
    return codebase.get_classes(path, name)


def read_method(path: str, name: str, class_name: str):
    """reads a given method from a file"""
    codebase = Codebase()
    return codebase.get_methods(path, name, class_name)


class CreateFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    content: str = Field(..., description="file content")
    append: bool = Field(
        False, description="if True and file exists, appends content to the file"
    )


@validate_call
def create_file(params: CreateFileParams):
    """creates a new file with the given content"""
    if not os.path.exists(os.path.dirname(params.path)):
        os.makedirs(os.path.dirname(params.path))

    if os.path.exists(params.path):
        if params.append:
            with open(params.path, "a") as f:
                f.write(params.content)
        else:
            raise FileExistsError(f"File {params.path} already exists")
    else:
        with open(params.path, "w") as f:
            f.write(params.content)


class ModifyFileParams(BaseModel):
    path: str = Field(..., description="relative file path, including file name")
    new_content: str = Field(..., description="new content for the modified file")
    line_start: int = Field(1, description="start line to modify content from")
    line_end: int = Field(-1, description="end line to modify content until")


@validate_call
def modify_file(params: ModifyFileParams):
    """modifies the content of a file"""
    # WARNING: currently not use due to difficulty for LLM to recognize lines to modify
    with open(params.path, "r") as f:
        lines = f.readlines()

    lines[params.line_start - 1 : params.line_end] = params.new_content

    with open(params.path, "w") as f:
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
