from pydantic import BaseModel

from codeas.commands import Context
from codeas.thread import Thread

SYSTEM_MESSAGE = """
You are CodeAs, a world-class programmer that can perform any coding request on large codebases using a set of tools (available via function calling).
"""


class Chat(BaseModel):
    context: Context = Context()
    thread: Thread = Thread(system_prompt=SYSTEM_MESSAGE)

    def ask(self, message):
        if "@add-context" in message:
            self.context.add(message)
        else:
            if any(self.context.files):
                message += self.context.get_file_contents()
            self.thread.add({"role": "user", "content": message})
            return self.thread.run()
