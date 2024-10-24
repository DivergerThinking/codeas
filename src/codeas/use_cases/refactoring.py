from pydantic import BaseModel

from codeas.configs import prompts
from codeas.core.agent import Agent
from codeas.core.retriever import ContextRetriever
from codeas.core.state import state
from codeas.core.usage_tracker import usage_tracker


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
        result = agent.run(state.llm_client, context=context)
        usage_tracker.record_usage(
            "define_refactoring_files", result.cost["total_cost"]
        )
        return result


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
        result = agent.run(state.llm_client, context=contexts)
        usage_tracker.record_usage(
            "generate_proposed_changes", result.cost["total_cost"]
        )
        return result


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
        result = agent.run(state.llm_client, context=contexts)
        usage_tracker.record_usage("generate_diffs", result.cost["total_cost"])
        return result
