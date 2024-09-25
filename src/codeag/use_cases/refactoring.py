from pydantic import BaseModel

from codeag.core.agent import Agent
from codeag.core.retriever import ContextRetriever
from codeag.ui.state import state
from codeag.use_cases import prompts


class FileGroup(BaseModel):
    name: str
    files_paths: list[str]


class RefactoringGroups(BaseModel):
    groups: list[FileGroup]


def define_refactoring_files(preview: bool = False):
    retriever = ContextRetriever(include_code_files=True, use_details=True)
    context = retriever.retrieve(
        state.repo.included_files_paths,
        state.repo.included_files_tokens,
        state.repo_metadata,
    )

    agent = Agent(
        instructions=prompts.define_refactoring_files,
        model="gpt-4o",
        response_format=RefactoringGroups,
    )
    if preview:
        return agent.preview(context=context)
    else:
        return agent.run(state.llm_client, context=context)


def generate_proposed_changes(groups: RefactoringGroups, preview: bool = False):
    contexts = {}
    for group in groups.groups:
        retriever = ContextRetriever(include_all_files=True)
        contexts[group.name] = retriever.retrieve(group.files_paths)
    agent = Agent(instructions=prompts.generate_proposed_changes, model="gpt-4o")
    if preview:
        return agent.preview(context=contexts)
    else:
        return agent.run(state.llm_client, context=contexts)


class RefactoredFile(BaseModel):
    file_path: str
    refactored_code: str


class RefactoredFiles(BaseModel):
    files: list[RefactoredFile]


def refactor_files(
    groups: RefactoringGroups, proposed_changes: dict[str, str], preview: bool = False
) -> list[RefactoredFile]:
    contexts = {}
    for group in groups.groups:
        retriever = ContextRetriever(include_all_files=True)
        contexts[group.name] = retriever.retrieve(group.files_paths)
        contexts[group.name] += f"\n\nProposed changes:\n{proposed_changes[group.name]}"
    agent = Agent(
        instructions=prompts.refactor_files,
        model="gpt-4o",
        response_format=RefactoredFiles,
    )
    if preview:
        return agent.preview(context=contexts)
    else:
        return agent.run(state.llm_client, context=contexts)
