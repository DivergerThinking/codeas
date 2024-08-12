import json
import string

import tokencost
from pydantic import BaseModel

from codeag.agents.llms import AsyncLLMClient, LLMClient


class Agent(BaseModel, arbitrary_types_allowed=True):
    agent_name: str
    prompt: str
    llm_params: dict
    system_prompt: str = None
    retriever: object = None
    storage: object = None
    messages: list = []
    llm_client: LLMClient = None

    def model_post_init(self, __context):
        if self.llm_client is None:
            self.llm_client = LLMClient()

    def run(self, write_output=False):
        self.messages = self.get_messages()
        responses = self.generate_responses()
        output = self.process_output(self.messages, responses)
        if write_output:
            self.write_output(output)
        return output

    def ask(self, prompt: str, write_output=False):
        self.messages.append({"role": "user", "content": prompt})
        responses = self.generate_responses()
        output = self.process_output(self.messages, responses)
        if write_output:
            self.write_output(output)
        return output

    def preview(self):
        self.messages = self.get_messages()
        tokens_and_cost = self.calculate_input_tokens_and_cost(
            self, self.llm_params["model"]
        )
        return {
            "messages": self.messages,
            "tokens_and_cost": tokens_and_cost,
        }

    def write_output(self, output: dict):
        self.storage.write(self.agent_name, output)

    def read_output(self):
        self.storage.read(self.agent_name)

    def exist_output(self):
        self.storage.exists(self.agent_name)

    def get_messages(self, *args, **kwargs):
        if self.retriever:
            formatted_prompt = self.format_prompt(self.prompt, *args, **kwargs)
            return self.get_messages_from_prompt(formatted_prompt)
        else:
            return self.get_messages_from_prompt(self.prompt)

    def format_prompt(self, prompt, *args, **kwargs):
        context = self.retrieve_context_from_prompt(prompt, *args, **kwargs)
        return prompt.format(**context)

    def retrieve_context_from_prompt(self, prompt: str, *args, **kwargs):
        placeholders = self.identify_placeholders(prompt)
        return {
            placeholder: getattr(self.retriever, placeholder)(*args, **kwargs)
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

    def generate_responses(self):
        return self.llm_client.run_completions(self.messages, **self.llm_params)

    def process_output(self, messages, responses):
        tokens_and_cost = self.calculate_tokens_and_cost(
            messages, responses, self.llm_params["model"]
        )
        content = self.parse_content(responses)
        return {
            "messages": messages,
            "content": content,
            "tokens_and_cost": tokens_and_cost,
        }

    def calculate_tokens_and_cost(self, messages, responses, model):
        tokens_and_cost = tokencost.calculate_all_costs_and_tokens(
            messages, responses["content"], model
        )
        tokens_and_cost["prompt_cost"] = float(tokens_and_cost["prompt_cost"])
        tokens_and_cost["completion_cost"] = float(tokens_and_cost["completion_cost"])
        return tokens_and_cost

    def parse_content(self, responses):
        if self.llm_params.get("response_format") == {"type": "json_object"}:
            return json.loads(responses["content"])
        else:
            return responses["content"]

    def calculate_input_tokens_and_cost(self, messages, model):
        return {
            "input_cost": float(tokencost.calculate_prompt_cost(messages, model)),
            "input_tokens": tokencost.count_message_tokens(messages, model),
        }

    def add_responses_to_messages(self):
        ...


class BatchAgent(Agent):
    messages: dict = {}
    batch_keys: list = []

    def model_post_init(self, __context):
        if self.llm_client is None:
            self.llm_client = AsyncLLMClient()

    def get_messages(self):
        messages = {}
        for key in self.batch_keys:
            messages[key] = super().get_messages(key)
        return messages

    def generate_responses(self):
        return self.llm_client.run_completions(
            list(self.messages.values()), **self.llm_params
        )

    def process_output(self, batch_messages, batch_responses):
        batch_outputs = {}
        for (key, messages), responses in zip(batch_messages.items(), batch_responses):
            batch_outputs[key] = super().process_output(messages, responses)
        return batch_outputs
