from typing import List

from pydantic import BaseModel, PrivateAttr

from codeas import tools
from codeas.thread import Thread
from codeas.tools import File


class ContextAgent(BaseModel):
    thread: Thread = Thread(
        system_prompt="""
You are a superintelligent machine who assists senior software engineers by interacting with a codebase.
The engineers will ask you to add certain parts of the codebase to the conversation context in order to later use that context for other tasks.
You can add a file's content, sections of it (lines, functions or classes) or its code structure. 
Some engineers' requests may specify the name and sections of the files to read, while others may not.
DO NOT GUESS ANY PATHS OR SECTIONS TO READ. Ask the user to be more specific if information is missing
""".strip(),
        tools=[tools.add_file, tools.add_file_element, tools.add_files_in_dir],
        model="gpt-4-1106-preview",
    )
    context: List[File] = []

    def run(self, message: str = None):
        if message:
            self.thread.add({"role": "user", "content": message})
        response = self.thread.run()
        self.thread.add(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in self.thread.run_calls(response["tool_calls"]):
                if isinstance(tool_call["output"], list):
                    self.context.extend(tool_call["output"])
                else:
                    self.context.append(tool_call["output"])

                self.thread.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": "Function call completed",
                    }
                )


class WritingAgent(BaseModel):
    thread: Thread = Thread(
        system_prompt="""
You are a superintelligent machine who assists senior software engineers to write content to files.
Pay close attention to the path and the format of the file you are given.
""".strip(),
        tools=[tools.create_file],
    )
    context: List[File] = []

    def run(self, message: str = None):
        self.thread.add_context(self.context)
        if message:
            self.thread.add({"role": "user", "content": message})
        response = self.thread.run()
        self.thread.add(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in self.thread.run_calls(response["tool_calls"]):
                self.thread.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": "Function call completed",
                    }
                )


class SearchAgent(BaseModel):
    thread: Thread = Thread(
        system_prompt="""
You are a superintelligent machine who assists senior software engineers to search through a codebase.
You can list the files in the codebase and view a file's content, sections of it (lines, functions or classes) or its code structure.
IMPORTANT:
Think step by step and keep searching through the codebase until you think you have found all of the relevant content.
GUIDELINES:
You should try and minimize the number of files you search through, focusing the part of the codebase you think more relevant.
When you find a relevant file, see which sections of that file are relevant.
""".strip(),
        tools=[tools.list_files, tools.view_file],
        model="gpt-4-1106-preview",
    )
    max_steps: int = 10
    _current_step: int = PrivateAttr(1)

    def run(self, message: str = None):
        if message:
            self.thread.add({"role": "user", "content": message})
        response = self.thread.run()
        self.thread.add(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in self.thread.run_calls(response["tool_calls"]):
                tool_call["output"] = (
                    tool_call["output"]
                    if isinstance(tool_call["output"], str)
                    else str(tool_call["output"])
                )
                self.thread.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_call["output"],
                    }
                )
            self._current_step += 1

            if self._current_step > self.max_steps:
                return "Maximum number of search steps reached"
            else:
                self.run()
