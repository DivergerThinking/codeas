from typing import List

from pydantic import BaseModel

from codeag.core.agent import Agent
from codeag.core.llm import LLMClient
from codeag.core.metadata import RepoMetadata
from codeag.core.repo import Repo
from codeag.core.retriever import ContextRetriever
from codeag.use_cases import prompts


class TestingStep(BaseModel):
    files_paths: List[str]
    type_of_test: str
    guidelines: str
    test_file_path: str


class TestingStrategy(BaseModel):
    strategy: List[TestingStep]


def define_testing_strategy(
    llm_client: LLMClient,
    repo: Repo,
    metadata: RepoMetadata,
    preview: bool = False,
) -> str:
    retriever = ContextRetriever(include_code_files=True, use_details=True)
    context = retriever.retrieve(
        repo.included_files_paths, repo.included_files_tokens, metadata
    )

    agent = Agent(
        instructions=prompts.define_testing_strategy,
        model="gpt-4o",
        response_format=TestingStrategy,
    )
    if preview:
        return agent.preview(context=context)
    else:
        return agent.run(llm_client, context=context)


def parse_response(response: object):
    return response.choices[0].message.parsed


def generate_tests_from_strategy(
    llm_client: LLMClient,
    strategy: TestingStrategy,
    preview: bool = False,
) -> str:
    contexts = {}
    for step in strategy.strategy:
        retriever = ContextRetriever(include_all_files=True)
        contexts[step.test_file_path] = [retriever.retrieve(step.files_paths)]
        contexts[step.test_file_path].append(f"## Guidelines\n{step.guidelines}")
        contexts[step.test_file_path].append(f"## Type of test\n{step.type_of_test}")
    agent = Agent(instructions=prompts.generate_tests_from_guidelines, model="gpt-4o")
    if preview:
        return agent.preview(context=contexts)
    else:
        return agent.run(llm_client, context=contexts)


if __name__ == "__main__":
    from codeag.core.metadata import RepoMetadata

    llm_client = LLMClient()
    repo = Repo(repo_path=".")
    repo.filter_files(include_patterns=["src/codeag/core"])
    metadata = RepoMetadata.load_metadata(repo_path=".")
    testing_strategy = define_testing_strategy(llm_client, repo, metadata)
    strategy = parse_response(testing_strategy.response)
    tests = generate_tests_from_strategy(llm_client, strategy)
    print(tests)