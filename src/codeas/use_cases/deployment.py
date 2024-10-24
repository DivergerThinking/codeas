from codeas.configs import prompts
from codeas.core.agent import Agent
from codeas.core.retriever import ContextRetriever
from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker


def define_deployment(preview: bool = False) -> str:
    retriever = ContextRetriever(include_code_files=True, use_descriptions=True)
    context = retriever.retrieve(
        state.repo.included_files_paths,
        state.repo.included_files_tokens,
        state.repo_metadata,
    )

    agent = Agent(
        instructions=prompts.define_aws_deployment,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=context)
    else:
        result = agent.run(state.llm_client, context=context)
        usage_tracker.record_usage("define_deployment", result.cost["total_cost"])
        return result


def generate_deployment(deployment_strategy: str, preview: bool = False) -> str:
    retriever = ContextRetriever(include_code_files=True, use_descriptions=True)
    context = [
        retriever.retrieve(
            state.repo.included_files_paths,
            state.repo.included_files_tokens,
            state.repo_metadata,
        )
    ]
    context.append(deployment_strategy)
    agent = Agent(
        instructions=prompts.generate_aws_deployment,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=context)
    else:
        result = agent.run(state.llm_client, context=context)
        usage_tracker.record_usage("generate_deployment", result.cost["total_cost"])
        return result
