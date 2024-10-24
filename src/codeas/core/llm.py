import asyncio
import logging

from openai import AsyncOpenAI, OpenAI

from codeas.configs.llm_params import OPENAI_PARAMS  # Import the parameters


def log_retry(retry_state):
    logging.info(
        "Retrying %s: attempt #%s ended with: %s",
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
    )


class LLMClient:
    batch_size: int = 100
    max_retries: int = 5

    def __init__(self):
        self._client = OpenAI(max_retries=self.max_retries)
        self.temperature = OPENAI_PARAMS["temperature"]
        self.top_p = OPENAI_PARAMS["top_p"]
        self.stream = OPENAI_PARAMS["stream"]
        self.timeout = OPENAI_PARAMS["timeout"]

    def __enter__(self):  # for context manager
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # for context manager
        if self._client is not None:
            self._client.close()  # Close the client
            self._client = None

    def run(self, messages, model="gpt-4o-mini", **kwargs) -> dict:
        kwargs.setdefault("temperature", self.temperature)
        kwargs.setdefault("top_p", self.top_p)
        if not kwargs.get("response_format"):
            kwargs.setdefault("timeout", self.timeout)
            kwargs.setdefault("stream", self.stream)

        if model == "gpt-4o":
            model = "gpt-4o-2024-08-06"
            logging.info("Using gpt-4o-2024-08-06 model")

        if isinstance(messages, list):
            return self.run_completions(messages, model, **kwargs)
        elif isinstance(messages, dict):
            return self.run_batch_completions(messages, model, **kwargs)

    def run_completions(self, messages, model="gpt-4o-mini", **kwargs) -> dict:
        """runs completions synchronously"""
        if kwargs.get("response_format"):
            response = self._client.beta.chat.completions.parse(
                messages=messages, model=model, **kwargs
            )
        else:
            response = self._client.chat.completions.create(
                messages=messages, model=model, **kwargs
            )
        if kwargs.get("stream"):
            response = self._parse_stream(response)
        return response

    def _parse_stream(self, stream):
        """parses stream response from completions"""
        response = {"role": "assistant", "content": None, "tool_calls": None}
        for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta and choice.delta.content:
                self._parse_delta_content(choice.delta, response)
            elif choice.delta and choice.delta.tool_calls:
                self._parse_delta_tools(choice.delta, response)
        return response

    def run_batch_completions(
        self, batch_messages: dict, model="gpt-4o-mini", **kwargs
    ) -> dict:
        """run completions by batch asynchronously"""
        return asyncio.run(self._run_batch_completions(batch_messages, model, **kwargs))

    async def _run_batch_completions(
        self, batch_messages: dict, model: str, **kwargs
    ) -> dict:
        """runs completions by batch asynchronously"""
        async with AsyncOpenAI(max_retries=self.max_retries) as client:
            coroutines = [
                self._run_async_completions(client, messages, model, **kwargs)
                for messages in batch_messages.values()
            ]
            responses = []
            async for batch_responses in self._run_batches(coroutines):
                responses.extend(batch_responses)
            return dict(zip(batch_messages.keys(), responses))

    # @retry(stop=stop_after_attempt(3), after=log_retry)
    async def _run_async_completions(self, client, messages, model: str, **kwargs):
        """runs completions asynchronously"""
        if kwargs.get("response_format"):
            response = await client.beta.chat.completions.parse(
                messages=messages, model=model, **kwargs
            )
        else:
            response = await client.chat.completions.create(
                messages=messages, model=model, **kwargs
            )
        if "stream" in kwargs and kwargs["stream"]:
            response = await self._parse_async_stream(response)
        return response

    async def _parse_async_stream(self, stream):
        """parses stream response from async completions"""
        response = {"role": "assistant", "content": None, "tool_calls": None}
        async for chunk in stream:
            choice = chunk.choices[0]
            if choice.delta and choice.delta.content:
                self._parse_delta_content(choice.delta, response)
            elif choice.delta and choice.delta.tool_calls:
                self._parse_delta_tools(choice.delta, response)
        return response

    async def _run_batches(self, coroutines: list):
        for batch in self._batches(coroutines, self.batch_size):
            yield await asyncio.gather(*batch)

    def _batches(self, items, batch_size):
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    def _parse_delta_content(self, delta, response):
        if response["content"] is None:
            response["content"] = ""

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
