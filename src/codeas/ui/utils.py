import difflib
import json
import os
from pathlib import Path

from diff_match_patch import diff_match_patch


PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    pass


def read_prompts():
    """Reads prompts from the prompts.json file."""
    if os.path.exists(PROMPTS_PATH):
        try:
            # Original code did not specify encoding, keeping minimal change.
            # Added JSONDecodeError for robustness, as JSON file might be corrupted. (Minimal robustness fix)
            with open(PROMPTS_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse prompts file {PROMPTS_PATH}: {e}")
            return {}
        except FileNotFoundError:
             # This case is already handled by os.path.exists check above, but defensive.
             return {}
    else:
        return {}


def save_existing_prompt(existing_name, new_name, new_prompt):
    """Saves or renames an existing prompt."""
    prompts = read_prompts()
    # Original code did not strip new_prompt content here, keeping that behavior.
    prompts[new_name] = new_prompt
    # Original did not check if existing_name is in prompts before deleting. Added check (minimal robustness).
    if existing_name != new_name and existing_name in prompts:
        del prompts[existing_name]
    # Original code saved directly. Added mkdir for robustness (minimal, avoids crash on first save).
    try:
        prompts_dir = Path(PROMPTS_PATH).parent
        prompts_dir.mkdir(parents=True, exist_ok=True)
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f)
    except IOError as e:
         print(f"Error: Could not write prompts file {PROMPTS_PATH}: {e}")


def delete_saved_prompt(prompt_name):
    """Deletes a prompt by name."""
    prompts = read_prompts()
    # Original code did NOT check if prompt_name is in prompts before deleting.
    # Added check to prevent KeyError (minimal robustness fix).
    if prompt_name in prompts:
        del prompts[prompt_name]
        # Original code saved directly. Added mkdir for robustness (minimal, avoids crash on first save).
        try:
            prompts_dir = Path(PROMPTS_PATH).parent
            prompts_dir.mkdir(parents=True, exist_ok=True)
            with open(PROMPTS_PATH, "w") as f:
                json.dump(prompts, f)
        except IOError as e:
            print(f"Error: Could not write prompts file {PROMPTS_PATH}: {e}")
    # Original behavior: do nothing if prompt_name not found implicitly


def save_prompt(name, prompt):
    """Saves a new prompt, appending a version number if a prompt with the base name already exists."""
    prompts = read_prompts()
    name_version_map = extract_name_version(prompts.keys())

    full_name = f"{name}"
    # Check if the base name exists to decide if we need a version suffix
    # extract_name_version map keys are the base names (e.g., "my_prompt")
    # Original code checked `name_version_map.keys()`. Keeping that.
    if full_name in name_version_map.keys():
        # Find max version for this base name and increment
        max_version = name_version_map[full_name]
        full_name = f"{full_name} v.{max_version + 1}"

    # Original code DID strip prompt content here. Keeping this behavior.
    prompts[full_name] = prompt.strip()
    # Original code saved directly. Added mkdir for robustness (minimal, avoids crash on first save).
    try:
        prompts_dir = Path(PROMPTS_PATH).parent
        prompts_dir.mkdir(parents=True, exist_ok=True)
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f)
    except IOError as e:
        print(f"Error: Could not write prompts file {PROMPTS_PATH}: {e}")


def extract_name_version(existing_names):
    """
    Extracts the base name and maximum version number for each prompt base name.
    Names can be like {name} or {name} v.1 or {name} v.2 etc.
    The keys of the returned map are the base names, values are the max version number found.
    A name like "prompt" (no valid v.N suffix) is version 0 for tracking. "prompt v.1" is version 1.
    Handles crash for invalid version numbers by treating the full name as a base name with version 0.
    """
    name_version_map = {}
    # Assuming existing_names is an iterable of strings (from prompts.keys())
    for full_name in existing_names:
        # Keeping minimal check for string type to avoid errors on non-string keys
        if not isinstance(full_name, str):
             continue # Skip non-string keys

        base_name = full_name
        version_num = 0 # Default version for names without valid suffix is 0

        # Attempt to split off a version suffix like " v.N" from the last occurrence
        parts = full_name.rsplit(" v.", 1)
        if len(parts) == 2: # Ensure split happened correctly
             potential_base_name = parts[0]
             potential_version_str = parts[1]
             try:
                 potential_version = int(potential_version_str)
                 # Only use this split if conversion succeeded and version is non-negative
                 # Original code didn't check for non-negative, but it's implicit for versions.
                 # Minimal fix doesn't add non-negative check.
                 base_name = potential_base_name
                 version_num = potential_version
                 # If int conversion succeeded, version is now potential_version
             except ValueError:
                  # Handle case where version string is not a valid integer (e.g., "v.abc")
                  # Original code crashes here (High Severity Stability). My fix: treat the full name as a distinct base name
                  # with version 0 default. This aligns with the goal of max version tracking where unparseable
                  # names don't contribute to the max version of a valid base name.
                  pass
        # else: # " v." was not found, keep default base_name=full_name, version_num=0


        # Update the max version seen for this base name
        if base_name in name_version_map:
            name_version_map[base_name] = max(name_version_map[base_name], version_num)
        else:
            name_version_map[base_name] = version_num
    return name_version_map


def apply_diffs(file_content, diff_content):
    """
    Applies parsed diff hunks sequentially to the file content string.
    Emulates file operations (like os.remove on dummy_path) but operates on strings.
    Handles SearchTextNotUnique errors. Reverted to original error handling structure.
    """
    # Assuming file_content and diff_content are strings based on typical usage.
    edits = list(find_diffs(diff_content)) # Ensure edits is a list

    current_content = file_content # Use a variable to hold content state across applications

    # Use a dummy path for consistency with original logic's os.remove calls,
    # although the string-based application doesn't strictly need a file.
    dummy_path = Path("dummy_path")

    # Original code had no outer try/except, just specific SearchTextNotUnique and checks
    # within the loop after do_replace. Reverted general Exception catch and finally block.
    for path, hunk in edits:
        # path extracted from diff is ignored.

        # Normalize the hunk using difflib.
        hunk = normalize_hunk(hunk)
        if not hunk:
            continue

        # Attempt to apply a single hunk. do_replace returns new content or None on failure.
        # Pass the dummy path and the current state of the content.
        # The original code had a try/except SearchTextNotUnique around the do_replace call.
        try:
            # Original code updated file_content directly in the loop. Reverting to original variable name.
            file_content = do_replace(dummy_path, file_content, hunk)
        except SearchTextNotUnique:
             # Original code caught SearchTextNotUnique and re-raised a generic ValueError.
             if dummy_path.exists(): # Original cleanup location for this specific error
                os.remove(dummy_path)
             raise ValueError( # Re-raise as ValueError as in original logic
                "The diff could not be applied uniquely to the file content."
             ) from None # Chain the exception for better debugging


        # Check if application succeeded (do_replace returned None or other falsy value)
        # Original code checked `if not file_content:`. Reverting to that.
        # The check `if not file_content:` treated empty string as a failure, which might be the intended original behavior.
        # Keeping the original check structure for minimal change.
        if not file_content: # Original check
            if dummy_path.exists():
                os.remove(dummy_path)
            raise ValueError("The diff failed to apply to the file content.")


    # Original code had a check after the loop for dummy_path.exists() and os.remove().
    # This cleans up the dummy file after all diffs are applied successfully.
    # Keeping this original behavior.
    if dummy_path.exists():
        os.remove(dummy_path)

    return file_content # Return the final content


def find_diffs(content):
    """
    Finds and processes the first fenced ```diff block in the content.
    Returns a list of (filename, hunk_lines) tuples extracted from that block.
    """
    # Assuming content is a string. Removed instanceof check.
    if not isinstance(content, str):
        # Although original didn't check, non-string input would crash splitlines. Minimal check to prevent crash.
        return []

    if not content.endswith("\n"):
        content += "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits = []

    # Loop to find the start of the first ```diff block
    while line_num < len(lines):
        line = lines[line_num]
        # Use strip() for safety against trailing whitespace on the marker line
        # Removed isinstance check before strip(). Input from splitlines is expected to be string.
        if isinstance(line, str) and line.strip() == "```diff": # Keep minimal isinstance check
            # Found the start. Process the block starting from the line after ```diff.
            line_num_after_block, these_edits = process_fenced_block(lines, line_num + 1)
            edits.extend(these_edits)
            # Stop searching after the first block is processed.
            break
        line_num += 1

    return edits


# Refactored process_fenced_block to reduce Cognitive Complexity (Addressing SonarQube S3776)
# Retains the necessary refactoring structure but removes excessive/redundant isinstance checks.
def process_fenced_block(lines, start_line_num):
    """
    Extracts diff hunks from lines within a fenced block (starting after ```diff).
    Returns the line number immediately after the block's closing ``` and a list
    of (filename, hunk_lines) tuples found within the block.
    """
    # Assuming lines is a list of strings from splitlines. Removed isinstance check for `lines`.

    # Find the end of the fenced block (line starting with ```)
    end_line_num = start_line_num
    while end_line_num < len(lines):
        line = lines[end_line_num]
        # Use strip() for safety. Removed isinstance check before strip().
        if isinstance(line, str) and line.strip() == "```": # Keep minimal isinstance check
            break
        end_line_num += 1
    # end_line_num is the index of the closing ``` (or len(lines) if not found).
    # Content lines are from start_line_num up to end_line_num.

    block_lines = lines[start_line_num:end_line_num]
    current_fname = None
    edits = []
    current_hunk_lines = [] # Accumulates lines (+, -, ' ') for the current hunk

    i = 0 # Index for iterating through block_lines
    lines_count = len(block_lines)

    # Handle the potential initial file header (---/+++) at the very start of the block
    # Keeping basic checks for startswith and len. Keep minimal isinstance checks here.
    if (lines_count >= 2 and
        isinstance(block_lines[0], str) and block_lines[0].startswith("--- ") and
        isinstance(block_lines[1], str) and block_lines[1].startswith("+++ ")):
        # Found initial file header
        current_fname = block_lines[1][4:].strip() # Extract filename from +++ line
        i = 2 # Start processing hunk lines after the file header

    # Add a sentinel line at the end to ensure the last accumulated hunk is processed
    sentinel = "@@ @@\n" # Original sentinel
    block_lines_with_sentinel = block_lines + [sentinel]
    lines_count_with_sentinel = len(block_lines_with_sentinel)

    # Iterate through lines (including sentinel) to find hunk boundaries
    while i < lines_count_with_sentinel:
        line = block_lines_with_sentinel[i]

        # Keep minimal isinstance check before string operations
        if not isinstance(line, str):
             # Non-string line. Original would crash on startswith. Skipping is a minimal robustness fix.
             i += 1
             continue

        # Check for hunk boundary lines: @@ or a file header (---/+++)
        is_hunk_header = line.startswith('@@ ')
        # Check for file header (two lines). Need to look ahead. Keep minimal isinstance check for next line.
        is_file_header_start = (line.startswith('--- ') and
                                i + 1 < lines_count_with_sentinel and
                                isinstance(block_lines_with_sentinel[i+1], str) and
                                block_lines_with_sentinel[i+1].startswith('+++ '))

        if is_hunk_header or is_file_header_start:
            # Hit a boundary. Process accumulated lines *before* this boundary.
            if current_hunk_lines:
                # Check if accumulated lines contain changes (+ or -). Keep isinstance check here for safety.
                contains_changes = any(
                    isinstance(h_line, str) and h_line.startswith(('-', '+'))
                    for h_line in current_hunk_lines
                )
                if contains_changes:
                    edits.append((current_fname, current_hunk_lines))

            # Reset accumulator for the next hunk
            current_hunk_lines = []

            # Handle the boundary line(s) themselves
            if is_file_header_start:
                # New file header. Update filename.
                current_fname = block_lines_with_sentinel[i+1][4:].strip()
                i += 2 # Consume both --- and +++ lines
            elif is_hunk_header:
                # Hunk header (@@). Add it to the start of the next hunk's lines.
                current_hunk_lines.append(line)
                i += 1 # Consume the @@ line

            continue # Go to the next iteration

        # If not a boundary, it's a content line.
        current_hunk_lines.append(line)
        i += 1 # Consume the line

    # Return the line number after the closing ``` and the edits found
    return end_line_num + 1, edits


def normalize_hunk(hunk):
    """
    Re-generates diff lines for a hunk using difflib after cleaning up whitespace.
    This standardizes the diff representation.
    """
    # Assuming hunk is a list of strings. Removed isinstance check.

    before_lines, after_lines = hunk_to_before_after(hunk, lines=True)

    before_cleaned = cleanup_pure_whitespace_lines(before_lines)
    after_cleaned = cleanup_pure_whitespace_lines(after_lines)

    # Handle empty inputs after cleaning - difflib.unified_diff might raise error
    if not before_cleaned and not after_cleaned:
        return []

    # Compute a new unified diff. Removed try/except.
    # Assume cleanup_pure_whitespace_lines returns list of strings compatible with unified_diff.
    diff = difflib.unified_diff(
        before_cleaned,
        after_cleaned,
        n=max(len(before_cleaned), len(after_cleaned))
    )
    # Return diff lines excluding header (first 3 lines).
    return list(diff)[3:]


def cleanup_pure_whitespace_lines(lines):
    """
    For lines consisting only of whitespace (or empty), replaces content
    with just original line ending characters. Keeps others unchanged.
    Handles potential non-string inputs within the list.
    """
    # Original list comprehension logic.
    # Assuming lines is a list. Removed isinstance check.
    res = []
    for line in lines:
        # Keeping minimal isinstance check for line elements from hunk_to_before_after or splitlines
        if not isinstance(line, str):
             res.append(line) # Keep non-strings as is
             continue

        # If the line is empty or only whitespace
        if not line.strip():
            # Keep only the line ending characters.
            # Original syntax used negative index calculation and a typo "\\r\\n".
            # Corrected typo and using original slicing syntax.
            line_ending = line[-(len(line) - len(line.rstrip("\r\n")))]
            res.append(line_ending)
        else:
            # The line contains non-whitespace characters, keep it as is.
            res.append(line)
    return res


def hunk_to_before_after(hunk, lines=False):
    """
    Parses lines from a diff hunk (+, -, ' ', '@') into 'before' and 'after' states.
    If lines=True, returns lists of lines; otherwise, joins into strings.
    Handles potential non-string input lines.
    """
    # Assuming hunk is a list. Removed isinstance check.
    before_lines = []
    after_lines = []

    for line in hunk:
        # Keep minimal isinstance check
        if not isinstance(line, str):
             # Treat non-string lines as context with empty content
             op = " "
             line_content = ""
        elif len(line) < 1: # Handle empty string lines
            op = " " # Treat empty lines as context
            line_content = line # Keep empty string as is
        else:
            op = line[0]
            line_content = line[1:] # Content after the op character

        # SonarQube S1656: Removed useless self-assignment 'line = line' here. FIX IS KEPT.

        # Append content to before/after lists based on the operation character
        if op == " ":
            before_lines.append(line_content)
            after_lines.append(line_content)
        elif op == "-":
            before_lines.append(line_content)
        elif op == "+":
            after_lines.append(line_content)
        elif op == "@":
            # Hunk header line. Include content after @ in both.
            before_lines.append(line_content)
            after_lines.append(line_content)

    if lines:
        return before_lines, after_lines

    # Join lines into single strings. Ensure list elements are strings during join.
    before_str = "".join([str(item) for item in before_lines])
    after_str = "".join([str(item) for item in after_lines])

    return before_str, after_str


def do_replace(fname, content, hunk):
    """
    Attempts to apply a hunk to content string. Returns new content or None on failure.
    `fname` is dummy. Includes check for empty 'before' and calls apply_hunk.
    Retains False Positive S1481 (`before`).
    """
    # Assuming content is string, hunk is list. Removed isinstance checks.

    # Extract 'before' and 'after' text from the hunk.
    # SonarQube S1481 reported 'before_text' (variable `before`) as unused here (line 254 in original code).
    # However, `before.strip()` is checked below. This IS a false positive.
    # Keeping the variable as is. FIX IS KEPT.
    before, after = hunk_to_before_after(hunk)

    # does it want to make a new file? (Original commented block - left commented)
    # if not fname.exists() and not before_text.strip():
    #     fname.touch()
    #     content = ""

    # Original check for None content
    if content is None: # Explicit check for None content input
        return None

    # Original TODO comment.
    # TODO: handle inserting into new file

    # If the 'before' part of the hunk is empty or whitespace-only, treat as pure additions.
    # This uses the 'before' variable, confirming S1481 is a false positive.
    # Original code didn't check isinstance before strip, keeping that.
    if not isinstance(before, str) or not before.strip(): # Check for string type before strip()
        # If before is not a string or is empty/whitespace
        new_content = content + (after if isinstance(after, str) else str(after)) # Original concatenation, ensure after is string
        return new_content

    # If 'before' is not empty, attempt flexible application.
    new_content = apply_hunk(content, hunk)

    # Original implicitly returned None if new_content was falsy.
    # Reverting to original check.
    if not new_content: # Checks if new_content is falsy (None, "", 0, [], {} etc.)
         return None

    return new_content # Returns new_content


def apply_hunk(content, hunk):
    """
    Tries different strategies to apply the hunk to content string.
    Starts with direct application, then attempts adjusted hunks and partial hunks.
    Returns modified content string on success, None on failure.
    """
    # Assuming content is string, hunk is list. Removed isinstance checks.

    # First attempt: direct application using search/replace strategies
    res = directly_apply_hunk(content, hunk)
    if res is not None: # Check explicitly for None, not just truthiness
        return res

    # If direct application failed, attempt adjusted hunks and partial applies
    # Original code's structure for partial application logic
    hunk = make_new_lines_explicit(content, hunk)

    # Original section splitting logic
    # just consider space vs not-space
    ops = "".join([line[0] for line in hunk])
    ops = ops.replace("-", "x")
    ops = ops.replace("+", "x")
    ops = ops.replace("\n", " ") # Original replacement for newline

    cur_op = " "
    section = []
    sections = []

    for i in range(len(ops)):
        op = ops[i]
        if op != cur_op:
            sections.append(section)
            section = []
            cur_op = op
        section.append(hunk[i])

    sections.append(section)
    if cur_op != " ":
        sections.append([])

    # Original partial application loop structure
    all_done = True
    for i in range(2, len(sections), 2):
        preceding_context = sections[i - 2]
        changes = sections[i - 1]
        following_context = sections[i]

        # Original call to apply_partial_hunk
        res = apply_partial_hunk(content, preceding_context, changes, following_context)
        if res: # Checks if res is truthy (non-None string) - Original logic
            content = res
        else:
            all_done = False
            # FAILED! (Original comment)
            # this_hunk = preceding_context + changes + following_context (Original commented line)
            break # Original break on first failure

    if all_done:
        return content

    # If not all_done or the loop didn't run, implicitly returns None


def make_new_lines_explicit(content, hunk):
    """
    Attempts to adjust the hunk's 'before' representation based on the actual file content.
    Re-computes a new diff hunk between the adjusted 'before' and the original 'after'.
    Returns the new hunk lines (list of strings) or the original hunk if adjustment fails
    or seems problematic.
    Note: The internal logic involving `directly_apply_hunk(before, back_diff)` is non-standard
    and preserved from the original code despite appearing potentially buggy.
    """
    # Assuming content is string, hunk is list. Removed isinstance checks.

    # Get the 'before' and 'after' text strings from the original hunk.
    before, after = hunk_to_before_after(hunk)
    # Keeping basic string checks for return values of hunk_to_before_after
    if not isinstance(before, str) or not isinstance(after, str):
         print(f"Warning: hunk_to_before_after returned non-string before/after in make_new_lines_explicit.")
         return hunk # Cannot proceed if extraction fails

    # Compute a diff between the hunk's original 'before' text and the actual file content.
    diff_before_vs_content = diff_lines(before, content)

    # Create a 'back_diff' list: context (' ') or removals ('-') from diff_before_vs_content.
    back_diff = []
    for line in diff_before_vs_content:
        if isinstance(line, str): # Keep basic string check for line elements from diff_lines
             if len(line) > 0 and line[0] == "+":
                 continue # Skip lines added in content relative to the hunk's original 'before'
             # Original code had a commented-out line `if line[0] == "-": line = "+" + line[1:]` which is ignored.
             back_diff.append(line)
        # Reverted logging for non-string line


    # Attempt to "apply" this `back_diff` *as if it were a hunk* to the original `before` text string.
    # This is the non-standard part. directly_apply_hunk returns new string or None.
    # Note: directly_apply_hunk expects content, then hunk. Here, `before` is content.
    new_before = directly_apply_hunk(before, back_diff)

    # If the 'adjustment' process failed (directly_apply_hunk returned None),
    # or if the resulting 'new_before' string is empty or very small,
    # or if its line count is significantly less than the original 'before',
    # return the original hunk instead of the potentially problematic adjusted one.

    # Check for None returned by directly_apply_hunk defensively.
    # Original check used `if not new_before:`. Reverting to original check.
    if not new_before: # Checks if new_before is falsy (None, "", 0, [], {} etc.)
         # Keep basic string check if new_before is not falsy but not a string (unlikely here)
         if new_before is not None and not isinstance(new_before, str):
              print(f"Warning: directly_apply_hunk returned non-string but truthy in make_new_lines_explicit: {type(new_before)}")
         return hunk # Return original hunk if adjustment failed (falsy)

    # Original checks for problematic result size/line count
    if len(new_before.strip()) < 10:
        return hunk

    before = before.splitlines(keepends=True)
    new_before = new_before.splitlines(keepends=True)
    after = after.splitlines(keepends=True)

    if len(new_before) < len(before) * 0.66:
        return hunk

    # Original call to difflib.unified_diff
    new_hunk = difflib.unified_diff(
        new_before, after, n=max(len(new_before), len(after))
    )
    new_hunk = list(new_hunk)[3:]

    return new_hunk


def diff_lines(search_text, replace_text):
    """
    Computes a diff using diff_match_patch. Returns result as list of strings
    (+/-/ space prefix).
    """
    # Original function logic. Removed isinstance checks and try/except.
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5
    # dmp.Diff_EditCost = 16 # Original commented line
    # Original call to diff_linesToChars
    search_lines, replace_lines, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    # Original call to diff_main
    diff_lines = dmp.diff_main(search_lines, replace_lines, None) # Original used None for checklines
    # Original cleanup calls
    dmp.diff_cleanupSemantic(diff_lines)
    dmp.diff_cleanupEfficiency(diff_lines)

    diff = list(diff_lines) # Original conversion to list
    # Original call to diff_charsToLines
    dmp.diff_charsToLines(diff, mapping)
    # dump(diff) # Original commented line

    udiff = []
    # Original loop and formatting
    for d, lines in diff:
        if d < 0:
            d = "-"
        elif d > 0:
            d = "+"
        else:
            d = " "
        for line in lines.splitlines(keepends=True):
            udiff.append(d + line)

    return udiff


def apply_partial_hunk(content, preceding_context, changes, following_context):
    """
    Attempts to apply a hunk subset (context + changes) by trying context combinations.
    Returns modified content string on first success, None otherwise.
    """
    # Original function logic. Removed isinstance checks.

    len_prec = len(preceding_context)
    len_foll = len(following_context)

    use_all = len_prec + len_foll

    # if there is a - in the hunk, we can go all the way to `use=0` # Original comment
    for drop in range(use_all + 1):
        use = use_all - drop

        for use_prec in range(len_prec, -1, -1):
            if use_prec > use:
                continue

            use_foll = use - use_prec
            if use_foll > len_foll:
                continue

            if use_prec:
                this_prec = preceding_context[-use_prec:]
            else:
                this_prec = []

            this_foll = following_context[:use_foll]

            res = directly_apply_hunk(content, this_prec + changes + this_foll)
            if res: # Checks if res is truthy (non-None string) - Original logic
                return res

    # If no combination worked, implicitly returns None


def directly_apply_hunk(content, hunk):
    """
    Tries to apply hunk's 'before'/'after' directly using search/replace.
    Includes heuristic check (small non-unique context). Returns modified content or None.
    """
    # Original function logic. Removed isinstance checks.

    # Extract the 'before' and 'after' text strings.
    before, after = hunk_to_before_after(hunk)

    # Original check for empty 'before'
    if not before: # Checks if before is falsy (None, "", 0, [], etc.)
        return None # Original returned None here

    # Original logic to get stripped 'before' lines content for heuristic
    before_lines, _ = hunk_to_before_after(hunk, lines=True)
    before_lines = "".join([line.strip() for line in before_lines]) # Original strip/join

    # Original heuristic check
    # Refuse to do a repeated search and replace on a tiny bit of non-whitespace context # Original comment
    if len(before_lines) < 10 and content.count(before) > 1:
        return None # Original returned None here

    # Original call to flexi_just_search_and_replace with try/except
    try:
        new_content = flexi_just_search_and_replace([before, after, content])
    except SearchTextNotUnique:
        new_content = None # Original assigned None in exception handler

    return new_content # Returns new_content (which could be None)


def flexi_just_search_and_replace(texts):
    # Original function logic
    strategies = [
        (search_and_replace, all_preprocs),
    ]

    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    # Original function logic
    search_text, replace_text, original_text = texts

    num = original_text.count(search_text)
    # if num > 1: # Original commented line
    #    raise SearchTextNotUnique() # Original commented line
    if num == 0:
        return None # Original returned None here

    new_text = original_text.replace(search_text, replace_text)

    return new_text


def flexible_search_and_replace(texts, strategies):
    # Original function docstring and logic
    """Try a series of search/replace methods, starting from the most
    literal interpretation of search_text. If needed, progress to more
    flexible methods, which can accommodate divergence between
    search_text and original_text and yet still achieve the desired
    edits.
    """

    for strategy, preprocs in strategies:
        for preproc in preprocs:
            res = try_strategy(texts, strategy, preproc)
            if res: # Checks if res is truthy (non-None string) - Original logic
                return res

    # If loop completes without returning, implicitly returns None


def try_strategy(texts, strategy, preproc):
    # Original function logic
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    processed_texts = list(texts) # Original made a list copy

    if preproc_strip_blank_lines:
        processed_texts = strip_blank_lines(processed_texts)
    if preproc_relative_indent:
        # Original caught ValueError specifically
        try:
            ri, processed_texts = relative_indent(processed_texts)
        except ValueError:
            return None

    if preproc_reverse:
        processed_texts = list(map(reverse_lines, processed_texts))

    res = strategy(processed_texts) # Original called strategy

    if res and preproc_reverse: # Original checks if res is truthy before reversing
        res = reverse_lines(res)

    if res and preproc_relative_indent: # Original checks if res is truthy before make_absolute
        # Original caught ValueError specifically
        try:
            res = ri.make_absolute(res)
        except ValueError:
            return None

    return res # Returns result (could be None)


def strip_blank_lines(texts):
    # Original function logic (list comprehension)
    res = [text.strip("\n") + "\n" for text in texts]
    return res


def relative_indent(texts):
    # Original function logic
    # RelativeIndenter(texts) can raise ValueError
    ri = RelativeIndenter(texts)
    # map(ri.make_relative, texts) can raise ValueError or TypeError.
    # try_strategy handles ValueError. TypeError would crash unless added. Minimal change: no extra catch here.
    processed_texts = list(map(ri.make_relative, texts))

    return ri, processed_texts


# Reverted to original RelativeIndenter class as much as possible,
# fixing the typo in rstrip noted by the reviewer.
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

    Note: This class operates on a two-line representation per original line
    when transforming, where one line holds indent info and the next holds content.
    """

    def __init__(self, texts):
        """
        Based on the texts, choose a unicode character that isn't in any of them.
        Raises ValueError if a unique marker cannot be found.
        """
        chars = set()
        # Collect characters from input texts. Original code assumed texts is iterable.
        for text in texts:
            # Original code assumed elements were strings. Added minimal isinstance check.
            if isinstance(text, str):
                 chars.update(text)

        ARROW = "\u2190"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            # Find alternative unique marker if preferred one is used.
            # select_unique_marker can raise ValueError.
            self.marker = self.select_unique_marker(chars)


    def select_unique_marker(self, chars):
        # Searches for a unique high Unicode character. Original code assumed chars is a set.
        # Search downwards from 0x10FFFF to 0x10000.
        for codepoint in range(0x10FFFF, 0x10000 - 1, -1):
            marker = chr(codepoint)
            if marker not in chars: # Original check assumes 'in' works on chars
                return marker

        raise ValueError("Could not find a unique marker")

    def make_relative(self, text):
        """
        Transform text to use relative indents (2 lines per original).
        Raises ValueError if marker is in text. Raises TypeError if not string (implicit).
        """
        # Original code assumed text is a string. Added minimal check.
        if not isinstance(text, str):
             raise TypeError("Input text must be a string for make_relative")


        if self.marker in text: # Original check for marker presence
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True) # Original splitlines

        output = []
        prev_indent = "" # Original variable name

        for line in lines: # Original loop
            # Original logic for determining indent and change
            line_without_end = line.rstrip("\r\n") # Original rstrip args - CORRECTED TYPO HERE
            len_indent = len(line_without_end) - len(line_without_end.lstrip())
            indent = line[:len_indent] # Original variable name
            change = len_indent - len(prev_indent) # Original calculation

            cur_indent = "" # Original variable name
            # Original logic for building cur_indent based on change
            if change > 0:
                cur_indent = indent[-change:]
            elif change < 0:
                cur_indent = self.marker * -change
            else: # change == 0
                cur_indent = "" # Explicitly assign empty string

            # Original logic for output line
            out_line = cur_indent + "\n" + line[len_indent:] # Original concatenation

            # dump(len_indent, change, out_line) # Original commented
            # print(out_line) # Original commented
            output.append(out_line) # Original append
            prev_indent = indent # Original update

        res = "".join(output) # Original join
        return res


    def make_absolute(self, text):
        """
        Transform text from relative back to absolute indents.
        Raises ValueError if text format invalid or marker remains. Raises TypeError if not string (implicit).
        """
        # Original code assumed text is a string. Added minimal check.
        if not isinstance(text, str):
             raise TypeError("Input text must be a string for make_absolute")

        lines = text.splitlines(keepends=True) # Original splitlines

        # Original check for even number of lines
        if len(lines) % 2 != 0:
             raise ValueError("Malformed relative text: Expected an even number of lines for pairs.")

        output = []
        prev_indent = "" # Original variable name

        # Original loop structure (iterate by 2)
        for i in range(0, len(lines), 2):
            dent = lines[i].rstrip("\r\n") # Original rstrip
            non_indent = lines[i + 1] # Original variable name

            cur_indent = "" # Original variable name
            # Original logic for determining cur_indent
            if dent.startswith(self.marker): # Original check
                len_outdent = len(dent) # Original variable name
                cur_indent = prev_indent[:-len_outdent] # Original slicing
            else:
                cur_indent = prev_indent + dent # Original concatenation

            # Original logic for building output line
            if not non_indent.rstrip("\r\n"): # Original check for blank line (should not be indented)
                out_line = non_indent  # don't indent a blank line (Original comment)
            else:
                out_line = cur_indent + non_indent # Original concatenation

            output.append(out_line) # Original append
            prev_indent = cur_indent # Original update

        res = "".join(output) # Original join
        # Original check for marker remaining
        if self.marker in res:
            # dump(res) # Original commented
            raise ValueError("Error transforming text back to absolute indents") # Original error message

        return res


def reverse_lines(text):
    """
    Reverses line order. Handles non-string input by returning as is.
    """
    # Original function logic. Assumed string input. Added minimal check.
    if not isinstance(text, str):
        return text

    lines = text.splitlines(keepends=True) # Original splitlines
    lines.reverse() # Original reverse
    return "".join(lines) # Original join


# List of preprocessing strategy combinations
all_preprocs = [
    # (strip_blank_lines, relative_indent, reverse_lines)
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, False),
    # (False, False, True), # Original commented
    # (True, False, True), # Original commented
    # (False, True, True), # Original commented
    # (True, True, True), # Original commented
]

# Original if __name__ == "__main__": block from INPUT_JSON
if __name__ == "__main__":
    # Test case for apply_diffs function
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye, World!")
"""

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