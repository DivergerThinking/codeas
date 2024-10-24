import logging
import os

import google.generativeai as genai
import openai
import tokencost
from anthropic import Anthropic
from pydantic import BaseModel

# Configure Google API
google_api_key = os.environ.get("GOOGLE_API_KEY")
if google_api_key:
    genai.configure(api_key=google_api_key)
else:
    logging.warning("GOOGLE_API_KEY not set. Google AI features may not work.")

MODELS = {
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "o1-preview": "openai",
    "o1-mini": "openai",
    "claude-3-5-sonnet": "anthropic",
    "claude-3-haiku": "anthropic",
    "gemini-1.5-flash": "google",
    "gemini-1.5-pro": "google",
}


class LLMClients(BaseModel):
    model: str
    provider: str = ""
    max_tokens: int = -1

    def model_post_init(self, _):
        self.provider = MODELS[self.model]
        if self.model == "claude-3-5-sonnet":
            self.model = "claude-3-5-sonnet-20241022"
            self.max_tokens = 8192
        if self.model == "claude-3-haiku":
            self.model = "claude-3-haiku-20240307"
            self.max_tokens = 4096
        if self.model == "gpt-4o":
            self.model = "gpt-4o-2024-08-06"

    def run(self, messages: list):
        """Run a non-streaming request."""
        if self.provider == "openai":
            return self._run_openai(messages)
        elif self.provider == "anthropic":
            return self._run_anthropic(messages)
        elif self.provider == "google":
            return self._run_google(messages)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def stream(self, messages: list):
        """Run a streaming request."""
        if self.provider == "openai":
            yield from self._stream_openai(messages)
        elif self.provider == "anthropic":
            yield from self._stream_anthropic(messages)
        elif self.provider == "google":
            yield from self._stream_google(messages)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def _run_openai(self, messages: list):
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model, messages=messages, stream=False
        )
        return response.choices[0].message.content

    def _stream_openai(self, messages: list):
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model, messages=messages, stream=True
        )
        for chunk in response:
            yield chunk.choices[0].delta.content or ""

    def _run_anthropic(self, messages: list):
        client = Anthropic()
        return client.messages.create(
            max_tokens=self.max_tokens,
            model=self.model,
            messages=messages,
        )

    def _stream_anthropic(self, messages: list):
        client = Anthropic()
        with client.messages.stream(
            max_tokens=self.max_tokens,
            model=self.model,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _run_google(self, messages: list):
        model = genai.GenerativeModel(self.model)
        chat = model.start_chat(history=self._convert_to_google_format(messages[:-1]))

        response = chat.send_message(messages[-1]["content"])
        return response.text

    def _stream_google(self, messages: list):
        model = genai.GenerativeModel(self.model)
        chat = model.start_chat(history=self._convert_to_google_format(messages[:-1]))

        response = chat.send_message(messages[-1]["content"], stream=True)
        for chunk in response:
            yield chunk.text

    def _convert_to_google_format(self, messages: list):
        google_messages = []
        for message in messages:
            if message["role"] == "user":
                google_messages.append({"role": "user", "parts": [message["content"]]})
            elif message["role"] == "assistant":
                google_messages.append({"role": "model", "parts": [message["content"]]})
        return google_messages

    def extract_strings(self, messages: list):
        return " ".join([message["content"] for message in messages])

    def calculate_cost(self, messages: list, completion: str = None):
        if completion:
            costs = tokencost.calculate_all_costs_and_tokens(
                self.extract_strings(messages), completion, self.model
            )
            return {
                "input_tokens": costs["prompt_tokens"],
                "input_cost": float(costs["prompt_cost"]),
                "output_tokens": costs["completion_tokens"],
                "output_cost": float(costs["completion_cost"]),
                "total_cost": float(costs["prompt_cost"])
                + float(costs["completion_cost"]),
            }
        else:
            costs = {
                "input_tokens": tokencost.count_string_tokens(
                    self.extract_strings(messages), self.model
                ),
            }
            costs["input_cost"] = float(
                tokencost.calculate_cost_by_tokens(
                    costs["input_tokens"], self.model, "input"
                )
            )
            return costs

    def estimate_cost(self, messages: list, oi_ratio: float):
        costs = self.calculate_cost(messages)
        costs["output_tokens"] = int(costs["input_tokens"] * oi_ratio)
        costs["output_cost"] = float(
            tokencost.calculate_cost_by_tokens(
                costs["output_tokens"], self.model, "output"
            )
        )
        costs["total_cost"] = costs["input_cost"] + costs["output_cost"]
        return costs


if __name__ == "__main__":
    clients = LLMClients(model="claude-3-5-sonnet")
    response = clients.run([{"role": "user", "content": "Hello, world!"}])
    ...
