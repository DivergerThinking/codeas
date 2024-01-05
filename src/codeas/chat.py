from pydantic import BaseModel

from codeas.commands import Context, Implementation
from codeas.thread import Thread

SYSTEM_MESSAGE = """
You are CodeAs, a world-class programmer that can perform any coding request on large codebases using a set of tools (available via function calling).
"""


class Chat(BaseModel):
    context: Context = Context()
    implementation: Implementation = Implementation()
    thread: Thread = Thread(system_prompt=SYSTEM_MESSAGE)

    def ask(self, message: str):
        if "@add-context" in message:
            message = {"role": "user", "content": message.replace("@add-context", "")}
            self.context.add(message)
            self.add_context_to_thread(self.thread)
            self.add_context_to_thread(self.implementation.thread)
        elif "@implement" in message:
            message = {"role": "user", "content": message.replace("@implement", "")}
            self.implementation.implement(self.thread.messages[-2:] + [message])
        else:
            message = {"role": "user", "content": message}
            self.thread.add(message)
            response = self.thread.run()
            self.thread.add(response)

    def add_context_to_thread(self, thread: Thread):
        context_msg = {"role": "user", "content": self.context.get_context()}
        # if context already added, we replace it with modified context
        if len(thread.messages) >= 2 and thread.messages[1]["content"].startswith(
            "CONTEXT:"
        ):
            thread.messages[1] = context_msg
        else:  # otherwise we insert context as first message
            thread.messages.insert(1, context_msg)
