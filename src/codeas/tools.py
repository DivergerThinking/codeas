import inspect

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validate_call
from rich.console import Console

load_dotenv()


class ReadFileParams(BaseModel):
    file_path: str = Field(
        ..., description="relative path of file, including file name"
    )
    line_start: int = Field(1, description="start line to read")
    line_end: int = Field(-1, description="end line to read")


class CreateFileParams(BaseModel):
    file_path: str = Field(
        ..., description="relative path of file, including file name"
    )
    content: str = Field("json", description="file content")


class ModifyFileParams(BaseModel):
    file_path: str = Field(..., description="file relative path, including file name")
    modifications: str = Field(..., description="modifications to apply to file")
    line_block: str = Field(
        None, description="line block where modifications should be applied"
    )


class File(BaseModel):
    path: str
    content: str
    line_start: int
    line_end: int


@validate_call
def read_file(params: ReadFileParams):
    """reads the content of a file"""
    try:
        console = Console()
        console.print("\n")
        console.rule("Function", style="blue")
        console.print(f"Reading file: {params.file_path}\n")

        with open(params.file_path) as f:
            content = "".join(f.readlines()[params.line_start - 1 : params.line_end])

        file_ = File(
            path=params.file_path,
            content=content,
            line_start=params.line_start,
            line_end=params.line_end,
        )
        console.print(f"Successfully read file: {params.file_path}")
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


@validate_call
def modify_file(params: ModifyFileParams):
    """modifies the content of a file"""
    ...


@validate_call
def create_file(params: CreateFileParams):
    """creates a new file with the given content"""
    with open(params.file_path, "w") as f:
        f.write(params.content)


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
