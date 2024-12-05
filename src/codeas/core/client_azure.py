import asyncio
import logging
import os

from openai import AsyncAzureOpenAI, AzureOpenAI

OPENAI_PARAMS = {
    "temperature": 0.3,
    "top_p": 0.7,
    "stream": True,
    "timeout": 10,
}


def log_retry(retry_state):
    logging.info(
        "Retrying %s: attempt #%s ended with: %s",
        retry_state.fn,
        retry_state.attempt_number,
        retry_state.outcome,
    )


class LLMClientAzure:
    batch_size: int = 100
    max_retries: int = 5

    def __init__(self):
        self._client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-10-21",
            max_retries=self.max_retries,
        )

    def __enter__(self):  # for context manager
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # for context manager
        if self._client is not None:
            self._client.close()  # Close the client
            self._client = None

    def run(self, messages, model="gpt-4o-mini", **kwargs) -> dict:
        kwargs.setdefault("temperature", OPENAI_PARAMS["temperature"])
        kwargs.setdefault("top_p", OPENAI_PARAMS["top_p"])
        if not kwargs.get("response_format"):
            kwargs.setdefault("timeout", OPENAI_PARAMS["timeout"])
            kwargs.setdefault("stream", OPENAI_PARAMS["stream"])

        if isinstance(messages, list):
            return self.run_completions(messages, model, **kwargs)
        elif isinstance(messages, dict):
            return self.run_batch_completions(messages, model, **kwargs)

    def vectorize(self, text, model="text-embedding-ada-002"):
        if isinstance(text, str):
            return self.vectorize_sync(text, model)
        elif isinstance(text, dict):
            return self.vectorize_batch(text, model)
        else:
            raise ValueError(
                "text must be a string or a dictionary of type Dict[str, str]"
            )

    def vectorize_batch(self, texts: dict, model="text-embedding-ada-002"):
        return asyncio.run(self._vectorize_batch(texts, model))

    async def _vectorize_batch(self, texts: dict, model: str):
        async with AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-10-21",
            max_retries=self.max_retries,
        ) as client:
            coroutines = [
                self._vectorize_async(client, text, model) for text in texts.values()
            ]
            responses = []
            async for batch_responses in self._run_batches(coroutines):
                responses.extend(batch_responses)
            return dict(zip(texts.keys(), responses))

    async def _vectorize_async(self, client, text, model="text-embedding-ada-002"):
        response = await client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    def vectorize_sync(self, text, model="text-embedding-ada-002"):
        response = self._client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

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
        content = ""
        for chunk in stream:
            if any(chunk.choices):
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    content += choice.delta.content
        return content

    def run_batch_completions(
        self, batch_messages: dict, model="gpt-4o-mini", **kwargs
    ) -> dict:
        """run completions by batch asynchronously"""
        return asyncio.run(self._run_batch_completions(batch_messages, model, **kwargs))

    async def _run_batch_completions(
        self, batch_messages: dict, model: str, **kwargs
    ) -> dict:
        """runs completions by batch asynchronously"""
        async with AsyncAzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-10-21",
            max_retries=self.max_retries,
        ) as client:
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
        content = ""
        async for chunk in stream:
            if any(chunk.choices):
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    content += choice.delta.content
        return content

    async def _run_batches(self, coroutines: list):
        for batch in self._batches(coroutines, self.batch_size):
            yield await asyncio.gather(*batch)

    def _batches(self, items, batch_size):
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]
