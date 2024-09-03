import json
import logging
import string
from typing import Union

import tokencost
from pydantic import BaseModel

from codeag.agents.storage import Storage
from codeag.core.llms import LLMClient


class Agent(BaseModel, arbitrary_types_allowed=True):
    agent_name: str
    prompt: str
    llm_params: dict
    system_prompt: str = None
    retriever: object = None
    storage: Storage = Storage()
    messages: list = []
    responses: dict = {}
    write_to_storage: bool = False
    llm_client: LLMClient = None

    def __init__(self, **fields):
        super().__init__(**fields)
        self.llm_client = LLMClient()

    def run(self):
        self.messages = self.get_messages()
        self.responses = self.generate_responses(self.messages)
        self.write_output()
        return self.responses

    def ask(self, prompt: str):
        self._check_messages()
        self.messages.append({"role": "user", "content": prompt})
        self.responses = self.generate_responses(self.messages)
        self.write_output()
        return self.responses

    def _check_messages(self):
        if not any(self.messages):
            raise ValueError("No messages found. Please run the agent first.")

    def generate_responses(self, messages):
        responses = self.llm_client.run_completions(messages, **self.llm_params)
        self._add_responses_to_messages(messages, responses)
        self._process_responses(messages, responses)
        return responses

    def write_output(self):
        if self.write_to_storage:
            self.storage.write(
                self.agent_name,
                {"messages": self.messages, "responses": self.responses},
            )

    def read_output(self):
        if self.exist_output():
            output = self.storage.read(self.agent_name)
            self.messages = output["messages"]
            self.responses = output["responses"]
            return output
        else:
            logging.warning(f"No output found for {self.agent_name}")

    def exist_output(self):
        return self.storage.exists(self.agent_name)

    def _add_responses_to_messages(self, messages, responses):
        messages.append({"role": "assistant", "content": responses["content"]})

    def _process_responses(self, messages: list, responses: dict):
        responses["tokens_and_cost"] = self.calculate_tokens_and_cost(
            messages, responses, self.llm_params["model"]
        )
        responses["content"] = self.parse_content(responses)
        responses.pop("role")
        if responses.get("tool_calls") is None:
            responses.pop("tool_calls")

    def parse_content(self, responses):
        if self.llm_params.get("response_format") == {"type": "json_object"}:
            return json.loads(responses["content"])
        else:
            return responses["content"]

    def preview(self):
        messages = self.get_messages()
        return self._process_inputs(messages)

    def _process_inputs(self, messages):
        tokens_and_cost = self.calculate_input_tokens_and_cost(
            messages, self.llm_params["model"]
        )
        return {
            "messages": messages,
            "tokens_and_cost": tokens_and_cost,
        }

    def get_messages(self, *key, **kwargs):
        if self.retriever:
            formatted_prompt = self.format_prompt(self.prompt, *key, **kwargs)
            return self.get_messages_from_prompt(formatted_prompt)
        else:
            return self.get_messages_from_prompt(self.prompt)

    def format_prompt(self, prompt, *key, **kwargs):
        context = self.retrieve_context_from_prompt(prompt, *key, **kwargs)
        return prompt.format(**context)

    def retrieve_context_from_prompt(self, prompt: str, *key, **kwargs):
        placeholders = self.identify_placeholders(prompt)
        return {
            placeholder: getattr(self.retriever, placeholder)(*key, **kwargs)
            for placeholder in placeholders
        }

    def identify_placeholders(self, prompt):
        formatter = string.Formatter()
        return [
            fname
            for _, fname, _, _ in formatter.parse(prompt)
            if fname and fname.startswith("get_")
        ]

    def get_messages_from_prompt(self, prompt):
        if self.system_prompt:
            return [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]
        else:
            return [{"role": "user", "content": prompt}]

    def calculate_tokens_and_cost(self, messages, responses, model):
        tokens_and_cost = tokencost.calculate_all_costs_and_tokens(
            messages, responses["content"], model
        )
        tokens_and_cost["prompt_cost"] = float(tokens_and_cost["prompt_cost"])
        tokens_and_cost["completion_cost"] = float(tokens_and_cost["completion_cost"])
        return tokens_and_cost

    def calculate_input_tokens_and_cost(self, messages, model):
        return {
            "input_cost": float(tokencost.calculate_prompt_cost(messages, model)),
            "input_tokens": tokencost.count_message_tokens(messages, model),
        }


class BatchAgent(Agent):
    messages: dict = {}
    batch_keys: Union[list, str] = []

    def get_batch_keys(self):
        if isinstance(self.batch_keys, str) and self.batch_keys.startswith("retriever"):
            return getattr(self.retriever, self.batch_keys.split(".")[-1])()
        else:
            return self.batch_keys

    def run(self):
        for key in self.get_batch_keys():
            self.messages[key] = self.get_messages(key)
        self.responses = self.generate_batch_responses(self.messages)
        self.write_output()
        return self.responses

    def ask(self, prompt: str, key: str):
        self._check_messages()
        self.messages[key].append({"role": "user", "content": prompt})
        self.responses[key] = self.generate_responses(self.messages[key])
        self.write_output()
        return self.responses[key]

    def generate_batch_responses(self, messages):
        responses = self.llm_client.run_batch_completions(messages, **self.llm_params)
        for key in self.get_batch_keys():
            self._add_responses_to_messages(messages[key], responses[key])
            self._process_responses(messages[key], responses[key])
        return responses

    def preview(self):
        inputs = {}
        for key in self.get_batch_keys():
            self.messages[key] = self.get_messages(key)
            inputs[key] = {
                "messages": self.messages[key],
                "tokens_and_cost": self._process_inputs(self.messages[key]),
            }
        return inputs
