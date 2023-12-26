from typing import Any, Callable, List

from openai import OpenAI
from pydantic import BaseModel

from codeas.console import RichConsole
from codeas.tools import get_schemas


class Thread(BaseModel):
    system_prompt: str = None
    tools: List[Callable] = None
    use_terminal: bool = False
    model: str = "gpt-3.5-turbo-1106"
    temperature: float = 0
    messages: List[str] = []

    def model_post_init(self, __context: Any) -> None:
        if self.system_prompt is not None:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def add(self, message: dict):
        if "tool_calls" in message and message["tool_calls"] is None:
            message.pop("tool_calls")
        self.messages.append(message)

    def run(self, display: bool = True):
        response = {"role": "assistant", "content": None, "tool_calls": None}
        console = RichConsole()
        for chunk in self._run_completion():
            if display:
                console.display(chunk.choices[0].delta.content)
            else:
                print(chunk.choices[0].delta.content, end="")
            self._parse(chunk, response)
        console.end()
        return response

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

    def run_tool_calls(self, tool_calls: list):
        outputs = []
        for tool_call in tool_calls:
            outputs.append(self.call(tool_call))
        return outputs

    def call(self, tool_call: dict):
        function = [
            tool
            for tool in self.tools
            if tool.__name__ == tool_call["function"]["name"]
        ][0]
        return function(eval(tool_call["function"]["arguments"]))


thread = Thread()
thread.add({"role": "user", "content": "Hello"})
thread.run()
