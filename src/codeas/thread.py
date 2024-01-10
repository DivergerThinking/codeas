from typing import Any, Callable, List

from openai import OpenAI
from pydantic import BaseModel
from rich.console import Console

from codeas.tools import get_schemas
from codeas.utils import File


class Thread(BaseModel):
    system_prompt: str = None
    tools: List[Callable] = None
    use_terminal: bool = False
    model: str = "gpt-3.5-turbo-1106"
    temperature: float = 0
    messages: List[str] = []
    use_console: bool = True

    def model_post_init(self, __context: Any) -> None:
        if self.system_prompt is not None:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def add(self, message: dict):
        if "tool_calls" in message and message["tool_calls"] is None:
            message.pop("tool_calls")
        self.messages.append(message)

    def add_context(self, context: List[File]):
        """adds codebase context to the thread"""
        if any(context):
            context_msg = {
                "role": "user",
                "content": (
                    """###CONTEXT###\n"""
                    + "\n".join([f"{c.path}\n{c.content}" for c in context])
                ),
            }
            messages = self.messages
            if len(messages) > 1 and messages[1]["content"].startswith("###CONTEXT###"):
                messages[1] = context_msg
            else:
                messages.insert(1, context_msg)

    def run(self):
        response = {"role": "assistant", "content": None, "tool_calls": None}
        console = Console()
        for chunk in self._run_completion():
            content = chunk.choices[0].delta.content
            if content:
                self._start_message_block(console, response)
                if self.use_console:
                    console.print(content, end="")
                else:
                    print(content, end="")
            self._parse(chunk, response)
        if response["content"] is not None:
            self._end_message_block(console)
        return response

    def _start_message_block(self, console, response):
        # only start block on first iteration, while response["content"] is still empty
        if response["content"] is None:
            console.print("\n")
            console.rule("Assistant")

    def _end_message_block(self, console):
        console.print("\n")
        console.rule()

    def _run_completion(self):
        client = OpenAI()
        for chunk in client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=get_schemas(self.tools),
            temperature=self.temperature,
            stream=True,
        ):
            yield chunk

    def _parse(self, chunk, response):
        delta = chunk.choices[0].delta
        if delta and delta.content:
            self._parse_delta_content(delta, response)
        elif delta and delta.tool_calls:
            self._parse_delta_tools(delta, response)

    def _parse_delta_content(self, delta, response):
        if response["content"] is None:
            response["content"] = delta.content
        else:
            response["content"] += delta.content

    def _parse_delta_tools(self, delta, response):
        if response["tool_calls"] is None:
            response["tool_calls"] = []
        for tchunk in delta.tool_calls:
            if len(response["tool_calls"]) <= tchunk.index:
                response["tool_calls"].append(
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                )
            if tchunk.id:
                response["tool_calls"][tchunk.index]["id"] += tchunk.id
            if tchunk.function.name:
                response["tool_calls"][tchunk.index]["function"][
                    "name"
                ] += tchunk.function.name
            if tchunk.function.arguments:
                response["tool_calls"][tchunk.index]["function"][
                    "arguments"
                ] += tchunk.function.arguments

    def call(self, tool_call: dict):
        function = [
            tool
            for tool in self.tools
            if tool.__name__ == tool_call["function"]["name"]
        ][0]
        # fix booleans without capital letters
        args = tool_call["function"]["arguments"]
        args = args.replace("true", "True")
        args = args.replace("false", "False")
        return function(eval(args))
