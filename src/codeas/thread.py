from typing import Any, Callable, List

import tiktoken
from openai import OpenAI
from pydantic import BaseModel, PrivateAttr
from rich.live import Live
from rich.pretty import Pretty, pprint

from codeas.tools import get_schemas
from codeas.utils import File, console, end_message_block, start_message_block

MODEL_INFO = {
    "gpt-4-1106-preview": {"context": 128192, "inprice": 0.01, "outprice": 0.03},
    "gpt-4": {"context": 8192, "inprice": 0.03, "outprice": 0.06},
    "gpt-4-0613": {"context": 8192, "inprice": 0.03, "outprice": 0.06},
    "gpt-4-32k": {"context": 32000, "inprice": 0.06, "outprice": 0.12},
    "gpt-4-32k-0613": {"context": 32000, "inprice": 0.06, "outprice": 0.12},
    "gpt-3.5-turbo-1106": {"context": 16385, "inprice": 0.0010, "outprice": 0.0020},
    "gpt-3.5-turbo-instruct": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo-0613": {"context": 4096, "inprice": 0.0015, "outprice": 0.0020},
    "gpt-3.5-turbo-16k": {"context": 16385, "inprice": 0.0030, "outprice": 0.0040},
    "gpt-3.5-turbo-16k-0613": {"context": 16385, "inprice": 0.0030, "outprice": 0.0040},
}
MAX_PCT_INPUT_TOKENS = 0.8  # leave at least 20% of context for output


class Thread(BaseModel):
    system_prompt: str = None
    tools: List[Callable] = None
    model: str = "gpt-3.5-turbo-1106"
    temperature: float = 0
    verbose: bool = True
    use_console: bool = True
    max_tokens_per_completion: int = None
    _context: PrivateAttr(str) = None
    _messages: PrivateAttr(List[str]) = []

    def model_post_init(self, __context: Any) -> None:
        # executed on model instantiation
        if self.system_prompt is not None:
            self.add_message({"role": "system", "content": self.system_prompt})

    def run(self):
        if self.verbose and self.use_console:
            start_message_block("Assistant", "blue")

        self._add_context_to_messages()

        self.trim_messages()
        response = self._run_messages()

        self._remove_context_from_messages()

        if self.verbose and self.use_console:
            end_message_block("blue")

        return response

    def _add_context_to_messages(self):
        if self._context is not None:
            msg_idx = 1 if self.system_prompt else 0
            self._messages.insert(msg_idx, {"role": "user", "content": self._context})

    def _remove_context_from_messages(self):
        if self._context is not None:
            msg_idx = 1 if self.system_prompt else 0
            self._messages.pop(msg_idx)

    def trim_messages(self):
        if self.check_messages_fit_context_window() is False:
            if self.check_codebase_context_fits() is False:
                print("ERROR: Context is too long. Reduce context size")
                return  # don't run if codebase context doesn't fit
            else:  # remove oldest messages until it fits
                self.remove_oldest_messages()

    def _run_messages(self):
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
        return response

    def check_messages_fit_context_window(self):
        num_tokens = self.count_tokens_from_messages()
        try:
            if self.max_tokens_per_completion is None:
                self.max_tokens_per_completion = (
                    MODEL_INFO[self.model]["context"] * MAX_PCT_INPUT_TOKENS
                )
        except KeyError:
            print("WARNING: model not found. Assuming model max context is 4k tokens.")
            self.max_tokens_per_completion = 4096 * MAX_PCT_INPUT_TOKENS
        if num_tokens > self.max_tokens_per_completion:
            return False
        return True

    def check_codebase_context_fits(self):
        if self._context:
            if self.count_tokens(self._context) > self.max_tokens_per_completion:
                return False
        return True

    def remove_oldest_messages(self):
        start_msg_idx = 1 if self.system_prompt else 0
        start_msg_idx += 1 if self._context else 0

        while self.count_tokens_from_messages() > self.max_tokens_per_completion:
            if len(self._messages) == start_msg_idx + 1:
                # if only one single message remaining, we stop there
                return
            else:
                self._messages.pop(start_msg_idx)

    def _run_completion(self):
        client = OpenAI()
        for chunk in client.chat.completions.create(
            model=self.model,
            messages=self._messages,
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

    def count_tokens_from_messages(self):
        """Return the number of tokens used by a list of messages.
        See: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens_per_message = 3
        tokens_per_name = 1
        num_tokens = 0
        for message in self._messages:
            num_tokens += tokens_per_message
            if len(message) == 2:
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
                if len(message) == 3:
                    for key, _, value in message.items():
                        num_tokens += len(encoding.encode(value))
                        if key == "name":
                            num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def count_tokens(self, text: str):
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))

    def add_message(self, message: dict):
        if "tool_calls" in message and message["tool_calls"] is None:
            message.pop("tool_calls")
        self._messages.append(message)

    def add_context(self, context: List[File]):
        """adds codebase context to the thread"""
        if any(context):
            self._context = """###CODEBASE CONTEXT###\n""" + "\n".join(
                [f"{c.path}\n{c.content}" for c in context]
            )


if __name__ == "__main__":
    from codeas import tools

    thread = Thread(
        console=False,
        tools=[tools.create_file],
        model="gpt-3.5-turbo-1106",
        max_tokens_per_completion=100,
    )
    thread.add_message(
        {"role": "user", "content": "hi, please write a random story of 10 words"}
    )
    response = thread.run()
