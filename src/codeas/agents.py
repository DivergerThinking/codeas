from typing import List

from pydantic import BaseModel, PrivateAttr

from codeas import tools
from codeas.thread import Thread
from codeas.tools import File


class ContextAgent(BaseModel):
    thread: Thread = Thread(
        system_prompt="""
You are a smart computer who need to read the content of files in the file system. 
The user will give you some information about the files that you need to read.
In case you are not given enough information, ask the user to provide it to you.
""".strip(),
        tools=[tools.read_file, tools.read_file_element, tools.ask_assistant_to_search],
    )
    context: List[File] = []

    def run(self, message: str = None):
        if message:
            self.thread.add({"role": "user", "content": message})

        response = self.thread.run()
        self.thread.add(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in response["tool_calls"]:
                self.context.append(self.thread.call(tool_call))
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
You are a smart computer who is capable of writing content to files on the file system.
When asked to modify files, pay attention to the lines of the file which you need to modify
""".strip(),
        tools=[tools.create_file],
    )
    context: List[File] = []

    def run(self, message: list):
        self.thread.add(message)
        response = self.thread.run()
        self.thread.add(response)
        if "tool_calls" in response and response["tool_calls"] is not None:
            _ = self.thread.run_tool_calls(response["tool_calls"])


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
Once you are done searching, return to the user a final answer listing the files and sections you have found relevant.
""".strip(),
        tools=[tools.list_files, tools.view_file, tools.return_answer],
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
            for tool_call in response["tool_calls"]:
                output = self.thread.call(tool_call)

                # as soon as the return_answer is given, we stop searching
                if tool_call["function"]["name"] == "return_answer":
                    return output

                output = output if isinstance(output, str) else str(output)
                self.thread.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": output,
                    }
                )
        self._current_step += 1

        if self._current_step > self.max_steps:
            return "Couldn't return an answer in the given number of search steps."
        else:
            self.search()


if __name__ == "__main__":
    search = SearchAgent()
    response = search.search("which code is related to parsing the codebase?")
    print(response)
