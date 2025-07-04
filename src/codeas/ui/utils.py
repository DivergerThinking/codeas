import difflib
import json
import os
from pathlib import Path

from diff_match_patch import diff_match_patch

PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    """Custom exception raised when search text for applying diffs is not unique."""
    pass


def read_prompts():
    """Reads prompts from the prompts.json file."""
    if os.path.exists(PROMPTS_PATH):
        try:
            with open(PROMPTS_PATH, "r") as f:
                content = f.read()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}
        except Exception:
             return {}
    else:
        return {}


def save_existing_prompt(existing_name, new_name, new_prompt):
    """Saves an edited prompt, potentially changing its name."""
    prompts = read_prompts()
    prompts[new_name] = new_prompt
    if existing_name != new_name:
        if existing_name in prompts:
             del prompts[existing_name]
    try:
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f, indent=4)
    except Exception:
         pass


def delete_saved_prompt(prompt_name):
    """Deletes a saved prompt by name."""
    prompts = read_prompts()
    if prompt_name in prompts:
        del prompts[prompt_name]
        try:
            with open(PROMPTS_PATH, "w") as f:
                json.dump(prompts, f, indent=4)
        except Exception:
            pass
    else:
        pass


def save_prompt(name, prompt):
    """Saves a new prompt, handling versioning if a prompt with the same name exists."""
    prompts = read_prompts()
    name_version_map = extract_name_version(prompts.keys())

    full_name = name
    if full_name in name_version_map:
        full_name = f"{full_name} v.{name_version_map[full_name] + 1}"

    prompts[full_name] = prompt.strip()
    try:
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f, indent=4)
    except Exception:
         pass


def extract_name_version(existing_names):
    """
    Extracts base name and highest version number from existing prompt names.
    Names can be like {name} or {name} v.1, {name} v.2 etc.
    """
    name_version_map = {}
    for full_name in existing_names:
        if " v." in full_name:
            parts = full_name.rsplit(" v.", 1)
            if len(parts) == 2:
                 name, version_str = parts
                 try:
                    version = int(version_str)
                 except ValueError:
                    name = full_name
                    version = 1
            else:
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


# Helper function for process_fenced_block
def _handle_boundary_logic(edits, current_fname, current_hunk_lines, hunk_contains_changes, line, lines_to_parse, parse_idx, is_hunk_start, is_file_header_start, in_hunk):
    """Handles the logic when a boundary line (@@ or ---/+++) is encountered."""
    if in_hunk and current_hunk_lines:
        if hunk_contains_changes:
             edits.append((current_fname, current_hunk_lines))

    new_hunk_lines = []
    new_in_hunk = False
    new_hunk_contains_changes = False
    next_parse_idx_increment = 1

    new_current_fname = current_fname

    if is_hunk_start:
        new_in_hunk = True
        next_parse_idx_increment = 1
    elif is_file_header_start:
         new_current_fname = lines_to_parse[parse_idx + 1][4:].strip()
         new_in_hunk = False
         next_parse_idx_increment = 2

    return parse_idx + next_parse_idx_increment, new_in_hunk, new_hunk_contains_changes, new_current_fname, new_hunk_lines


# Refactored process_fenced_block for complexity (S3776)
# Original Cognitive Complexity: 22
def process_fenced_block(lines, start_line_num):
    """
    Parses a fenced diff block (lines between ```diff and ```) to extract hunks.
    Handles initial file headers and internal file headers (multi-file diffs).
    Returns the line number after the block and a list of edits (fname, hunk_lines).
    """
    end_line_num = start_line_num
    for i in range(start_line_num, len(lines)):
        line = lines[i]
        if line.strip() == "```":
            end_line_num = i
            break
    else:
        end_line_num = len(lines)

    block_lines = lines[start_line_num:end_line_num]

    edits = []
    current_fname = None

    lines_to_parse = block_lines

    parse_idx = 0
    if len(lines_to_parse) >= 2 and lines_to_parse[0].strip().startswith("---") and lines_to_parse[1].strip().startswith("+++"):
         current_fname = lines_to_parse[1][4:].strip()
         parse_idx = 2

    current_hunk_lines = []
    in_hunk = False
    hunk_contains_changes = False

    while parse_idx < len(lines_to_parse):
        line = lines_to_parse[parse_idx]

        is_hunk_start = line.startswith("@@")
        is_file_header_start = False
        if parse_idx + 1 < len(lines_to_parse):
             is_file_header_start = (lines_to_parse[parse_idx].strip().startswith("---") and
                                      lines_to_parse[parse_idx + 1].strip().startswith("+++"))

        is_boundary = is_hunk_start or is_file_header_start

        if is_boundary:
            parse_idx, in_hunk, hunk_contains_changes, current_fname, current_hunk_lines = _handle_boundary_logic(
                edits, current_fname, current_hunk_lines, hunk_contains_changes, line, lines_to_parse, parse_idx, is_hunk_start, is_file_header_start, in_hunk
            )
            continue


        if in_hunk:
            current_hunk_lines.append(line)
            if line.startswith("+") or line.startswith("-"):
                hunk_contains_changes = True

        parse_idx += 1

    if in_hunk and current_hunk_lines and hunk_contains_changes:
         edits.append((current_fname, current_hunk_lines))


    end_line_num_in_orig = start_line_num + (end_line_num - start_line_num)
    return end_line_num_in_orig + 1, edits


def find_diffs(content):
    """
    Finds and parses fenced diff blocks (lines between ```diff and ```) within content.
    Returns a list of edits found across all blocks.
    """
    if not content.endswith("\n"):
        content = content + "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits = []
    while line_num < len(lines):
        line = lines[line_num]
        if line.strip() == "```diff":
            next_line_num, these_edits = process_fenced_block(lines, line_num + 1)
            edits.extend(these_edits)
            line_num = next_line_num
            continue
        line_num += 1

    return edits


def normalize_hunk(hunk):
    """
    Normalizes a hunk by regenerating it using difflib after cleaning whitespace.
    This helps standardize hunk format for application.
    Returns a list of lines representing the normalized hunk, or None if hunk is empty.
    """
    if not hunk:
        return None

    before, after = hunk_to_before_after(hunk, lines=True)

    before = cleanup_pure_whitespace_lines(before)
    after = cleanup_pure_whitespace_lines(after)

    diff = difflib.unified_diff(before, after, n=max(len(before), len(after)))
    diff = list(diff)[3:]

    if not diff:
         return None

    return diff


def cleanup_pure_whitespace_lines(lines):
    """
    Standardizes lines that contain only whitespace.
    Replaces a line consisting only of whitespace with just its newline characters.
    e.g., "   \\n" becomes "\\n".
    """
    res = [
        line if line.strip() else line[-(len(line) - len(line.rstrip("\r\n"))):]
        for line in lines
    ]
    return res


def hunk_to_before_after(hunk, lines=False):
    """
    Separates lines in a hunk into 'before' and 'after' content based on +/-/space prefixes.
    Handles lines that might not have a standard prefix.

    Args:
        hunk (list[str]): List of lines in the hunk, including prefixes.
        lines (bool): If True, return lists of lines; otherwise, return joined strings.

    Returns:
        tuple[list[str], list[str]] or tuple[str, str]: The before and after content.
    """
    before = []
    after = []
    for line in hunk:
        if not line or len(line) < 2:
            op = " "
            processed_line = line
        elif line[0] in (" ", "-", "+", "\\"):
            op = line[0]
            processed_line = line[1:]
        else:
             op = " "
             processed_line = line

        if op == " ":
            before.append(processed_line)
            after.append(processed_line)
        elif op == "-":
            before.append(processed_line)
        elif op == "+":
            after.append(processed_line)

    if lines:
        return before, after

    before = "".join(before)
    after = "".join(after)

    return before, after


def apply_diffs(file_content, diff_content):
    """Applies diff hunks found in diff_content to file_content string."""
    edits = list(find_diffs(diff_content))

    for path, hunk in edits:
        hunk = normalize_hunk(hunk)
        if not hunk:
            continue

        try:
            file_content = do_replace(None, file_content, hunk)
        except SearchTextNotUnique:
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )

        if file_content is None:
            raise ValueError("The diff failed to apply to the file content.")

    return file_content


def do_replace(fname, content, hunk):
    """
    Applies a hunk to the content string.
    Handles simple append/insert cases and delegates complex replacements to apply_hunk.
    Returns the modified content string or None if the hunk cannot be applied.

    Args:
        fname: The filename from the diff header (unused in string-based application).
        content (str): The original content string to modify.
        hunk (list[str]): The list of lines representing the hunk.

    Returns:
        str or None: The content string after applying the hunk, or None on failure.
    """
    before_text, after_text = hunk_to_before_after(hunk)

    if not before_text.strip():
        new_content = content + after_text
        return new_content

    new_content = apply_hunk(content, hunk)
    if new_content is not None:
        return new_content


def apply_hunk(content, hunk):
    """
    Attempts to apply a hunk to the content string using different search and replacement strategies.
    Returns the modified content string or None on failure.

    Args:
        content (str): The content string to modify.
        hunk (list[str]): The list of lines representing the hunk.

    Returns:
        str or None: The content string after applying the hunk, or None if application fails.
    """
    _, _ = hunk_to_before_after(hunk)

    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    hunk_explicit_newlines = make_new_lines_explicit(content, hunk)

    res_explicit = directly_apply_hunk(content, hunk_explicit_newlines)
    if res_explicit is not None:
         return res_explicit

    return None


def make_new_lines_explicit(content, hunk):
    """
    Creates a new hunk by adjusting the 'before' part of the original hunk
    to better match the line endings/whitespace of the actual content.
    This is a preparation step for applying hunks that might not match content exactly.
    Returns the adjusted hunk (list of lines) or the original hunk if adjustment fails/is insignificant.
    """
    before, after = hunk_to_before_after(hunk)

    diff = diff_lines(before, content)

    back_diff = []
    for line in diff:
        if line.startswith(" ") or line.startswith("-"):
             back_diff.append(line)

    new_before = directly_apply_hunk(before, back_diff)

    if new_before is None or len(str(new_before).strip()) < 10:
        return hunk

    before_lines = before.splitlines(keepends=True)
    new_before_lines = str(new_before).splitlines(keepends=True)

    if len(new_before_lines) < len(before_lines) * 0.66:
        return hunk

    after_lines = after.splitlines(keepends=True)
    new_hunk_lines = difflib.unified_diff(
        new_before_lines, after_lines, n=max(len(new_before_lines), len(after_lines))
    )
    new_hunk = list(new_hunk_lines)[3:]

    if not new_hunk:
        return hunk

    return new_hunk


def diff_lines(search_text, replace_text):
    """
    Generates a diff between two strings, treating each line as a distinct element.
    Uses diff_match_patch library for line-based differencing.
    Returns a list of lines prefixed with standard diff characters (+, -, ' ').
    """
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5

    search_lines_chars, replace_lines_chars, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    diff_results = dmp.diff_main(search_lines_chars, replace_lines_chars, False)

    dmp.diff_cleanupSemantic(diff_results)
    dmp.diff_cleanupEfficiency(diff_results)

    diff = list(diff_results)

    dmp.diff_charsToLines(diff, mapping)

    udiff = []
    for op_type, lines_string in diff:
        if op_type < 0:
            d_char = "-"
        elif op_type > 0:
            d_char = "+"
        else:
            d_char = " "
        for line in lines_string.splitlines(keepends=True):
            udiff.append(d_char + line)

    return udiff


# Helper function for apply_partial_hunk
def _get_context_slice(context, num_lines, from_end=True):
    """Helper to safely get a slice of context lines."""
    if num_lines <= 0 or not context:
        return []

    num_lines = min(num_lines, len(context))

    if from_end:
        return context[-num_lines:]
    else:
        return context[:num_lines]


def apply_partial_hunk(content, preceding_context, changes, following_context):
    """
    Attempts to apply a hunk using partial context lines.
    It tries different combinations of preceding and following context lines
    from the available context sections.
    Returns modified content or None on failure.

    Args:
        content (str): The content string to modify.
        preceding_context (list[str]): Lines from the original content just before the hunk's 'before' section.
        changes (list[str]): Lines representing the changes section of the hunk (+/- lines).
        following_context (list[str]): Lines from the original content just after the hunk's 'before' section.

    Returns:
        str or None: The content string after applying a successful partial hunk, or None if no partial hunk applies.
    """
    len_prec = len(preceding_context)
    len_foll = len(following_context)

    for use_prec in range(len_prec, -1, -1):
        for use_foll in range(len_foll, -1, -1):
               this_prec = _get_context_slice(preceding_context, use_prec, from_end=True)
               this_foll = _get_context_slice(following_context, use_foll, from_end=False)

               partial_hunk_lines = this_prec + changes + this_foll
               res = directly_apply_hunk(content, partial_hunk_lines)

               if res is not None:
                   return res

    return None


def directly_apply_hunk(content, hunk):
    """
    Attempts to apply a hunk by directly searching for the hunk's 'before'
    text in the content and replacing it with the hunk's 'after' text.
    Includes a heuristic to prevent applying trivial changes on short,
    repeated context strings, which could lead to unintended replacements.
    Returns the modified content string or None on failure (e.g., 'before' text not found uniquely).

    Args:
        content (str): The content string to modify.
        hunk (list[str]): The list of lines representing the hunk.

    Returns:
        str or None: The content string after application, or None on failure.
    """
    before, after = hunk_to_before_after(hunk)

    if not before:
        return None

    before_lines_list, _ = hunk_to_before_after(hunk, lines=True)
    before_stripped_content = "".join(before_lines_list).strip()

    if len(before_stripped_content) < 10 and content.count(before) > 1:
        return None

    try:
        new_content = flexi_just_search_and_replace([before, after, content])

        return new_content

    except Exception:
         return None


def flexi_just_search_and_replace(texts):
    """
    Applies the basic search_and_replace strategy combined with various preprocessor permutations.
    This provides robustness against minor differences in indentation or blank lines.
    Returns the modified text using the first successful combination, or None if all fail.

    Args:
        texts (list[str]): A list containing [search_text, replace_text, original_text].

    Returns:
        str or None: The modified text or None if no combination succeeds.
    """
    strategies = [
        (search_and_replace, all_preprocs),
    ]

    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    """
    Performs a simple string search and replace.
    Returns modified text if the search_text is found, None otherwise.
    Note: This function replaces ALL occurrences of search_text if multiple exist.
    Higher-level logic (like directly_apply_hunk's heuristic) handles uniqueness concerns.

    Args:
        texts (list[str]): A list containing [search_text, replace_text, original_text].

    Returns:
        str or None: The modified text string if search_text is found, None otherwise.
    """
    search_text, replace_text, original_text = texts

    num = original_text.count(search_text)

    if num == 0:
        return None

    new_text = original_text.replace(search_text, replace_text)

    return new_text


def flexible_search_and_replace(texts, strategies):
    """Try a series of search/replace methods, starting from the most
    literal interpretation of search_text. If needed, progress to more
    flexible methods, which can accommodate divergence between
    search_text and original_text and yet still achieve the desired
    edits."""

    for strategy, preprocs in strategies:
        for preproc in preprocs:
            res = try_strategy(texts, strategy, preproc)
            if res is not None:
                return res

    return None


def try_strategy(texts, strategy, preproc):
    """
    Applies specified preprocessors to texts, then runs the strategy, then applies post-processors.
    Catches any exceptions raised during the process (preproc, strategy, post-proc) and returns None.

    Args:
        texts (list[str]): A list containing [search_text, replace_text, original_text].
        strategy (function): The core search/replace function to apply.
        preproc (tuple): A tuple specifying which preprocessors to apply (strip_blank_lines, relative_indent, reverse_lines).

    Returns:
        str or None: The modified text string if the process completes successfully, or None if an exception occurs or the strategy fails.
    """
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    current_texts = list(texts)

    try:
        if preproc_strip_blank_lines:
            current_texts = strip_blank_lines(current_texts)
        if preproc_relative_indent:
            ri, current_texts = relative_indent(current_texts)
        if preproc_reverse:
            current_texts = list(map(reverse_lines, current_texts))

        res = strategy(current_texts)

        if res is not None:
             if preproc_reverse:
                 res = reverse_lines(res)

             if preproc_relative_indent:
                 res = ri.make_absolute(res)

        return res

    except Exception:
         return None


def strip_blank_lines(texts):
    res_texts = [text.strip("\n") + "\n" if text else "" for text in texts]
    return res_texts


def relative_indent(texts):
    ri = RelativeIndenter(texts)
    res_texts = list(map(ri.make_relative, texts))

    return ri, res_texts


class RelativeIndenter:
    """Rewrites text files to have relative indentation, which involves
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
        chars = set()
        for text in texts:
            if text:
                 chars.update(text)

        ARROW = "\u2190"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars):
        for codepoint in range(0x10FFFF, 0x10000, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker

        raise ValueError("Could not find a unique marker within the search range.")


    def make_relative(self, text):
        if not text: return ""

        if self.marker in text:
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)

        output = []
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

            out_line = cur_indent_marker + "\n" + line[len_indent:]

            output.append(out_line)
            prev_indent = indent

        res = "".join(output)
        return res

    def make_absolute(self, text):
        if not text: return ""

        lines = text.splitlines(keepends=True)

        if len(lines) % 2 != 0:
             raise ValueError("Input text has odd number of lines, expected pairs of relative indent marker and content.")

        output = []
        prev_indent = ""
        for i in range(0, len(lines), 2):
            dent_line = lines[i]
            non_indent_line = lines[i + 1]

            dent = dent_line.rstrip("\r\n")

            cur_indent = ""
            if dent.startswith(self.marker):
                len_outdent = len(dent)
                if len(prev_indent) < len_outdent:
                    raise ValueError(f"Cannot outdent {len_outdent} columns from current indent level {len(prev_indent)}. Input segment: '{dent_line.strip()}'")
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent

            if not non_indent_line.strip():
                out_line = non_indent_line
            else:
                out_line = cur_indent + non_indent_line

            output.append(out_line)
            prev_indent = cur_indent

        res = "".join(output)
        if self.marker in res:
            raise ValueError("Error transforming text back to absolute indents: marker still present after conversion.")

        return res


def reverse_lines(text):
    if not text: return ""

    lines = text.splitlines(keepends=True)
    lines.reverse()
    return "".join(lines)


all_preprocs = [
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, False),
]

if __name__ == "__main__":
    original_content = """def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye, World!")
"""

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
     print("See you next time!")