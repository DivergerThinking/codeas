from typing import List

from pydantic import BaseModel

from codeas import tools
from codeas.thread import Thread
from codeas.tools import File

CONTEXT_MESSAGE = """
You are a smart computer who need to read the content of files in the file system. 
The user will give you some information about the files that you need to read.
In case you are not given enough information, ask the user to provide it to you.
""".strip()

CONTEXT_TOOLS = [tools.read_file]


class Context(BaseModel):
    files: List[File] = []
    thread: Thread = Thread(system_prompt=CONTEXT_MESSAGE, tools=CONTEXT_TOOLS)

    def add(self, message):
        self.thread.add(message)
        response = self.thread.run()
        self.thread.add(response)
        if "tool_calls" in response and response["tool_calls"] is not None:
            outputs = self.thread.run_tool_calls(response["tool_calls"])
            for output in outputs:
                self.files.append(output)
                # output_msg = {
                #     "role": "tool", "tool_call_id": tool_call["id"], "content": output,
                # }
                # self.thread.add(output_msg)

    def view(self):
        ...

    def preview(self):
        ...

    def get_file_contents(self):
        file_contents = "\n".join([file_.model_dump_json() for file_ in self.files])
        return "CONTEXT:" + file_contents


IMPLEMENT_MESSAGE = """
You are a smart computer who is capable of creating and modifying files.
When asked to modify files, pay attention to the lines of the file which you need to modify""".strip()

IMPLEMENT_TOOLS = [tools.create_file, tools.modify_file]


class Implementation(BaseModel):
    thread: Thread = Thread(system_prompt=IMPLEMENT_MESSAGE, tools=IMPLEMENT_TOOLS)

    def implement(self, messages: list):
        for message in messages:
            self.thread.add(message)
        response = self.thread.run()
        self.thread.add(response)
        if "tool_calls" in response and response["tool_calls"] is not None:
            _ = self.thread.run_tool_calls(response["tool_calls"])
