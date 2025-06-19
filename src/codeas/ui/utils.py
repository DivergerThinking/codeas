import difflib
import json
import os
from pathlib import Path
import string # Needed for robust version number parsing

from diff_match_patch import diff_match_patch

# Define the path for the prompts file
PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    """Custom exception for cases where search text is not unique."""
    pass


def read_prompts() -> dict:
    """
    Reads saved prompts from a JSON file.
    Handles missing file or invalid JSON.
    Returns an empty dictionary if the file is missing, empty, or contains invalid JSON.
    """
    if os.path.exists(PROMPTS_PATH):
        try:
            with open(PROMPTS_PATH, "r") as f:
                # Check if file is empty before attempting to load JSON
                content = f.read().strip()
                if not content:
                    return {}
                f.seek(0) # Reset file pointer to the beginning after reading
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError):
            # Return empty dict on JSON decode error, file not found (redundant due to outer check), or IO error
            # Suppress logging/printing as per original code style
            return {}
    else:
        # If the file does not exist, return an empty dictionary
        return {}


def save_existing_prompt(existing_name: str, new_name: str, new_prompt: str):
    """
    Saves or renames an existing prompt.
    If renaming (existing_name != new_name), deletes the old entry if it exists.
    Saves the prompt with the new_name, overwriting if it already exists.
    Saves the updated prompts dictionary to the JSON file with indentation.

    Args:
        existing_name: The current name of the prompt to rename/update.
        new_name: The new name for the prompt.
        new_prompt: The new content for the prompt.
    """
    prompts = read_prompts()

    # If the user is renaming a prompt
    if existing_name != new_name:
        # Check if the prompt with the old name exists before attempting to delete it
        if existing_name in prompts:
            del prompts[existing_name]
        # Note: If new_name already exists, the assignment below will overwrite it.

    # Add or update the prompt with the new name, ensuring the prompt content is stripped
    prompts[new_name] = new_prompt.strip()

    # Save the updated prompts dictionary to the JSON file
    try:
        with open(PROMPTS_PATH, "w") as f:
            # Use indent=4 for human-readable JSON formatting
            json.dump(prompts, f, indent=4)
    except IOError:
        # Suppress console output for IO errors as per original code style
        pass


def delete_saved_prompt(prompt_name: str):
    """
    Deletes a saved prompt by name.
    Checks if the prompt exists before attempting deletion.
    Saves the updated prompts dictionary to the JSON file with indentation.

    Args:
        prompt_name: The name of the prompt to delete.
    """
    prompts = read_prompts()
    # Check if the prompt exists in the dictionary
    if prompt_name in prompts:
        # Delete the prompt entry
        del prompts[prompt_name]
        # Save the updated dictionary back to the file
        try:
            with open(PROMPTS_PATH, "w") as f:
                json.dump(prompts, f, indent=4) # Use indent=4 for readability
        except IOError:
            # Suppress console output for IO errors
            pass
    else:
        # Suppress console output if prompt is not found
        pass


def save_prompt(name: str, prompt: str):
    """
    Saves a new prompt. If a prompt with the same base name already exists
    (either directly as "name" or as a version "name v.X"), a new version
    ("name v.Y") is created, where Y is the highest existing version + 1.

    Args:
        name: The desired base name for the prompt.
        prompt: The content of the prompt.
    """
    prompts = read_prompts()

    base_name = name.strip() # Use the stripped name as the base name

    # If the base name is empty, do not save
    if not base_name:
        # Optionally print a warning or raise an error, but original code was silent.
        return # Skip saving if name is empty

    # Find existing keys that match the base name or its versions ("name", "name v.1", "name v.2", etc.)
    # Initialize the highest version found among the "v.X" keys to -1.
    # The base name itself ("name") can be thought of as version 0 for sequence determination.
    current_max_version = -1

    for key in prompts.keys():
         if key == base_name:
             current_max_version = max(current_max_version, 0) # Base name "name" corresponds to version 0
         elif key.startswith(f"{base_name} v."):
             try:
                 # Extract the version number from the key (e.g., "1" from "name v.1")
                 version_str = key[len(f"{base_name} v."):].strip()
                 # Check if the extracted part consists purely of digits before converting to int
                 if version_str and all(c in string.digits for c in version_str):
                     version = int(version_str)
                     # Update highest_version found among "v.X" keys
                     current_max_version = max(current_max_version, version)
                 # Ignore keys like "name v.abc" due to ValueError on int conversion
             except ValueError:
                 pass # Ignore malformed version keys

    # Determine the final full name for the new prompt entry.
    # If the base name exists (version 0) or any higher "v.X" key exists (current_max_version >= 0),
    # the new prompt gets the next sequential version number.
    if current_max_version >= 0:
        next_version = current_max_version + 1
        full_name = f"{base_name} v.{next_version}"
    else:
        # If no existing keys match the base name or any version, use the base name directly.
        full_name = base_name

    # Store the prompt with the determined full name, stripping whitespace.
    prompts[full_name] = prompt.strip()

    # Save the updated prompts dictionary back to the file.
    try:
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f, indent=4) # Use indent=4 for readability
    except IOError:
        # Suppress console output for IO errors
        pass


# The original extract_name_version function is no longer used and is removed.


def apply_diffs(file_content: str, diff_content: str) -> str | None:
    """
    Applies diffs found within a string (`diff_content`) to another string (`file_content`).
    Simulates file creation/append logic using a dummy file path.
    Processes multiple diff hunks sequentially against the evolving content string.

    Args:
        file_content: The initial content of the file as a string.
        diff_content: A string containing one or more diff blocks fenced by ```diff.

    Returns:
        The content string after applying all diffs, or None if any hunk application failed.

    Raises:
        ValueError: If a diff hunk fails to apply (either due to ambiguity or other errors).
    """
    # Use a dummy file path on the filesystem to simulate file operations like existence checks and touch.
    # The diffs themselves are applied to the `current_content` string in memory.
    dummy_path = Path("dummy_path_for_diff_sim")

    # Ensure cleanup of any leftover dummy file from previous failed runs
    if dummy_path.exists():
        try:
            os.remove(str(dummy_path))
        except OSError:
            # Suppress errors during cleanup attempt
            pass

    # Find and extract diff hunks from the diff_content string.
    # `find_diffs` handles finding ```diff blocks and calling `process_fenced_block`.
    edits = list(find_diffs(diff_content))

    # The content string that will be modified sequentially by applying each hunk.
    current_content = file_content

    try:
        # Iterate through each extracted hunk (edit).
        for path, hunk in edits:
            # The 'path' from the diff header is currently ignored for string application.
            # The `dummy_path` is passed to `do_replace` solely for simulating file existence/creation logic.

            # Normalize the raw hunk lines into a consistent format (lines with +/-/space prefixes).
            normalized_hunk = normalize_hunk(hunk)
            if not normalized_hunk:
                continue # Skip if the normalization resulted in an empty hunk (e.g., headers only)

            # Apply the normalized hunk to the current content string.
            # `do_replace` handles different strategies (direct, partial, append).
            # It's passed the dummy_path to check `fname.exists()` and potentially simulate `fname.touch()`.
            content_after_hunk = do_replace(dummy_path, current_content, normalized_hunk)

            # Check if the application of the hunk resulted in None (signaling a failure to apply).
            if content_after_hunk is None:
                 # If any single hunk fails to apply, the entire process fails.
                 raise ValueError("A diff hunk failed to apply to the file content.")

            # Update the current content with the result of applying the hunk.
            current_content = content_after_hunk

    except SearchTextNotUnique:
        # Catch the specific exception raised when context for direct application is ambiguous.
        # Re-raise it with a more user-friendly message and suppress the original exception chain.
        raise ValueError(
            "The diff could not be applied uniquely to the file content."
        ) from None
    except Exception as e:
        # Catch any other unexpected errors during the diff application process.
        # Re-raise with an informative message and include the original exception.
        raise ValueError(f"An error occurred during diff application: {e}") from e
    finally:
        # Ensure the dummy file created for simulation is removed after the process finishes,
        # regardless of whether it succeeded or failed.
        if dummy_path.exists():
            try:
                os.remove(str(dummy_path))
            except OSError:
                 # Suppress errors during final cleanup attempt
                 pass

    return current_content


def find_diffs(content: str) -> list[tuple[str | None, list[str]]]:
    """
    Finds and extracts diff blocks from a string fenced by ```diff markers.
    Processes each fenced block to identify and collect individual diff hunks.
    Returns a list of (filename, hunk_lines) tuples. Filename can be None.

    Args:
        content: A string that may contain one or more fenced diff blocks.

    Returns:
        A list of tuples, where each tuple contains the filename from the diff header
        (or None if no header) and a list of the raw hunk lines (including @@/---/+++ headers).
    """
    # Ensure content ends with a newline for consistent splitlines behavior
    if not content.endswith("\n"):
        content = content + "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits: list[tuple[str | None, list[str]]] = [] # List to store all extracted (filename, hunk) tuples

    # Iterate through lines to find the start of ```diff blocks
    while line_num < len(lines):
        line = lines[line_num]
        # Check for ```diff marker, stripping leading/trailing whitespace and case-insensitive match
        if line.strip().lower().startswith("```diff"):
            # Process the fenced block starting from the line *after* the ```diff marker.
            # `process_fenced_block` extracts hunks from this block and returns the line number
            # *after* the block ends, allowing the outer loop to continue searching from there.
            line_num, these_edits = process_fenced_block(lines, line_num + 1)
            # Add the extracted hunks from this block to the main list of edits.
            edits.extend(these_edits)
            # Continue the outer while loop from the new `line_num` returned by `process_fenced_block`.
            continue # Jump to the next iteration of the outer while loop

        # If the current line is not the start of a ```diff block, move to the next line.
        line_num += 1

    # The original code had 'edits = edits[:1]' commented out, which would only process the first hunk.
    # Keeping it commented to process all found hunks.
    # edits = edits[:1]

    return edits


# Refactored process_fenced_block to reduce cognitive complexity (Addresses Issue 1)
# This version identifies header indices first, then iterates through these to define hunk boundaries and extract slices.
def process_fenced_block(lines: list[str], start_line_num: int) -> tuple[int, list[tuple[str | None, list[str]]]]:
    """
    Processes lines within a ```diff ... ``` block (excluding the fences)
    to identify and extract diff hunks.
    Assumes the input `lines` includes the start fence line (processed before calling)
    and potentially the end fence line (within the range checked).
    Finds the block end and then parses the content within by identifying header indices.
    Returns the line number *after* the block and a list of extracted (filename, hunk_lines) tuples.

    Args:
        lines: A list of string lines potentially containing the fenced block.
        start_line_num: The index of the line *after* the starting ```diff marker.

    Returns:
        A tuple containing:
        - The index of the line immediately following the closing ``` marker (or the end of `lines`).
        - A list of extracted edits, where each edit is a tuple of (filename, hunk_lines).
          Filename is the string from the +++ line (or None), and hunk_lines is a list of strings
          representing the raw hunk content including @@ or ---/+++ headers if present within the hunk structure.
    """
    # Find the line number where the fenced block ends (the next line starting with ```).
    # If no end fence is found within the provided `lines`, the block is assumed to extend
    # to the end of the `lines` list.
    end_line_num = len(lines) # Default end is the end of the input lines
    for i in range(start_line_num, len(lines)):
        # Check for closing ``` marker, stripping leading/trailing whitespace and case-insensitive match
        if lines[i].strip().lower().startswith("```"):
            end_line_num = i # Found the end fence line
            break

    # Extract the lines that are *inside* the fenced block, between start_line_num and end_line_num.
    block_lines = lines[start_line_num:end_line_num]

    initial_fname: str | None = None # Filename from the optional initial ---/+++ header
    block_content_start_index = 0 # Index in block_lines where diff content starts

    # Check for the standard unified diff initial file header pair (--- followed immediately by +++)
    # at the very beginning of the extracted block lines.
    if len(block_lines) >= 2 and block_lines[0].startswith("--- ") and block_lines[1].startswith("+++ "):
        # If present, extract the filename from the +++ line (stripping leading/trailing whitespace).
        initial_fname = block_lines[1][4:].strip()
        # The actual diff hunk content starts after these two header lines.
        block_content_start_index = 2

    # `content_lines` now contains only the lines from the block that are potentially part of a diff hunk.
    # This excludes the initial ```diff, ```, and the optional initial ---/+++ lines.
    content_lines = block_lines[block_content_start_index:]

    # Find indices of all potential hunk start headers (@@ or ---/+++) within content_lines
    # Also determine the filename associated with each header if it's a file header.
    header_info: list[tuple[int, str | None]] = [] # List of tuples (index_in_content_lines, potential_fname_after_header)
    i = 0
    while i < len(content_lines):
        line = content_lines[i]
        is_hunk_header = line.strip().startswith("@@")
        is_file_header = (line.startswith("--- ") and
                          i + 1 < len(content_lines) and
                          content_lines[i+1].startswith("+++ "))

        if is_hunk_header:
             header_info.append((i, None)) # None means filename is inherited
             i += 1 # Move past @@
        elif is_file_header:
             # Filename is on the next line (+), add it to the header info
             fname = content_lines[i+1][4:].strip()
             header_info.append((i, fname))
             i += 2 # Move past --- and +++
        else:
             i += 1 # Move to next line

    edits: list[tuple[str | None, list[str]]] = []
    current_fname: str | None = initial_fname # Start with initial filename from block header

    # Define the start indices of raw hunk blocks. The first block starts at 0 (in content_lines).
    # Subsequent blocks start at each header index.
    block_start_indices = [0] + [info[0] for info in header_info]

    # Iterate through the defined block start indices to extract hunk lines and determine filenames.
    # Note: The filename is associated with the block *starting* at a header.
    for k in range(len(block_start_indices)):
        start_idx = block_start_indices[k]

        # The end index of the current block is the start index of the next block, or the end of content_lines.
        end_idx = len(content_lines)
        if k + 1 < len(block_start_indices):
            end_idx = block_start_indices[k+1]

        # Extract the raw lines for this hunk block.
        raw_hunk_lines = content_lines[start_idx:end_idx]

        # If this block starts with a header that specified a filename (and it's not the implicit start at 0),
        # update the current filename.
        # Check if the current start_idx is among the actual header indices found (not the implicit 0 start).
        # And if it is, check if the corresponding header_info entry had a specified filename.
        header_entry_for_this_block = next((info for info in header_info if info[0] == start_idx), None)
        if header_entry_for_this_block and header_entry_for_this_block[1] is not None:
             current_fname = header_entry_for_this_block[1]
        # else: keep the current_fname (either initial or from a previous file header)


        # Add the extracted hunk block with its associated filename.
        # We only add it if `hunk_to_before_after` can extract any actual diff content (' ' or +/- lines).
        # This excludes initial preamble before the first hunk header.
        before_check, after_check = hunk_to_before_after(raw_hunk_lines)
        if before_check or after_check: # Add only if hunk_to_before_after finds content
             edits.append((current_fname, raw_hunk_lines))
        # else: Skip empty blocks or pure preamble before first actual hunk header.

    # Return the line number *after* the entire fenced block (end_line_num + 1) and the extracted edits.
    # The original line_num calculation was correct.
    return end_line_num + 1, edits


def normalize_hunk(hunk: list[str]) -> list[str]:
    """
    Normalizes a raw hunk (list of lines possibly including headers like @@, ---, +++)
    into a standard representation containing only diff lines (prefixed with +, -, or space).
    This is done by parsing the 'before' and 'after' content lines from the raw hunk
    and then generating a unified diff between them.
    Also cleans up pure whitespace lines in the 'before'/'after' sections before diffing.

    Args:
        hunk: A list of string lines representing a raw diff hunk block.

    Returns:
        A list of strings representing the normalized diff hunk lines (prefixed with +, -, or space).
        Returns an empty list if the raw hunk contains no diff content lines.
    """
    # Extract the 'before' and 'after' content lines from the raw hunk.
    # `hunk_to_before_after` is designed to ignore lines that are not standard diff lines
    # (lines without '+', '-', or ' ' prefixes like @@, ---, +++).
    before_lines, after_lines = hunk_to_before_after(hunk, lines=True)

    # Clean up pure whitespace lines in both the before and after sections.
    # This step helps difflib match context correctly when only whitespace differs on otherwise blank lines.
    before_lines_cleaned = cleanup_pure_whitespace_lines(before_lines)
    after_lines_cleaned = cleanup_pure_whitespace_lines(after_lines)

    # Generate a unified diff between the cleaned before and after lines.
    # This process effectively standardizes the hunk representation.
    # Use generic filenames 'a' and 'b' in the diff header.
    # Set `n` to a large value (`max` of list lengths) to include maximum possible context lines.
    diff = difflib.unified_diff(before_lines_cleaned, after_lines_cleaned,
                                fromfile='a', tofile='b', # Standard diff header filenames
                                n=max(len(before_lines_cleaned), len(after_lines_cleaned)))

    # The output of `difflib.unified_diff` includes header lines (---, +++, @@) followed by the hunk content lines.
    # Convert the diff iterator to a list and skip these first 3 header lines
    # to get just the hunk content lines with +/-/space prefixes.
    normalized_diff_lines = list(diff)[3:]

    return normalized_diff_lines


def cleanup_pure_whitespace_lines(lines: list[str]) -> list[str]:
    """
    Replaces lines containing only whitespace (spaces, tabs, form feeds) or that are empty
    with just their trailing line endings (newline, carriage return).
    Lines containing any non-whitespace character (after stripping line endings) are returned unchanged.
    This helps treat blank lines consistently when matching context in diffs.

    Args:
        lines: A list of string lines.

    Returns:
        A new list of string lines with pure whitespace lines replaced by just their endings.
    """
    # Using a list comprehension for conciseness.
    # For each line:
    # 1. rstrip("\r\n") removes trailing line endings.
    # 2. strip() removes all remaining leading/trailing whitespace (spaces, tabs, etc.).
    # 3. If the result is empty (`not ...`), the original line (after removing endings) was pure whitespace or empty.
    #    In this case, calculate the length of the original line ending part (`len(line) - len(line.rstrip("\r\n"))`)
    #    and take the suffix of the original line corresponding to this length (`line[-(len of ending part)]`).
    #    Example: "  \t\n" -> rstrip("\r\n") -> "  \t" -> strip() -> "". Length of ending part is 1. line[-1:] is "\n".
    #    Example: "  \t\r\n" -> rstrip("\r\n") -> "  \t" -> strip() -> "". Length of ending part is 2. line[-2:] is "\r\n".
    #    Example: "abc \n" -> rstrip("\r\n") -> "abc " -> strip() -> "abc". Not empty. Keep original line.
    # 4. If the result is not empty, the line contained non-whitespace content. Keep the original line as is.
    res = [line[len(line.rstrip("\r\n")):] if not line.rstrip("\r\n").strip() else line for line in lines]
    return res


def hunk_to_before_after(hunk: list[str], lines: bool = False) -> tuple[str, str] | tuple[list[str], list[str]]:
    """
    Separates a list of diff hunk lines (strings with '+', '-', or ' ' prefixes)
    into two lists: one for the 'before' content and one for the 'after' content.
    Lines without these specific prefixes (like @@, ---, +++) are ignored.

    Args:
        hunk: A list of strings, where each string is a line from a diff hunk,
              expected to be prefixed with '+', '-', ' ', or potentially other characters.
              Only lines starting with '+', '-', or ' ' are processed for before/after content.
        lines: If True, returns lists of lines. If False, returns joined strings.

    Returns:
        A tuple containing the 'before' and 'after' content. This will be
        (str, str) if `lines` is False, or (list[str], list[str]) if `lines` is True.
    """
    before_lines: list[str] = []
    after_lines: list[str] = []
    # Removed unused initial assignment 'op = " "' and useless self-assignment 'line = line' (Addresses Issue 3, Issue 4)

    for line in hunk:
        # Ensure the line is not empty before checking the prefix.
        if len(line) < 1: # Corrected from < 2 in original
            continue # Skip empty strings or lines too short for prefix

        op = line[0] # Get the first character (the diff prefix)

        # Based on the prefix, add the rest of the line (after the prefix)
        # to the appropriate list(s).
        if op == " ":
            # Context lines (' ') are present in both the 'before' and 'after' versions.
            before_lines.append(line[1:]) # Add content after the space prefix.
            after_lines.append(line[1:]) # Add content after the space prefix.
        elif op == "-":
            # Removed lines ('-') are only present in the 'before' version.
            before_lines.append(line[1:]) # Add content after the minus prefix.
        elif op == "+":
            # Added lines ('+') are only present in the 'after' version.
            after_lines.append(line[1:]) # Add content after the plus prefix.
        # Lines with other prefixes (like '@', '\', etc.) are ignored.

    if lines:
        # If the `lines` flag is True, return the lists of lines directly.
        return before_lines, after_lines

    # If the `lines` flag is False, concatenate the lines in each list into a single string.
    before_text = "".join(before_lines)
    after_text = "".join(after_lines)

    return before_text, after_text


def do_replace(fname: Path, content: str, hunk: list[str]) -> str | None:
    """
    Applies a single normalized hunk (list of diff lines with prefixes)
    to the current file content string.
    Simulates file creation/append logic based on the hunk's 'before' text
    and the existence of the dummy file specified by `fname`.

    Args:
        fname: The Path object representing the dummy file for simulation.
                      Its `.exists()` and `.touch()` methods are used.
        content: The current string content of the file *before* applying this hunk.
        hunk: A normalized hunk (list of lines with +/-/space prefixes).

    Returns:
        The content string after applying the hunk, or None if application failed.
    """
    # Calculate the 'before' and 'after' text strings from the normalized hunk once.
    # These variables are used below (Addresses Issue 5 & 6 - they are used).
    before_text, after_text = hunk_to_before_after(hunk)

    # Simulate file creation scenario:
    # If the target 'file' (represented by `fname`, the dummy_path) does not exist yet (`not fname.exists()`)
    # AND the hunk's 'before' text is empty (`not before_text.strip()`),
    # this indicates the diff is intended to create a new file starting with additions.
    if not fname.exists() and not before_text.strip():
        try:
            # Simulate creating the file on disk. This makes `fname.exists()` return True for subsequent hunks.
            fname.touch()
            # For a new file, the starting content is empty.
            content = ""
        except OSError:
             # Ignore potential errors if dummy file creation fails during simulation.
             pass

    # Handle the append case: if the hunk's 'before' text is empty after the potential simulation.
    # This condition is true if the hunk is purely additions (starts with '+' lines).
    # This happens when creating a new file (content was just set to "") or when appending
    # content to an existing file where the hunk adds to the end.
    if not before_text.strip():
        # Simply append the 'after' text (the added lines) to the current content string.
        new_content = content + after_text
        return new_content # The append case is handled here, and the function finishes.

    # If the hunk's 'before' text is NOT empty, it means the hunk expects to modify
    # or delete existing content. In this case, delegate the application to the
    # `apply_hunk` function, which attempts various strategies (direct, partial)
    # to find and replace the 'before' text with the 'after' text within the `content` string.
    # Pass the pre-calculated `before_text` and `after_text` to `apply_hunk` to avoid recalculation.
    new_content = apply_hunk(content, hunk, before_text, after_text)

    # Return the result of applying the hunk (can be None if application failed).
    return new_content


def apply_hunk(content: str, hunk: list[str], original_before_text: str, original_after_text: str) -> str | None:
    """
    Attempts to apply a normalized hunk to the content string using multiple strategies.
    Strategies include:
    1. Direct application using flexible search and replace.
    2. Applying after making newlines explicit in the hunk based on actual content alignment.
    3. Trying partial applications with reduced context if other strategies fail.

    Args:
        content: The current content string.
        hunk: The normalized hunk lines (with +/-/space prefixes).
        original_before_text: The 'before' text derived from the original hunk.
        original_after_text: The 'after' text derived from the original hunk.

    Returns:
        The content string after applying the hunk, or None if no strategy succeeded.
    """
    # The original before/after text derived from the hunk is received as arguments.

    # Strategy 1: Try directly applying the hunk using flexible search and replace.
    # `directly_apply_hunk` internally calculates the 'before' and 'after' from the hunk
    # it receives (which is the full hunk here) and performs uniqueness checks before replacing.
    try:
        res = directly_apply_hunk(content, hunk)
        if res is not None: # Check explicitly for None (success)
            return res
    except SearchTextNotUnique:
        # If direct application failed due to non-unique search text, this strategy failed.
        # We catch it and proceed to attempt other strategies.
        pass # Continue to the next strategy

    # Strategy 2: If direct application failed (or raised SearchTextNotUnique),
    # try a realignment step by making newlines explicit based on content alignment,
    # which might produce a more applicable hunk.
    # Pass the actual content and the original hunk's before/after texts to `make_new_lines_explicit`.
    modified_hunk = make_new_lines_explicit(content, hunk, original_before_text, original_after_text)

    # If `make_new_lines_explicit` returned None or the original hunk (indicating realignment failed or wasn't helpful),
    # modified_hunk might be the same as hunk or None.
    # If modified_hunk is None, it means realignment failed. We cannot proceed with partial application.
    if modified_hunk is None or modified_hunk == hunk:
         # If realignment didn't help, the overall hunk application fails.
        return None # Signal failure

    # Strategy 3: Attempt partial application using the potentially `modified_hunk`.
    # This involves splitting the modified hunk into context and change sections
    # and trying to apply combinations with varying context amounts.

    # Segment the modified hunk into contiguous sections of context (' ') and changes ('+/-').
    simplified_sections: list[tuple[str, list[str]]] = []
    current_section: list[str] = []
    current_op_type: str | None = None # 'c' for changes (+/-), 'n' for non-changes (space)

    for line in modified_hunk:
        # Hunk lines are expected to have prefixes or be empty (should be skipped by `hunk_to_before_after`).
        # Check the first character for the operator type.
        op = line[0] if len(line) > 0 else ''

        # Classify lines into 'change' ('+/-') or 'non-change' (' ') sections.
        # Lines without these prefixes (like @@ headers in a non-normalized hunk, though modified_hunk should be normalized)
        # are treated as non-change or simply skipped if not ' '.
        if op in (' ', '-', '+'):
             op_type = 'c' if op in '-+' else 'n' # 'c' for change, 'n' for non-change (context)
        else:
             continue # Skip lines that don't start with ' ', '-', or '+'

        # Check if the operator type changes compared to the previous line, or if this is the first line being processed.
        if op_type != current_op_type and current_section:
            # If the type is changing and we have accumulated lines in `current_section`, finalize that section.
            simplified_sections.append((current_op_type, current_section))
            # Start a new section with the current line.
            current_section = [line]
            current_op_type = op_type
        else:
            # If the operator type is the same, or it's the very first line in the loop, add the line to the current section.
            current_section.append(line)
            # Initialize `current_op_type` if this was the first line added.
            if current_op_type is None:
                 current_op_type = op_type


    # After the loop, add the last accumulated section to the list, if it contains lines.
    if current_section:
        simplified_sections.append((current_op_type, current_section))

    # Now, iterate through the `simplified_sections` to attempt partial applications.
    # We look for sections containing changes ('c') and try to apply them with their surrounding context ('n').
    all_partial_applications_succeeded = True # Flag to track if all necessary partial applications succeed.
    k = 0 # Index for iterating through `simplified_sections`.

    while k < len(simplified_sections):
        section_type, section_lines = simplified_sections[k]

        # We are primarily interested in sections that contain changes ('c').
        if section_type == 'c':
            changes = section_lines # This is the 'changes' section.

            # Identify potential preceding context section (immediately before the changes).
            preceding_context: list[str] = []
            # Check if there is a section before the current one (k > 0) and if its type is 'n' (context).
            if k > 0 and simplified_sections[k-1][0] == 'n':
                 preceding_context = simplified_sections[k-1][1] # This is the 'preceding context' section lines.

            # Identify potential following context section (immediately after the changes).
            following_context: list[str] = []
            # Check if there is a section after the current one (k + 1 < len) and if its type is 'n' (context).
            if k + 1 < len(simplified_sections) and simplified_sections[k+1][0] == 'n':
                 following_context = simplified_sections[k+1][1] # This is the 'following context' section lines.

            # Attempt to apply this hunk slice composed of the preceding context, changes, and following context.
            # `apply_partial_hunk` will try applying this slice using varying amounts of the provided context.
            res = apply_partial_hunk(content, preceding_context, changes, following_context)

            if res is not None: # Check explicitly for None (success of this partial application)
                 content = res # Update the content string if the application was successful.
                 # Advance index `k` past the sections that were just part of this successful application.
                 # The sections involved are potentially simplified_sections[k-1] (if preceding_context used),
                 # simplified_sections[k] (changes, always used), and potentially simplified_sections[k+1]
                 # (if following_context used).
                 # We need to skip past the last section used.
                 last_section_index_used = k # Changes section is always at index k
                 if following_context: # If a following context section was used (at index k+1)
                      last_section_index_used = k + 1
                 # The next section to process in the outer loop is one index past the last section used.
                 k = last_section_index_used + 1
            else:
                 # If the partial application failed for this specific 'changes' section and its surrounding context,
                 # the overall application of the `modified_hunk` fails.
                 all_partial_applications_succeeded = False # Mark the overall process as failed.
                 break # Exit the while loop as we stop on the first partial application failure.

        # If the current section is not a 'changes' section ('c')...
        elif section_type == 'n':
             # If it's a 'context' section ('n'), we cannot apply it alone.
             # We only attempt application when we encounter a 'changes' section.
             # Just move to the next section in the simplified_sections list.
             k += 1
        else:
             # This case should theoretically not happen if our sectioning logic only produces 'n' and 'c' types.
             # Add a defensive step to advance the index.
             k += 1

    # After iterating through all sections, return the content string if all necessary
    # partial applications succeeded (`all_partial_applications_succeeded` is True),
    # or return None if any partial application failed.
    if all_partial_applications_succeeded:
        return content
    else:
        return None # Signal failure to apply the hunk via partial strategies.


def make_new_lines_explicit(content: str, hunk: list[str], original_before_text: str, original_after_text: str) -> list[str] | None:
    """
    Creates a new hunk representation where the 'before' section is realigned
    to the actual content string (`content`). This helps the diff matching algorithm
    find the correct location for applying the hunk even if whitespace or blank lines
    differ between the hunk's expected 'before' state and the actual content.

    Args:
        content: The actual file content string.
        hunk: The original normalized hunk lines (with +/-/space prefixes).
        original_before_text: The 'before' text derived from the original hunk.
        original_after_text (str): The 'after' text derived from the original hunk.

    Returns:
        list[str] or None: A new list of diff lines representing the realigned hunk,
                            or the original hunk if realignment is not feasible or beneficial.
                            Returns None if a critical step in realignment fails (e.g., applying back_diff).
    """
    # Received `original_before_text` and `original_after_text` from the calling function (`apply_hunk`).
    # This avoids redundant calculation.

    # Compare the original expected 'before_text' from the hunk with the actual file 'content'.
    # `diff_lines` generates a diff in the same format (+/- space prefixes).
    # This diff highlights how the content differs from what the hunk expected as its 'before' state.
    diff_from_content = diff_lines(original_before_text, content)

    # Construct a 'back_diff' (a list of lines with +/-/space prefixes) from `diff_from_content`.
    # The goal of the 'back_diff' is to represent the changes needed to transform the
    # `original_before_text` into a version that aligns with the actual `content`.
    # We keep lines that were 'context' (' ') or 'removed' ('-') in `diff_from_content`.
    # Lines marked as 'added' ('+') in `diff_from_content` (meaning they exist in `content` but
    # not in `original_before_text`) are skipped, as they are not part of the original `before_text`.
    back_diff: list[str] = []
    for line in diff_from_content:
        # Keep lines from the diff that represent removed lines ('-') or context lines (' ')
        # in the comparison between `original_before_text` and `content`.
        if line.startswith("+"):
            continue # Skip lines added in content relative to original_before_text
        # Lines starting with '-' or ' ' from `diff_from_content` correspond to content from `original_before_text`.
        # These are the lines we want to keep or mark as removed in our `back_diff`.
        back_diff.append(line)

    # Apply this 'back_diff' hunk structure to the `original_before_text`.
    # This attempts to simulate transforming the `original_before_text` by applying the differences
    # found when comparing it to the actual `content`. The result `aligned_before_text`
    # should be a version of `original_before_text` that contains only the lines
    # that successfully matched as context in the actual `content` (`' '` lines in `back_diff`)
    # and lines that were marked for removal by the back_diff process (`'-'` lines in `back_diff`).
    # `directly_apply_hunk` needs a target string (`original_before_text`) and a hunk (`back_diff`).
    aligned_before_text = directly_apply_hunk(original_before_text, back_diff)

    # If applying the `back_diff` failed (e.g., `directly_apply_hunk` returned None),
    # it means the realignment process failed. In this case, we cannot produce a useful
    # modified hunk, so return the original hunk or None to signal failure. Returning original hunk
    # seems safer as a fallback.
    if aligned_before_text is None: # Check explicitly for None (failure of directly_apply_hunk on back_diff)
        # print("Warning: Realignment step (apply_hunk on back_diff) failed.")
        return hunk # Fallback to original hunk

    # Perform heuristic checks on the realigned 'before' text (`aligned_before_text`)
    # to evaluate if the realignment was successful or meaningful enough to be useful.

    # Check 1: If the realigned text is very short after stripping all whitespace, it might not provide
    # sufficient context for reliable matching later. Original threshold was 10 characters.
    # `aligned_before_text.strip()` removes all leading/trailing whitespace.
    if len(aligned_before_text.strip()) < 10:
        # print(f"Warning: Realigned before text too short ({len(aligned_before_text.strip())} chars). Falling back.")
        return hunk # Fallback to original hunk if realigned context is minimal.

    # Convert the texts to lists of lines, preserving line endings, for line count comparison.
    original_before_lines = original_before_text.splitlines(keepends=True)
    aligned_before_lines = aligned_before_text.splitlines(keepends=True)
    original_after_lines = original_after_text.splitlines(keepends=True) # Keep original after_lines

    # Check 2: If the realigned text has significantly fewer lines than the original before text.
    # This might indicate that too much context was lost or mismatched during the realignment process,
    # suggesting the result might not be a good basis for a new hunk. Original threshold was 66%.
    # Avoid division by zero if original_before_lines was empty (handled by strip() check above).
    if original_before_lines and len(aligned_before_lines) < len(original_before_lines) * 0.66:
        # print(f"Warning: Realigned before text significantly shorter in lines ({len(aligned_before_lines)} vs {len(original_before_lines)}). Falling back.")
        return hunk # Fallback to original hunk if line count reduction is too drastic.

    # If the checks pass, the realigned `aligned_before_text` is deemed acceptable.
    # Generate a *new hunk* representing the difference between this realigned 'before' state
    # (which is found in the actual `content`) and the desired 'after' state (using the original `original_after_text`).
    # This new hunk is what `apply_hunk` will attempt to apply using partial application strategies.
    new_hunk_diff = difflib.unified_diff(
        aligned_before_lines, original_after_lines, # Diff between realigned before and original after
        fromfile='a', tofile='b', # Standard diff file indicators
        n=max(len(aligned_before_lines), len(original_after_lines)) # Set context to max lines
    )

    # Convert the new diff iterator to a list and strip the header lines (---, +++, @@)
    # to get just the hunk content lines with prefixes.
    new_hunk_lines = list(new_hunk_diff)[3:]

    # A final check: If the newly generated hunk is empty (no changes between aligned_before and original_after),
    # it implies the realignment process somehow resulted in a state already matching the target.
    # This is unexpected for a hunk that failed direct application. Fallback to original hunk.
    check_before, check_after = hunk_to_before_after(new_hunk_lines)
    if not check_before and not check_after:
        # print("Warning: Realigned hunk resulted in no changes. Falling back.")
        return hunk # Fallback if the new hunk is empty

    return new_hunk_lines # Return the newly generated, realigned hunk


def diff_lines(search_text: str, replace_text: str) -> list[str]:
    """
    Generates a line-by-line diff between two strings using the diff-match-patch library.
    Returns the diff as a list of strings formatted like unified diff lines
    (prefixed with '+', '-', or ' ').

    Args:
        search_text: The first string to compare ('before').
        replace_text: The second string to compare ('after').

    Returns:
        A list of strings representing the line-based diff.
    """
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5  # Set a timeout (in seconds) for the diff computation.
    # dmp.Diff_EditCost = 16 # This was commented out in the original code, keep it commented.

    # Convert lines in both input strings to character sequences.
    # This allows diff_match_patch to treat each line as a single 'character' for faster
    # and more accurate line-based diffing. The `mapping` dictionary stores the original
    # line content corresponding to the character sequences.
    search_lines_chars, replace_lines_chars, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    # Perform the core diff computation on the character sequences.
    # The `checklines=False` argument disables an internal post-processing step in dmp
    # that can sometimes produce less desirable diffs for line-based input.
    diff_chars = dmp.diff_main(search_lines_chars, replace_lines_chars, False)

    # Clean up the diff results.
    dmp.diff_cleanupSemantic(diff_chars) # Attempts to reduce redundant edits for semantic clarity.
    dmp.diff_cleanupEfficiency(diff_chars) # Attempts to improve the diff by reducing operations.

    # Convert the diff results back from character sequences to actual lines using the `mapping`.
    diff = list(diff_chars) # Ensure the result is a list for `diff_charsToLines`.
    dmp.diff_charsToLines(diff, mapping)

    # Format the diff into a list of strings with standard unified diff prefixes (' ', '+', '-').
    udiff_lines: list[str] = []
    # Each item in the `diff` list is a tuple: `(diff_type, text_chunk)`.
    # `diff_type` is -1 (removed), 0 (equal/context), 1 (added).
    for d_type, text_chunk in diff:
        prefix = " " # Default prefix for context lines (diff_type 0)

        if d_type == -1: # If the text chunk represents lines removed from `search_text`
            prefix = "-"
        elif d_type == 1: # If the text chunk represents lines added in `replace_text`
            prefix = "+"

        # Split the text chunk into individual lines, ensuring line endings are kept.
        # Add a newline if the chunk is not empty and doesn't end with one, for consistent splitting.
        if text_chunk and not text_chunk.endswith("\n"):
             text_chunk += "\n"

        # Append each individual line from the chunk to the result list, prefixed by the determined operator.
        for line in text_chunk.splitlines(keepends=True):
             udiff_lines.append(prefix + line)

    return udiff_lines

# Helper function for apply_partial_hunk to reduce cognitive complexity (Addresses Issue 7, part 1)
def generate_context_combinations(len_prec: int, len_foll: int) -> list[tuple[int, int]]:
    """
    Generates valid pairs of (use_prec, use_foll) representing the number of
    preceding and following context lines to use when attempting to apply a
    partial hunk. The combinations are ordered such that larger total context
    sizes (`use_prec + use_foll`) are attempted first, and for a given total,
    combinations with more preceding context are tried first.

    Args:
        len_prec: The total number of available preceding context lines.
        len_foll: The total number of available following context lines.

    Returns:
        A list of (preceding_context_count, following_context_count) tuples
                                to try, ordered by descending total count, then descending preceding count.
    """
    combinations: list[tuple[int, int]] = []
    # Calculate the maximum possible total number of context lines available.
    max_total_use = len_prec + len_foll

    # Iterate downwards through the desired total number of context lines to use.
    # Starting with the maximum context amount is a common strategy in diff application.
    for total_use in range(max_total_use, -1, -1): # Example: if max_total_use=5, try total_use 5, 4, 3, 2, 1, 0.
        # For the current `total_use`, iterate through all possible numbers of preceding
        # context lines (`use_prec`) that don't exceed the total available preceding
        # context (`len_prec`) and don't exceed the desired total context (`total_use`).
        # Iterate downwards for `use_prec` to prioritize using more preceding context lines
        # when the total context amount is fixed.
        for use_prec in range(len_prec, -1, -1): # Example: if len_prec=3, try use_prec 3, 2, 1, 0.

            # Check if the number of preceding lines we want to use (`use_prec`)
            # exceeds the total context allowed for this iteration (`total_use`).
            # If it does, this combination is not possible for the current `total_use`.
            if use_prec > total_use:
                continue # Skip this combination of (use_prec, total_use)

            # Calculate the required number of following context lines to meet the `total_use` target.
            use_foll = total_use - use_prec

            # Check if the required number of following lines (`use_foll`) exceeds the total
            # available following context (`len_foll`).
            # If it does, this combination is not possible.
            if use_foll > len_foll:
                continue # Skip this combination of (use_prec, use_foll)

            # If we reached this point, the combination (use_prec, use_foll) is valid
            # given the available context (`len_prec`, `len_foll`) and the current target
            # total context (`total_use`). Add this valid combination to the list.
            combinations.append((use_prec, use_foll))

    return combinations


# Refactored apply_partial_hunk to reduce cognitive complexity (Addresses Issue 7, part 2)
# Uses the helper function `generate_context_combinations`.
def apply_partial_hunk(content: str, preceding_context_lines: list[str], changes_lines: list[str], following_context_lines: list[str]) -> str | None:
    """
    Attempts to apply a partial hunk (defined by lists of preceding context,
    changes, and following context lines) to the content string.
    It tries applying the hunk slice using varying amounts of the provided
    context lines, starting with the largest amount of context and gradually reducing it.

    Args:
        content: The content string to apply the hunk to.
        preceding_context_lines: List of lines (with prefixes) for preceding context.
        changes_lines: List of lines (with prefixes) for changes (+/-).
        following_context_lines: List of lines (with prefixes) for following context.

    Returns:
        The content string after successful application, or None if no variation worked.
    """
    # Get the total number of available preceding and following context lines.
    len_prec = len(preceding_context_lines)
    len_foll = len(following_context_lines)

    # Generate a list of valid (use_prec, use_foll) combinations to try.
    # `generate_context_combinations` ensures these are ordered from most context to least context.
    combinations_to_try = generate_context_combinations(len_prec, len_foll)

    # Iterate through the generated context combinations.
    for use_prec, use_foll in combinations_to_try:
        # Extract the specific slices of context lines from the provided lists
        # based on the current combination's desired counts (`use_prec`, `use_foll`).
        # `preceding_context_lines[-use_prec:]` gets the last `use_prec` lines of preceding context.
        # `following_context_lines[:use_foll]` gets the first `use_foll` lines of following context.
        # List slicing handles edge cases where `use_prec` or `use_foll` is 0 correctly (returns an empty list).
        this_prec_slice = preceding_context_lines[-use_prec:]
        this_foll_slice = following_context_lines[:use_foll]

        # Construct the full hunk slice to attempt applying by concatenating the selected
        # preceding context slice, the core changes lines, and the selected following context slice.
        # The lines in these lists are assumed to already have their diff prefixes (' ', '+', or '-').
        hunk_slice_to_apply = this_prec_slice + changes_lines + this_foll_slice

        # Skip if the constructed hunk slice is empty (e.g., an empty change set with 0 context lines chosen).
        if not hunk_slice_to_apply:
             continue # Move to the next combination

        # Attempt to apply this specific `hunk_slice_to_apply` directly to the content string.
        # `directly_apply_hunk` will derive the 'before' text from this slice and try to find/replace it.
        res = directly_apply_hunk(content, hunk_slice_to_apply)

        # If `directly_apply_hunk` was successful (returned a non-None result)...
        if res is not None:
            # Return the modified content string immediately, as we found a working combination.
            return res

    # If the loop completes without any of the context combinations resulting in a successful application...
    return None # Signal failure for this partial hunk application attempt.


def directly_apply_hunk(content: str, hunk_lines: list[str]) -> str | None:
    """
    Attempts to apply a list of hunk lines (with prefixes) literally to the content string
    by using flexible search and replace. It derives the 'before' and 'after' text
    from the hunk lines and tries to replace the 'before' text with the 'after' text
    in the content. Includes a check for ambiguity based on context length to prevent
    incorrect replacements on short, non-unique context.

    Args:
        content: The content string to apply the hunk to.
        hunk_lines: A list of strings, each a line from a diff hunk slice with a prefix.

    Returns:
        str | None: The content string after successful replacement, or None if replacement failed.

    Raises:
        SearchTextNotUnique: If the derived 'before' text is short and ambiguous in the content.
    """
    # Extract the 'before' and 'after' text strings by processing the hunk lines.
    # `hunk_to_before_after` only considers lines with ' ', '+', '-' prefixes, ignoring headers if any remained.
    before_text, after_text = hunk_to_before_after(hunk_lines)

    # If there is no 'before' text extracted from the hunk lines, this method cannot apply the hunk,
    # as it relies on finding something to search for in the content.
    # This case (pure addition) should primarily be handled by the append logic in `do_replace`.
    if not before_text:
        # print("Debug: directly_apply_hunk called with no before_text.")
        return None # Cannot apply a hunk slice with no 'before' context via search/replace.

    # Implement a check to prevent ambiguous replacements based on minimal context.
    # This is crucial because `str.replace` replaces *all* occurrences.
    # First, get the lines that constitute the 'before' section *without* their prefixes.
    before_lines_content, _ = hunk_to_before_after(hunk_lines, lines=True)
    # Concatenate the stripped content of these lines to get the effective length ignoring indentation and blank lines.
    # Example: `["    pass\n"]` -> stripped content is `"pass"` (length 4).
    before_stripped_content = "".join([line.strip() for line in before_lines_content])

    # If the effective 'before' content (ignoring indentation and whitespace-only lines) is very short (<10)
    # AND the full `before_text` string (which includes indentation and possibly blank lines)
    # appears more than once in the target `content` string, the location to apply the hunk is ambiguous.
    # In this scenario, the original code raised `SearchTextNotUnique`.
    if len(before_stripped_content) < 10 and content.count(before_text) > 1:
        # Raise the specific exception to signal this particular type of failure upstream.
        # This allows the caller (`apply_diffs`) to provide a specific error message.
        raise SearchTextNotUnique("Search text (before_text) is not unique in the content for direct application with minimal context.")

    try:
        # Attempt to replace `before_text` with `after_text` in the `content` string.
        # Use the flexible search and replace mechanism, which tries different preprocessor combinations.
        # The `search_and_replace` strategy used within `flexi_just_search_and_replace`
        # employs `str.replace`, which replaces all occurrences by default.
        # The ambiguity check above should significantly reduce the chance of incorrect multiple replacements.
        new_content = flexi_just_search_and_replace([before_text, after_text, content])

        # Return the result of the flexible search and replace attempt.
        # It will be the modified content string if a strategy succeeded and returned a non-None value,
        # or None if no combination worked.
        return new_content
    except SearchTextNotUnique:
        # If the underlying strategy (`search_and_replace`) somehow still raises `SearchTextNotUnique`
        # (e.g., if its internal, commented-out check were re-enabled, or other unexpected scenario),
        # re-raise it to be caught by `apply_diffs`.
        raise


# Define the available preprocessors for the flexible search and replace mechanism.
# Each tuple represents a combination of boolean flags:
# (strip_blank_lines_flag, relative_indent_flag, reverse_lines_flag).
# These determine which text transformations are applied to the search_text,
# replace_text, and original_text before attempting the search/replace strategy.
all_preprocs: list[tuple[bool, bool, bool]] = [
    # The format is: (apply_strip_blank_lines, apply_relative_indent, apply_reverse_lines)
    # Always try the most literal interpretation first (no preprocessors applied).
    (False, False, False),
    # Then try applying single preprocessors independently.
    (True, False, False),  # Try stripping leading/trailing blank lines.
    (False, True, False),  # Try applying relative indentation.
    # (False, False, True), # Try reversing lines (this was commented out in the original code, keep it commented).
    # Then try combinations of the active preprocessors (strip_blank_lines and relative_indent).
    (True, True, False),  # Try stripping blank lines AND applying relative indentation.
    # Other combinations involving `reverse_lines` were commented out in original code, keep them commented:
    # (True, False, True),
    # (False, True, True),
    # (True, True, True),
]


def flexi_just_search_and_replace(texts: list[str]) -> str | None:
    """
    Configures and runs the flexible search and replace mechanism.
    Defines which core strategies and preprocessor combinations to attempt.
    Currently uses only the basic `search_and_replace` strategy with the `all_preprocs` list.

    Args:
        texts: A list or tuple containing [search_text, replace_text, original_text].

    Returns:
        str | None: The result of the first successful application attempt (modified text),
                    or None if no combination of preprocessors and strategies succeeded.
    """
    strategies: list[tuple[callable, list[tuple[bool, bool, bool]]]] = [
        # Define the strategy function (`search_and_replace`) and the list of preprocessor
        # combinations (`all_preprocs`) to try with this strategy.
        (search_and_replace, all_preprocs),
    ]

    # Call the general flexible search and replace runner function.
    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts: list[str]) -> str | None:
    """
    The basic core search and replace strategy.
    Takes a tuple/list `texts` containing `(search_text, replace_text, original_text)`.
    Attempts to replace `search_text` with `replace_text` in `original_text`.
    Uses Python's built-in `str.replace()`, which replaces ALL occurrences by default.
    Uniqueness checks are expected to be handled by the calling logic (`directly_apply_hunk`).

    Args:
        texts: A list or tuple containing [search_text, replace_text, original_text].

    Returns:
        str | None: The modified text string if the replacement resulted in a change,
                    or None if `search_text` was not found or the replacement resulted in no change.
    """
    search_text, replace_text, original_text = texts

    # If the search text is an empty string, `str.replace` behaves in a way that
    # is not useful for applying diffs (inserts `replace_text` between every character).
    # Also, `before_text` derived from a hunk should not be empty in the path leading here.
    # Handle this case explicitly just in case.
    if not search_text:
         # print("Warning: search_and_replace called with empty search_text.")
         return None # Cannot apply with empty search text

    # Check if search_text exists in the original content. If not, this strategy fails.
    if search_text not in original_text:
         # print(f"Debug: Search text not found: {search_text[:50]}{'...' if len(search_text) > 50 else ''}")
         return None # Return None if search text is not found

    # Perform the replacement. Note: str.replace replaces ALL occurrences of search_text.
    # The calling logic (`directly_apply_hunk`) is expected to check for ambiguity
    # before calling this if unique replacement is critical for that context.
    new_text = original_text.replace(search_text, replace_text)

    # Return the new text only if a change actually occurred.
    # If `search_text` was found but was identical to `replace_text`, `str.replace` returns
    # the original string, and no change is detected here.
    if new_text != original_text:
         return new_text
    else:
         # If no change occurred, this attempt wasn't successful or necessary for changing the text.
         # Return None to signal failure for this specific strategy/preprocessor combination,
         # prompting the caller to try other strategies.
         return None


def flexible_search_and_replace(texts: list[str], strategies: list[tuple[callable, list[tuple[bool, bool, bool]]]]) -> str | None:
    """
    Orchestrates trying multiple search/replace strategies, each potentially combined
    with different preprocessor transformations (like relative indent, stripping blank lines).
    It iterates through the defined strategies and their associated preprocessor combinations,
    applying the preprocessors, running the strategy, and reversing the preprocessors.
    Returns the result of the first successful attempt (where the strategy returned a non-None value).

    Args:
        texts: The input texts [search_text, replace_text, original_text].
        strategies: List of (strategy_func, list_of_preprocessor_combinations) tuples.

    Returns:
        str | None: The modified text string from the first successful strategy/preprocessor combination,
                    or None if no combination succeeded after trying all options.
    """
    # Iterate through each defined search/replace strategy.
    for strategy, preprocs in strategies:
        # For the current strategy, iterate through each combination of preprocessor flags defined for it.
        for preproc in preprocs:
            # Attempt to apply the current strategy with the current preprocessor combination.
            # `try_strategy` handles applying and reversing the preprocessors.
            # It returns None if the attempt failed at any stage (preprocessing failed, strategy failed, or reversing failed).
            res = try_strategy(texts, strategy, preproc)
            # If `try_strategy` returned a result (i.e., a value that is not None)...
            if res is not None:  # Explicitly check for None to allow empty string results ("")
                return res # Return the successful result immediately.

    # If the loops complete without any strategy/preprocessor combination succeeding
    return None # Signal overall failure


def try_strategy(texts: list[str], strategy: callable, preproc: tuple[bool, bool, bool]) -> str | None:
    """
    Applies a single preprocessor combination to the input texts, runs the
    specified search/replace strategy on the transformed texts, and then
    reverses the preprocessors on the result if the strategy was successful.
    Includes error handling for issues during preprocessing or strategy execution.

    Args:
        texts: The input texts [search_text, replace_text, original_text].
        strategy: The core search/replace function to apply (e.g., `search_and_replace`).
        preproc: A tuple of boolean flags (strip_blank_lines, relative_indent, reverse_lines)
                                          indicating which preprocessors to apply.

    Returns:
        str | None: The final result after applying and reversing preprocessors if the strategy
                    was successful, or None if the strategy failed or reversing failed.
    """
    # Unpack the boolean flags from the preprocessor combination tuple.
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri: RelativeIndenter | None = None # Variable to hold the RelativeIndenter instance if relative_indent is used.

    # Create a mutable copy of the input texts to apply transformations to.
    current_texts = list(texts)

    try:
        # Apply preprocessors based on the boolean flags.
        if preproc_strip_blank_lines:
            current_texts = strip_blank_lines(current_texts)
        if preproc_relative_indent:
            # The `relative_indent` function returns the indenter instance needed for reversing,
            # and the transformed texts. It might raise ValueError if marker selection fails.
            ri, current_texts = relative_indent(current_texts)
        if preproc_reverse:
            # Apply the `reverse_lines` transformation to each text string in the list.
            current_texts = [reverse_lines(text) for text in current_texts]

        # Apply the core search/replace strategy function to the transformed texts.
        # The strategy should return the modified text or None if it failed.
        res = strategy(current_texts)

        # If the strategy returned a result (i.e., a value that is not None), reverse the preprocessors.
        if res is not None: # Check explicitly for None (success)
            if preproc_reverse:
                # Reverse the line order back.
                res = reverse_lines(res)

            if preproc_relative_indent and ri: # Ensure ri is not None if relative_indent was applied
                # Reverse the relative indentation transformation back to absolute indentation.
                try:
                    # Use the saved RelativeIndenter instance to perform the reverse transformation.
                    # This might raise ValueError if the transformed text is not in a valid relative format.
                    res = ri.make_absolute(res)
                except ValueError:
                    # If reversing the relative indent fails (e.g., invalid format produced by strategy),
                    # this entire strategy+preprocessor combination is considered failed.
                    # print(f"Warning: Failed to revert relative indent for strategy {strategy.__name__} with preproc {preproc}")
                    return None # Signal failure for this attempt.

        # Return the final result. This is the successfully transformed text if all steps worked,
        # or None if the strategy failed (`res` was None initially) or reversing failed.
        return res

    except Exception: # Catch any exceptions during preprocessing or strategy execution
        # print(f"Error applying strategy {strategy.__name__} with preproc {preproc}: {e}")
        return None # Signal failure for this attempt.


def strip_blank_lines(texts: list[str]) -> list[str]:
    """
    Strips leading and trailing blank lines (lines containing only whitespace
    or empty, including just line endings) from each string in the input list.
    Preserves internal blank lines.

    Args:
        texts: A list of text strings.

    Returns:
        list[str]: A new list of strings with leading/trailing blank lines removed.
    """
    processed_texts: list[str] = []
    for text in texts:
        lines = text.splitlines(keepends=True)
        if not lines: # Handle empty input text: result is empty string.
            processed_texts.append("")
            continue

        # Find the index of the first line that is not blank (contains non-whitespace characters).
        first_non_blank_idx = 0
        for i, line in enumerate(lines):
            # Check if the line, after stripping all whitespace, is non-empty.
            if line.strip():
                first_non_blank_idx = i
                break
        else: # If the loop completes without finding a non-blank line, all lines are blank.
            processed_texts.append("") # The result is an empty string.
            continue # Move to the next text in the input list.

        # Find the index of the last line that is not blank.
        last_non_blank_idx = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
             if lines[i].strip():
                  last_non_blank_idx = i
                  break

        # Rejoin the lines from the first non-blank line's index to the last non-blank line's index (inclusive).
        # If all lines were blank, the first_non_blank_idx loop would hit `else` and `continue`.
        # So, if we reach here, first_non_blank_idx <= last_non_blank_idx.
        processed_text = "".join(lines[first_non_blank_idx : last_non_blank_idx + 1])
        processed_texts.append(processed_text)

    return processed_texts


def relative_indent(texts: list[str]):
    """
    Applies relative indentation transformation to each text in the input list.
    A single `RelativeIndenter` instance is created based on all texts to ensure
    a consistent outdent marker is chosen that is unique across all inputs.

    Args:
        texts (list[str]): A list of text strings.

    Returns:
        tuple[RelativeIndenter, list[str]]: A tuple containing:
            - The `RelativeIndenter` instance used for transformation.
            - A list of the transformed text strings with relative indentation.

    Raises:
         ValueError: If a unique marker cannot be found or if any input text already
                     contains the selected marker.
    """
    # Create a single indenter instance based on all input texts. This ensures
    # the unique marker selection considers characters from all texts.
    # The constructor `RelativeIndenter()` can raise ValueError if a unique marker isn't found.
    ri = RelativeIndenter(texts)
    # Apply the relative indentation transformation to each text in the list.
    # `make_relative()` can raise ValueError if an input text already contains the marker.
    processed_texts = [ri.make_relative(text) for text in texts]
    return ri, processed_texts


class RelativeIndenter:
    """
    A utility class to transform text between absolute and relative indentation representations.
    Relative indentation encodes changes in indentation relative to the previous line,
    using literal characters for increases and a special marker for decreases (outdents).
    This format can improve the robustness of diff matching against code blocks
    that have undergone global indentation shifts.
    """

    def __init__(self, texts: list[str]):
        """
        Initializes the `RelativeIndenter` by analyzing the input texts to find
        a unique character to use as the outdent marker that is not present in any of the texts.

        Args:
            texts: A list of text strings that will potentially be transformed.

        Raises:
             ValueError: If a suitable unique marker character cannot be found within a searched range.
        """
        chars: set[str] = set()
        # Collect all characters present in all input texts into a set.
        for text in texts:
            # Check if text is None or not a string before iterating over it
            if isinstance(text, str):
                 chars.update(text)
            # Optionally log a warning for unexpected types

        # Preferred marker character: Leftwards Arrow (U+2190).
        # This is a character unlikely to appear in typical code but might appear in documentation.
        ARROW = "\u2190"

        # Check if the preferred marker is already present in any of the input texts.
        if ARROW not in chars:
            # If the preferred marker is not in the texts, use it.
            self.marker: str = ARROW
        else:
            # If the preferred marker is present, we need to find a different, unique character.
            # `select_unique_marker()` searches for an unused high unicode character.
            # This method can raise ValueError if it fails to find one.
            self.marker = self.select_unique_marker(chars)
            # print(f"Warning: Preferred indent marker '{ARROW}' found in text. Using '{self.marker}' instead.")


    def select_unique_marker(self, chars: set[str]) -> str:
        """
        Finds a unique character (not present in the given set `chars`) by
        iterating downwards from a high unicode code point range, prioritizing
        Private Use Areas less likely to contain meaningful data.

        Args:
            chars: A set of characters already present in the texts.

        Returns:
            str: A single character string that is not in `chars`.

        Raises:
            ValueError: If no unique marker could be found within the searched range.
        """
        # Iterate downwards from a high unicode code point (U+10FFFF) towards the Basic Multilingual Plane (BMP).
        # Prioritize ranges like Supplementary Private Use Area B (U+100000 to U+10FFFF)
        # and Private Use Area A (U+E000 to U+F8FF) as they are intended for private use
        # and less likely to cause conflicts with standard text.
        # Search from high values downwards.
        try:
            # Search in Supplementary Private Use Area B and A.
            # Start from a known high value (U+10FFFF) and go down.
            for codepoint in range(0x10FFFF, 0xE000, -1):
                 # Check if the character corresponding to this codepoint is not in the set of existing characters.
                 marker = chr(codepoint)
                 if marker not in chars:
                     return marker # Found a unique marker!

        except OverflowError:
             # This might occur on systems with limited integer size, though unlikely for standard Python 3.
             # If caught, fall through to the final ValueError.
             pass

        # If the loop finishes without finding a unique marker in the searched range
        raise ValueError("Could not find a unique marker for relative indentation.")


    def make_relative(self, text: str) -> str:
        """
        Transforms text from absolute indentation to relative indentation.
        Each original line `[indent][content][ending]` becomes a pair of lines:
        `[relative_indent_prefix]\n` and `[content][ending]`.
        The relative indent prefix is the characters representing the added indent
        (for indent increases) or the unique `marker` repeated (for outdents).

        Args:
            text (str): A text string with absolute indentation.

        Returns:
            str: A text string represented with relative indentation.

        Raises:
            ValueError: If the input text already contains the outdent marker,
                        suggesting it might be already transformed or has a character conflict.
        """
        # Check if the text already contains the marker. This indicates it might be
        # already in a relative format or contains the character coincidentally.
        if self.marker in text:
            # Raising ValueError signals an issue with the input text format or marker selection.
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)

        output: list[str] = [] # List to store the output lines (will be pairs)
        prev_indent: str = "" # Stores the absolute indentation string of the *previous* content line processed.

        for line in lines:
            # Separate the line content from its potential trailing line endings (\n or \r).
            line_without_end = line.rstrip("\n\r")

            # Calculate the length of the leading whitespace (absolute indentation) of the content part.
            # `lstrip()` removes all leading whitespace characters (space, tab, form feeds, etc.).
            lstripped_line = line_without_end.lstrip()
            len_indent = len(line_without_end) - len(lstripped_line)
            # Extract the actual absolute indentation string (the leading whitespace characters).
            indent = line[:len_indent]

            # Calculate the change in indentation length compared to the previous line's absolute indent.
            change = len_indent - len(prev_indent)

            cur_indent_prefix_line: str = "" # This string will form the first line of the output pair.

            if change > 0:
                # Indented more: The relative prefix is the part of the current indent
                # that was added compared to the previous indent.
                # Example: prev="    ", indent="        " -> change=4. `cur_indent_prefix_line` should be "    ".
                # `indent[-change:]` correctly extracts this last part.
                # Ensure `indent` is long enough to slice if change is large relative to current indent.
                cur_indent_prefix_line = indent[-change:] if change <= len(indent) else indent # Defensive slicing

            elif change < 0:
                # Outdented: The relative prefix is the unique marker character repeated
                # by the magnitude of the outdent (`-change`).
                # Example: prev="        ", indent="    " -> change=-4. `cur_indent_prefix_line` should be marker * 4.
                cur_indent_prefix_line = self.marker * -change

            # If change is 0, `cur_indent_prefix_line` remains "" (same indent level).

            # Construct the output pair of lines:
            # 1. The calculated relative indent prefix string followed by a newline character `\n`.
            # 2. The rest of the original line content (starting from the character after the absolute indent)
            #    followed by its original line ending(s).
            out_line1 = cur_indent_prefix_line + "\n"
            out_line2 = line[len_indent:] # This slice includes the original line ending(s)

            # Add these two lines to the output list.
            output.append(out_line1)
            output.append(out_line2)

            # Update the `prev_indent` to the current line's absolute indentation for the next iteration.
            prev_indent = indent

        # Join all the collected output lines (pairs) into a single string.
        res = "".join(output)
        return res


    def make_absolute(self, text: str) -> str:
        """
        Transforms text from the relative indentation representation (produced by `make_relative`)
        back to absolute indentation. Interprets the unique marker as outdents.
        Assumes the input text is in the format: pairs of lines like `[indent_prefix]\n` and `[content_line]`.

        Args:
            text: A text string with relative indentation representation.

        Returns:
            str: A text string with absolute indentation.

        Raises:
            ValueError: If the input text is not in the expected relative format
                        (e.g., odd number of lines, missing content line, outdent exceeding current level)
                        or if the marker character is unexpectedly still present in the final result.
        """
        lines = text.splitlines(keepends=True)

        output: list[str] = [] # List to store the reconstructed absolute lines.
        prev_indent: str = "" # Reconstructs the absolute indent string level by level.

        # The input text format is expected to be pairs of lines. Check if the total number of lines is even.
        if len(lines) % 2 != 0:
             # If the number of lines is odd, the format is incorrect (a pair is incomplete).
             raise ValueError("Invalid relative indent format: Mismatched lines (odd number of lines).")

        # Process lines in pairs: the relative indent prefix line (at index i) and the content line (at index i+1).
        for i in range(0, len(lines), 2):
            # This check is redundant due to the len % 2 check above, but adds safety.
            if i + 1 >= len(lines):
                 # This indicates an incomplete pair.
                 raise ValueError("Invalid relative indent format: Missing content line for indent prefix.") # Should not be reached if total lines is even

            # Get the content of the relative indent prefix line, removing its trailing newline.
            dent_line = lines[i].rstrip("\n\r")
            # Get the content line (includes its original line ending).
            non_indent_line = lines[i + 1]

            cur_indent: str = "" # Calculate the current absolute indent string based on the previous indent and the `dent_line`.

            if dent_line.startswith(self.marker):
                # The `dent_line` starts with the marker: it represents an outdent from the `prev_indent`.
                # The length of the `dent_line` is the number of markers, indicating the magnitude of the outdent.
                len_outdent = len(dent_line)

                # Calculate the current absolute indent by removing the outdent amount (`len_outdent`)
                # from the `prev_indent` string.
                # This requires the `prev_indent` to be at least as long as the outdent amount.
                if len_outdent > len(prev_indent):
                    # Trying to outdent more than the current absolute indent level allows.
                    # This indicates an invalid relative indent format or a bug in `make_relative`.
                     raise ValueError(f"Invalid relative indent format: Outdent of {len_outdent} characters exceeds previous indent level of {len(prev_indent)}.")

                cur_indent = prev_indent[:-len_outdent] # Remove the last `len_outdent` characters from `prev_indent`.
            else:
                # The `dent_line` does not start with the marker: it contains characters that should be appended
                # to the `prev_indent` string. This represents an indent increase or maintaining the same level.
                cur_indent = prev_indent + dent_line # Concatenate the previous indent and the characters in `dent_line`.

            # Construct the final output line: the calculated absolute indent string followed by the content line.
            # Handle blank lines: If the content line (stripped of its line ending and all whitespace) is empty,
            # don't add any absolute indentation before it; just append the content line as is (it includes its ending).
            if not non_indent_line.rstrip("\n\r").strip():
                out_line = non_indent_line # If it's effectively a blank line, just keep the original line endings/whitespace.
            else:
                out_line = cur_indent + non_indent_line # Add the calculated absolute indent before the content.

            output.append(out_line) # Add the reconstructed absolute line to the output list.
            prev_indent = cur_indent # Update the `prev_indent` to the current line's absolute indent for the next pair.

        # Join all the collected output lines (pairs) into a single string.
        res = "".join(output)

        # Final check: Ensure the unique marker character is not present in the resulting absolute text.
        # If it is, the conversion back to absolute indentation failed somehow.
        if self.marker in res:
            # Original code had a dump() call here for debugging.
            raise ValueError(f"Error transforming text back to absolute indents: Marker '{self.marker}' still present in result.")

        return res


def reverse_lines(text: str) -> str:
    """
    Reverses the order of lines in a text string. Preserves original line endings.

    Args:
        text (str): The input string.

    Returns:
        str: A new string with lines in reversed order.
    """
    # Split the text into a list of lines, ensuring line endings are kept (`keepends=True`).
    lines = text.splitlines(keepends=True)
    # Reverse the list of lines in place.
    lines.reverse()
    # Join the reversed list of lines back into a single string.
    return "".join(lines)


if __name__ == "__main__":
    # Test case for apply_diffs function with multiple hunks
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye, World!")
"""

    # Added standard file paths to diff headers for better example format.
    # Includes two separate hunks within the same diff block.
    diff_content = """```diff
--- a/original.py
+++ b/modified.py
@@ -1,5 +1,8 @@
 def hello():
 -    print("Hello, World!")
 +    print("Hello, Universe!")
 +    print("How are you today?")

 def goodbye():
 -    print("Goodbye, World!")
 +    print("Farewell, Universe!")
 +    print("See you next time!")