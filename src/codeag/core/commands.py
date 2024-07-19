from __future__ import annotations

from typing import TYPE_CHECKING

from codeag.configs.command_args import COMMAND_ARGS
from codeag.configs.db_configs import STORAGE_PATH
from codeag.utils.costs import calculate_cost

if TYPE_CHECKING:
    from codeag.core.agent import Agent


class Commands:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.COMMAND_ARGS = COMMAND_ARGS

    def run(self, command_name):
        args = self.COMMAND_ARGS[command_name]
        messages = self.agent.get_messages(args.prompt)
        if args.multiple_requests:
            return self.execute_multiple_requests(
                messages=messages, api_params=args.api_params
            )
        else:
            return self.execute_single_request(
                messages=messages, api_params=args.api_params
            )

    def estimate(self, command_name):
        args = self.COMMAND_ARGS[command_name]
        messages = self.agent.get_messages(args.prompt)
        if args.multiple_requests:
            return self.estimate_multiple_requests(
                messages=messages,
                api_params=args.api_params,
                estimate_multiplier=args.estimate_multiplier,
            )
        else:
            return self.estimate_single_request(
                messages=messages,
                api_params=args.api_params,
                estimate_multiplier=args.estimate_multiplier,
            )

    def read(self, command_name):
        return self.agent.read_output(f"{STORAGE_PATH}/{command_name}.json")

    def write(self, command_name, outputs):
        self.agent.write_output(f"{STORAGE_PATH}/{command_name}.json", outputs)

    def estimate_single_request(self, messages, api_params, estimate_multiplier):
        in_tokens = self.agent.count_in_tokens(messages, api_params)
        estimated_cost = calculate_cost(
            in_tokens, estimate_multiplier, api_params["model"]
        )
        return {
            "messages": messages,
            "tokens": in_tokens + estimate_multiplier,
            "in_tokens": in_tokens,
            "out_tokens": estimate_multiplier,
            "cost": estimated_cost,
        }

    def estimate_multiple_requests(self, messages, api_params, estimate_multiplier):
        in_tokens = self.agent.count_in_tokens(messages, api_params)
        estimated_out_tokens = estimate_multiplier * len(messages)
        estimated_cost = calculate_cost(
            in_tokens, estimated_out_tokens, api_params["model"]
        )
        return {
            "messages": messages,
            "tokens": in_tokens + estimated_out_tokens,
            "in_tokens": in_tokens,
            "out_tokens": estimated_out_tokens,
            "cost": estimated_cost,
        }

    def execute_single_request(self, messages, api_params):
        response = self.agent.generate_responses(messages, api_params)
        if api_params.get("response_format") == {"type": "json_object"}:
            content = eval(response["content"])
        else:
            content = response["content"]
        in_tokens = self.agent.count_in_tokens(messages, api_params)
        out_tokens = self.agent.count_out_tokens(response, api_params)
        tokens = in_tokens + out_tokens
        cost = self.agent.calculate_cost(messages, response, api_params)
        return {
            "contents": content,
            "cost": cost,
            "tokens": tokens,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
        }

    def execute_multiple_requests(self, messages, api_params):
        responses = self.agent.generate_responses(messages, api_params)
        if api_params.get("response_format") == {"type": "json_object"}:
            contents = {
                path: eval(response["content"])
                for path, response in zip(messages.keys(), responses)
            }
        else:
            contents = {
                path: response["content"]
                for path, response in zip(messages.keys(), responses)
            }
        in_tokens = self.agent.count_in_tokens(messages, api_params)
        out_tokens = self.agent.count_out_tokens(responses, api_params)
        tokens = in_tokens + out_tokens
        cost = self.agent.calculate_cost(messages, responses, api_params)
        return {
            "contents": contents,
            "cost": cost,
            "tokens": tokens,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
        }


if __name__ == "__main__":
    from codeag.core.agent import Agent

    agent = Agent(repo_path=".")
    commands = Commands(agent=agent, write_output=False)
    estimates = commands.estimate("generate_documentation_sections")
    outputs = commands.run("generate_documentation_sections")
    estimates["tokens"]