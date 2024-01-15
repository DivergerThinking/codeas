import os

from codeas import tools
from codeas.utils import read_yaml, write_yaml

chat_config = {
    "system_prompt": """

You are a superintelligent machine who assists senior software engineers on working with their codebase.
You will be given context about the codebase at the start of the conversation and some tasks to perform on it.
Think through the request carefully and answer it as well as you can.
In case of doubts, ask the user to provide more information.

""".strip(),
    "model": "gpt-3.5-turbo-1106",
    "temperature": 0,
}


context_agent_config = {
    "system_prompt": """

You are a superintelligent machine who assists senior software engineers by interacting with a codebase.
The engineers will ask you to add certain parts of the codebase to the conversation context in order to later use that context for other tasks.
You can add a file's content, sections of it (lines, functions or classes) or its code structure. 
Some engineers' requests may specify the name and sections of the files to read, while others may not.
DO NOT GUESS ANY PATHS OR SECTIONS TO READ. Ask the user to be more specific if information is missing.

""".strip(),
    "tools": [tools.add_file, tools.add_file_element, tools.add_files_in_dir],
    "model": "gpt-4-1106-preview",
    "temperature": 0,
}

writing_agent_config = {
    "system_prompt": """

You are a superintelligent machine who assists senior software engineers to write content to files.
Pay close attention to the path and the format of the file you are given.

""".strip(),
    "tools": [tools.create_file],
    "model": "gpt-4-1106-preview",
    "temperature": 0,
}

search_agent_config = {
    "system_prompt": """

You are a superintelligent machine who assists senior software engineers to search through a codebase.
You can list the files in the codebase and view a file's content, sections of it (lines, functions or classes) or its code structure.
IMPORTANT:
Think step by step and keep searching through the codebase until you think you have found all of the relevant content.
GUIDELINES:
You should try and minimize the number of files you search through, focusing the part of the codebase you think more relevant.
When you find a relevant file, see which sections of that file are relevant.

""".strip(),
    "tools": [tools.list_files, tools.view_file],
    "model": "gpt-4-1106-preview",
    "temperature": 0,
}


def write_settings():
    settings_keys = ["model", "temperature"]

    if not os.path.exists(".codeas"):
        os.makedirs(".codeas")

    write_yaml(
        ".codeas/settings.yaml",
        {
            "chat_config": {
                key: value for key, value in chat_config.items() if key in settings_keys
            },
            "context_agent_config": {
                key: value
                for key, value in context_agent_config.items()
                if key in settings_keys
            },
            "writing_agent_config": {
                key: value
                for key, value in writing_agent_config.items()
                if key in settings_keys
            },
            "search_agent_config": {
                key: value
                for key, value in search_agent_config.items()
                if key in settings_keys
            },
        },
    )


def update_settings():
    chat_config.update(settings.get("chat_config", {}))
    context_agent_config.update(settings.get("context_agent_config", {}))
    writing_agent_config.update(settings.get("writing_agent_config", {}))
    search_agent_config.update(settings.get("search_agent_config", {}))


if os.path.exists(".codeas/settings.yaml"):
    settings = read_yaml(".codeas/settings.yaml")
    update_settings()
else:
    write_settings()
