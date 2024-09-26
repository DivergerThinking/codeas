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


prompt_refactor_files = """
As an expert software architect, your task is to implement the proposed refactoring changes for a group of related files. You will be provided with the original file contents and the proposed changes. Your goal is to generate diffs that represent the necessary changes.

Follow these guidelines:

1. Carefully review the original file contents and the proposed changes for each file.
2. Generate diffs that accurately represent the proposed changes.
3. Use unified diff format for each file.
4. Include only the changed parts of the files in the diffs.
5. Ensure that applying these diffs will result in the desired refactored code.

Your output should be a list of RefactoredFile objects, where each object contains:
- file_path: The path of the original file
- diff: The unified diff representing the changes to be made

Ensure that all files mentioned in the proposed changes are included in your output, with their corresponding diffs.

# File editing rules:

Return edits similar to unified diffs that `diff -U0` would produce.

Make sure you include the first 2 lines with the file paths.
Don't include timestamps with the file paths.

Start each hunk of changes with a `@@ ... @@` line.
Don't include line numbers like `diff -U0` does.
The user's patch tool doesn't need them.

The user's patch tool needs CORRECT patches that apply cleanly against the current contents of the file!
Think carefully and make sure you include and mark all lines that need to be removed or changed as `-` lines.
Make sure you mark all new or modified lines with `+`.
Don't leave out any lines or the diff patch won't apply correctly.

Indentation matters in the diffs!

Start a new hunk for each section of the file that needs changes.

Only output hunks that specify changes with `+` or `-` lines.
Skip any hunks that are entirely unchanging ` ` lines.

Output hunks in whatever order makes the most sense.
Hunks don't need to be in any particular order.

When editing a function, method, loop, etc use a hunk to replace the *entire* code block.
Delete the entire existing version with `-` lines and then add a new, updated version with `+` lines.
This will help you generate correct code and correct diffs.

To move code within a file, use 2 hunks: 1 to delete it from its current location, 1 to insert it in the new location.

""".strip()


class RefactoredFile(BaseModel):
    file_path: str
    diff: str


class RefactoredFiles(BaseModel):
    files: list[RefactoredFile]


def refactor_files(
    groups: RefactoringGroups, proposed_changes: dict[str, str], preview: bool = False
) -> RefactoredFiles:
    contexts = {}
    for group in groups.groups:
        retriever = ContextRetriever(include_all_files=True)
        contexts[group.name] = retriever.retrieve(group.files_paths)
        contexts[group.name] += f"\n\nProposed changes:\n{proposed_changes[group.name]}"
    agent = Agent(
        instructions=prompt_refactor_files,
        model="gpt-4o",
        response_format=RefactoredFiles,
    )
    if preview:
        return agent.preview(context=contexts)
    else:
        return agent.run(state.llm_client, context=contexts)


if __name__ == "__main__":
    ...
