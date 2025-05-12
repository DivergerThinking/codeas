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
            # Pass None for fname as it's not used for file operations in this flow
            file_content = do_replace(None, file_content, hunk)
        except SearchTextNotUnique:
            # Removed dummy_path cleanup as dummy_path is no longer used
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )

        if file_content is None: # Explicitly check for None return indicating failure
             # Removed dummy_path cleanup
            raise ValueError("The diff failed to apply to the file content.")


    # Removed dummy_path cleanup
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
        line = lines[line_num]
        if line.startswith("```diff"):
            line_num, these_edits = process_fenced_block(lines, line_num + 1)
            edits += these_edits
            # After processing a block, the outer loop continues from the line *after* the block
            # process_fenced_block returns the line number after the closing fence
            # So, no inner loop or break needed here, the outer while continues
            # if there are more lines after the processed block.
            continue # Go to the next iteration of the outer loop from the new line_num

        line_num += 1 # Move to the next line if no block started here

    return edits


def _process_current_hunk_and_reset(hunk, edits, fname):
    """Helper to process a complete hunk and reset for the next one."""
    if hunk: # Only append if hunk is not empty
         # Remove the last line if it's the "@@ @@" marker
         if hunk[-1].strip() == "@@ @@":
             hunk = hunk[:-1]
         if hunk: # Append only if there's content left
             edits.append((fname, hunk))
    return [], False # Return empty new hunk and reset keeper state


def process_fenced_block(lines, start_line_num):
    end_line_num = start_line_num
    for line_num in range(start_line_num, len(lines)):
        line = lines[line_num]
        if line.startswith("```"):
            end_line_num = line_num
            break
    else: # No closing