import difflib
import json
import os
from pathlib import Path

from diff_match_patch import diff_match_patch

PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    pass


def read_prompts():
    if os.path.exists(PROMPTS_PATH):
        with open(PROMPTS_PATH, "r") as f:
            return json.load(f)
    else:
        return {}


def save_existing_prompt(existing_name, new_name, new_prompt):
    prompts = read_prompts()
    prompts[new_name] = new_prompt
    if existing_name != new_name:
        del prompts[existing_name]
    with open(PROMPTS_PATH, "w") as f:
        json.dump(prompts, f)


def delete_saved_prompt(prompt_name):
    prompts = read_prompts()
    del prompts[prompt_name]
    with open(PROMPTS_PATH, "w") as f:
        json.dump(prompts, f)


def save_prompt(name, prompt):
    prompts = read_prompts()
    name_version_map = extract_name_version(prompts.keys())

    full_name = f"{name}"
    if full_name in name_version_map.keys():
        full_name = f"{full_name} v.{name_version_map[full_name] + 1}"

    prompts[full_name] = prompt.strip()
    with open(PROMPTS_PATH, "w") as f:
        json.dump(prompts, f)


def extract_name_version(existing_names):
    # names can be like {name} or {name} v.1 or {name} v.2 etc.
    name_version_map = {}
    for full_name in existing_names:
        if " v." in full_name:
            name, version = full_name.rsplit(" v.", 1)
            version = int(version)
        else:
            name = full_name
            version = 1

        if name in name_version_map:
            name_version_map[name] = max(name_version_map[name], version)
        else:
            name_version_map[name] = version
    return name_version_map


def apply_diffs(file_content, diff_content):
    edits = list(find_diffs(diff_content))

    for path, hunk in edits:
        hunk = normalize_hunk(hunk)
        if not hunk:
            continue

        try:
            # Using a dummy path as the function signature requires it, but
            # the actual file is not modified on disk within this function.
            file_content = do_replace(Path("dummy_path"), file_content, hunk)
        except SearchTextNotUnique:
            # Clean up dummy file if created by do_replace in the error path
            if os.path.exists("dummy_path"):
                os.remove("dummy_path")
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )

        if not file_content:
            # Clean up dummy file if it wasn't removed by the exception handler
            if os.path.exists("dummy_path"):
                os.remove("dummy_path")
            raise ValueError("The diff failed to apply to the file content.")

    # Final clean up of dummy file
    if os.path.exists("dummy_path"):
        os.remove("dummy_path")
    return file_content


def find_diffs(content):
    # We can always fence with triple-quotes, because all the udiff content
    # is prefixed with +/-/space.

    if not content.endswith("\n"):
        content = content + "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits = []
    while line_num < len(lines):
        while line_num < len(lines):
            line = lines[line_num]
            if line.startswith("```diff"):
                line_num, these_edits = process_fenced_block(lines, line_num + 1)
                edits += these_edits
                break
            line_num += 1

    return edits


def process_fenced_block(lines, start_line_num):
    """
    Processes a block of lines from a diff string, looking for diff hunks.

    Args:
        lines: List of lines from the input string.
        start_line_num: The line number in `lines` where the fenced block starts (after