from typing import Union

from pydantic import BaseModel
from tokencost import (
    calculate_all_costs_and_tokens,
    calculate_cost_by_tokens,
    calculate_prompt_cost,
    count_message_tokens,
)

from codeag.core.llms import LLMClient


class FilePathsOutput(BaseModel):
    paths: list[str]


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
    system_prompt: str
    instructions: str
    model: str
    response_format: object = None

    def run(
        self,
        llm_client: LLMClient,
        context: Union[dict, list, str] = [],
    ) -> AgentOutput:
        messages = self.get_messages(context)
        completion = llm_client.run(
            messages, model=self.model, response_format=self.response_format
        )
        response, tokens, cost = self.parse_completion(messages, completion)
        return AgentOutput(
            messages=messages, response=response, tokens=tokens, cost=cost
        )

    def parse_completion(self, messages, completion):
        if self.response_format:
            response = completion.choices[0].message.parsed
            tokens = {
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens,
            }
            cost = {
                "input_cost": float(
                    calculate_cost_by_tokens(
                        completion.usage.prompt_tokens, self.model, "input"
                    )
                ),
                "output_cost": float(
                    calculate_cost_by_tokens(
                        completion.usage.completion_tokens, self.model, "output"
                    )
                ),
            }
            cost["total_cost"] = cost["input_cost"] + cost["output_cost"]
            return response, tokens, cost
        else:
            tokens, cost = self.calculate_tokens_and_cost(messages, completion)
            return completion, tokens, cost

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


if __name__ == "__main__":
    from codeag.configs.agents_configs import AGENTS_CONFIGS
    from codeag.core.context import Context
    from codeag.core.llms import LLMClient
    from codeag.ui.Home import get_files_content

    llm_client = LLMClient()
    agent = Agent(**AGENTS_CONFIGS["auto_select_files"])
    files_content = get_files_content(["requirements.txt", "Makefile", "LICENSE"])
    ctx = Context()
    context = ctx.retrieve(
        files_content=files_content,
        agents_output={
            "document_configs": "document all of the configurations of the project"
        },
    )
    response = agent.run(llm_client, context=context)
    print(response)
