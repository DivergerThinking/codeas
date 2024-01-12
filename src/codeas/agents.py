from typing import List

from pydantic import BaseModel, PrivateAttr

from codeas.configs import (
    context_agent_config,
    search_agent_config,
    writing_agent_config,
)
from codeas.thread import Thread
from codeas.tools import File


class ContextAgent(BaseModel):
    thread: Thread = Thread(**context_agent_config)
    context: List[File] = []

    def run(self, message: str = None):
        if message:
            self.thread.add_message({"role": "user", "content": message})
        response = self.thread.run()
        self.thread.add_message(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in self.thread.run_calls(response["tool_calls"]):
                if isinstance(tool_call["output"], list):
                    self.context.extend(tool_call["output"])
                else:
                    self.context.append(tool_call["output"])

                self.thread.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": "Function call completed",
                    }
                )


class WritingAgent(BaseModel):
    thread: Thread = Thread(**writing_agent_config)
    context: List[File] = []

    def run(self, message: str = None):
        self.thread.add_context(self.context)
        if message:
            self.thread.add_message({"role": "user", "content": message})
        response = self.thread.run()
        self.thread.add_message(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in self.thread.run_calls(response["tool_calls"]):
                self.thread.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": "Function call completed",
                    }
                )


class SearchAgent(BaseModel):
    thread: Thread = Thread(**search_agent_config)
    max_steps: int = 10
    _current_step: int = PrivateAttr(1)

    def run(self, message: str = None):
        if message:
            self.thread.add_message({"role": "user", "content": message})
        response = self.thread.run()
        self.thread.add_message(response)

        if "tool_calls" in response and response["tool_calls"] is not None:
            for tool_call in self.thread.run_calls(response["tool_calls"]):
                tool_call["output"] = (
                    tool_call["output"]
                    if isinstance(tool_call["output"], str)
                    else str(tool_call["output"])
                )
                self.thread.add_message(
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
