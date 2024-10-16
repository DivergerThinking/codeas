import openai
from anthropic import Anthropic
from pydantic import BaseModel

# import google.generativeai as genai


PROVIDERS = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "o1-preview": "openai",
    "o1-mini": "openai",
    "claude-3-5-sonnet": "anthropic",
    "claude-3-haiku": "anthropic",
    "gemini-15-flash": "google",
    "gemini-15-pro": "google",
}


class LLMClients(BaseModel):
    model: str

    def run(self, messages: list):
        """Run a non-streaming request."""
        provider = PROVIDERS.get(self.model)

        if provider == "openai":
            return self._run_openai(messages)
        elif provider == "anthropic":
            return self._run_anthropic(messages)
        elif provider == "google":
            return self._run_google(messages)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def stream(self, messages: list):
        """Run a streaming request."""
        provider = PROVIDERS.get(self.model)

        if provider == "openai":
            yield from self._stream_openai(messages)
        elif provider == "anthropic":
            yield from self._stream_anthropic(messages)
        elif provider == "google":
            yield from self._stream_google(messages)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def _run_openai(self, messages: list):
        client = openai.OpenAI()
        return client.chat.completions.create(
            model=self.model, messages=messages, stream=False
        )

    def _stream_openai(self, messages: list):
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model, messages=messages, stream=True
        )
        for chunk in response:
            yield chunk.choices[0].delta.content or ""

    def _run_anthropic(self, messages: list):
        if self.model == "claude-3-5-sonnet":
            self.model = "claude-3-5-sonnet-20240620"
        client = Anthropic()
        return client.messages.create(
            max_tokens=8192,
            model=self.model,
            messages=messages,
        )

    def _stream_anthropic(self, messages: list):
        if self.model == "claude-3-5-sonnet":
            self.model = "claude-3-5-sonnet-20240620"
        client = Anthropic()
        with client.messages.stream(
            max_tokens=8192,
            model=self.model,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _run_google(self, messages: list):
        # Implement non-streaming Google API call here
        return "Google API response"

    def _stream_google(self, messages: list):
        # Implement streaming Google API call here
        yield "Google API streaming response"


if __name__ == "__main__":
    clients = LLMClients(model="gpt-4o-mini")
    # test the stream method
    for chunk in clients.stream([{"role": "user", "content": "Hello, world!"}]):
        print(chunk, end="", flush=True)
    ...
