from typing import Any, Callable, List

from openai import OpenAI
from pydantic import BaseModel
from rich.live import Live
from rich.pretty import Pretty, pprint

from codeas.tools import get_schemas
from codeas.utils import File, console, end_message_block, start_message_block


class Thread(BaseModel):
    system_prompt: str = None
    tools: List[Callable] = None
    use_terminal: bool = False
    model: str = "gpt-3.5-turbo-1106"
    temperature: float = 0
    messages: List[str] = []
    verbose: bool = True
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
        if self.verbose and self.use_console:
            start_message_block("Assistant", "blue")

        response = {"role": "assistant", "content": None, "tool_calls": None}
        for chunk in self._run_completion():
            choice = chunk.choices[0]

            if choice.delta and choice.delta.content:
                self._parse_delta_content(choice.delta, response)
                if self.verbose:
                    self._print_delta_content(choice.delta)

            elif choice.delta and choice.delta.tool_calls:
                if response["tool_calls"] is None:  # only runs on first chunk
                    response["tool_calls"] = []
                    if self.verbose and self.use_console:
                        live = Live()
                        live.start()

                self._parse_delta_tools(choice.delta, response)
                if self.verbose and self.use_console:
                    self._print_delta_tools(response, live)

            elif choice.finish_reason is not None:  # only runs on last chunk
                if self.verbose and self.use_console and response["tool_calls"]:
                    live.stop()
                elif (
                    self.verbose
                    and self.use_console is False
                    and response["tool_calls"]
                ):
                    pprint(response, expand_all=True)

        if self.verbose and self.use_console:
            end_message_block("blue")

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

    def _parse_delta_content(self, delta, response):
        if response["content"] is None:
            response["content"] = delta.content
        else:
            response["content"] += delta.content

    def _print_delta_content(self, delta):
        if self.use_console:
            console.print(delta.content, end="")
        else:
            print(delta.content, end="")

    def _parse_delta_tools(self, delta, response):
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

    def _print_delta_tools(self, response, live):
        pretty = Pretty(response, expand_all=True)
        live.update(pretty)

    def run_calls(self, tool_calls: List[dict]):
        if self.verbose and self.use_console:
            start_message_block("Calls", "blue")

        for tool_call in tool_calls:
            tool_call["output"] = self.call(tool_call)
            yield tool_call

        if self.verbose and self.use_console:
            end_message_block("blue")

    def call(self, tool_call: dict):
        function, args = self._get_function_args(tool_call)
        try:
            self._print_call(function, args)
            output = function(eval(args))
            self._print_call_success()
            return output
        except Exception as e:
            self._print_call_error(e)

    def _get_function_args(self, tool_call: dict):
        function = [
            tool
            for tool in self.tools
            if tool.__name__ == tool_call["function"]["name"]
        ][0]
        # fix booleans without capital letters
        args = tool_call["function"]["arguments"]
        args = args.replace("true", "True")
        args = args.replace("false", "False")
        return function, args

    def _print_call(self, function, args):
        if self.use_console:
            console.print(f"Calling: {function.__name__}({args})")
        else:
            print(f"Calling: {function.__name__}({args})")

    def _print_call_success(self):
        if self.use_console:
            console.print(">>> Call successful\n")
        else:
            print(">>> Call successful\n")

    def _print_call_error(self, e):
        if self.use_console:
            console.print(f">>> Call failed: {e}\n")
        else:
            print(f">>> Call failed: {e}\n")


if __name__ == "__main__":
    from codeas import tools

    thread = Thread(
        console=False, tools=[tools.create_file], model="gpt-4-1106-preview"
    )
    thread.add({"role": "user", "content": "write hello world to ./file.txt"})
    response = thread.run()
    for tool_call in thread.run_calls(response["tool_calls"]):
        pass
