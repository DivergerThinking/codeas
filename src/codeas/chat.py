from openai import OpenAI
from pydantic import BaseModel, PrivateAttr
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from codeas import tools

SYSTEM_MESSAGE = """
You are CodeAs, a world-class programmer that can perform any coding request on large codebases using a set of tools (available via function calling).
These tools are mostly related to interacting with your file system such as viewing the current directory structure and reading/modifying/creating files. 
IMPORTANT: First, write a plan on how you are going to interact with the file system. **Always recap the plan each step of the way** (you have extreme short-term memory loss, so you need to recap the plan between each message block to retain it).
An example on modifying a file based on some request would be: 1. get the file path, 2. read the file, 3. identify what changes need to be made to the file, 4. modify the file
"""


class Chat(BaseModel):
    use_terminal: bool = True
    stream: bool = True
    model: str = "gpt-3.5-turbo-1106"
    temperature: float = 0
    _messages: list = PrivateAttr(
        default=[{"content": SYSTEM_MESSAGE, "role": "system"}]
    )

    def ask(self, message):
        self._messages.append({"role": "user", "content": message})

        response = self._run_and_display(self._messages)

        if response["tool_calls"] is None:
            response.pop("tool_calls")
            self._messages.append(response)
        else:
            self._messages.append(response)
            self._execute_tool_calls(response)

    def _execute_tool_calls(self, response):
        for tool_call in response["tool_calls"]:
            function_output = str(
                self._execute_function(
                    tool_call["function"]["name"], tool_call["function"]["arguments"]
                )
            )
            self._messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": function_output,
                }
            )
        # re-execute assistant with function output
        response = self._run_and_display(self._messages)
        self._messages.append(response)
        # if the model returns tool calls again, re-execute them
        if response["tool_calls"] is not None:
            self._execute_tool_calls(response)

    def _execute_function(self, function_name, arguments):
        return getattr(tools, function_name)(eval(arguments))

    def _run_and_display(self, messages):
        response = self._run_completion(messages)
        if self.use_terminal:
            response = self._parse_and_display_in_terminal(response)
        else:
            response = self._parse_and_display(response)
        return response

    def _run_completion(self, messages):
        client = OpenAI()
        return client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=self.stream,
            tools=tools.get_schemas(),
        )

    def _parse_and_display_in_terminal(self, response):
        console = Console()
        if self.stream:
            dynamic_text = Text()
            panel = Panel(dynamic_text, title="OpenAI Response")
            with Live(
                panel, console=console, refresh_per_second=10, transient=True
            ) as live:
                response = self._parse_and_display(response, dynamic_text, live)
            console.print(panel)
        else:
            response = self._parse_and_display(response, console=console)
        return response

    def _parse_and_display(self, response, dynamic_text=None, live=None, console=None):
        if self.stream:
            response = self._parse_and_display_stream(response, dynamic_text, live)
        else:
            response = self._parse_and_display_response(response, console)
        return response

    def _parse_and_display_stream(self, stream, dynamic_text=None, live=None):
        response = {"role": "assistant", "content": None, "tool_calls": None}
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                self._parse_delta_content(delta, response)
                self._display_delta_content(delta, dynamic_text, live)
            elif delta and delta.tool_calls:
                self._parse_delta_tools(delta, response)
        return response

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

    def _display_delta_content(self, delta, dynamic_text=None, live=None):
        if live:
            dynamic_text.append(delta.content)
            live.update(Panel(dynamic_text, title="OpenAI Response"))
        else:
            print(delta["content"], end="")

    def _parse_and_display_response(self, response, console=None):
        content = response.choices[0].message.content
        if content is not None:
            if console is not None:
                console.print(Panel(Text(content), title="OpenAI Response"))
            else:
                print(content)
        return response.choices[0].message.model_dump()
