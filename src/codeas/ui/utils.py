import difflib
import json
import os
from pathlib import Path
from typing import List, Tuple, Any, Dict, Union, Iterable, Callable

from diff_match_patch import diff_match_patch

PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    pass


def read_prompts() -> Dict[str, str]:
    """Reads prompts from the prompts.json file in the user's codeas directory."""
    try:
        if os.path.exists(PROMPTS_PATH):
            with open(PROMPTS_PATH, "r") as f:
                # Ensure the file is not empty before attempting to load JSON
                content = f.read()
                if not content:
                    return {}
                f.seek(0) # Reset file pointer if read
                return json.load(f)
        else:
            return {}
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading prompts file {PROMPTS_PATH}: {e}")
        # Return empty prompts on error to prevent downstream issues
        return {}


def save_prompts(prompts_data: Dict[str, str]):
    """Saves the given prompts dictionary to the prompts.json file."""
    try:
        # Ensure the directory exists
        prompts_dir = Path(PROMPTS_PATH).parent
        prompts_dir.mkdir(parents=True, exist_ok=True)

        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts_data, f, indent=4) # Use indent for readability
    except IOError as e:
        # Log or handle the error appropriately in a real application
        print(f"Error saving prompts file {PROMPTS_PATH}: {e}")


def save_existing_prompt(existing_name: str, new_name: str, new_prompt: str):
    """Updates an existing prompt by name or renames it."""
    prompts = read_prompts()
    prompts[new_name] = new_prompt.strip()

    if existing_name != new_name and existing_name in prompts:
        del prompts[existing_name]

    save_prompts(prompts)


def delete_saved_prompt(prompt_name: str):
    """Deletes a prompt by name."""
    prompts = read_prompts()
    if prompt_name in prompts:
        del prompts[prompt_name]
        save_prompts(prompts)


def save_prompt(name: str, prompt: str):
    """Saves a new prompt, incrementing version if name exists."""
    prompts = read_prompts()
    # Determine the base name without potential version suffix
    base_name = name.rsplit(" v.", 1)[0] if " v." in name else name

    name_version_map = extract_name_version(prompts.keys())

    full_name = base_name
    if base_name in name_version_map:
        next_version = name_version_map[base_name] + 1
        full_name = f"{base_name} v.{next_version}"

    prompts[full_name] = prompt.strip()
    save_prompts(prompts)


def extract_name_version(existing_names: Iterable[str]) -> Dict[str, int]:
    """
    Parses prompt names like '{name}', '{name} v.1' etc.,
    and returns a map from the base name to the highest version number found.
    """
    name_version_map = {}
    for full_name in existing_names:
        parts = full_name.rsplit(" v.", 1)
        if len(parts) == 2:
            name, version_str = parts
            try:
                version = int(version_str)
            except ValueError:
                # Handle cases where version is not a number, treat as base version 1
                name = full_name
                version = 1
        else:
            name = full_name
            version = 1

        if name in name_version_map:
            name_version_map[name] = max(name_version_map[name], version)
        else:
            name_version_map[name] = version
    return name_version_map


def finalize_hunk(buffer: List[str], fname: str | None, edits: List[Tuple[str | None, List[str]]], exclude_last_n: int = 0) -> List[str]:
     """
     Adds buffer content (excluding last n lines) as a hunk to the edits list.
     Returns an empty list to reset the buffer.
     """
     hunk_content = buffer[:-exclude_last_n] if exclude_last_n > 0 else buffer
     # Keep the original behavior of appending the hunk list even if empty
     edits.append((fname, hunk_content))
     return [] # Return empty list for new buffer

# Issue 1: CRITICAL (S3776) - Refactor process_fenced_block to reduce Cognitive Complexity.
# Original line 122
def process_fenced_block(lines: List[str], start_line_num: int) -> Tuple[int, List[Tuple[str | None, List[str]]]]:
    """
    Parses a fenced diff block from a list of lines.

    Handles standard unified diff format and a specific non-standard format
    where multiple file diffs are concatenated within a single block,
    separated by '---' and '+++' lines.

    Args:
        lines: List of strings representing the file content lines.
        start_line_num: The index in `lines` where the '```diff' line was found.

    Returns:
        A tuple: (line number after the block, list of edits)
        The line number is the index in `lines` where the closing '```' was found, plus 1.
        Returns len(lines) if no closing '```' is found.
        Edits is a list of tuples (fname, hunk), where hunk is a list of lines.
    """
    # Find the end of the block (line containing ```)
    end_line_num = len(lines) # Default to end of input
    for i in range(start_line_num, len(lines)):
        if lines[i].startswith("```"):
            end_line_num = i
            break

    # Extract lines within the fenced block (exclusive of fence lines)
    block_lines = lines[start_line_num:end_line_num]

    # Handle initial block headers (---/+++) if present.
    initial_fname = None
    lines_to_process = list(block_lines) # Start with all lines inside the block

    # Original code handled the first ---/+++ header pair at the beginning.
    if len(lines_to_process) >= 2 and \
       lines_to_process[0].startswith("--- ") and \
       lines_to_process[1].startswith("+++ "):
        initial_fname = lines_to_process[1][4:].strip() if len(lines_to_process[1]) >= 4 else ""
        lines_to_process = lines_to_process[2:]

    # Add sentinel "@@ @@" to trigger processing of the last hunk
    lines_to_process.append("@@ @@") # Original added without newline

    edits: List[Tuple[str | None, List[str]]] = []
    current_hunk_lines: List[str] = [] # Buffer to accumulate lines for the current hunk
    in_change_section = False
    current_fname = initial_fname

    for line in lines_to_process:
        is_multi_file_trigger = (len(current_hunk_lines) >= 1 and line.startswith("+++ ") and current_hunk_lines[-1].startswith("--- "))
        is_at_trigger = line.startswith("@")

        if is_multi_file_trigger:
            # Finalize previous hunk before the --- line
            current_hunk_lines = finalize_hunk(current_hunk_lines[:-1], current_fname, edits)
            in_change_section = False
            current_fname = line[4:].strip() if len(line) >= 4 else ""
            current_hunk_lines = [] # Reset buffer
            continue # Skip appending this line

        elif is_at_trigger:
             # Finalize previous hunk if in change section, reset buffer otherwise
             if in_change_section:
                  current_hunk_lines = finalize_hunk(current_hunk_lines, current_fname, edits)
             current_hunk_lines = [] # Reset buffer
             in_change_section = False
             continue # Skip appending this line

        else:
            # Not a trigger line, append to buffer and update state
            current_hunk_lines.append(line)
            if len(line) >= 2 and line[0] in "-+":
                in_change_section = True

    # The loop processes the sentinel "@". The logic above handles finalization.
    # current_hunk_lines should be empty after the loop.

    return end_line_num + 1, edits


def find_diffs(content: str) -> List[Tuple[str | None, List[str]]]:
    """
    Parses fenced diff blocks (```diff ... ```) from content
    and extracts diff edits using process_fenced_block.
    """
    if not content.endswith("\n"):
        content = content + "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits: List[Tuple[str | None, List[str]]] = []

    while line_num < len(lines):
        line = lines[line_num]
        if line.startswith("```diff"):
            line_num_after_block, these_edits = process_fenced_block(lines, line_num + 1)
            edits.extend(these_edits)
            line_num = line_num_after_block
            continue

        line_num += 1

    return edits


def normalize_hunk(hunk: List[str]) -> List[str]:
    """
    Canonicalizes a hunk by extracting before/after content, cleaning whitespace,
    and regenerating a standard unified diff hunk.
    """
    before, after = hunk_to_before_after(hunk, lines=True)

    before = cleanup_pure_whitespace_lines(before)
    after = cleanup_pure_whitespace_lines(after)

    if not before and not after:
        return []

    diff = difflib.unified_diff(before, after, n=max(len(before), len(after)), lineterm='')

    normalized_diff_lines = list(diff)[3:]

    # Ensure lines have newlines as expected downstream
    normalized_diff_lines_with_newlines = [line + '\n' for line in normalized_diff_lines]

    return normalized_diff_lines_with_newlines


def cleanup_pure_whitespace_lines(lines: List[str]) -> List[str]:
    """
    Replaces lines containing only whitespace with a string containing only their original line ending.
    Corrected original indexing bug.
    """
    res = [
        line if line.strip() else line[len(line.rstrip('\r\n')):]
        for line in lines
    ]
    return res


def hunk_to_before_after(hunk_lines: List[str], lines: bool = False) -> Union[Tuple[str, str], Tuple[List[str], List[str]]]:
    """
    Converts diff hunk lines (with '+', '-', ' ' prefixes) into 'before' and 'after' content.
    """
    before: List[str] = []
    after: List[str] = []

    for line in hunk_lines:
        if len(line) < 2: # Replicate original logic for short lines
            op = " "
            content_line = line
        else:
            op = line[0]
            content_line = line[1:]

        if op == " ":
            before.append(content_line)
            after.append(content_line)
        elif op == "-":
            before.append(content_line)
        elif op == "+":
            after.append(content_line)
        # Other prefixes (like '@') are ignored

    if lines:
        return before, after

    return "".join(before), "".join(after)


def apply_diffs(file_content: str, diff_content: str) -> str:
    """
    Applies diffs described in diff_content to the given file_content string.
    Processes all hunks found in all fenced diff blocks sequentially.
    """
    edits = find_diffs(diff_content)

    # Dummy path interaction as per original code, inconsistent with string processing
    dummy_path = Path("dummy_path")

    current_content = file_content

    for path, hunk in edits:
        normalized_hunk = normalize_hunk(hunk)
        if not normalized_hunk:
            continue

        try:
            result_content = do_replace(dummy_path, current_content, normalized_hunk)

            if result_content is None:
                 if dummy_path.exists():
                     dummy_path.unlink()
                 raise ValueError("The diff failed to apply to the file content.")

            current_content = result_content

        except SearchTextNotUnique:
            if dummy_path.exists():
                 dummy_path.unlink()
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )
        except Exception as e:
            if dummy_path.exists():
                 dummy_path.unlink()
            raise ValueError(f"An error occurred while applying diff hunk: {e}") from e

    if dummy_path.exists():
        dummy_path.unlink()

    return current_content


def do_replace(fname: Path, content: str | None, hunk: List[str]) -> str | None:
    """
    Attempts to apply a normalized hunk to the content string using search and replace logic.
    Handles pure additions and dummy file creation as in original code.
    """
    before_text, after_text = hunk_to_before_after(hunk)

    # Handle pure addition hunk (empty before_text)
    if not before_text.strip():
        if not fname.exists():
            fname.touch()
            content = "" if content is None else content
        new_content = content + after_text
        return new_content

    # Cannot apply if content is None and requires finding before_text
    if content is None:
        return None

    # Use apply_hunk for search/replace logic
    return apply_hunk(content, hunk)


def apply_hunk(content: str, hunk: List[str]) -> str | None:
    """
    Attempts to apply a normalized hunk to the content string.
    Tries direct application first, then flexible partial application.
    """
    # Issue 2: MAJOR (S1656) - Remove or correct useless self-assignment.
    # The assignment `content = res` below is NOT useless as it updates the content
    # sequentially with results of partial hunk applications. This appears to be a
    # false positive. No code change needed.

    before_text, after_text = hunk_to_before_after(hunk)

    # Try direct application
    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    # If direct fails, realign and try applying sections
    new_hunk = make_new_lines_explicit(content, hunk)

    sections: List[List[str]] = []
    current_section_lines: List[str] = []
    cur_op = " "

    # Generate ops string from hunk lines, handling empty lines
    ops_string = "".join([line[0] for line in new_hunk if len(line) > 0])

    # Replace +/- with x and newlines with space as in original
    ops_string = ops_string.replace("-", "x")
    ops_string = ops_string.replace("+", "x")
    ops_string = ops_string.replace("\n", " ")

    # Split hunk lines into sections based on ops_string
    for i in range(len(ops_string)):
        op = ops_string[i]
        if op != cur_op:
            sections.append(list(current_section_lines))
            current_section_lines = []
            cur_op = op
        current_section_lines.append(new_hunk[i])

    sections.append(list(current_section_lines))

    # Add empty section if last op wasn't context (' ')
    if cur_op != " ":
         sections.append([])

    all_done = True
    # Iterate through sections in groups of 3 (preceding, changes, following)
    for i in range(2, len(sections), 2):
        preceding_context = sections[i - 2]
        changes = sections[i - 1]
        following_context = sections[i]

        res = apply_partial_hunk(content, preceding_context, changes, following_context)
        if res is not None:
            content = res # This line flagged by S1656 (false positive)
        else:
            all_done = False
            break

    if all_done:
        return content

    return None


def make_new_lines_explicit(content: str, hunk: List[str]) -> List[str]:
    """
    Attempts to realign the hunk's 'before' content with the actual file content.
    """
    before, after = hunk_to_before_after(hunk)

    # Diff hunk's 'before' vs actual 'content'
    diff = diff_lines(before, content)

    # Keep context (' ') and removed ('-') lines from this diff
    back_diff = []
    for line in diff:
        if line.startswith("+"):
            continue
        back_diff.append(line)

    # Apply back_diff to original hunk's 'before'
    new_before = directly_apply_hunk(before, back_diff)

    if new_before is None:
        return hunk # Realign failed

    # Check if realignment resulted in significantly smaller/shorter content
    before_lines_orig = before.splitlines(keepends=True)
    new_before_lines = new_before.splitlines(keepends=True)

    # Check 1: stripped length too short
    if len(new_before.strip()) < 10:
        return hunk

    # Check 2: number of lines too few
    if len(new_before_lines) < len(before_lines_orig) * 0.66:
        return hunk

    # Realign succeeded and significant, create new hunk diff
    after_lines = after.splitlines(keepends=True)
    new_hunk_diff = difflib.unified_diff(
        new_before_lines, after_lines, n=max(len(new_before_lines), len(after_lines)), lineterm=''
    )
    new_hunk_lines = list(new_hunk_diff)[3:]

    # Ensure lines have newlines
    new_hunk_lines_with_newlines = [line + '\n' for line in new_hunk_lines]

    # The result is a list of lines starting with '+', '-', or ' ', representing the realigned hunk.
    return new_hunk_lines_with_newlines


def diff_lines(search_text: str, replace_text: str) -> List[str]:
    """
    Uses diff_match_patch to generate a diff formatted as lines with +/-/ prefixes.
    """
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5

    search_lines_chars, replace_lines_chars, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    diff_result_chars = dmp.diff_main(search_lines_chars, replace_lines_chars, None)
    dmp.diff_cleanupSemantic(diff_result_chars)
    dmp.diff_cleanupEfficiency(diff_result_chars)

    diff_result_lines = list(diff_result_chars)
    dmp.diff_charsToLines(diff_result_lines, mapping)

    udiff_lines = []
    for op_type, text in diff_result_lines:
        prefix = " "
        if op_type < 0:
            prefix = "-"
        elif op_type > 0:
            prefix = "+"

        for line in text.splitlines(keepends=True):
            udiff_lines.append(prefix + line)

    return udiff_lines


def apply_partial_hunk(content: str, preceding_context: List[str], changes: List[str], following_context: List[str]) -> str | None:
    """
    Attempts to apply a partial hunk by trying progressively smaller amounts of context.
    """
    len_prec = len(preceding_context)
    len_foll = len(following_context)
    use_all = len_prec + len_foll

    # Try using `use` context lines total, from all down to 0
    for use in range(use_all, -1, -1):
        # Distribute context between preceding and following sections
        for use_prec in range(len_prec, -1, -1):
            use_foll = use - use_prec

            if use_foll > len_foll:
                continue

            this_prec = preceding_context[-use_prec:] if use_prec > 0 else []
            this_foll = following_context[:use_foll]

            partial_hunk = this_prec + changes + this_foll

            res = directly_apply_hunk(content, partial_hunk)

            if res is not None:
                return res

    return None


def directly_apply_hunk(content: str, hunk: List[str]) -> str | None:
    """
    Attempts to apply a hunk directly using search and replace.
    Refuses if before_text is empty or if tiny, non-unique context is found.
    """
    # Issue 3: MINOR (S1481) - Replace unused local variable "before_text" with "_".
    # The variable `before_text` is used below in `content.count(before_text)` and
    # passed to `flexi_just_search_and_replace`. It is NOT unused.
    # This appears to be a false positive. No code change needed.
    before_text, after_text = hunk_to_before_after(hunk)

    if not before_text:
        return None # Cannot apply if before_text is empty

    # Check for tiny, non-unique context
    before_lines_list, _ = hunk_to_before_after(hunk, lines=True)
    before_lines_stripped_joined = "".join([line.strip() for line in before_lines_list])

    if len(before_lines_stripped_joined) < 10 and content.count(before_text) > 1:
        return None # Refuse risky application

    try:
        # Attempt flexible search and replace using before_text and after_text
        new_content = flexi_just_search_and_replace([before_text, after_text, content])
    except SearchTextNotUnique:
        # This block is likely unreachable given the current search_and_replace implementation
        new_content = None

    return new_content


def flexi_just_search_and_replace(texts: List[str]) -> str | None:
    """Wrapper to try search/replace with different preprocessing strategies."""
    strategies = [
        (search_and_replace, all_preprocs),
    ]
    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts: List[str]) -> str | None:
    """Performs simple string search and replace."""
    search_text, replace_text, original_text = texts

    num = original_text.count(search_text)
    if num == 0:
        return None

    # Replaces all occurrences if found
    new_text = original_text.replace(search_text, replace_text)

    return new_text


def flexible_search_and_replace(texts: List[str], strategies: List[Tuple[Callable, List[Tuple[bool, bool, bool]]]]) -> str | None:
    """Try a series of search/replace methods with preprocessors."""
    for strategy, preprocs in strategies:
        for preproc in preprocs:
            res = try_strategy(texts, strategy, preproc)
            if res is not None:
                return res
    return None


def try_strategy(texts: List[str], strategy: Callable, preproc: Tuple[bool, bool, bool]) -> str | None:
    """Applies preprocessors, runs strategy, applies postprocessors."""
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    processed_texts = list(texts)

    # Apply preprocessors
    if preproc_strip_blank_lines:
        processed_texts = strip_blank_lines(processed_texts)
    if preproc_relative_indent:
        try:
            ri, processed_texts = relative_indent(processed_texts)
        except ValueError: # RelativeIndenter init can raise ValueError
             return None
    if preproc_reverse:
        processed_texts = list(map(reverse_lines, processed_texts))

    # Apply strategy
    res = strategy(processed_texts)

    # Apply postprocessors if strategy was successful
    if res is not None:
        if preproc_reverse:
            res = reverse_lines(res)

        if preproc_relative_indent:
            try:
                res = ri.make_absolute(res)
            except ValueError: # make_absolute can raise ValueError
                return None

    return res


def strip_blank_lines(texts: List[str]) -> List[str]:
    """Strips leading/trailing newlines and adds one back."""
    return [text.strip("\r\n") + "\n" for text in texts]


def relative_indent(texts: List[str]) -> Tuple['RelativeIndenter', List[str]]:
    """Applies relative indentation transformation."""
    ri = RelativeIndenter(texts)
    # make_relative can raise ValueError
    transformed_texts = list(map(ri.make_relative, texts))
    return ri, transformed_texts


class RelativeIndenter:
    """Rewrites text to use relative indentation markers."""

    def __init__(self, texts: List[str]):
        """Chooses a unique marker character."""
        chars = set()
        for text in texts:
            chars.update(text)

        ARROW = "\u2190"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars: set[str]) -> str:
        """Finds a unicode character not present in the given set."""
        # Search for a marker in a high Unicode range
        for codepoint in range(0x10FFFF, 0xFFFF, -1):
             marker = chr(codepoint)
             if marker not in chars:
                 return marker

        raise ValueError("Could not find a unique marker")

    def make_relative(self, text: str) -> str:
        """Transforms text to relative indent representation."""
        if self.marker in text:
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)
        output: List[str] = []
        prev_indent = ""

        for line in lines:
            line_without_end = line.rstrip("\n\r")
            len_indent = len(line_without_end) - len(line_without_end.lstrip())
            indent = line[:len_indent]
            change = len_indent - len(prev_indent)

            cur_indent_marker = ""
            if change > 0:
                cur_indent_marker = indent[-change:]
            elif change < 0:
                cur_indent_marker = self.marker * -change
            # else change == 0, cur_indent_marker remains ""

            output.append(cur_indent_marker + "\n")
            output.append(line[len_indent:])
            prev_indent = indent

        return "".join(output)

    def make_absolute(self, text: str) -> str:
        """Transforms text from relative back to absolute indents."""
        lines = text.splitlines(keepends=True)

        if len(lines) % 2 != 0:
             raise ValueError("Malformed relative indent text: odd number of lines.")

        output: List[str] = []
        prev_indent = ""

        for i in range(0, len(lines), 2):
            marker_line = lines[i]
            content_line = lines[i + 1]
            dent = marker_line.rstrip("\r\n")

            if dent.startswith(self.marker):
                len_outdent = len(dent)
                if len_outdent > len(prev_indent):
                     raise ValueError(f"Malformed relative indent text: cannot outdent {len_outdent} beyond previous indent of {len(prev_indent)}")
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent

            if not content_line.rstrip("\r\n"):
                out_line = content_line
            else:
                out_line = cur_indent + content_line

            output.append(out_line)
            prev_indent = cur_indent

        res = "".join(output)

        if self.marker in res:
            raise ValueError("Error transforming text back to absolute indents: marker found in output")

        return res


def reverse_lines(text: str) -> str:
    """Reverses the order of lines in a string."""
    lines = text.splitlines(keepends=True)
    lines.reverse()
    return "".join(lines)


# Preprocessor combinations to try
all_preprocs: List[Tuple[bool, bool, bool]] = [\
    (False, False, False), # No preprocessors
    (True, False, False),  # Strip blank lines only
    (False, True, False),  # Relative indent only
    (True, True, False),   # Strip blank lines and relative indent
]

if __name__ == "__main__":
    # Test case for apply_diffs function
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye, World!")
"""

    # Added missing closing ``` for the diff block
    diff_content = """```diff
--- a/file.py
+++ b/file.py
@@ -1,5 +1,8 @@
 def hello():
-    print("Hello, World!")
+    print("Hello, Universe!")
+    print("How are you today?")

 def goodbye():
-    print("Goodbye, World!")
+    print("Farewell, Universe!")
+    print("See you next time!")