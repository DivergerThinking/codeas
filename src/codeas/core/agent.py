from typing import Union

from pydantic import BaseModel
from tokencost import (
    calculate_all_costs_and_tokens,
    calculate_cost_by_tokens,
    calculate_prompt_cost,
    count_message_tokens,
)

from codeas.core.client_azure import LLMClientAzure


class AgentOutput(BaseModel):
    tokens: dict
    cost: dict
    messages: Union[list, dict]
    response: Union[str, dict, object]


class AgentPreview(BaseModel):
    tokens: dict
    cost: dict
    messages: Union[list, dict]


class Agent(BaseModel):
    model: str
    response_format: object = None

    def run(
        self,
        messages: Union[list, dict],
        llm_client: LLMClientAzure,
    ) -> AgentOutput:
        response = llm_client.run(
            messages, model=self.model, response_format=self.response_format
        )
        tokens, cost = self.calculate_tokens_and_cost(messages, response)
        return AgentOutput(
            messages=messages, response=response, tokens=tokens, cost=cost
        )

    def preview(self, messages: list) -> AgentPreview:
        tokens, cost = self.calculate_tokens_and_cost(messages)
        return AgentPreview(messages=messages, tokens=tokens, cost=cost)

    def calculate_tokens_and_cost(self, messages: Union[list, dict], response=None):
        if isinstance(messages, dict):
            if self.response_format and response is not None:
                return self._sum_get_request_tokens_and_cost(response)
            else:
                return self._sum_calculate_tokens_and_cost(messages, response)
        else:
            if self.response_format and response is not None:
                return self._get_request_tokens_and_cost(response)
            else:
                return self._calculate_tokens_and_cost(messages, response)

    def _sum_get_request_tokens_and_cost(self, responses: dict):
        results = []
        for response in responses.values():
            results.append(self._get_request_tokens_and_cost(response))

        tokens = {
            "input_tokens": sum(result[0]["input_tokens"] for result in results),
            "output_tokens": sum(result[0]["output_tokens"] for result in results),
            "total_tokens": sum(result[0]["total_tokens"] for result in results),
        }
        cost = {
            "input_cost": sum(result[1]["input_cost"] for result in results),
            "output_cost": sum(result[1]["output_cost"] for result in results),
            "total_cost": sum(result[1]["total_cost"] for result in results),
        }
        return tokens, cost

    def _get_request_tokens_and_cost(self, response):
        tokens = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        cost = {
            "input_cost": float(
                calculate_cost_by_tokens(
                    response.usage.prompt_tokens, self.model, "input"
                )
            ),
            "output_cost": float(
                calculate_cost_by_tokens(
                    response.usage.completion_tokens, self.model, "output"
                )
            ),
        }
        cost["total_cost"] = cost["input_cost"] + cost["output_cost"]
        return tokens, cost

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
                messages, response, self.model
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
