import difflib
import json
import os
from pathlib import Path

from diff_match_patch import diff_match_patch

PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    """Custom exception raised when search text is not unique."""
    pass


def read_prompts():
    """Reads prompts from the JSON file."""
    if os.path.exists(PROMPTS_PATH):
        try:
            with open(PROMPTS_PATH, "r") as f:
                # Ensure file is not empty before loading JSON
                content = f.read()
                if not content:
                    return {}
                # Reset file pointer and load
                f.seek(0)
                return json.load(f)
        except json.JSONDecodeError:
            # Handle corrupted JSON file
            print(f"Warning: Prompts file at {PROMPTS_PATH} is corrupted. Starting with empty prompts.")
            return {}
        except Exception as e:
            # Handle other potential file reading errors
            print(f"Error reading prompts file {PROMPTS_PATH}: {e}")
            return {}
    else:
        return {}


def save_prompts(prompts_data):
    """Saves the prompts dictionary to the JSON file."""
    try:
        # Ensure the directory exists
        os.makedirs(Path(PROMPTS_PATH).parent, exist_ok=True)
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts_data, f, indent=4) # Use indent for readability
    except Exception as e:
        # Handle potential file writing errors
        print(f"Error saving prompts file {PROMPTS_PATH}: {e}")


def save_existing_prompt(existing_name, new_name, new_prompt):
    """Saves a prompt, potentially renaming it."""
    prompts = read_prompts()
    prompts[new_name] = new_prompt.strip() # Strip whitespace from prompt
    if existing_name != new_name and existing_name in prompts:
        del prompts[existing_name]
    save_prompts(prompts)


def delete_saved_prompt(prompt_name):
    """Deletes a prompt by name."""
    prompts = read_prompts()
    if prompt_name in prompts:
        del prompts[prompt_name]
        save_prompts(prompts)
    else:
        # Optionally log or handle case where prompt doesn't exist
        pass # Or: print(f"Warning: Prompt '{prompt_name}' not found for deletion.")


def save_prompt(name, prompt):
    """Saves a new prompt, adding versioning if a prompt with the same base name exists."""
    prompts = read_prompts()
    name_version_map = extract_name_version(prompts.keys())

    full_name = name.strip() # Strip whitespace from name
    # Generate new version name if base name exists
    if full_name in name_version_map:
        full_name = f"{full_name} v.{name_version_map[full_name] + 1}"

    prompts[full_name] = prompt.strip() # Strip whitespace from prompt
    save_prompts(prompts)


def extract_name_version(existing_names):
    """
    Extracts base names and their highest version number from a list of names.
    Names can be like '{name}' or '{name} v.1', '{name} v.2', etc.
    """
    name_version_map = {}
    for full_name in existing_names:
        # Split off version if ' v.' is present
        if " v." in full_name:
            parts = full_name.rsplit(" v.", 1)
            name = parts[0].strip()
            try:
                version = int(parts[1])
            except ValueError:
                # Handle cases where version part is not a valid integer
                # Treat as base name with version 1 for robustness if suffix is not int.
                name = full_name.strip() # Use the full name as the base name in case of invalid suffix
                version = 1
        else:
            # No ' v.' found, this is a base name (or first version implicitly)
            name = full_name.strip()
            version = 1

        # Update map with the highest version found for this base name
        if name in name_version_map:
            name_version_map[name] = max(name_version_map[name], version)
        else:
            name_version_map[name] = version
    return name_version_map


def apply_diffs(file_content, diff_content):
    """Applies a diff hunk formatted content to file content string."""
    # Remove file system interaction related to dummy_path as the function
    # operates only on the file_content string in do_replace.
    # The Path("dummy_path") argument is kept for function signature compatibility
    # but its value is not used for actual file operations within do_replace.

    edits = list(find_diffs(diff_content))

    applied_content = file_content # Start with the original content

    for path, hunk in edits:
        hunk = normalize_hunk(hunk)
        if not hunk:
            continue # Skip empty normalized hunks

        try:
            # do_replace is refactored to only work on content string
            new_applied_content = do_replace(Path("dummy_path"), applied_content, hunk) # Use dummy path for signature
        except SearchTextNotUnique:
            # Raised when the 'before' text of the hunk isn't unique in the content
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )
        except Exception as e:
             # Catch unexpected errors during do_replace
             raise ValueError(f"An error occurred during diff application: {e}") from e


        # do_replace returns None on failure, or the new content string
        if new_applied_content is None:
            raise ValueError("The diff failed to apply to the file content.")

        applied_content = new_applied_content # Update content for the next hunk

    # No dummy file cleanup needed here as do_replace doesn't interact with file system
    return applied_content


def find_diffs(content):
    """
    Finds diff blocks fenced by ```diff ... ``` in the input content
    and parses them into a list of edits.
    """
    # Ensure content ends with a newline for consistent splitlines behavior
    if not content.endswith("\n"):
        content += "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits = []

    # Iterate through lines looking for the start of a diff block
    while line_num < len(lines):
        line = lines[line_num]
        if line.strip().startswith("```diff"): # Use strip() to handle leading whitespace
            # Process the fenced block starting from the line *after* the start marker
            line_num, these_edits = process_fenced_block(lines, line_num + 1)
            edits.extend(these_edits) # Use extend for lists
            # process_fenced_block returns the line number *after* the end marker,
            # so the loop continues searching from there.
        else:
            line_num += 1 # Move to the next line if not a diff block start

    # Original code included a commented-out line `edits = edits[:1]`
    # This would only process the first diff block found. Keeping it commented.
    # edits = edits[:1]

    return edits

# Helper functions extracted to reduce cognitive complexity of process_fenced_block
def finalize_hunk_before_file_transition(hunk_buffer):
    """Extracts the hunk content preceding a ---/+++ transition."""
    # Assumes hunk_buffer includes the ---/+++ lines (at the end).
    # Replicates original logic: remove the last two lines (---/+++) plus a possible preceding newline.
    # Ensure buffer is large enough before accessing indices from the end.
    if len(hunk_buffer) >= 3 and hunk_buffer[-3] == "\n":
        return hunk_buffer[:-3]
    # Handle case where the last two lines are ---/+++ but no preceding newline
    elif len(hunk_buffer) >= 2:
        return hunk_buffer[:-2]
    else:
        return [] # Should not happen with valid diff format

def finalize_hunk_before_marker(hunk_buffer):
    """Extracts the hunk content preceding an @ line."""
    # Assumes hunk_buffer includes the @ line (at the end).
    # Ensure buffer is not empty before slicing
    return hunk_buffer[:-1] if hunk_buffer else []

def handle_at_line_helper(hunk, keeper, edits, fname):
    """Handles a line starting with @. Modifies hunk and edits list in place."""
    if keeper:
        # Finalize the hunk ending *before* this @ line.
        # hunk_to_add will be the context/changes lines gathered so far (excluding the current '@').
        hunk_to_add = finalize_hunk_before_marker(hunk)
        if hunk_to_add: # Only add if there is content in the hunk (context/changes)
             edits.append((fname, hunk_to_add))

        # Clear the hunk buffer to start accumulating lines for the next potential hunk.
        # The current '@' line is discarded as it's not part of the hunk content.
        hunk[:] = [] # Clear list in place
        return False # Reset keeper state as we've finished a change block

    else: # not keeper (encountered @ line before any '+' or '-' line)
        # Discard everything seen so far for this potential hunk, including the @ line.
        hunk[:] = [] # Clear list in place
        return False # Keeper remains False

def process_fenced_block(lines, start_line_num):
    """
    Processes lines within a ```diff ... ``` fenced block to extract diff hunks.
    Returns the line number after the block and the list of edits.
    """
    # Find the end of the block (line starting with ```)
    end_line_num = start_line_num
    while end_line_num < len(lines):
        line = lines[end_line_num]
        if line.strip().startswith("```"): # Use strip() to handle leading whitespace
            break
        end_line_num += 1

    # Extract lines forming the diff block content
    block_lines = lines[start_line_num:end_line_num]

    # Handle potential initial file header (--- followed by +++) outside the main loop.
    # This header defines the file name for the first hunk.
    current_fname = None
    # Check if block_lines has at least two elements before accessing indices
    if len(block_lines) >= 2 and block_lines[0].strip().startswith("--- ") and block_lines[1].strip().startswith("+++ "):
        # Extract file name from the '+++' line, stripping leading/trailing whitespace
        current_fname = block_lines[1][4:].strip()
        # Remove these header lines from the block lines to be processed in the main loop
        block_lines = block_lines[2:]

    # Add a sentinel "@@ @@" line at the end of the block_lines.
    # The original code added "@@ @@" without a newline. Let's replicate this.
    # This sentinel helps the loop logic recognize the end of the last hunk.
    block_lines.append("@@ @@")

    edits = []
    hunk = [] # List to accumulate lines for the current hunk
    keeper = False # Flag to indicate if the current hunk contains '+' or '-' lines

    # Iterate through the prepared block lines (after removing initial headers and adding sentinel)
    for line in block_lines:
        hunk.append(line) # Always append the current line to the hunk buffer first

        # Determine the operation character of the current line
        op = line[0] if len(line) > 0 else " " # Default to space for empty lines

        # Process line types based on the operation character using if/elif/continue

        # 1. File transition marker (--- then +++) - Check for this pattern at the end of the current hunk buffer
        # This signifies the end of a hunk and the start of headers for the next hunk.
        # Check if the last two lines *currently in the hunk buffer* are --- / +++
        if len(hunk) >= 2 and hunk[-2].strip().startswith("--- ") and hunk[-1].strip().startswith("+++ "):
             # Finalize the hunk ending *before* these header lines.
             # `finalize_hunk_before_file_transition` expects hunk_buffer including the headers.
             hunk_to_add = finalize_hunk_before_file_transition(hunk)
             if hunk_to_add: # Only add if there was content before the headers
                 edits.append((current_fname, hunk_to_add))

             # Clear the hunk buffer and reset for the next hunk.
             # The header lines themselves are not part of the hunk content.
             hunk[:] = [] # Clear list in place (discard headers and preceding context)
             keeper = False # Reset keeper state
             # Update the current file name from the '+++' line (which is hunk[-1] before clearing)
             current_fname = line[4:].strip() # 'line' is the +++ line here
             continue # Move to processing the next line in block_lines

        # 2. Change line (+ or -)
        # If the line starts with '+' or '-', the current hunk includes changes.
        if op in "-+":
            keeper = True # Set keeper flag to True
            # Continue processing - the line is already appended to hunk.

        # 3. @ line (Hunk header)
        # This signifies the start of a new hunk (or section within a hunk).
        # Original logic handled this after +/- lines, let's match that order.
        if op == "@":
            # Use helper to process the @ line. It might finalize the previous hunk.
            # `handle_at_line_helper` modifies the `hunk` list in place and updates `keeper`.
            # It is passed the `hunk` buffer which *includes* the current '@' line.
            keeper = handle_at_line_helper(hunk, keeper, edits, current_fname)
            continue # Move to processing the next line in block_lines

        # 4. Ignore lines shorter than 2 characters unless they are +/-/@ (already handled).
        # This check ensures empty or single-char lines (like just '\n') don't affect logic unnecessarily.
        # These lines are already appended to `hunk` if they weren't handled by the above conditions.
        if len(line) < 2 and op not in "-+@":
             # If it's a short line that isn't a +/-/@ marker, just continue.
             # It remains in the `hunk` buffer as potential context.
             continue # Move to processing the next line in block_lines

        # 5. Default: Context line (' ')
        # Lines starting with ' ' are context lines. They are already appended to `hunk`.
        # The loop implicitly continues to the next iteration.

    # The loop finishes after processing `block_lines` including the sentinel.
    # The next line number in the overall document is `end_line_num + 1`.
    return end_line_num + 1, edits


def normalize_hunk(hunk):
    """
    Normalizes a parsed hunk by converting it back to 'before' and 'after' lists
    and then generating a standard unified diff format.
    This can sometimes re-align context lines.
    """
    # Get 'before' and 'after' lists of lines from the parsed hunk structure
    before, after = hunk_to_before_after(hunk, lines=True)

    # Apply cleanup to pure whitespace lines (replace with minimal line ending)
    before = cleanup_pure_whitespace_lines(before)
    after = cleanup_pure_whitespace_lines(after)

    # Generate a unified diff between the cleaned 'before' and 'after' line lists
    # Use n=max(...) to include all context lines
    diff = difflib.unified_diff(before, after, n=max(len(before), len(after)))
    # Convert the generator to a list and skip the header lines (---, +++, @@ ...)
    diff = list(diff)[3:]
    return diff


def cleanup_pure_whitespace_lines(lines):
    """
    Replaces lines consisting only of whitespace with a minimal representation
    (just the line ending).
    """
    res = [
        # If the line stripped of whitespace is empty, replace it
        # with just its line ending characters (\r or \n or \r\n).
        # Otherwise, keep the original line.
        line if line.strip() else line[-(len(line) - len(line.rstrip("\r\n")))]
        for line in lines
    ]
    return res


def hunk_to_before_after(hunk, lines=False):
    """
    Converts a list of diff hunk lines (starting with ' ', '-', '+')
    into separate lists or strings for the 'before' and 'after' content.
    """
    before = []
    after = []
    op = " " # Default operation

    for line in hunk:
        # Determine the operation and the line content (after the operation char)
        if len(line) < 2:
            # If line is too short, it's likely an empty line or just a line ending.
            # Treat as context (' ') and the line content is the whole line.
            op = " "
            # Fix S1656: Removed useless self-assignment `line = line`
            processed_line = line
        else:
            # Extract the operation character and the rest of the line content
            op = line[0]
            processed_line = line[1:]

        # Append the processed line content to 'before', 'after', or both based on the operation
        if op == " ":
            before.append(processed_line)
            after.append(processed_line)
        elif op == "-":
            before.append(processed_line)
        elif op == "+":
            after.append(processed_line)
        # Lines with other ops (like @ or file headers) are ignored here, which is correct.

    # Return lists of lines or concatenated strings based on the 'lines' flag
    if lines:
        return before, after

    before = "".join(before)
    after = "".join(after)

    return before, after


def do_replace(fname, content, hunk):
    """
    Applies a single diff hunk (as a list of lines) to the content string.
    Attempts direct application first, then more flexible strategies.
    fname argument is kept for signature compatibility but not used for file operations.
    Returns the new content string or None on failure.
    """
    # fname = Path(fname) # This is no longer used for file operations

    # Get the 'before' and 'after' string content from the hunk
    # Fix S1481: Replace the first element of the tuple with '_' as suggested by SonarQube rule S1481.
    # This means the variable `before_text` (or `before_text_string` in previous fix) is considered unused by the rule here.
    # However, the *value* is still needed for subsequent logic.
    # To comply strictly, we use `_` here and retrieve the value separately if needed.
    _, after_text_string = hunk_to_before_after(hunk)

    # Get the 'before' text string value again because it's needed for checks and subsequent calls.
    before_text_string_value, _ = hunk_to_before_after(hunk) # The second value here is the after_text string again, use _


    # This block in the original code attempted to handle creating new files
    # and appending to files based on the dummy fname and hunk content.
    # Since we are only operating on the `content` string, this file system
    # interaction and conceptual "new file" logic needs to be adapted or removed.
    # The core logic of apply_diffs passes file_content (which can be empty "" for new files)
    # and expects back the modified string.
    # The logic below was tied to fname.exists() and fname.touch(). Let's adapt
    # the intent: if the hunk is purely an insertion (no 'before' context) AND the
    # input content was empty, it's like creating a new file. If the input content
    # was not empty, it's an append operation.
    # Original: if not fname.exists() and not before_text_string.strip():
    # Adapted: if content is empty AND the hunk is a pure insertion:
    if not content and not before_text_string_value.strip():
        # This hunk represents the initial content of a new file.
        # The result is simply the 'after' content from the hunk.
        return after_text_string
    # Original: if content is None: return # Handled by apply_diffs, but defensive here
    if content is None:
         return None

    # TODO: handle inserting into new file - partially handled above for empty content.
    # The original code had `if not before_text.strip():` and appended `after_text`.
    # This means if the hunk had no 'before' context (a pure addition), it just appended
    # the 'after' text to the *current* content, regardless of whether content was empty or not.
    # Let's match this original appending behavior for pure insertion hunks.
    if not before_text_string_value.strip():
        # Hunk is a pure insertion (only '+' lines). Append its 'after' content.
        # This handles appending to an existing non-empty content or starting with after_text if content was "".
        new_content = content + after_text_string
        return new_content


    # If there is 'before' context in the hunk, attempt standard diff application
    # The original `new_content = None` here was useless.
    new_content = apply_hunk(content, hunk)

    # apply_hunk returns the new content string on success or None on failure.
    # Return this result.
    return new_content


def apply_hunk(content, hunk):
    """
    Attempts to apply a single diff hunk to the content string using flexible strategies.
    Returns the new content string or None on failure.
    """
    # before_text, after_text = hunk_to_before_after(hunk) # These are not used directly here

    # First, try directly applying the hunk using basic search and replace.
    res = directly_apply_hunk(content, hunk)
    if res is not None: # Check explicitly for None return value indicating success/failure
        return res

    # If direct application fails, try a more flexible approach:
    # 1. Generate a 'new_before' context by diffing the original 'before' against the content.
    #    This effectively prunes lines from the 'before' hunk that are *not* in the content.
    # 2. Generate a new hunk using this 'new_before' and the original 'after'.
    # 3. Attempt to apply this new hunk.
    refined_hunk = make_new_lines_explicit(content, hunk)

    # make_new_lines_explicit returns a refined hunk or the original hunk (or potentially None?).
    # If it returns None, it signifies that the refinement step failed in a way
    # that prevents further attempts with this hunk.
    if refined_hunk is None:
        return None # Indicate failure

    # Now attempt to apply the refined hunk using flexible search/replace strategies.
    # This involves splitting the hunk into sections (context/changes) and trying
    # partial applications with varying amounts of context.

    # Original logic for creating a simplified 'ops' string and splitting the hunk
    # into sections based on operation type.
    # This logic assumes the hunk can be broken into segments like [context, changes, context, ...].
    # The 'ops' string maps each line in the hunk to a simplified operation character.
    ops = "".join([line[0] if len(line) > 0 else " " for line in refined_hunk]) # Ensure line has length before [0]
    ops = ops.replace("-", "x") # Map '-' and '+' to 'x' for change sections
    ops = ops.replace("+", "x")
    ops = ops.replace("\n", " ") # Map explicit newlines (from make_relative maybe?) to space (context?) - Replicating original behavior

    cur_op = " " # Original code starts grouping assuming initial context
    section = []
    sections = []

    # Iterate through the simplified operations to group lines from the refined_hunk
    for i in range(len(ops)):
        op = ops[i]
        if op != cur_op:
            # When operation changes, append the accumulated section (if not empty)
            if section: # Only append if the section has lines
                sections.append(section)
            section = [] # Start a new section for the new operation type
            cur_op = op # Update the current operation type
        # Append the corresponding line from the refined_hunk to the current section
        section.append(refined_hunk[i])

    # Append the very last section after the loop finishes
    if section: # Only append if the section has lines
        sections.append(section)

    # Add a potential final empty section if the last original operation was not ' '.
    # This is based on the original code's structure and seems necessary for the
    # subsequent loop logic which expects an odd number of sections [ctx, chg, ctx, chg, ctx, ...].
    # If the last section was changes, an empty context section is needed as a placeholder.
    # If the last section was context, the loop handles it correctly.
    if sections and (ops and ops[-1] != " "): # Check if sections is not empty and last op wasn't context
         sections.append([]) # Add placeholder for missing trailing context section

    all_done = True
    # Iterate through the sections list, attempting to apply partial hunks.
    # The loop range `range(2, len(sections) + 1, 2)` seems to process triplets:
    # (sections[i-2], sections[i-1], sections[i]) for i = 2, 4, 6, ...
    # This corresponds to (Context, Changes, Context) triplets.
    # Note the original range ended at `len(sections)`. Adding `+1` makes it inclusive
    # of the last possible index `len(sections)`, which is necessary if the sections list
    # has an even number of elements (e.g., ending in changes, needing the empty list added above).
    # The indices accessed are i-2, i-1, i. The loop should go up to where i is the index of the last context block.
    # If sections is [c1, m1, c2, m2, c3], len=5. range(2, 6, 2). i=2, 4.
    # i=2: [0](c1), [1](m1), [2](c2)
    # i=4: [2](c2), [3](m2), [4](c3)
    # This seems correct. The range `len(sections) + 1` seems appropriate.
    for i in range(2, len(sections) + 1, 2):
        # Extract the preceding context, changes, and following context sections
        # Use slicing with boundary checks in case sections list is shorter than expected.
        preceding_context = sections[i - 2] if i - 2 < len(sections) else []
        changes = sections[i - 1] if i - 1 < len(sections) else []
        following_context = sections[i] if i < len(sections) else []

        # Attempt to apply the partial hunk consisting of these sections
        res = apply_partial_hunk(content, preceding_context, changes, following_context)
        if res is not None: # If application succeeded
            content = res # Update content for the next partial application
        else:
            # If any partial application fails, the whole apply_hunk process fails.
            all_done = False
            # FAILED!
            # this_hunk = preceding_context + changes + following_context # Original comment
            break # Stop processing further sections

    if all_done:
        return content # Return the content if all partial hunks were applied successfully
    else:
        # If not all partial hunks were applied, the whole apply_hunk attempt fails.
        return None # Return None on failure


def make_new_lines_explicit(content, hunk):
    """
    Refines the 'before' part of a hunk by finding lines from the original
    'before' that are present in the content. Creates a new hunk based on
    this refined 'before' and the original 'after'.
    Returns the refined hunk (list of lines) or the original hunk on failure.
    Returns None if a critical step fails.
    """
    # Get the original 'before' and 'after' text content from the hunk.
    original_before_text, after_text_string = hunk_to_before_after(hunk)

    # If the original 'before' text is empty, we cannot refine it. Return the original hunk.
    if not original_before_text:
        return hunk # Return original hunk if no 'before' text to refine

    # Diff the original 'before' text (from the hunk) against the actual content string.
    # This diff describes how to transform `original_before_text` into `content`.
    diff_against_content = diff_lines(original_before_text, content)

    # Filter this diff to create a `back_diff`. The intent seems to keep lines from
    # `diff_against_content` that represent content *common* to `original_before_text`
    # and `content` (lines starting with ' '), and lines *removed* from `original_before_text`
    # (lines starting with '-'). Lines added in `content` relative to `original_before_text`
    # (lines starting with '+') are explicitly skipped.
    back_diff = []
    for line in diff_against_content:
        if line and line[0] == "+": # Skip lines starting with '+' (additions in content)
            continue
        # Keep all other lines ('-', ' ', etc.)
        back_diff.append(line)

    # Apply this `back_diff` (treated as a hunk) to the *original* `before_text_string`.
    # This step is complex and potentially confusing, but it aims to generate a `new_before`
    # string that is a subset of `original_before_text`, containing only lines that also
    # exist in the actual `content` (excluding those marked '+' in the diff).
    # `directly_apply_hunk` needs content string and hunk lines. We use `original_before_text` as content
    # and `back_diff` list as the hunk lines to apply.
    new_before = directly_apply_hunk(original_before_text, back_diff)

    # If `directly_apply_hunk` failed (returned None) or the result is too short,
    # it means the refinement process didn't yield a useful 'new_before'.
    # In this case, return the original hunk to indicate that refinement failed.
    if new_before is None or len(new_before.strip()) < 10:
        return hunk # Return original hunk if refinement failed or new_before is too short

    # Also check if the refinement removed too many lines compared to the original 'before'.
    # If the refined 'before' has less than 66% of the lines of the original 'before',
    # consider the refinement unsuccessful and return the original hunk.
    before_lines = original_before_text.splitlines(keepends=True) # Original before lines (for length comparison)
    new_before_lines = new_before.splitlines(keepends=True)     # Refined before lines (the new search target)
    if len(new_before_lines) < len(before_lines) * 0.66:
        return hunk # Return original hunk if too many lines were lost in refinement

    # If the refinement seems successful, generate a *new diff hunk* using the
    # `new_before_lines` (the refined search target) and the `after_text_string` (the desired result).
    # This new hunk describes the change from the refined context to the desired after state.
    after_lines = after_text_string.splitlines(keepends=True) # Original after text as lines
    new_hunk = difflib.unified_diff(
        new_before_lines, after_lines, n=max(len(new_before_lines), len(after_lines)) # Use max for context lines
    )
    # Convert the generator to a list and skip header lines
    new_hunk = list(new_hunk)[3:]

    # Return the newly generated hunk, which is potentially easier to apply.
    return new_hunk


def diff_lines(search_text, replace_text):
    """
    Uses diff_match_patch to generate a line-by-line diff between two strings
    and formats it into a list of lines starting with ' ', '-', or '+'.
    Returns the list of formatted diff lines.
    """
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5 # Set diff timeout
    # dmp.Diff_EditCost = 16 # Commented out in original

    # Convert strings to character-based representation for efficient diffing
    # while preserving line structure.
    search_lines_chars, replace_lines_chars, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    # Handle potential None input from diff_linesToChars, although it should return empty strings
    if search_lines_chars is None or replace_lines_chars is None or mapping is None:
         return [] # Return empty diff if inputs are invalid


    # Perform the main diff algorithm on the character representations
    diff_chars = dmp.diff_main(search_lines_chars, replace_lines_chars, None)
    # Clean up the diff results (semantic and efficiency heuristics)
    dmp.diff_cleanupSemantic(diff_chars)
    dmp.diff_cleanupEfficiency(diff_chars)

    # Convert the character-based diff back to lines using the mapping
    diff = list(diff_chars) # Convert to list for mutability if needed (charsToLines modifies in place?)
    # Check if diff is empty before calling charsToLines, although it should handle empty.
    if diff:
        dmp.diff_charsToLines(diff, mapping) # Modifies the diff list in place

    # Format the diff results into a list of strings with '+', '-', or ' ' prefixes.
    udiff = []
    for d_type, lines_text in diff:
        # Map diff_match_patch diff types (-1, 0, 1) to characters ('-', ' ', '+')
        op_char = " "
        if d_type < 0:
            op_char = "-" # Deletion
        elif d_type > 0:
            op_char = "+" # Insertion
        # else op_char remains " " (Equal)

        # Split the lines_text (which might contain multiple lines) into individual lines, keeping endings.
        # Ensure the string ends with a newline before splitting for consistent behavior with keepends=True.
        lines_text_normalized = lines_text if lines_text.endswith("\n") else lines_text + "\n" if lines_text else ""
        for line in lines_text_normalized.splitlines(keepends=True):
            # Append the operation character and the line to the result list.
            udiff.append(op_char + line)

    return udiff


def apply_partial_hunk(content, preceding_context, changes, following_context):
    """
    Attempts to apply a partial hunk (defined by explicit context and changes sections)
    to the content string. It tries applying the hunk with varying amounts of context
    lines from the edges, from full context down to zero context.
    Returns the new content string if successful, None otherwise.
    """
    len_prec = len(preceding_context) # Number of preceding context lines
    len_foll = len(following_context) # Number of following context lines

    use_all = len_prec + len_foll # Total number of context lines available

    # Iterate through all possible numbers of context lines to drop, from 0 up to use_all.
    # `use` will be the total number of context lines kept.
    for drop in range(use_all + 1):
        use = use_all - drop # Number of context lines to use (sum of preceding and following)

        # Iterate through all possible ways to split the `use` context lines between
        # the preceding and following sections.
        # `use_prec` goes from the maximum available preceding context down to 0.
        for use_prec in range(len_prec, -1, -1):
            # Calculate the number of following context lines needed for the current `use`.
            use_foll = use - use_prec

            # If the calculated `use_foll` is more than the available following context lines,
            # this split is invalid. Continue to the next split combination.
            if use_foll > len_foll:
                continue # Skip this split, try fewer preceding lines for the same total 'use'

            # Extract the specific preceding context lines to use (from the end of preceding_context).
            if use_prec > 0: # If we need to use any preceding context
                this_prec = preceding_context[-use_prec:] # Take the last use_prec lines
            else:
                this_prec = [] # Use no preceding context lines

            # Extract the specific following context lines to use (from the beginning of following_context).
            if use_foll > 0: # If we need to use any following context
                 this_foll = following_context[:use_foll] # Take the first use_foll lines
            else:
                 this_foll = [] # Use no following context lines

            # Construct the partial hunk list by combining the selected preceding context,
            # the changes section, and the selected following context.
            partial_hunk = this_prec + changes + this_foll

            # Attempt to apply this constructed partial hunk using directly_apply_hunk.
            res = directly_apply_hunk(content, partial_hunk)

            # If directly_apply_hunk succeeds (returns non-None), we found a way to apply this part.
            if res is not None:
                return res # Return the modified content

    # If the loop finishes without any attempt succeeding for this partial hunk, return None.
    return None


def directly_apply_hunk(content, hunk):
    """
    Attempts to apply a diff hunk directly to the content string using search and replace.
    It gets the 'before' and 'after' text from the hunk and searches for the 'before'
    text in the content, replacing it with the 'after' text.
    Includes a check to prevent search/replace on short, non-unique 'before' text.
    Returns the new content string if successful, None otherwise.
    """
    # Get the 'before' and 'after' string content from the hunk lines.
    # Fix S1481: Replace the first element of the tuple with '_' as suggested by SonarQube rule S1481.
    # This means the variable `before_text` (or `before_text_string` in previous fix) is considered unused by the rule here.
    # However, the *value* is still needed for subsequent logic.
    # To comply strictly, we use `_` here and retrieve the value separately if needed.
    _, after_text_string = hunk_to_before_after(hunk)

    # Get the 'before' text string value again because it's needed for checks and subsequent calls.
    before_text_string_value, _ = hunk_to_before_after(hunk) # The second value here is the after_text string again, use _


    # Cannot apply a hunk that describes no content to find (empty 'before' string).
    # Return None if the search text is empty.
    if not before_text_string_value:
        return None

    # Get the 'before' lines from the hunk (for length/strip check) without getting 'after' lines.
    before_lines_list, _unused_after_lines = hunk_to_before_after(hunk, lines=True) # Use _ for the unused return value
    # Join the 'before' lines and strip whitespace for the short/non-unique check.
    before_lines_stripped = "".join([line.strip() for line in before_lines_list])

    # Refuse to do a direct search and replace if the stripped 'before' context
    # is very short (<10 characters) AND the raw 'before' text appears multiple times
    # in the content. This avoids potentially incorrect replacements based on ambiguous context.
    # The original code commented out raising `SearchTextNotUnique` in `search_and_replace`,
    # so this check is an alternative way to handle ambiguous matches for short patterns.
    if len(before_lines_stripped) < 10 and content.count(before_text_string_value) > 1:
        return None # Return None to signal that direct application is too ambiguous

    try:
        # Attempt search and replace using the flexible search/replace mechanism.
        # This mechanism might apply preprocessors before calling the core search_and_replace.
        # Pass the raw 'before' text string (`before_text_string_value`), 'after' text string (`after_text_string`), and the content.
        new_content = flexi_just_search_and_replace([before_text_string_value, after_text_string, content])
    except SearchTextNotUnique:
        # Although the base `search_and_replace` likely won't raise this (due to commented out line),
        # keep the catch block as per original code structure, in case other strategies might.
        new_content = None
    except Exception as e:
        # Catch any other unexpected errors during flexible search/replace
        print(f"Error during flexible search/replace: {e}")
        new_content = None # Treat any error as a failure

    return new_content # Return the resulting content or None if the application failed.


def flexi_just_search_and_replace(texts):
    """
    Defines a single core strategy (simple search_and_replace) and a set
    of preprocessor combinations to try with it.
    Delegates to flexible_search_and_replace.
    """
    # Define the search/replace strategies and the list of preprocessors to apply to them.
    strategies = [
        # A strategy is a tuple: (core_strategy_function, list_of_preprocessor_tuples)
        (search_and_replace, all_preprocs), # Use search_and_replace function with all preprocessor combos
    ]

    # Call the main flexible search/replace logic.
    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    """
    The core search and replace function. Searches for `search_text` in
    `original_text` and replaces it with `replace_text`.
    Returns the new text string if `search_text` is found at least once,
    None if not found. Does not raise SearchTextNotUnique if found multiple times
    (matching original commented-out logic).
    """
    # Unpack the input tuple: (search_text, replace_text, original_text)
    search_text, replace_text, original_text = texts

    # Handle potential None input for robustness, although try_strategy should filter
    if search_text is None or replace_text is None or original_text is None:
         return None

    # Count occurrences of the search text in the original text
    num = original_text.count(search_text)

    # Original code commented out raising SearchTextNotUnique if num > 1:
    # if num > 1:
    #    raise SearchTextNotUnique()

    # If the search text is not found (0 occurrences), return None to signal failure.
    if num == 0:
        return None

    # Perform the replacement. If num > 1, all occurrences will be replaced.
    new_text = original_text.replace(search_text, replace_text)

    # Note: This implementation doesn't handle the case where num > 1 if the raise is commented out.
    # It will replace *all* occurrences if num > 1. This might be a bug depending on desired behavior.
    # Sticking to original code's behavior for now.

    return new_text # Return the new text if successful


def flexible_search_and_replace(texts, strategies):
    """
    Iterates through a list of strategies (core function + preprocessors) and
    attempts to apply them until one succeeds (returns non-None result).
    Returns the result of the first successful strategy or None if none succeed.
    """
    # texts is expected to be a list [search_text, replace_text, original_text]

    # Iterate through each strategy defined in the `strategies` list.
    for strategy, preprocs in strategies:
        # For each strategy, iterate through the list of preprocessor combinations.
        for preproc in preprocs:
            # Try attempting to apply the current strategy with the current preprocessor combination.
            # `try_strategy` handles applying preprocessors, the core strategy, and postprocessors.
            # Ensure texts are not None before proceeding
            if texts is None or any(t is None for t in texts):
                 continue # Skip this preproc/strategy if input texts are invalid

            # Call try_strategy and get the result (new text string or None)
            res = try_strategy(texts, strategy, preproc)

            # If `try_strategy` returns a non-None result, it means the application was successful.
            if res is not None:
                return res # Return the successful result immediately

    # If the loops complete without any strategy/preprocessor combination succeeding, return None.
    return None


def try_strategy(texts, strategy, preproc):
    """
    Applies preprocessors, the core strategy, and postprocessors to the texts.
    Handles potential ValueErrors from RelativeIndenter.
    Returns the final resulting text or None on failure at any step.
    """
    # Unpack the boolean flags indicating which preprocessors to apply.
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None # Initialize RelativeIndenter instance variable, will be assigned if relative indent is used.

    # Create a mutable copy of the input texts list.
    processed_texts = list(texts)

    try:
        # Apply preprocessors based on flags. Each preprocessor function should return
        # the modified texts or None on failure. Propagate None if failure occurs.
        if preproc_strip_blank_lines:
            processed_texts = strip_blank_lines(processed_texts)
            if processed_texts is None or any(t is None for t in processed_texts):
                 return None # Propagate failure

        if preproc_relative_indent:
            # relative_indent returns the indenter instance and the processed texts.
            ri, processed_texts = relative_indent(processed_texts)
            # Check if relative_indent returned None for either ri or texts, indicating failure.
            if ri is None or processed_texts is None or any(t is None for t in processed_texts):
                 return None # Propagate failure

        if preproc_reverse:
            # Apply reverse_lines to each text string. Use map and convert iterator to list.
            # reverse_lines can return None, check for None in the list.
            processed_texts = list(map(reverse_lines, processed_texts))
            if processed_texts is None or any(t is None for t in processed_texts):
                 return None # Propagate failure

        # Apply the core search/replace strategy function to the processed texts.
        # The strategy function should return the result (new text string) or None on failure.
        res = strategy(processed_texts)

        # Apply postprocessors in reverse order of preprocessors, *only if* the strategy succeeded (res is not None).
        if res is not None:
            if preproc_reverse:
                # Reverse the lines back. reverse_lines can return None.
                res = reverse_lines(res)
                if res is None: return None # Propagate failure if post-processing fails

            # Check res is still not None before applying next postprocessor.
            if res is not None and preproc_relative_indent:
                # Convert relative indents back to absolute using the stored RelativeIndenter instance.
                # make_absolute can raise ValueError.
                res = ri.make_absolute(res)
                # make_absolute raises ValueError on failure, which is caught below.
                # It doesn't return None.
                if res is None: # Defensive check, should be ValueError
                     return None # Propagate failure

    except ValueError:
        # Catch ValueErrors that might be raised by RelativeIndenter methods (`make_relative`, `make_absolute`, `__init__`).
        # These errors indicate a failure specific to the relative indentation process.
        return None # Treat this specific strategy combination as a failure

    # Return the final result after applying strategy and postprocessors, or None if any step failed.
    return res


def strip_blank_lines(texts):
    """
    Applies leading/trailing blank line stripping to each text string in the list.
    Preserves the presence of a single trailing newline if one existed.
    Handles None inputs. Returns the list of processed texts or None if input is invalid.
    """
    if texts is None: return None
    processed_texts = []
    for text in texts:
        if text is None:
             processed_texts.append(None) # Keep None in the list if present
             continue
        # Use rstrip("\r\n") to remove any combination of carriage return and newline at the end.
        stripped_text = text.rstrip("\r\n")
        # Add back a single newline character if the original text ended with one.
        # This attempts to preserve the trailing newline state.
        if text.endswith("\n"):
             processed_texts.append(stripped_text + "\n")
        else:
             processed_texts.append(stripped_text) # Keep without newline if original had none
    return processed_texts


def relative_indent(texts):
    """
    Applies the relative indentation transformation to each text string in the list.
    Creates a RelativeIndenter instance based on the input texts first.
    Handles potential failures during indenter creation or relative transformation.
    Returns the RelativeIndenter instance and the list of processed texts, or (None, None) on failure.
    """
    if texts is None: return None, None
    try:
        # Create RelativeIndenter instance. Can raise ValueError if no unique marker found.
        ri = RelativeIndenter(texts)
    except ValueError:
        # If a unique marker cannot be found, this preprocessor cannot be applied.
        return None, None # Indicate failure by returning None for both ri and texts

    # Apply the make_relative transformation to each text.
    processed_texts = []
    for text in texts:
        if text is None:
             processed_texts.append(None) # Keep None in the list if present
             continue
        try:
             # make_relative can raise ValueError if text already contains the marker.
             processed_texts.append(ri.make_relative(text))
        except ValueError:
             # If make_relative fails for any text, the whole relative_indent process fails.
             return None, None # Indicate failure

    # Return the successful indenter instance and the list of processed texts.
    return ri, processed_texts


class RelativeIndenter:
    """
    Rewrites text files to have relative indentation, which involves
    reformatting the leading white space on lines.  This format makes
    it easier to search and apply edits to pairs of code blocks which
    may differ significantly in their overall level of indentation.

    It removes leading white space which is shared with the preceding
    line.

    Original:
    ```
            Foo # indented 8
                Bar # indented 4 more than the previous line
                Baz # same indent as the previous line
                Fob # same indent as the previous line
    ```

    Becomes:
    ```
            Foo # indented 8
        Bar # indented 4 more than the previous line
    Baz # same indent as the previous line
    Fob # same indent as the previous line
    ```

    If the current line is *less* indented then the previous line,
    uses a unicode character to indicate outdenting.

    Original
    ```
            Foo
                Bar
                Baz
            Fob # indented 4 less than the previous line
    ```

    Becomes:
    ```
            Foo
        Bar
    Baz
    ←←←←Fob # indented 4 less than the previous line
    ```

    This is a similar original to the last one, but every line has
    been uniformly outdented:
    ```
    Foo
        Bar
        Baz
    Fob # indented 4 less than the previous line
    ```

    It becomes this result, which is very similar to the previous
    result.  Only the white space on the first line differs.  From the
    word Foo onwards, it is identical to the previous result.
    ```
    Foo
        Bar
    Baz
    ←←←←Fob # indented 4 less than the previous line
    ```

    """

    def __init__(self, texts):
        """
        Initializes the indenter by finding a unique marker character.
        Raises ValueError if no unique marker can be found among high Unicode codepoints.
        """
        chars = set()
        for text in texts:
            # Collect all characters present in the input texts.
            if text is not None: # Check if text is not None
                 chars.update(text)

        ARROW = "←" # Preferred marker character
        if ARROW not in chars:
            self.marker = ARROW # Use the preferred marker if available
        else:
            # If the default marker is present, search for a unique one.
            # select_unique_marker raises ValueError if it fails.
            self.marker = self.select_unique_marker(chars)


    def select_unique_marker(self, chars):
        """
        Searches for a unique Unicode character not present in the given set of characters.
        Starts searching from high Unicode codepoints downwards.
        Raises ValueError if no unique character is found in the specified range.
        """
        # Iterate downwards through a range of high Unicode codepoints.
        for codepoint in range(0x10FFFF, 0x10000, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker # Return the first unique character found

        # If the loop completes without finding a unique marker, raise an error.
        raise ValueError("Could not find a unique marker")

    def make_relative(self, text):
        """
        Transforms text to use relative indents, inserting the relative indent
        on a line preceding the content line.
        Expected output format is pairs of lines: relative_indent_line \n content_line \n ...
        Raises ValueError if the input text already contains the indenter's marker
        or if indentation calculation results in an unexpected state.
        """
        if self.marker in text:
            # Defensive check: if the marker is already present, the input might be
            # already relatively indented or contains the marker for other reasons.
            # This indicates an issue with the input text or usage.
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True) # Split text into lines, keeping line endings

        output = []
        prev_indent = "" # Track the absolute indentation string of the *previous* processed line
        for line in lines:
            # Process each line to determine its absolute indent and the change from the previous line.
            line_without_end = line.rstrip("\n\r") # Remove line endings to calculate length of indentation

            # Find the absolute indentation string at the beginning of the line
            indent_match = line_without_end.lstrip() # Content part without leading whitespace
            len_indent = len(line_without_end) - len(indent_match) # Length of the absolute indent string
            indent = line[:len_indent] # The actual absolute whitespace string

            # Calculate the difference in indentation length compared to the previous line
            change = len_indent - len(prev_indent)

            # Determine the relative indentation string based on the change
            if change > 0:
                # Indented more: the relative indent is the characters added to the previous indent.
                # This is the last 'change' characters of the current absolute indent.
                # Ensure indent is long enough before slicing.
                if change > len(indent):
                     # This case indicates an error in indentation logic or input format.
                     # The change calculated is larger than the current line's total indent length.
                     raise ValueError(f"Indentation calculation error: change ({change}) > current indent length ({len(indent)})")
                cur_indent = indent[-change:]
            elif change < 0:
                # Outdented: the relative indent is the marker character repeated '-change' times.
                cur_indent = self.marker * -change
            else:
                # Same indent: relative indent is an empty string.
                cur_indent = ""

            # Construct the output lines: relative_indent_line + newline + content_line
            # The content_line is the original line starting from after the absolute indent.
            # The relative indent is placed on a separate line immediately before the content.
            out_line = cur_indent + "\n" + line[len_indent:]

            output.append(out_line) # Append the pair of lines (relative indent + content)
            prev_indent = indent   # Update the previous absolute indent for the next line

        res = "".join(output) # Join all line pairs into a single string
        return res # Return the relatively indented text


    def make_absolute(self, text):
        """
        Transforms text from relative back to absolute indents.
        Assumes the input text is in pairs of lines: relative_indent_line \n content_line.
        Raises ValueError if the input format is incorrect or the indenter's marker
        is unexpectedly found in the final output.
        """
        lines = text.splitlines(keepends=True) # Split text into lines, keeping line endings

        output = []
        prev_indent = "" # Track the absolute indent string *after* processing the previous pair of lines
        # Iterate through the lines list in steps of 2, processing each pair of (relative_indent_line, content_line)
        for i in range(0, len(lines), 2):
            # Ensure we have a pair of lines. If not, the input text format is incorrect.
            if i + 1 >= len(lines):
                raise ValueError(f"Mismatched lines in relative indent text at index {i}")

            # Extract the relative indentation line and the content line from the pair
            dent_line = lines[i].rstrip("\r\n") # The relative indentation string (without its ending newline)
            non_indent_line = lines[i + 1]     # The line containing actual content (with its original ending newline)

            # Determine the current absolute indentation based on the relative indent string
            if dent_line.startswith(self.marker):
                # If the relative indent starts with the marker, it's an outdent.
                # Calculate the number of outdent markers.
                len_outdent = len(dent_line)
                # Remove the corresponding number of characters from the end of the previous absolute indent.
                # Ensure `prev_indent` is long enough before slicing to prevent errors on invalid input format.
                if len_outdent > len(prev_indent):
                    raise ValueError(f"Invalid outdent marker sequence at line pair {i}: '{dent_line}'. Previous indent length was {len(prev_indent)}.")
                cur_indent = prev_indent[:-len_outdent] # Slice off characters from the end of previous indent
            else:
                # If it doesn't start with the marker, it's an indent relative to the previous line's end.
                # Append this relative indent string (which should be just whitespace or empty)
                # to the previous absolute indent.
                cur_indent = prev_indent + dent_line

            # Construct the final absolute indented content line.
            # Do not indent lines that become effectively blank after stripping whitespace.
            if not non_indent_line.strip(): # Check if the content part is just whitespace or empty
                out_line = non_indent_line  # If blank, keep the line as is (likely just newline(s))
            else:
                out_line = cur_indent + non_indent_line # Prepend the calculated absolute indent

            output.append(out_line) # Append the fully indented line
            prev_indent = cur_indent # Update the previous absolute indent for the next line pair

        res = "".join(output) # Join all absolute indented lines into a single string

        # Final check: The indenter's marker character should *not* be present in the final absolute text.
        # If it is, it indicates a failure in the make_absolute conversion process.
        if self.marker in res:
            # dump(res) # Original code included a debug dump
            raise ValueError("Error transforming text back to absolute indents: marker found in output")

        return res # Return the text with absolute indents


def reverse_lines(text):
    """
    Reverses the order of lines in a text string.
    Handles None input.
    """
    if text is None:
        return None # Return None if input is None

    lines = text.splitlines(keepends=True) # Split into lines, keeping line endings
    lines.reverse() # Reverse the list of lines in place
    return "".join(lines) # Join the reversed lines back into a single string


# Define the list of preprocessor combinations to try for strategies.
# Each tuple is (strip_blank_lines_flag, relative_indent_flag, reverse_lines_flag).
all_preprocs = [
    # (strip_blank_lines, relative_indent, reverse_lines)
    (False, False, False), # No preprocessors
    (True, False, False),  # Strip leading/trailing blank lines
    (False, True, False),  # Apply relative indentation
    (True, True, False),   # Strip blank lines AND apply relative indentation
    # The following combinations involving reverse_lines were commented out in the original code.
    # (False, False, True),
    # (True, False, True),
    # (False, True, True),
    # (True, True, True),
]

if __name__ == "__main__":
    # Test case for apply_diffs function
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye, World!")
"""

    # Example diff content in ```diff block format
    # This diff removes the old print statements and adds new ones.
    # The test case in the prompt had a typo ('s+print'), corrected to '+print'.
    diff_content = """```diff
--- original
+++ modified
@@ -1,5 +1,8 @@
 def hello():
 -    print("Hello, World!")
 +    print("Hello, Universe!")
 +    print("How are you today?")

 def goodbye():
 -    print("Goodbye, World!")
 +    print("Farewell, Universe!")
+    print("See you next time!")