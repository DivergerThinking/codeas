import inspect

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from codeas.codebase import Codebase

load_dotenv()


class GetPathsParams(BaseModel):
    dir_path: str = Field(".", description="relative path of directory to list")


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


def get_file_paths(params: GetPathsParams):
    """reads the current working directory structure"""
    return Codebase().get_modules_paths()


def read_file(params: ReadFileParams):
    """reads the content of a file"""
    try:
        with open(params.file_path) as f:
            return f.read()
    except FileNotFoundError:
        return "File not found. Make sure the full file path is specified. You can use the get_file_paths function to get the list of relevant file paths."


def modify_file(params: ModifyFileParams):
    """modifies the content of a file"""
    ...


def create_file(params: CreateFileParams):
    """creates a new file with the given content"""
    with open(params.file_path, "w") as f:
        f.write(params.content)


def get_schema(function):
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


def get_tools():
    schemas = []
    for function in [get_file_paths, read_file, modify_file, create_file]:
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": function.__name__,
                    "description": function.__doc__,
                    "parameters": get_schema(function),
                },
            }
        )
    return schemas


# def chat_completion_request(messages, model="gpt-3.5-turbo-1106", use_terminal=True):
#     client = OpenAI()

#     if use_terminal:
#         # use rich to display the response as a text panel in the terminal
#         console = Console()
#         dynamic_text = Text()
#         panel = Panel(dynamic_text, title="OpenAI Response")
#         with Live(panel, console=console, refresh_per_second=10, transient=True) as live:
#             # Start streaming response from the OpenAI client
#             stream = client.chat.completions.create(
#                 model=model,
#                 messages=messages,
#                 stream=True,
#                 tools=get_tools(),
#             )
#             # Iterate over each chunk in the stream
#             response = ""
#             for chunk in stream:
#                 content = chunk.choices[0].delta.content
#                 if content is not None:
#                     dynamic_text.append(content)
#                     live.update(Panel(dynamic_text, title="OpenAI Response"))
#                     response += content

#         # This is outside the "with" scope, so when streaming ends, the updated panel will persist
#         console.print(panel)
#     else:
#         # Start streaming response from the OpenAI client
#         stream = client.chat.completions.create(
#             model=model,
#             messages=messages,
#             stream=True,
#             tools=get_tools(),
#         )
#         # Iterate over each chunk in the stream
#         response = ""
#         for chunk in stream:
#             content = chunk.choices[0].delta.content
#             if content is not None:
#                 print(content, end="")
#                 response += content

#     return response


# SYSTEM_MESSAGE = """
# You are CodeAs, a world-class programmer that can perform any coding request on large codebases using a set of tools (available via function calling).
# These tools are mostly related to interacting with your file system such as viewing the current directory structure and reading/modifying/creating files.
# IMPORTANT: First, write a plan on how you are going to interact with the file system. **Always recap the plan each step of the way** (you have extreme short-term memory loss, so you need to recap the plan between each message block to retain it).
# An example on modifying a file based on some request would be: 1. get the file path, 2. read the file, 3. identify what changes need to be made to the file, 4. modify the file
# """


# class Thread(BaseModel):
#     _messages: list = PrivateAttr(
#         default=[{"content": SYSTEM_MESSAGE, "role": "system"}]
#     )

#     def ask(self, msg):
#         self._messages.append({"content": msg, "role": "user"})
#         return chat_completion_request(self._messages)


# client = OpenAI()
# stream = client.chat.completions.create(
#     model="gpt-3.5-turbo-1106",
#     messages=[{"content": SYSTEM_MESSAGE, "role": "system"}, {"content": "can you read main.py file", "role": "user"}],
#     stream=True,
#     tools=get_function_schemas(
#         [get_file_paths, read_file, modify_file, create_file]
#     ),
# )

# accumulated_deltas = {}
# # Iterate over each chunk in the stream
# response = ""
# for chunk in stream:
#     chunk = chunk.model_dump()
#     if "choices" not in chunk or len(chunk["choices"]) == 0:
#         # This happens sometimes
#         continue

#     delta = chunk["choices"][0]["delta"]
#     # Accumulate deltas
#     accumulated_deltas = merge_deltas(accumulated_deltas, delta)
#     print(accumulated_deltas)
# thread = Thread()
# res = thread.ask("Can you help me modify a file?")
# print()
