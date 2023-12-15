import inspect

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validate_call

load_dotenv()


class ReadFileParams(BaseModel):
    file_path: str = Field(
        ..., description="relative path of file, including file name"
    )


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


@validate_call
def read_file(params: ReadFileParams):
    """reads the content of a file"""
    try:
        with open(params.file_path) as f:
            return f.read()
    except FileNotFoundError:
        return (
            "File not found. Please specify the exact file path, including file name."
        )


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


def get_schemas():
    schemas = []
    for function in [read_file, modify_file, create_file]:
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
