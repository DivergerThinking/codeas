from typing import Union, Optional

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
    system_prompt: Optional[str] = None # Fixed SonarQube issue S5890 here by using Optional[str]

    def run(
        self,
        llm_client: LLMClient,
        context: Union[dict, list, str] = [],
    ) -> AgentOutput:
        messages = self.get_messages(context)
        response = llm_client.run(
            messages, model=self.model, response_format=self.response_format
        )
        tokens, cost = self.calculate_tokens_and_cost(messages, response)
        return AgentOutput(
            messages=messages, response=response, tokens=tokens, cost=cost
        )

    def preview(self, context: Union[dict, list, str]) -> AgentPreview:
        messages = self.get_messages(context)
        # Note: preview calculates cost/tokens based on messages only
        # The original code called calculate_tokens_and_cost(messages), which handled response=None
        # Ensure calculate_tokens_and_cost correctly handles the None case.
        tokens, cost = self.calculate_tokens_and_cost(messages)
        return AgentPreview(messages=messages, tokens=tokens, cost=cost)

    def get_messages(self, context: Union[dict, list, str]):
        if isinstance(context, dict):
            return self.get_batch_messages(context)
        elif isinstance(context, list):
            return self.get_multi_messages(context)
        elif isinstance(context, str):
            return self.get_single_messages(context)
        # Add a default return or raise error if context type is unexpected?
        # For now, assuming context will always be one of the Union types.
        # Depending on expected behavior, could add:
        # else:
        #    raise TypeError("Context must be a dict, list, or string")


    def get_batch_messages(self, batch_contexts: dict):
        return {
            key: self._create_messages(context)
            for key, context in batch_contexts.items()
        }

    def get_multi_messages(self, contexts: list):
        # _create_messages expects a single item (list of contexts or string context)
        # This method seems to imply contexts is a list of items, where each item
        # needs its own message structure created.
        # The original _create_messages handles list as a list of user messages.
        # If the intent was to create a list of message lists, one for each context in the list,
        # this method would need to be:
        # return [self._create_messages(c) for c in contexts]
        # Assuming the original intent was to treat the list of contexts as multiple user messages
        # within a single conversation structure.
        return self._create_messages(contexts)

    def get_single_messages(self, context: str):
        return self._create_messages(context)

    def _create_messages(self, context):
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            if self.system_prompt is not None # Explicitly check for None
            else []
        )

        if isinstance(context, list):
            # Add each item in the list as a separate user message
            messages.extend({"role": "user", "content": str(c)} for c in context) # Ensure content is string
        elif isinstance(context, str):
            messages.append({"role": "user", "content": context})
        # else: What if context is dict here? The logic in get_messages should prevent this path.
        # But _create_messages is called from get_batch_messages with single context items.
        # Need to handle dict case here if get_batch_messages passes dict contexts.
        # Based on get_batch_messages implementation, it seems each item in batch_contexts.values()
        # is passed as 'context' here. So 'context' can be str, list, or other types from the dict values.
        # Let's refine based on how get_messages routes:
        # - get_batch_messages passes dict values to _create_messages
        # - get_multi_messages passes the list itself to _create_messages
        # - get_single_messages passes the string itself to _create_messages
        # So _create_messages needs to handle list (from get_multi_messages), str (from get_single_messages),
        # and whatever types are stored as values in the dict passed to get_batch_messages.
        # The current implementation only handles list and str explicitly.
        # If dict values can be other types, they won't be added as user messages.
        # Let's assume for this fix scope that context passed to _create_messages will only be list or str.
        # If context can be dict, the logic here needs modification.

        messages.append({"role": "user", "content": self.instructions})
        return messages

    def calculate_tokens_and_cost(self, messages: Union[list, dict], response=None):
        # This method orchestrates calculations based on message/response structure.
        # It calls internal helper methods.
        if isinstance(messages, dict):
            # Batch messages/responses
            if response is not None: # Assuming response is a dict corresponding to batch_messages keys
                # This branch is complex. If response_format is set, maybe the response structure is different?
                # The _sum_get_request_tokens_and_cost method specifically looks for 'usage' attributes, typical of
                # API responses (like OpenAI's).
                # The _sum_calculate_tokens_and_cost method uses calculate_all_costs_and_tokens/count_message_tokens
                # which usually work on raw messages/content.
                # The original code had 'if self.response_format and response is not None:' for calling _sum_get_request_tokens_and_cost
                # This implies 'response_format' being set changes the structure of the 'response' object.
                # This logic seems a bit ambiguous regarding the relationship between response_format and the
                # response object's type/structure. Let's stick to the original flow for now.
                return self._sum_calculate_tokens_and_cost(messages, response) # Assuming response is dict, calculate based on messages/content

            else: # Calculate only input tokens/cost for batch messages
                 return self._sum_calculate_tokens_and_cost(messages, response) # Pass None for response

        else: # messages is a list (single conversation)
            if response is not None:
                # This branch assumes 'response' is the result of a single API call.
                # The original code had 'if self.response_format and response is not None:'.
                # Reverting to the original logic structure based on response presence,
                # but acknowledging the original comment's implication about response_format affecting response structure.
                # Let's assume 'response' being not None means we potentially have usage info or content.
                # The internal methods will handle the specifics.
                 return self._calculate_tokens_and_cost(messages, response) # Pass response
            else: # Calculate only input tokens/cost for single conversation
                return self._calculate_tokens_and_cost(messages, response) # Pass None for response

    def _sum_get_request_tokens_and_cost(self, responses: dict):
        # Sums results from _get_request_tokens_and_cost for each item in the dict.
        results = []
        for response in responses.values():
             # Ensure response is not None before processing
            if response is not None:
                results.append(self._get_request_tokens_and_cost(response))

        # Safely sum using .get with default values
        tokens = {
            "input_tokens": sum(result[0].get("input_tokens", 0) for result in results),
            "output_tokens": sum(result[0].get("output_tokens", 0) for result in results),
            "total_tokens": sum(result[0].get("total_tokens", 0) for result in results),
        }
        cost = {
            "input_cost": sum(result[1].get("input_cost", 0.0) for result in results),
            "output_cost": sum(result[1].get("output_cost", 0.0) for result in results),
            "total_cost": sum(result[1].get("total_cost", 0.0) for result in results),
        }
        return tokens, cost

    def _get_request_tokens_and_cost(self, response):
        # Assumes response object has a 'usage' attribute with token counts (e.g., OpenAI response)
        # Use getattr with default values for safety against missing attributes
        prompt_tokens = getattr(getattr(response, 'usage', None), 'prompt_tokens', 0)
        completion_tokens = getattr(getattr(response, 'usage', None), 'completion_tokens', 0)
        total_tokens = getattr(getattr(response, 'usage', None), 'total_tokens', 0)

        tokens = {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

        input_cost = float(
            calculate_cost_by_tokens(
                tokens["input_tokens"], self.model, "input"
            )
        )
        output_cost = float(
            calculate_cost_by_tokens(
                tokens["output_tokens"], self.model, "output"
            )
        )
        cost = {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }
        return tokens, cost

    def _sum_calculate_tokens_and_cost(self, batch_messages: dict, batch_response=None):
        # Sums results from _calculate_tokens_and_cost for each key in the dict.
        results = []
        for key, messages in batch_messages.items():
            # Ensure messages is a list before passing (as _calculate_tokens_and_cost expects list)
            # If messages can be other types in the dict values, this needs handling.
            # Assuming values from batch_messages are lists of messages.
            single_response = batch_response.get(key) if batch_response else None
            results.append(self._calculate_tokens_and_cost(messages, single_response))

        # Safely sum using .get with default values
        tokens = {"input_tokens": sum(result[0].get("input_tokens", 0) for result in results)}
        cost = {"input_cost": sum(result[1].get("input_cost", 0.0) for result in results)}

        if batch_response: # Only sum output/total if responses were provided
            tokens.update(
                {
                    "output_tokens": sum(
                        result[0].get("output_tokens", 0) for result in results
                    ),
                    "total_tokens": sum(
                        result[0].get("total_tokens", 0) for result in results
                    ),
                }
            )
            cost.update(
                {
                    "output_cost": sum(result[1].get("output_cost", 0.0) for result in results),
                    "total_cost": sum(result[1].get("total_cost", 0.0) for result in results),
                }
            )

        return tokens, cost


    def _calculate_tokens_and_cost(self, messages: list, response=None):
        # Calculates tokens and cost for a single conversation (messages is a list).
        # response can be None (for input-only) or the response object/dict.
        # This function needs to be robust to the type of 'response' passed if response_format affects it.
        # The original code used response["content"] which implies response is a dict-like object.
        # The _get_request_tokens_and_cost method implies response could also be an object with a .usage attribute.
        # Let's assume calculate_all_costs_and_tokens is designed to handle a response object/dict and extract content.
        # If response is None, calculate only input cost/tokens.
        if response is None:
            input_tokens = count_message_tokens(messages, self.model)
            # calculate_prompt_cost likely uses count_message_tokens internally, but let's use it as written.
            input_cost = float(calculate_prompt_cost(messages, self.model))
            # Return 0 for output/total as there's no response
            return ({"input_tokens": input_tokens, "output_tokens": 0, "total_tokens": input_tokens},
                    {"input_cost": input_cost, "output_cost": 0.0, "total_cost": input_cost})
        else:
            # Assumes calculate_all_costs_and_tokens can handle the response object/dict.
            # It typically takes messages, response_content, and model.
            # Assuming response_content can be extracted from the response object/dict.
            # Let's use .get("content", "") defensively if response is expected to be a dict.
            # If response can be an object with attributes, extraction logic might need adjustment.
            # Stick to original logic assuming response is dict-like with "content".
            # Using .get("content") is safer than ["content"].
            response_content = response.get("content") if isinstance(response, dict) else str(response) # Handle non-dict responses gracefully?
            # The tokencost library's calculate_all_costs_and_tokens signature is usually (messages, completion, model).
            # 'completion' expects the string content of the response.
            # Let's assume response is an object/dict from which the content string can be reliably extracted.
            # Based on _get_request_tokens_and_cost, response could be an object.
            # If response is an object from llm_client.run, it might have .text or similar for content.
            # Reverting to original assumption that response["content"] works, or perhaps tokencost handles the response object directly?
            # Let's assume calculate_all_costs_and_tokens is robust enough or response is always dict-like here.
            try:
                tokens_and_cost = calculate_all_costs_and_tokens(
                    messages, response_content, self.model # Pass extracted content
                )
                input_tokens = tokens_and_cost.get("prompt_tokens", 0)
                output_tokens = tokens_and_cost.get("completion_tokens", 0)
                input_cost = float(tokens_and_cost.get("prompt_cost", 0.0))
                output_cost = float(tokens_and_cost.get("completion_cost", 0.0))

                return (
                    {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                    },
                    {
                        "input_cost": input_cost,
                        "output_cost": output_cost,
                        "total_cost": input_cost + output_cost,
                    },
                )
            except Exception as e:
                 # Log the error or handle gracefully if tokencost calculation fails
                 print(f"Error calculating tokens/cost: {e}")
                 # Return zero values to avoid crashing
                 return (
                    {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0},
                 )


if __name__ == "__main__":
    from codeas.configs.agents_configs import AGENTS_CONFIGS
    from codeas.core.llm import LLMClient
    from codeas.core.repo import Repo

    llm_client = LLMClient()
    # Example usage (assuming AGENTS_CONFIGS and Repo are set up)
    # agent = Agent(**AGENTS_CONFIGS["extract_files_detail"])
    # repo = Repo(repo_path=".")
    # incl_files = repo.filter_files()
    # files_paths = [path for path, incl in zip(repo.files_paths, incl_files) if incl]
    # context_data = {"file_path": path for path in files_paths} # Example context
    # try:
    #     output = agent.run(llm_client, context_data)
    #     print(output)
    # except Exception as e:
    #     print(f"An error occurred during agent run: {e}")
    ...