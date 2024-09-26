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


class FileChanges(BaseModel):
    file_path: str
    file_changes: str


class ProposedChanges(BaseModel):
    changes: list[FileChanges]


def generate_proposed_changes(groups: RefactoringGroups, preview: bool = False):
    contexts = {}
    for group in groups.groups:
        retriever = ContextRetriever(include_all_files=True)
        contexts[group.name] = retriever.retrieve(group.files_paths)
    agent = Agent(
        instructions=prompts.generate_proposed_changes,
        model="gpt-4o",
        response_format=ProposedChanges,
    )
    if preview:
        return agent.preview(context=contexts)
    else:
        return agent.run(state.llm_client, context=contexts)


def generate_diffs(groups_changes: list[ProposedChanges], preview: bool = False) -> str:
    contexts = {}
    for proposed_changes in groups_changes:
        for change in proposed_changes.changes:
            retriever = ContextRetriever(include_all_files=True)
            file_content = retriever.retrieve([change.file_path])
            contexts[change.file_path] = [f"File content:\n{file_content}"]
            contexts[change.file_path].append(
                f"Proposed changes:\n{change.file_changes}"
            )

    agent = Agent(
        instructions=prompts.generate_diffs,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=contexts)
    else:
        return agent.run(state.llm_client, context=contexts)
