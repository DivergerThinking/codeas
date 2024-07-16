import json
import logging
import os
from typing import Union

from codeag.core.context import Context
from codeag.utils.costs import calculate_cost, count_tokens, count_tokens_from_messages
from codeag.utils.llm import Llm


class Agent:
    def __init__(self, repo_path: str):
        self.context = Context(repo_path)
        self._llm = Llm()

    def get_messages(
        self,
        prompt_template: str,
        system_prompt: str = None,
        add_context: bool = True,
    ):
        if add_context:
            prompt = self.context.fill(prompt_template)
        else:
            prompt = prompt_template

        if isinstance(prompt, dict):
            if system_prompt:
                return {
                    key: [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": value},
                    ]
                    for key, value in prompt.items()
                }
            else:
                return {
                    key: [{"role": "user", "content": value}]
                    for key, value in prompt.items()
                }
        elif isinstance(prompt, str):
            if system_prompt:
                return [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
            else:
                return [{"role": "user", "content": prompt}]

    def generate_responses(self, messages: Union[dict, list], openai_params: dict):
        if isinstance(messages, dict):
            return self._llm.run_batch_completions(messages.values(), **openai_params)
        else:
            return self._llm.run_completions(messages, **openai_params)

    def calculate_cost(
        self,
        messages: Union[dict, list] = None,
        responses: Union[dict, list] = None,
        openai_params: dict = {},
    ):
        in_tokens = self.count_in_tokens(messages, openai_params) if messages else 0
        out_tokens = self.count_out_tokens(responses, openai_params) if responses else 0
        return calculate_cost(
            intokens=in_tokens,
            outtokens=out_tokens,
            model=openai_params["model"],
        )

    def count_in_tokens(self, messages: Union[dict, list], openai_params: dict):
        if not isinstance(messages, dict):
            return count_tokens_from_messages(messages, model=openai_params["model"])
        else:
            return sum(
                count_tokens_from_messages(messages, model=openai_params["model"])
                for messages in messages.values()
            )

    def count_out_tokens(self, responses: Union[dict, list], openai_params: dict):
        if isinstance(responses, dict):
            return count_tokens(responses["content"], model=openai_params["model"])
        else:
            return sum(
                count_tokens(response["content"], model=openai_params["model"])
                for response in responses
            )

    def write_output(self, output_path, content):
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))

        with open(output_path, "w") as f:
            json.dump(content, f)

    def read_output(self, output_path):
        try:
            with open(output_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"File not found: {output_path}")
