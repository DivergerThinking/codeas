from typing import Union

from pydantic import BaseModel
from tokencost import (
    calculate_all_costs_and_tokens,
    calculate_cost_by_tokens,
    calculate_prompt_cost,
    count_message_tokens,
)

from codeas.core.llm import LLMClient


class FilePathsOutput(BaseModel):
    paths: list[str]


class ApplicableResponse(BaseModel):
    applicable: bool
    response: str


class FileDetailsOutput(BaseModel):
    technologies_and_dependencies: ApplicableResponse
    architectural_insights: ApplicableResponse
    application_layer: ApplicableResponse
    design_patterns: ApplicableResponse
    data_models: ApplicableResponse
    key_components: ApplicableResponse


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
    instructions: str
    model: str
    response_format: object = None
    system_prompt: str = None

    def run(
        self,
        llm_client: LLMClient,
        context: Union[dict, list, str] = [],
    ) -> AgentOutput:
        # IMPORTANT: If 'context' originates from untrusted user input,
        # it MUST be validated and sanitized BEFORE being passed to this method
        # to mitigate prompt injection risks. Basic string casting is applied
        # internally, but robust sanitization logic is the caller's responsibility.
        messages = self.get_messages(context)

        try:
            response = llm_client.run(
                messages, model=self.model, response_format=self.response_format
            )
        except Exception as e:
            # Log the error and re-raise or handle appropriately
            print(f"Error during LLM run: {e}")
            raise RuntimeError(f"Failed to get response from LLM: {e}") from e

        try:
            tokens, cost = self.calculate_tokens_and_cost(messages, response)
        except Exception as e:
            # Log the error and re-raise or handle appropriately
            print(f"Error calculating tokens/cost after run: {e}")
            raise RuntimeError(f"Failed to calculate tokens or cost: {e}") from e

        return AgentOutput(
            messages=messages, response=response, tokens=tokens, cost=cost
        )

    def preview(self, context: Union[dict, list, str]) -> AgentPreview:
        # IMPORTANT: If 'context' originates from untrusted user input,
        # it MUST be validated and sanitized BEFORE being passed to this method
        # to mitigate prompt injection risks. Basic string casting is applied
        # internally, but robust sanitization logic is the caller's responsibility.
        messages = self.get_messages(context)
        try:
            tokens, cost = self.calculate_tokens_and_cost(messages)
        except Exception as e:
            # Log the error and re-raise or handle appropriately
            print(f"Error calculating tokens/cost during preview: {e}")
            raise RuntimeError(f"Failed to calculate tokens or cost for preview: {e}") from e

        return AgentPreview(messages=messages, tokens=tokens, cost=cost)

    def get_messages(self, context: Union[dict, list, str]):
        # IMPORTANT: If 'context' originates from untrusted user input,
        # it MUST be validated and sanitized BEFORE being passed to this method
        # to mitigate prompt injection risks. Basic string casting is applied
        # internally, but robust sanitization logic is the caller's responsibility.
        if isinstance(context, dict):
            return self.get_batch_messages(context)
        elif isinstance(context, list):
            return self.get_multi_messages(context)
        elif isinstance(context, str):
            return self.get_single_messages(context)
        # Consider adding a default case or raising an error for unsupported types

    def get_batch_messages(self, batch_contexts: dict):
        return {
            key: self._create_messages(context)
            for key, context in batch_contexts.items()
        }

    def get_multi_messages(self, contexts: list):
        return self._create_messages(contexts)

    def get_single_messages(self, context: str):
        return self._create_messages(context)

    def _create_messages(self, context):
        # IMPORTANT: The content of 'context' should be validated and sanitized
        # by the caller if it originates from untrusted user input to mitigate
        # prompt injection risks. The string casting here is only for type
        # consistency, not sanitization.
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            if self.system_prompt
            else []
        )

        if isinstance(context, list):
            # Ensure list elements are string representations for message content
            context_list_as_strings = [str(c) for c in context]
            messages.extend({"role": "user", "content": c} for c in context_list_as_strings)
        elif isinstance(context, str):
            # Ensure context is a string representation
            context_str = str(context)
            messages.append({"role": "user", "content": context_str})
        # else: context type is unexpected based on get_messages, handle or assume previous validation

        messages.append({"role": "user", "content": self.instructions})
        return messages

    def calculate_tokens_and_cost(self, messages: Union[list, dict], response=None):
        try:
            if isinstance(messages, dict):
                if self.response_format and response is not None:
                    return self._sum_get_request_tokens_and_cost(response)
                else:
                    return self._sum_calculate_tokens_and_cost(messages, response)
            else:  # messages is a list
                if self.response_format and response is not None:
                    return self._get_request_tokens_and_cost(response)
                else:
                    return self._calculate_tokens_and_cost(messages, response)
        except Exception as e:
            # Log the error and re-raise or handle appropriately
            print(f"Error within calculate_tokens_and_cost logic: {e}")
            raise RuntimeError(f"Calculation failed: {e}") from e

    def _sum_get_request_tokens_and_cost(self, responses: dict):
        results = []
        for response in responses.values():
            # Rely on the outer try/except in calculate_tokens_and_cost
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
        # Rely on the outer try/except in calculate_tokens_and_cost
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
            # Rely on the outer try/except in calculate_tokens_and_cost
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
        # Rely on the outer try/except in calculate_tokens_and_cost
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
    from codeas.configs.agents_configs import AGENTS_CONFIGS
    from codeas.core.llm import LLMClient
    from codeas.core.repo import Repo

    llm_client = LLMClient()
    agent = Agent(**AGENTS_CONFIGS["extract_files_detail"])
    repo = Repo(repo_path=".")
    incl_files = repo.filter_files()
    files_paths = [path for path, incl in zip(repo.files_paths, incl_files) if incl]
    ...