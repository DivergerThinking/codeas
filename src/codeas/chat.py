from typing import List

from prompt_toolkit import prompt
from pydantic import BaseModel

from codeas.agents import ContextAgent, SearchAgent, WritingAgent
from codeas.commands import clear_chat, copy_last_message, view_context
from codeas.thread import Thread
from codeas.utils import File


class Chat(BaseModel):
    context: List[File] = []
    thread: Thread = Thread(
        system_prompt="""
You are a superintelligent machine who assists senior software engineers on working with their codebase.
You will be given context about the codebase at the start of the conversation and some tasks to perform on it.
Think through the request carefully and answer it as well as you can.
In case of doubts, ask the user to provide more information.
""".strip()
    )

    def ask(self, message: str):
        message = self.check_message(message)
        if any(agent in message for agent in ["@context", "@write", "@search"]):
            self.run_agent(message)
        elif any(command in message for command in ["/view", "/clear", "/copy"]):
            self.run_command(message)
        else:
            self.run_thread(message)

    def check_message(self, message: str):
        if "context" in message:
            answer = prompt(
                "Did you mean to use @context agent to add context to the conversation? (y/n): "
            )
            if answer == "y":
                message = message.replace("context", "@context")
        elif "write" in message:
            answer = prompt(
                "Did you mean to use @write agent to write to a file? (y/n): "
            )
            if answer == "y":
                message = message.replace("write", "@write")
        elif "search" in message:
            answer = prompt(
                "Did you mean to use @search agent to search for a file? (y/n): "
            )
            if answer == "y":
                message = message.replace("search", "@search")
        return message

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
            view_context(self)
        elif message.strip() == "/clear":
            clear_chat(self)
        elif message.strip() == "/copy":
            copy_last_message(self)

    def run_thread(self, message: str):
        self.thread.add_context(self.context)
        message = {"role": "user", "content": message}
        self.thread.add(message)
        response = self.thread.run()
        self.thread.add(response)
