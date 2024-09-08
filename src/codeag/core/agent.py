from typing import Union

from pydantic import BaseModel
from tokencost import (
    calculate_all_costs_and_tokens,
    calculate_prompt_cost,
    count_message_tokens,
)

from codeag.core.llms import LLMClient


class AgentOutput(BaseModel):
    tokens: dict
    cost: dict
    messages: Union[list, dict]
    response: Union[str, dict]


class AgentPreview(BaseModel):
    tokens: dict
    cost: dict
    messages: Union[list, dict]


class Agent(BaseModel):
    system_prompt: str
    instructions: str
    model: str

    def run(
        self, llm_client: LLMClient, context: Union[dict, list, str]
    ) -> AgentOutput:
        messages = self.get_messages(context)
        response = llm_client.run(messages, model=self.model)
        tokens, cost = self.calculate_tokens_and_cost(messages, response)
        return AgentOutput(
            messages=messages, response=response, tokens=tokens, cost=cost
        )

    def preview(self, context: Union[dict, list, str]) -> AgentPreview:
        messages = self.get_messages(context)
        tokens, cost = self.calculate_tokens_and_cost(messages)
        return AgentPreview(messages=messages, tokens=tokens, cost=cost)

    def get_messages(self, context: Union[dict, list, str]):
        if isinstance(context, dict):
            return self.get_batch_messages(context)
        elif isinstance(context, list):
            return self.get_multi_messages(context)
        elif isinstance(context, str):
            return self.get_single_messages(context)

    def get_batch_messages(self, batch_contexts: dict):
        messages = {}
        for key, context in batch_contexts.items():
            if isinstance(context, list):
                messages[key] = self.get_multi_messages(context)
            elif isinstance(context, str):
                messages[key] = self.get_single_messages(context)
        return messages

    def get_multi_messages(self, contexts: list):
        messages = [{"role": "system", "content": self.system_prompt}]
        for context in contexts:
            messages.append({"role": "user", "content": context})
        messages.append({"role": "user", "content": self.instructions})
        return messages

    def get_single_messages(self, context: str):
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
            {"role": "user", "content": self.instructions},
        ]

    def calculate_tokens_and_cost(self, messages: Union[list, dict], response=None):
        if isinstance(messages, dict):
            return self._sum_calculate_tokens_and_cost(messages, response)
        else:
            return self._calculate_tokens_and_cost(messages, response)

    def _sum_calculate_tokens_and_cost(self, batch_messages: dict, batch_response=None):
        results = []
        for key, messages in batch_messages.items():
            response = batch_response[key] if batch_response else None
            results.append(self._calculate_tokens_and_cost(messages, response))

        tokens = {"input_tokens": sum(result[0]["input_tokens"] for result in results)}
        cost = {"input_cost": sum(result[1]["input_cost"] for result in results)}

        if batch_response:
            tokens.update(
                {
                    "output_tokens": sum(
                        result[0]["output_tokens"] for result in results
                    ),
                    "total_tokens": sum(
                        result[0]["total_tokens"] for result in results
                    ),
                }
            )
            cost.update(
                {
                    "output_cost": sum(result[1]["output_cost"] for result in results),
                    "total_cost": sum(result[1]["total_cost"] for result in results),
                }
            )

        return tokens, cost

    def _calculate_tokens_and_cost(self, messages: list, response=None):
        if response is None:
            input_tokens = count_message_tokens(messages, self.model)
            input_cost = float(calculate_prompt_cost(messages, self.model))
            return ({"input_tokens": input_tokens}, {"input_cost": input_cost})
        else:
            tokens_and_cost = calculate_all_costs_and_tokens(
                messages, response["content"], self.model
            )
            return (
                {
                    "input_tokens": tokens_and_cost["prompt_tokens"],
                    "output_tokens": tokens_and_cost["completion_tokens"],
                    "total_tokens": tokens_and_cost["prompt_tokens"]
                    + tokens_and_cost["completion_tokens"],
                },
                {
                    "input_cost": float(tokens_and_cost["prompt_cost"]),
                    "output_cost": float(tokens_and_cost["completion_cost"]),
                    "total_cost": float(
                        tokens_and_cost["prompt_cost"]
                        + tokens_and_cost["completion_cost"]
                    ),
                },
            )
