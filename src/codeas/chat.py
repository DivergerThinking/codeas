from typing import List

from pydantic import BaseModel

from codeas.agents import ContextAgent, SearchAgent, WritingAgent
from codeas.commands import view_context
from codeas.thread import Thread
from codeas.utils import File

SYSTEM_MESSAGE = """
You are a superintelligent machine who assists senior software engineers on working with their codebase.
You will be given context about the codebase at the start of the conversation and some tasks to perform on it.
Think through the request carefully and answer it as well as you can.
In case of doubts, ask the user to provide more information.
"""


class Chat(BaseModel):
    context: List[File] = []
    thread: Thread = Thread(system_prompt=SYSTEM_MESSAGE)

    def ask(self, message: str):
        if "@" in message and message.split("@", 1)[1].split(" ")[0] in [
            "context",
            "write",
            "search",
        ]:
            self.run_agent(message)
        elif message.strip() in ["/view", "/clear"]:
            self.run_command(message)
        else:
            self.run_thread(message)

    def run_agent(self, message: str):
        if "@context" in message:
            agent = ContextAgent()
            agent.run(message)
            self.context = agent.context
        elif "@write" in message:
            agent = WritingAgent(context=self.context)
            agent.run(message)
        elif "@search" in message:
            agent = SearchAgent()
            agent.run(message)

    def run_command(self, message: str):
        if message.strip() == "/view":
            view_context(self.context)
        elif message.strip() == "/clear":
            self.context = []

    def run_thread(self, message: str):
        self.thread.add_context(self.context)
        message = {"role": "user", "content": message}
        self.thread.add(message)
        response = self.thread.run()
        self.thread.add(response)
