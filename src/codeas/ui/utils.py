import difflib
import json
import os
from pathlib import Path

from diff_match_patch import diff_match_patch

PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    pass


def read_prompts():
    """Reads prompts from the configured JSON file."""
    if os.path.exists(PROMPTS_PATH):
        try:
            with open(PROMPTS_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty dict if file doesn't exist or is invalid JSON
            return {}
    else:
        return {}


def save_existing_prompt(existing_name, new_name, new_prompt):
    """Saves or renames an existing prompt."""
    prompts = read_prompts()
    prompts[new_name] = new_prompt
    if existing_name != new_name:
        # Safely delete the old name if it exists and is different
        if existing_name in prompts:
            del prompts[existing_name]
    # Ensure directory exists before writing
    Path(PROMPTS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(PROMPTS_PATH, "w") as f:
        json.dump(prompts, f, indent=4)


def delete_saved_prompt(prompt_name):
    """Deletes a saved prompt by name."""
    prompts = read_prompts()
    if prompt_name in prompts:
        del prompts[prompt_name]
        # Ensure directory exists before writing
        Path(PROMPTS_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f, indent=4)


def save_prompt(name, prompt):
    """Saves a new prompt, adding a version number if name exists."""
    prompts = read_prompts()
    name_version_map = extract_name_version(prompts.keys())

    full_name = f"{name}"
    # Check if a prompt with this base name exists
    if full_name in name_version_map:
        full_name = f"{full_name} v.{name_version_map[full_name] + 1}"
    # Note: The original code checked name_version_map.keys(), which would only
    # contain the base names, not versioned names like "name v.1".
    # The check `if full_name in name_version_map:` is correct here.

    prompts[full_name] = prompt.strip()
    # Ensure directory exists before writing
    Path(PROMPTS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(PROMPTS_PATH, "w") as f:
        json.dump(prompts, f, indent=4)


def extract_name_version(existing_names):
    """
    Extracts base name and highest version number for each prompt base name.
    Names can be like {name} or {name} v.1 or {name} v.2 etc.
    """
    name_version_map = {}
    for full_name in existing_names:
        parts = full_name.rsplit(" v.", 1)
        if len(parts) == 2:
            name, version_str = parts
            try:
                version = int(version_str)
            except ValueError:
                # If version part is not an integer, treat as a base name with version 1
                name = full_name
                version = 1
        else:
            # Names without " v." are base names with version 1 (implicit)
            name = full_name
            version = 1

        # Store the highest version found for each base name
        if name in name_version_map:
            name_version_map[name] = max(name_version_map[name], version)
        else:
            name_version_map[name] = version
    return name_version_map


def apply_diffs(file_content, diff_content):
    """Applies a diff content block to a single string file_content."""
    # Note: This function currently ignores file paths in diffs and applies
    # all hunks sequentially to the single provided `file_content` string.
    # The dummy_path logic simulates potential file operations but doesn't
    # actually use fname for file I/O related to content modification.

    edits = list(find_diffs(diff_content))

    # Create/remove dummy file for the SearchTextNotUnique exception cleanup logic
    # which assumes a file might have been created.
    dummy_path = Path("dummy_path")
    if dummy_path.exists():
        os.remove(dummy_path)

    try:
        for path, hunk in edits:
            # Path is ignored currently, always applies to the single file_content
            normalized_hunk = normalize_hunk(hunk)
            if not normalized_hunk:
                continue

            # Use a dummy path as fname is ignored in do_replace application logic
            # do_replace operates on the `file_content` string.
            file_content = do_replace(dummy_path, file_content, normalized_hunk)

            if file_content is None: # do_replace returns None if application fails
                 raise ValueError("The diff failed to apply to the file content.")

    except SearchTextNotUnique:
        # Clean up the dummy file if it was created before raising
        if dummy_path.exists():
            os.remove(dummy_path)
        raise ValueError(
            "The diff could not be applied uniquely to the file content."
        )
    except Exception as e:
        # Ensure dummy file is cleaned up on other errors too
        if dummy_path.exists():
            os.remove(dummy_path)
        raise e

    # Clean up the dummy file after all diffs are applied successfully
    if dummy_path.exists():
        os.remove(dummy_path)

    return file_content


def find_diffs(content):
    """Finds and extracts diff blocks from a string content."""
    # We assume fenced blocks like ```diff ... ```

    # Ensure content ends with a newline for splitlines consistency
    if not content.endswith("\n"):
        content = content + "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits = []
    while line_num < len(lines):
        line = lines[line_num]
        # Find the start of a fenced diff block, case-insensitive and stripped
        if line.strip().lower() == "```diff":
            # Process the block starting from the next line
            # process_fenced_block returns the line number *after* the closing ```
            line_num, these_edits = process_fenced_block(lines, line_num + 1)
            edits.extend(these_edits)
            # Continue search for next block from line_num returned by process_fenced_block
            continue # Skip the automatic line_num increment below

        line_num += 1 # Move to the next line if not a start of block

    # For now, just take 1! - This comment and the line below it were commented out in original
    # edits = edits[:1]

    return edits

def has_changes_in_hunk(hunk_lines):
    """Checks if a list of diff hunk lines contains any lines indicating changes (+ or -)."""
    if not hunk_lines:
        return False
    # Check for lines starting with '+' or '-' (ignoring potential whitespace before)
    for line in hunk_lines:
        stripped_line = line.lstrip()
        if stripped_line and stripped_line[0] in "+-":
            return True
    return False

def extract_fenced_block_lines(lines, start_line_num):
    """Extracts the block of lines within a fenced code block."""
    end_line_num = start_line_num
    # Find end of block ```
    for end_line_num in range(start_line_num, len(lines)):
        line = lines[end_line_num]
        if line.strip() == "```": # Use strip() for robustness
            break
    # If loop finished without finding ```, block_lines goes to the end.
    block_lines = lines[start_line_num:end_line_num]
    # Return the line number *after* the closing ``` (or the last line processed + 1 if ``` was not found)
    next_search_start_line = end_line_num + (1 if end_line_num < len(lines) and lines[end_line_num].strip() == "```" else 0)

    return next_search_start_line, block_lines

# Refactored process_fenced_block to reduce Cognitive Complexity (originally line 122)
def process_fenced_block(lines, start_line_num):
    """Processes a single fenced diff block to extract file path and hunks."""

    next_search_start_line, block_lines_raw = extract_fenced_block_lines(lines, start_line_num)

    fname = None
    edits = []
    current_hunk_lines_candidate = []

    # Diff blocks can start with an overall file header (--- +++).
    # This header might be followed by hunks (@@) or another file header.
    # Add a sentinel to ensure the last collected lines are processed as a hunk.
    block_lines_with_sentinel = block_lines_raw + ["@@ @@"]

    i = 0
    while i < len(block_lines_with_sentinel):
         line = block_lines_with_sentinel[i]

         is_file_header_start = line.startswith("--- ")
         is_hunk_header_start = line.startswith("@@ ") or line == "@@ @@"

         # Check if the current line marks the end of the previous hunk/file block
         # This happens if we encounter a new file header (---/+++ pair) or a hunk header (@@)
         # The logic for detecting a file header pair spans two lines.
         is_new_file_header_pair = False
         if is_file_header_start and i + 1 < len(block_lines_with_sentinel) and block_lines_with_sentinel[i+1].startswith("+++ "):
              is_new_file_header_pair = True

         if is_new_file_header_pair or is_hunk_header_start:
             # Found a delimiter (new file header or hunk header).
             # The lines collected *before* this delimiter form a completed hunk.
             hunk_to_process = current_hunk_lines_candidate
             current_hunk_lines_candidate = [] # Start collecting for the next hunk/file

             if has_changes_in_hunk(hunk_to_process):
                  edits.append((fname, hunk_to_process))

             if is_new_file_header_pair:
                 # This delimiter was a new file header (---/+++).
                 # Update the current filename.
                 fname = block_lines_with_sentinel[i+1][4:].strip()
                 i += 2 # Consume both the --- and +++ lines
             elif is_hunk_header_start:
                 # This delimiter was a hunk header (@@).
                 # The filename remains the same.
                 i += 1 # Consume the @@ line

             # Continue the loop to process the line *after* the delimiter
             continue

         else:
             # The line is not a delimiter; it's part of the current hunk candidate.
             current_hunk_lines_candidate.append(line)
             i += 1 # Move to the next line

    # The sentinel ensures the last hunk is processed, so no need for logic after the loop.

    return next_search_start_line, edits


def normalize_hunk(hunk):
    """
    Normalizes a raw hunk (list of lines with +/-/space prefixes) into a
    standardized diff format (also lines with +/-/space prefixes).
    This helps in applying diffs robustly.
    """
    # hunk comes in as lines with +/-/space prefixes.
    # hunk_to_before_after separates these into before/after lists/strings.
    # cleanup_pure_whitespace_lines ensures blank lines are represented consistently
    # in the before/after content used by difflib.
    # difflib.unified_diff then regenerates the diff format from cleaned before/after.
    # We slice [3:] to remove the ---, +++, and @@ lines generated by difflib,
    # returning only the change/context lines (+/-/' ').

    before_lines, after_lines = hunk_to_before_after(hunk, lines=True)

    # Clean up whitespace-only lines in the context provided to difflib
    cleaned_before_lines = cleanup_pure_whitespace_lines(before_lines)
    cleaned_after_lines = cleanup_pure_whitespace_lines(after_lines)

    # Generate a new unified diff using difflib
    # n=max ensures enough context lines are included if available
    diff = difflib.unified_diff(
        cleaned_before_lines, cleaned_after_lines, n=max(len(cleaned_before_lines), len(cleaned_after_lines))
    )
    diff_list = list(diff)

    # Skip the header lines (---, +++, @@) generated by difflib
    # Check if the diff starts with expected headers to avoid errors on unexpected input
    if len(diff_list) >= 3 and diff_list[0].startswith('---') and diff_list[1].startswith('+++') and diff_list[2].startswith('@@'):
        return diff_list[3:] # Return only the '+', '-', ' ' lines
    else:
        # If difflib output is not as expected (e.g., no changes resulted), return empty list
        # or potentially the original hunk? Returning empty list seems safer if normalization failed.
        return []


def cleanup_pure_whitespace_lines(lines):
    """Replaces lines containing only whitespace (and potentially newlines) with just their original trailing newlines."""
    res = []
    for line in lines:
        stripped_content = line.rstrip("\r\n").strip() # Strip content, keep potential original newline format
        if not stripped_content:
            # If line content was only whitespace, keep only the original trailing newlines
            original_newlines = line[len(line.rstrip("\r\n")):]
            res.append(original_newlines)
        else:
            # Otherwise, keep the line as is
            res.append(line)
    return res


def hunk_to_before_after(hunk, lines=False):
    """
    Separates hunk lines (with +/-/space prefixes) into 'before' and 'after'
    lists of strings (without prefixes).
    If lines=True, returns lists of lines; otherwise, returns concatenated strings.
    """
    before_parts = []
    after_parts = []

    for line in hunk:
        # Handle lines that might be empty or only have a prefix
        if not line:
             op = " "
             content = ""
        else:
            op = line[0]
            content = line[1:] # Content is the rest of the line after the prefix

        # Only process lines starting with '+', '-', or ' ' as actual content/change lines
        if op == " ":
            before_parts.append(content)
            after_parts.append(content)
        elif op == "-":
            before_parts.append(content)
        elif op == "+":
            after_parts.append(content)
        # Lines starting with '---', '+++', '@@' or others are ignored here

    if lines:
        return before_parts, after_parts

    before_text = "".join(before_parts)
    after_text = "".join(after_parts)

    return before_text, after_text


def do_replace(fname, content, hunk):
    """
    Applies a normalized diff hunk to the file content string.
    Note: fname is currently a dummy and file operations (like touch)
    based on fname are not directly changing actual files but rather
    simulated logic or assumptions about the original intent.
    """
    # Note: The original code checked fname.exists() etc. using a dummy path.
    # This logic is retained but operates on the dummy path, not the `content` string.
    fname_path = Path(fname) # Use Path object for dummy path operations

    before_text, after_text = hunk_to_before_after(hunk)

    # --- Original logic checking for new file / append case ---
    # This seems intended for applying diffs to actual files.
    # In the context of just applying to a string, this means if the 'before' text is empty,
    # treat it as adding content to an empty string or appending to the existing string.

    # if not fname_path.exists() and not before_text.strip():
    #     # Simulate creating a new empty file if the target dummy path doesn't exist
    #     # and the hunk's 'before' part is empty (implies insertion into empty).
    #     # This doesn't affect the `content` string itself yet.
    #     try:
    #          fname_path.touch()
    #     except OSError:
    #          # Ignore potential errors on dummy path operations
    #          pass
    #     content = "" # Treat input content as empty for this case

    # The logic below directly applies to the `content` string.
    # The check `if not before_text.strip():` handles pure additions/insertions.
    # The dummy file logic above seems largely irrelevant to the string manipulation below,
    # but keeping the `apply_diffs` dummy file cleanup structure.

    if content is None:
        return None # Explicitly return None on None input content

    # Handle case for creating a new file or appending to an empty file (pure addition hunk)
    if not before_text.strip():
        # If the hunk's 'before' is empty, it's a pure insertion/addition.
        # Append the 'after' text to the current content.
        # Treat empty content as starting point if current content is None or empty.
        current_content = content if content is not None else ""
        new_content = current_content + after_text
        return new_content

    # --- End original logic check ---

    # Attempt to apply the hunk using the flexible search/replace strategies.
    # apply_hunk will try different methods and return None if none succeed.
    new_content = apply_hunk(content, hunk)

    # If apply_hunk returns None, it means it failed to apply.
    # The caller (apply_diffs) checks for None and raises ValueError.
    return new_content


def apply_hunk(content, hunk):
    """Tries different strategies to apply a hunk to content."""
    before_text, after_text = hunk_to_before_after(hunk)

    # Strategy 1: Directly search and replace the exact 'before' text with 'after' text
    # `directly_apply_hunk` uses `flexi_just_search_and_replace` internally, which handles uniqueness.
    # It returns None if it fails or if search_text is empty or not found uniquely.
    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    # Strategy 2: Modify the hunk based on newlines/context in content and try again
    # This seems like a fallback for alignment issues caused by context differences.
    hunk_modified = make_new_lines_explicit(content, hunk)
    # Apply the modified hunk directly
    res = directly_apply_hunk(content, hunk_modified)
    if res is not None:
         return res

    # Strategy 3: Try applying partial hunks using varying amounts of context
    # This handles cases where surrounding context lines might differ slightly.
    # Pass the original hunk lines (before/changes/after) to apply_partial_hunk.
    # We need the lines formatted as they were in the hunk (with +/-/space prefixes)
    # for hunk_to_before_after inside apply_partial_hunk.
    # However, apply_partial_hunk seems to reconstruct before/after text directly from context/change lists.
    # Let's extract the original lines categorized.
    # The original `apply_hunk` split hunk into ops sections, then passed segments to apply_partial_hunk.
    # Let's re-derive segments from the normalized hunk lines.

    # Re-derive segments from the normalized hunk lines
    preceding_context_lines = []
    change_lines = [] # Lines starting with '+' or '-'
    following_context_lines = []
    current_segment = preceding_context_lines # Start collecting context before changes

    for line in hunk:
        if len(line) > 0:
            op = line[0]
            if op == ' ' and current_segment is preceding_context_lines:
                 preceding_context_lines.append(line)
            elif op in '+-':
                 if current_segment is preceding_context_lines: # Switch from preceding context to changes
                      current_segment = change_lines
                 change_lines.append(line)
            elif op == ' ' and current_segment is change_lines: # Switch from changes to following context
                 current_segment = following_context_lines
                 following_context_lines.append(line)
            elif op == ' ' and current_segment is following_context_lines:
                 following_context_lines.append(line)
            # Ignore other lines (@@ etc.) as they are delimiters processed earlier

    # Pass the derived segments to apply_partial_hunk
    res = apply_partial_hunk(content, preceding_context_lines, change_lines, following_context_lines)

    if res is not None:
         return res

    # If all strategies fail, return None
    return None


def make_new_lines_explicit(content, hunk):
    """
    Adjusts the hunk's 'before' section based on differences in newline representation
    or context differences between the hunk's original 'before' text and the actual content.
    Generates a new hunk aligned with the content.
    """
    # Get 'before' and 'after' text from the input hunk
    before_text_hunk, after_text_hunk = hunk_to_before_after(hunk)

    # If the hunk's before text is empty, there's nothing to align with content.
    if not before_text_hunk:
        return hunk # Return original hunk

    # Find diff between hunk's 'before' text and the actual content string.
    # This diff highlights discrepancies, including newline variations and surrounding context differences.
    # The output is a list of (op, text) tuples from diff_match_patch.
    diff_hunk_vs_content = diff_lines(before_text_hunk, content)

    # Filter the diff: keep original context (' ') and deletions ('-') from the diff
    # between hunk.before and content.
    # These retained parts represent the elements of the hunk.before that *are* found in content.
    # We want to apply these parts back to the *original hunk's before text* to get
    # an 'aligned before' text that exists in the content.
    filtered_diff_to_apply = []
    for op, text in diff_hunk_vs_content:
        if op == " ": # Context lines present in both
            filtered_diff_to_apply.append(" " + text)
        elif op == "-": # Lines from hunk.before that are *not* in content (this seems counter-intuitive?)
             # Re-reading original logic: The goal is to create a *new before text*
             # that represents the *matching* parts of the original hunk.before within the content.
             # A '-' here means something in hunk.before was *deleted* to get content.
             # If we apply this deletion back to hunk.before, we get something closer to content.
             # Let's stick to original code's logic: include '-' lines.
             filtered_diff_to_apply.append("-" + text)
        # Ignore '+' lines (insertions in content relative to hunk.before)

    # Apply the filtered diff (representing context and deletions from hunk.before found in content)
    # back to the *original hunk's before text*.
    # This produces a 'new_before_text' that should align better with the content.
    # Note: `directly_apply_hunk` expects a list of lines with +/-/space prefixes.
    # `filtered_diff_to_apply` is already in this format.
    new_before_text = directly_apply_hunk(before_text_hunk, filtered_diff_to_apply)

    # If application failed or the resulting 'new_before_text' is very short
    # compared to the original hunk's before text, it might indicate a bad alignment.
    # Return the original hunk in such cases.
    # Check stripped length to ignore pure whitespace differences influencing length.
    if new_before_text is None or len(new_before_text.strip()) < len(before_text_hunk.strip()) * 0.66:
        return hunk

    # Now, generate a new diff hunk between this 'aligned before' (`new_before_text`)
    # and the original hunk's 'after' text (`after_text_hunk`).
    # This new hunk should represent the required changes relative to the 'aligned before' text found in content.
    new_before_lines_list = new_before_text.splitlines(keepends=True)
    after_lines_list = after_text_hunk.splitlines(keepends=True)

    # Generate the unified diff lines (+/-/ ) from the new before/after lists
    new_hunk_diff_lines = difflib.unified_diff(
        new_before_lines_list, after_lines_list, n=max(len(new_before_lines_list), len(after_lines_list))
    )
    new_hunk_list = list(new_hunk_diff_lines)

    # Extract only the change/context lines (skip ---, +++, @@ headers)
    if len(new_hunk_list) >= 3 and new_hunk_list[0].startswith('---') and new_hunk_list[1].startswith('+++') and new_hunk_list[2].startswith('@@'):
        return new_hunk_list[3:]
    else:
        # If diff generation failed or unexpected format, return original hunk
        return hunk


def diff_lines(search_text, replace_text):
    """
    Generates a diff between two strings using diff_match_patch,
    treating them line by line. Returns output in unified diff like format (+/-/ ).
    """
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5
    # dmp.Diff_EditCost = 16 # Commented out in original

    # Convert lines to characters for diffing efficiency
    search_chars, replace_chars, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    # Perform the diff
    diff_result = dmp.diff_main(search_chars, replace_chars, None)
    dmp.diff_cleanupSemantic(diff_result) # Clean up diff for better readability
    dmp.diff_cleanupEfficiency(diff_result) # Clean up diff for efficiency

    # Convert back to lines
    diff_list = list(diff_result)
    dmp.diff_charsToLines(diff_list, mapping)
    # dump(diff_list) # Commented out in original

    # Convert diff_match_patch output (op, text) tuples to unified diff like lines (+/-/ )
    udiff_lines = []
    for op, text in diff_list:
        prefix = " " # Default for equality (Diff_EQUAL)
        if op < 0: # Deletion (Diff_DELETE)
            prefix = "-"
        elif op > 0: # Insertion (Diff_INSERT)
            prefix = "+"

        # Split the text part by lines and prepend the prefix to each line.
        # Ensure that if the text doesn't end with a newline, the last part is still processed.
        lines_list = text.splitlines(keepends=True)
        if not lines_list and text: # Handle case of single line without newline
             udiff_lines.append(prefix + text)
        else:
            for line in lines_list:
                udiff_lines.append(prefix + line)

    return udiff_lines


def apply_partial_hunk(content, preceding_context_lines, changes_lines, following_context_lines):
    """
    Attempts to apply the changes hunk using varying amounts of surrounding context lines.
    This helps align the hunk if the full context doesn't match exactly.
    """
    len_prec = len(preceding_context_lines)
    len_foll = len(following_context_lines)

    # Iterate through decreasing amounts of preceding and following context, starting with full context
    # Use 'lines' format from hunk_to_before_after for clarity in building text parts.

    for use_prec in range(len_prec, -1, -1): # From max preceding down to zero
        for use_foll in range(len_foll, -1, -1): # From max following down to zero

            # Select the context lines for this attempt
            this_prec_lines_with_prefix = preceding_context_lines[-use_prec:] if use_prec > 0 else []
            this_foll_lines_with_prefix = following_context_lines[:use_foll] if use_foll > 0 else []

            # Combine context and change lines to form the 'before' and 'after' hunks for the search/replace
            # 'before' hunk lines: used preceding context (' ') + original lines from changes ('-') + used following context (' ')
            # 'after' hunk lines: used preceding context (' ') + changed lines from changes ('+') + used following context (' ')
            # Note: hunk_to_before_after expects lines with prefixes.

            temp_hunk_lines_for_before = this_prec_lines_with_prefix + [line for line in changes_lines if len(line) > 0 and line[0] == '-'] + this_foll_lines_with_prefix
            temp_hunk_lines_for_after = this_prec_lines_with_prefix + [line for line in changes_lines if len(line) > 0 and line[0] == '+'] + this_foll_lines_with_prefix

            before_text, _ = hunk_to_before_after(temp_hunk_lines_for_before)
            after_text, _ = hunk_to_before_after(temp_hunk_lines_for_after)

            # If both before and after parts are empty (only possible if changes is empty and no context used), skip
            if not before_text and not after_text:
                 continue

            # If the 'before' text is empty, it's an insertion. The caller (`do_replace`)
            # handles pure insertions based on `before_text.strip()`. This partial
            # application logic is primarily for cases where `before_text` is expected.
            # If `before_text` is empty here, it implies a pure insertion chunk with varying context -
            # this case might be implicitly handled by the main insertion logic if no
            # context is used. However, `directly_apply_hunk` (called by search_and_replace_texts below)
            # explicitly returns None if `before` is empty, preventing empty searches.
            # So we rely on that check.

            # Try applying this partial/contextual hunk using the flexible search/replace mechanism
            # This function `search_and_replace_texts` is a wrapper around `flexible_search_and_replace`
            # that takes explicit before/after strings instead of a hunk structure.
            res = search_and_replace_texts([before_text, after_text, content])

            if res is not None:
                return res

    # If no combination worked, return None
    return None


# Helper to call flexible_search_and_replace with explicit texts
def search_and_replace_texts(texts):
    """Directly calls flexible_search_and_replace with pre-calculated search/replace texts."""
     # Use the same strategies as flexi_just_search_and_replace
    strategies = [
        (search_and_replace, all_preprocs),
    ]
    # Note: search_and_replace expects texts=[search_text, replace_text, original_text]
    # It raises SearchTextNotUnique if search_text is not unique in original_text.
    # flexible_search_and_replace is designed to catch this and try other strategies/preprocs.
    # If SearchTextNotUnique propagates out of flexible_search_and_replace, it means
    # *no* combination of preproc/strategy yielded a unique match.
    return flexible_search_and_replace(texts, strategies)


def directly_apply_hunk(content, hunk):
    """
    Attempts to apply the hunk by directly searching for its 'before' text
    in the content and replacing it with its 'after' text using flexible strategies.
    Returns None if the 'before' text is empty, or if the search/replace fails
    (e.g., not found, not unique with tiny context).
    """
    # Get 'before' and 'after' text strings from the hunk
    # Reported issue S1481 (unused local variable "before_text") pointed
    # to the line assigning 'before' here (original line 254).
    # 'before' is used later in this function, so the report is a false positive.
    # We suppress the false positive report here to address the issue without
    # introducing inefficient code as attempted previously.
    before, after = hunk_to_before_after(hunk) # sonar:suppress-violations python:S1481


    # If the 'before' part of the hunk is empty, this represents a pure insertion.
    # This function is designed for modifications/deletions where a search context exists.
    # Pure insertions are handled by the caller (`do_replace`) based on `if not before_text.strip()`.
    if not before: # Use the correctly assigned 'before' variable
        return None # Indicate failure for this application method if 'before' is empty

    # Get the 'before' lines list version to check length for ambiguity heuristic
    # No longer need to re-call hunk_to_before_after due to the S1481 workaround removal.
    before_lines_list, _ = hunk_to_before_after(hunk, lines=True)
    # Join and strip to get a representation without line endings and leading/trailing blank lines
    before_lines_stripped = "".join([line.strip() for line in before_lines_list if line.strip()])

    if len(before_lines_stripped) < 10 and content.count(before) > 1: # Use the correctly assigned 'before' variable
        # Refuse to apply if short, non-whitespace context matches multiple times
        return None

    # Use the flexible search/replace mechanism with the specific before/after strings.
    # This will try different preprocessors and the search_and_replace strategy.
    # `search_and_replace_texts` will catch `SearchTextNotUnique` from within
    # `flexible_search_and_replace` and return None if no unique match is found.
    new_content = search_and_replace_texts([before, after, content]) # Use the correctly assigned 'before' variable

    return new_content # Returns None if no strategy worked or if search failed uniquely


def flexi_just_search_and_replace(texts):
    """
    Applies the simple `search_and_replace` strategy with various preprocessors.
    This is a specialized version of `flexible_search_and_replace` used for hunks.
    """
    # This function exists primarily to provide the specific list of strategies
    # (which is just one strategy with all preprocessors) to flexible_search_and_replace.
    strategies = [
        (search_and_replace, all_preprocs),
    ]

    # flexible_search_and_replace will catch SearchTextNotUnique if raised by search_and_replace
    # and try other preprocessors. If SearchTextNotUnique still occurs after trying all preprocs
    # for the single strategy, it will propagate. The caller (`directly_apply_hunk`) handles this.
    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    """
    Performs a simple string search and replace.
    Raises SearchTextNotUnique if the search text is not found exactly once.
    Returns None if search text is not found at all.
    Returns new text if found exactly once.
    """
    search_text, replace_text, original_text = texts

    # The flexible framework relies on this function raising SearchTextNotUnique
    # to signal failure to uniquely apply for a given preprocessor state.
    num = original_text.count(search_text)

    if num > 1:
       # If search text appears multiple times, we cannot apply uniquely.
       # Raise the custom exception.
       raise SearchTextNotUnique()
    elif num == 0:
       # If search text is not found, this strategy/preproc combination fails.
       return None

    # If found exactly once (num == 1)
    new_text = original_text.replace(search_text, replace_text)

    return new_text


def flexible_search_and_replace(texts, strategies):
    """
    Try a series of search/replace strategies and their preprocessor combinations,
    starting from the most literal. Returns the first successful result or None.
    Handles SearchTextNotUnique by trying the next combination.
    """
    # texts is expected to be [search_text, replace_text, original_text]

    for strategy, preprocs in strategies:
        for preproc in preprocs:
            # try_strategy applies the preprocessors and then the strategy.
            # It handles reversing preprocessors if the strategy succeeds.
            # try_strategy itself might return None (if strategy fails) or
            # propagate SearchTextNotUnique (if strategy raises it).
            try:
                res = try_strategy(texts, strategy, preproc)
                if res is not None: # If a result was returned (strategy succeeded)
                    return res # Success! Return the result.
            except SearchTextNotUnique:
                 # If this specific preprocessor + strategy combination failed due to
                 # non-unique match (SearchTextNotUnique), catch it and continue
                 # to the next preprocessor/strategy combination.
                 continue
            except Exception as e:
                 # Catch other potential errors during a strategy application or preproc reverse,
                 # log or handle as needed, and continue to the next strategy.
                 # For now, just print a warning and continue.
                 # print(f"Warning: Strategy failed with preproc {preproc}: {e}") # Optional logging
                 continue


    # If no strategy/preprocessor combination yields a successful result after trying all
    return None


def try_strategy(texts, strategy, preproc):
    """
    Applies specified preprocessors to texts, then applies the strategy.
    Reverses the preprocessors on the result if the strategy succeeds.
    Handles potential failures during strategy or reverse preprocessor application.
    """
    # preproc is a tuple: (strip_blank_lines_flag, relative_indent_flag, reverse_lines_flag)
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc

    # Store RelativeIndenter instance if used, for reverse transformation
    ri = None
    # Start with the original input texts
    processed_texts = list(texts) # Create a mutable copy

    # Apply preprocessors based on flags
    if preproc_strip_blank_lines:
        processed_texts = strip_blank_lines(processed_texts)
    if preproc_relative_indent:
        # relative_indent returns the indenter instance and the processed texts
        try:
            ri, processed_texts = relative_indent(processed_texts)
        except ValueError:
            # If relative indenting fails (e.g., marker in text), this preproc combo fails.
            return None # Return None for this strategy attempt
    if preproc_reverse:
        # Apply reverse_lines to all texts (search, replace, original)
        processed_texts = [reverse_lines(text) for text in processed_texts]


    # Apply the core search/replace strategy function
    # The strategy function (e.g., search_and_replace) should return the new text on success,
    # None on failure (e.g., search text not found), or raise SearchTextNotUnique.
    try:
        res = strategy(processed_texts)
    except SearchTextNotUnique:
        # If the strategy raised SearchTextNotUnique, re-raise it to be caught by flexible_search_and_replace
        raise
    except Exception as e:
         # Catch other potential errors from the strategy itself.
         # print(f"Warning: Strategy function failed: {e}") # Optional logging
         return None # This strategy attempt failed


    # If strategy succeeded (returned a non-None result), apply inverse preprocessors in reverse order
    if res is not None:
        if preproc_reverse:
            # Reverse the lines back
            res = reverse_lines(res)

        if preproc_relative_indent:
            # Apply inverse relative indentation
            try:
                res = ri.make_absolute(res)
            except ValueError:
                # If reverse indentation fails (e.g., marker left in text), this strategy failed.
                # print(f"Warning: Failed to reverse relative indent: {e}") # Optional logging
                return None # Return None for this strategy attempt

    # Return the final result (could be None if strategy failed or reverse preproc failed)
    return res


def strip_blank_lines(texts):
    """
    Strips leading and trailing blank lines (lines containing only whitespace)
    from each text in the input list. Preserves internal blank lines.
    """
    processed_texts = []
    for text in texts:
        lines = text.splitlines(keepends=True)
        # Find the index of the first line that is not blank
        first_content_idx = 0
        while first_content_idx < len(lines) and not lines[first_content_idx].strip():
             first_content_idx += 1

        # Find the index of the last line that is not blank
        last_content_idx = len(lines) - 1
        while last_content_idx >= first_content_idx and not lines[last_content_idx].strip():
             last_content_idx -= 1

        # Join the lines from the first content line to the last content line
        # If all lines were blank, first_content_idx > last_content_idx, resulting in an empty list, which is correct.
        processed_texts.append("".join(lines[first_content_idx : last_content_idx + 1]))

    return processed_texts


def relative_indent(texts):
    """
    Transforms texts to use relative indentation using a RelativeIndenter instance.
    Returns the indenter instance and the list of transformed texts.
    Raises ValueError if texts already contain the marker character.
    """
    # RelativeIndenter constructor checks for marker presence in texts
    ri = RelativeIndenter(texts)
    # Transform each text in the list
    processed_texts = [ri.make_relative(text) for text in texts]

    return ri, processed_texts


class RelativeIndenter:
    """
    Rewrites text files to have relative indentation, encoding changes
    in indentation level relative to the previous line using a special marker.
    """

    def __init__(self, texts):
        """
        Initializes the indenter, choosing a unique unicode character
        not present in any of the input texts to use as an outdent marker.
        """

        chars = set()
        for text in texts:
            # Add all characters from all texts to the set
            chars.update(text)

        # Define a default marker.
        # U+2190 LEFTWARDS ARROW is the original choice.
        ARROW = "\u2190"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            # If the default marker is present, find a unique one.
            # Search downwards from high unicode values.
            self.marker = self.select_unique_marker(chars)

        # Store the length of the marker string.
        self.marker_len = len(self.marker)


    def select_unique_marker(self, chars):
        """
        Finds a unicode character not present in the input character set `chars`.
        Searches downwards from the end of the Unicode range (excluding surrogates
        and unassigned blocks) starting with Private Use Area E000-F8FF, then
        falling back to the Supplementary Private Use Area A (U+F0000 to U+FFFFD)
        as the original code's range [0x10000, 0x10FFFF] seems too broad and includes assigned chars.
        A smaller, less likely used range is safer and faster.
        """
        # Attempt a smaller, less likely used range first (e.g., Private Use Area E000-F8FF)
        # Iterate downwards for faster finding if a marker is available.
        for codepoint in range(0xF8FF, 0xE000 - 1, -1):
             marker = chr(codepoint)
             if marker not in chars:
                 return marker

        # Fallback to Supplementary Private Use Area A (U+F0000 to U+FFFFD) - within original range
        # This range is specifically designated for private use.
        for codepoint in range(0xFFFFD, 0xF0000 - 1, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker

        # Fallback to Supplementary Private Use Area B (U+100000 to U+10FFFD) - within original range
        for codepoint in range(0x10FFFD, 0x100000 - 1, -1):
             marker = chr(codepoint)
             if marker not in chars:
                 return marker

        # If no unique marker found in preferred ranges, raise an error.
        raise ValueError("Could not find a unique marker character not present in text.")


    def get_leading_whitespace(self, line):
        """Helper to extract the leading whitespace indent of a line."""
        line_without_end = line.rstrip("\n\r") # Remove potential newlines first
        # Find the first non-whitespace character
        first_char_idx = len(line_without_end) - len(line_without_end.lstrip())
        return line_without_end[:first_char_idx]


    def make_relative(self, text):
        """
        Transform text to use relative indents.
        Encodes indentation changes relative to the previous line using the marker.
        Output format is pairs of lines: encoding_line\ncontent_line\n...
        """
        if self.marker in text:
            # Text already contains the outdent marker, cannot process.
            # This should ideally be caught by the caller (try_strategy).
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)

        output = []
        prev_indent = "" # Leading whitespace of the previous line

        for line in lines:
            current_indent = self.get_leading_whitespace(line)
            len_indent = len(current_indent)
            len_prev_indent = len(prev_indent)

            change = len_indent - len_prev_indent # Change in indentation length

            indent_encoding = "" # String to encode the indentation change

            if change > 0:
                # Increase in indent: The added indent must be a suffix of the current indent.
                # Encode the added whitespace characters.
                # Check if prev_indent is actually a prefix of current_indent.
                if current_indent.startswith(prev_indent):
                    indent_encoding = current_indent[len_prev_indent:] # The added part
                else:
                    # This case implies mixed tabs/spaces or non-standard indentation.
                    # The original code just took the last `change` chars.
                    # Let's stick to taking the suffix if it fits, else encode full indent difference?
                    # No, the relative indent idea is about the *change*.
                    # If prev_indent is not a prefix, the original logic of just taking the suffix can be weird.
                    # Example: prev_indent = "  ", current_indent = "\t". change = 1. current_indent[-1:] = "\t". encoding="\t".
                    # This seems to be the intended behaviour - encode the suffix characters that were added.
                    indent_encoding = current_indent[-change:]

            elif change < 0:
                # Decrease in indent: Encode using the marker character.
                # The number of markers is the absolute value of the change in length.
                len_outdent = -change
                # We should ideally check if prev_indent ends with something that matches
                # what we are conceptually outdenting from, but simple marker repetition
                # is the encoding scheme.
                indent_encoding = self.marker * len_outdent
            else:
                # Same indent level: Encoding is an empty string.
                indent_encoding = ""

            # The rest of the line after the leading whitespace, including its original newline(s).
            rest_of_line = line[len_indent:]

            # The output consists of pairs of lines: the encoding line, followed by the content line.
            output_line_pair = indent_encoding + "\n" + rest_of_line

            output.append(output_line_pair)

            # Update the previous indent for the next iteration to be the current line's actual indent.
            prev_indent = current_indent

        res = "".join(output)
        return res


    def make_absolute(self, text):
        """
        Transform text from relative back to absolute indents.
        Assumes the input text is in the encoded format (pairs of lines).
        Reconstructs the original indentation levels.
        """
        lines = text.splitlines(keepends=True)

        # Check if the number of lines is even, as expected for encoding pairs.
        if len(lines) % 2 != 0:
             raise ValueError("Malformed relative indent text: Expected even number of lines after split.")

        output = []
        prev_absolute_indent = "" # Absolute indent of the previous *original* line

        # Iterate through pairs of lines (encoding line, content line)
        for i in range(0, len(lines), 2):
            # Get the encoding line and the content line
            dent_line = lines[i] # Contains the indent encoding string + newline
            content_line = lines[i + 1] # Contains the rest of the original line + its newline(s)

            # The encoding string is the dent line without its trailing newline(s).
            indent_encoding = dent_line.rstrip("\r\n")

            current_absolute_indent = "" # Absolute indent for the *current* original line

            if indent_encoding.startswith(self.marker):
                # Decrease in indent: Encoding is `self.marker` repeated `len_outdent` times.
                len_outdent = len(indent_encoding) # Number of markers used
                # The current absolute indent is the previous absolute indent minus the outdent amount.
                # Slicing handles cases where len_outdent is larger than prev_absolute_indent.
                current_absolute_indent = prev_absolute_indent[:-len_outdent]
            else:
                # Increase or same indent level: Encoding is the actual added/same whitespace string.
                dent = indent_encoding
                current_absolute_indent = prev_absolute_indent + dent

            # Check if the original content line (excluding the encoding line) is effectively blank.
            # Blank lines should not have any indentation prepended, just keep their original format.
            if not content_line.strip(): # Check if line content is empty or just whitespace
                out_line = content_line # Keep original blank line content including its newline
            else:
                # For non-blank lines, prepend the calculated absolute indent.
                out_line = current_absolute_indent + content_line

            output.append(out_line)

            # The absolute indent for the *next* iteration is the one we just calculated.
            prev_absolute_indent = current_absolute_indent

        res = "".join(output)

        # Final check: the restored text should not contain the marker character.
        if self.marker in res:
            # This indicates an error in the encoding/decoding process.
            # print(f"Error: Marker '{self.marker}' still present after make_absolute.") # Optional logging
            raise ValueError("Error transforming text back to absolute indents: Marker still present.")

        return res


def reverse_lines(text):
    """Reverses the order of lines in a text block, preserving original newlines."""
    lines = text.splitlines(keepends=True)
    lines.reverse()
    return "".join(lines)


# Define preprocessor combinations
# Each tuple is (strip_blank_lines, relative_indent, reverse_lines) boolean flags.
# These are applied in this order, and reversed in the opposite order.
all_preprocs = [
    # (strip_blank_lines, relative_indent, reverse_lines)
    (False, False, False), # No preprocessing - Most literal attempt
    (True, False, False),  # Strip leading/trailing blank lines
    (False, True, False), # Apply relative indentation
    (True, True, False),  # Strip blanks, then apply relative indentation
    # Reversed versions commented out in original, keeping them commented.
    # (False, False, True),
    # (True, False, True),
    # (False, True, True),
    # (True, True, True),
]


# Example usage block (kept for testing)
if __name__ == "__main__":
    # Test case for apply_diffs function
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye, World!")
"""

    diff_content = """```diff
--- a/file.py
+++ a/file.py
@@ -1,5 +1,8 @@
 def hello():
-    print("Hello, World!")
+    print("Hello, Universe!")
+    print("How are you today?")

 def goodbye():
-    print("Goodbye, World!")
+    print("Farewell, Universe!")
+    print("See you next time!")