import difflib
import json
import os
from pathlib import Path

from diff_match_patch import diff_match_patch

PROMPTS_PATH = str(Path.home() / "codeas" / "prompts.json")


class SearchTextNotUnique(ValueError):
    pass


def read_prompts():
    try:
        if os.path.exists(PROMPTS_PATH):
            with open(PROMPTS_PATH, "r") as f:
                return json.load(f)
        else:
            return {}
    except json.JSONDecodeError as e:
        raise IOError(f"Failed to decode prompts file {PROMPTS_PATH}: {e}") from e
    except IOError as e:
         raise IOError(f"Failed to read prompts file {PROMPTS_PATH}: {e}") from e
    except Exception as e:
        raise IOError(f"An unexpected error occurred reading prompts file {PROMPTS_PATH}: {e}") from e


def save_existing_prompt(existing_name, new_name, new_prompt):
    prompts = read_prompts()
    prompts[new_name] = new_prompt
    if existing_name != new_name:
        prompts.pop(existing_name, None)
    try:
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f, indent=4)
    except IOError as e:
        raise IOError(f"Failed to write prompts file {PROMPTS_PATH}: {e}") from e
    except Exception as e:
        raise IOError(f"An unexpected error occurred writing prompts file {PROMPTS_PATH}: {e}") from e


def delete_saved_prompt(prompt_name):
    prompts = read_prompts()
    if prompts.pop(prompt_name, None) is not None:
        try:
            with open(PROMPTS_PATH, "w") as f:
                json.dump(prompts, f, indent=4)
        except IOError as e:
            raise IOError(f"Failed to write prompts file {PROMPTS_PATH}: {e}") from e
        except Exception as e:
            raise IOError(f"An unexpected error occurred writing prompts file {PROMPTS_PATH}: {e}") from e


def save_prompt(name, prompt):
    prompts = read_prompts()
    name_version_map = extract_name_version(prompts.keys())

    full_name = f"{name}"
    if full_name in name_version_map:
        full_name = f"{full_name} v.{name_version_map[full_name] + 1}"

    prompts[full_name] = prompt.strip()
    try:
        with open(PROMPTS_PATH, "w") as f:
            json.dump(prompts, f, indent=4)
    except IOError as e:
        raise IOError(f"Failed to write prompts file {PROMPTS_PATH}: {e}") from e
    except Exception as e:
        raise IOError(f"An unexpected error occurred writing prompts file {PROMPTS_PATH}: {e}") from e


def extract_name_version(existing_names):
    # names can be like {name} or {name} v.1 or {name} v.2 etc.
    name_version_map = {}
    for full_name in existing_names:
        if " v." in full_name:
            parts = full_name.rsplit(" v.", 1)
            name = parts[0]
            version_str = parts[1]
            try:
                version = int(version_str)
            except ValueError:
                version = 1
        else:
            name = full_name
            version = 1

        if name in name_version_map:
            name_version_map[name] = max(name_version_map[name], version)
        else:
            name_version_map[name] = version
    return name_version_map


def apply_diffs(file_content, diff_content):
    """Applies diff hunks from diff_content to file_content."""
    try:
        edits = list(find_diffs(diff_content))
    except ValueError as e:
        raise ValueError(f"Error parsing diff content: {e}") from e
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while parsing diff content: {e}") from e


    current_content = file_content

    for path, hunk in edits:
        try:
            normalized_hunk = normalize_hunk(hunk)
            if not normalized_hunk:
                continue

            result_content = do_replace(None, current_content, normalized_hunk)

            if result_content is None and normalized_hunk:
                 raise ValueError(f"Failed to apply hunk for path '{path or 'unknown'}'.")

            current_content = result_content

        except SearchTextNotUnique:
             raise ValueError(
                "The diff could not be applied uniquely to the file content."
             )
        except Exception as e:
             raise ValueError(f"An error occurred while applying hunk for path '{path or 'unknown'}': {e}") from e

    return current_content


def find_diffs(content):
    """Finds diff blocks (hunks) within the provided text content."""
    if not content.endswith("\n"):
        content = content + "\n"

    lines = content.splitlines(keepends=True)
    line_num = 0
    edits = []
    while line_num < len(lines):
        try:
            if line_num >= len(lines):
                 break

            line = lines[line_num]

            if line.startswith("```diff"):
                line_num, these_edits = process_fenced_block(lines, line_num + 1)
                edits += these_edits
                continue
            line_num += 1
        except Exception as e:
             raise ValueError(f"Error parsing diff content at line {line_num}: {e}") from e

    return edits


def process_fenced_block(lines, start_line_num):
    """Processes lines within a fenced diff block to extract hunks."""
    end_line_num = start_line_num
    while end_line_num < len(lines) and not lines[end_line_num].startswith("```"):
        end_line_num += 1

    block = lines[start_line_num:end_line_num]

    fname = None
    block_start_index = 0

    if len(block) >= 2 and block[0].startswith("--- ") and block[1].startswith("+++ "):
        fname = block[1][4:].strip()
        block_start_index = 2

    edits = []
    current_fname = fname
    current_hunk_start_index = block_start_index

    for i in range(block_start_index, len(block) + 1):
        line = block[i] if i < len(block) else "```"
        is_file_header = line.startswith("--- ") or line.startswith("+++ ")
        is_hunk_header = line.strip().startswith("@@")
        is_end_block = i == len(block)

        if is_file_header or is_hunk_header or is_end_block:
            hunk_body = block[current_hunk_start_index:i]

            has_changes_in_body = False
            for body_line in hunk_body:
                prefix = body_line[0] if len(body_line) > 0 else ' '
                if prefix in '-+':
                    has_changes_in_body = True
                    break

            if has_changes_in_body and current_fname is not None:
                 edits.append((current_fname, hunk_body))

            if line.startswith("+++ "):
                current_fname = line[4:].strip()

            current_hunk_start_index = i + 1

    return end_line_num + 1, edits


def normalize_hunk(hunk):
    """Normalizes a diff hunk to a consistent format."""
    try:
        before_lines, after_lines = hunk_to_before_after(hunk, lines=True)
    except Exception as e:
        raise ValueError(f"Error converting hunk lines to before/after: {e}") from e


    cleaned_before_lines = cleanup_pure_whitespace_lines(before_lines)
    cleaned_after_lines = cleanup_pure_whitespace_lines(after_lines)

    try:
        diff_generator = difflib.unified_diff(
            cleaned_before_lines, cleaned_after_lines, n=max(len(cleaned_before_lines), len(cleaned_after_lines))
        )
        normalized_diff_lines = list(diff_generator)[3:]
    except Exception as e:
        raise ValueError(f"Error generating normalized diff from hunk: {e}") from e

    return normalized_diff_lines


def cleanup_pure_whitespace_lines(lines):
    """Replaces lines containing only whitespace with just their line ending."""
    res = []
    for line in lines:
        if line.strip():
            res.append(line)
        else:
            ending_start_index = len(line.rstrip("\r\n"))
            res.append(line[ending_start_index:])
    return res


def hunk_to_before_after(hunk, lines=False):
    """Converts a list of diff hunk lines (+, -, space prefixes) into 'before' and 'after' text."""
    before = []
    after = []

    for line in hunk:
        current_op = line[0] if len(line) > 0 else " "
        line_content = line[1:] if len(line) else ""

        if current_op == " ":
            before.append(line_content)
            after.append(line_content)
        elif current_op == "-":
            before.append(line_content)
        elif current_op == "+":
            after.append(line_content)

    if lines:
        return before, after
    else:
        return "".join(before), "".join(after)


def do_replace(fname, content, hunk):
    """Applies a single normalized hunk to the file content."""
    _, _ = hunk_to_before_after(hunk)

    if content is None:
        pass

    before_text_for_check, after_text_for_append = hunk_to_before_after(hunk)
    if not before_text_for_check.strip():
        if content is None:
             new_content = after_text_for_append
        else:
             new_content = content + after_text_for_append
        return new_content

    new_content = apply_hunk(content, hunk)

    return new_content


def apply_hunk(content, hunk):
    """Attempts to apply a hunk to content using direct search/replace or flexible strategies."""
    _, _ = hunk_to_before_after(hunk)

    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    adjusted_hunk = make_new_lines_explicit(content, hunk)

    prefixes = [line[0] if len(line) > 0 else ' ' for line in adjusted_hunk]
    ops = "".join(prefixes)
    ops = ops.replace("-", "x").replace("+", "x")

    sections = []
    current_section_lines = []
    current_op_char = None

    for i in range(len(adjusted_hunk)):
        line = adjusted_hunk[i]
        op_char = ops[i] if i < len(ops) else ' '

        if current_op_char is None:
            current_op_char = op_char

        if op_char != current_op_char:
            sections.append(current_section_lines)
            current_section_lines = [line]
            current_op_char = op_char
        else:
            current_section_lines.append(line)

    if current_section_lines:
         sections.append(current_section_lines)

    if current_op_char != " ":
         sections.append([])

    all_segments_applied_successfully = True

    for i in range(2, len(sections), 2):
        preceding_context = sections[i - 2]
        changes = sections[i - 1]
        following_context = sections[i]

        res = apply_partial_hunk(content, preceding_context, changes, following_context)

        if res is not None:
            content = res
        else:
            all_segments_applied_successfully = False
            break

    if all_segments_applied_successful:
        return content
    else:
        return None


def make_new_lines_explicit(content, hunk):
    """
    Adjusts the hunk's 'before' context based on the actual file content
    and generates a new hunk if context differs but can be aligned.
    """
    before_text_hunk, _ = hunk_to_before_after(hunk)

    try:
        context_diff = diff_lines(before_text_hunk, content)
    except Exception as e:
        return hunk

    back_diff = []
    for line in context_diff:
        if line.startswith("+"):
            continue
        back_diff.append(line)

    new_before_text = directly_apply_hunk(before_text_hunk, back_diff)

    if new_before_text is None:
        return hunk

    before_lines_orig = before_text_hunk.splitlines(keepends=True)
    new_before_lines = new_before_text.splitlines(keepends=True)
    after_lines_orig = hunk_to_before_after(hunk, lines=True)[1]

    if len(new_before_text.strip()) < 10:
        return hunk

    if len(new_before_lines) < len(before_lines_orig) * 0.66:
         return hunk

    try:
        new_hunk_generator = difflib.unified_diff(
            new_before_lines, after_lines_orig, n=max(len(new_before_lines), len(after_lines_orig))
        )
        new_hunk_lines = list(new_hunk_generator)[3:]
    except Exception as e:
        return hunk


    return new_hunk_lines


def diff_lines(search_text, replace_text):
    """Computes a line-based diff between two strings using diff_match_patch."""
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5

    try:
        search_lines_chars, replace_lines_chars, mapping = dmp.diff_linesToChars(
            search_text, replace_text
        )
    except Exception as e:
         raise ValueError(f"Error during diff_linesToChars: {e}") from e


    try:
        diff_chars = dmp.diff_main(search_lines_chars, replace_lines_chars, False)
        dmp.diff_cleanupSemantic(diff_chars)
        dmp.diff_cleanupEfficiency(diff_chars)
    except Exception as e:
        raise ValueError(f"Error during diff_main or cleanup: {e}") from e


    try:
        diff = list(diff_chars)
        dmp.diff_charsToLines(diff, mapping)
    except Exception as e:
        raise ValueError(f"Error during diff_charsToLines: {e}") from e


    udiff_lines = []
    for d_type, lines_text in diff:
        if d_type < 0:
            d_char = "-"
        elif d_type > 0:
            d_char = "+"
        else:
            d_char = " "
        for line in lines_text.splitlines(keepends=True):
            udiff_lines.append(d_char + line)

    return udiff_lines


def apply_partial_hunk(content, preceding_context, changes, following_context):
    """
    Tries to apply a hunk segment with varying amounts of surrounding context
    to the content using `directly_apply_hunk`.
    Starts with full available context and gradually reduces context symmetrically or from one side.
    """
    len_prec = len(preceding_context)
    len_foll = len(following_context)

    for total_context_use in range(len_prec + len_foll, -1, -1):
        min_use_prec = max(0, total_context_use - len_foll)
        max_use_prec = min(len_prec, total_context_use)
        inner_range_stop = min_use_prec - 1

        for use_prec in range(max_use_prec, inner_range_stop, -1):
            use_foll = total_context_use - use_prec

            this_prec = preceding_context[-use_prec:] if use_prec > 0 else []
            this_foll = following_context[:use_foll] if use_foll > 0 else []

            hunk_subset = this_prec + changes + this_foll

            if not hunk_subset:
                continue

            res = directly_apply_hunk(content, hunk_subset)

            if res is not None:
                return res

    return None


def directly_apply_hunk(content, hunk):
    """
    Attempts to apply a hunk by directly searching for its 'before' text and
    replacing it with the 'after' text using flexible strategies.
    Includes a heuristic check for ambiguous short contexts.
    """
    try:
        before_text, after_text = hunk_to_before_after(hunk)
    except Exception as e:
         return None


    if not before_text:
        return None

    try:
        before_lines_orig = hunk_to_before_after(hunk, lines=True)[0]
        before_lines_stripped = "".join([line.strip() for line in before_lines_orig])

        num_occurrences = content.count(before_text) if content is not None else 0


        if len(before_lines_stripped) < 10 and num_occurrences > 1:
            return None

    except Exception as e:
        return None


    try:
        new_content = flexi_just_search_and_replace([before_text, after_text, content])
    except SearchTextNotUnique:
        new_content = None
    except Exception as e:
        new_content = None


    return new_content


def flexi_just_search_and_replace(texts):
    """
    Applies search and replace strategies with various preprocessing steps.
    This function defines which strategies and preprocessors are attempted.
    """
    strategies = [
        (search_and_replace, all_preprocs),
    ]

    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    """Basic search and replace strategy: finds search_text and replaces all occurrences with replace_text."""
    search_text, replace_text, original_text = texts

    if not search_text:
         return None

    try:
        num = original_text.count(search_text) if original_text is not None else 0
    except Exception:
         return None

    if num == 0:
        return None

    try:
        if original_text is None:
             new_text = replace_text if not search_text else None
        else:
             new_text = original_text.replace(search_text, replace_text)
    except Exception:
         return None


    return new_text


def flexible_search_and_replace(texts, strategies):
    """
    Iterates through provided strategies and preprocessing combinations,
    attempting to apply each one until a successful result is obtained.
    """
    for strategy, preprocs in strategies:
        for preproc in preprocs:
            res = try_strategy(texts, strategy, preproc)
            if res is not None:
                return res

    return None


def try_strategy(texts, strategy, preproc):
    """Applies a specific search/replace strategy with a given preprocessing step and reverses preprocessing on success."""
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    processed_texts = list(texts)

    try:
        if preproc_strip_blank_lines:
            processed_texts = strip_blank_lines(processed_texts)
        if preproc_relative_indent:
            ri, processed_texts = relative_indent(processed_texts)
        if preproc_reverse:
            processed_texts = list(map(reverse_lines, processed_texts))
    except ValueError as e:
        return None
    except Exception as e:
        return None


    res = strategy(processed_texts)

    if res is not None:
        try:
            if preproc_reverse:
                res = reverse_lines(res)
            if preproc_relative_indent:
                res = ri.make_absolute(res)
        except ValueError as e:
            return None
        except Exception as e:
             return None


    return res


def strip_blank_lines(texts):
    """Strips leading and trailing blank lines from each text in the input list."""
    texts_stripped = []
    for text in texts:
        if text is None:
             texts_stripped.append(None)
        else:
             texts_stripped.append(text.strip("\n") + "\n")
    return texts_stripped


def relative_indent(texts):
    """Calculates relative indentation based on input texts and transforms texts to use relative indents."""
    ri = RelativeIndenter(texts)
    texts_relative = []
    for text in texts:
        if text is None:
             texts_relative.append(None)
        else:
             texts_relative.append(ri.make_relative(text))

    return ri, texts_relative


class RelativeIndenter:
    """Rewrites text files to have relative indentation format and converts back."""

    def __init__(self, texts):
        """
        Initializes the indenter and chooses a unique unicode marker character
        not present in the input texts. Raises ValueError if no unique marker is found.
        """
        chars = set()
        for text in texts:
            if text is not None:
                chars.update(text)

        ARROW = "\u2190"

        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars):
        """Finds a unicode character not present in the given set of chars."""
        for codepoint in range(0x10FFFF, 0x10000, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker

        raise ValueError("Could not find a unique marker")

    def make_relative(self, text):
        """
        Transforms a text block to use relative indentation markers.
        Raises ValueError if the marker is unexpectedly found in the text.
        """
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
            else:
                cur_indent_marker = ""

            out_line = cur_indent_marker + "\n" + line[len_indent:]

            output.append(out_line)

            prev_indent = indent

        res = "".join(output)
        return res

    def make_absolute(self, text):
        """
        Transforms text from the relative indentation format back to absolute indents.
        This reverses the process performed by `make_relative`.
        Raises ValueError if the input format is incorrect or the marker is found
        unexpectedly in the final result.
        """
        lines = text.splitlines(keepends=True)

        output = []
        prev_indent = ""

        if len(lines) % 2 != 0:
             raise ValueError("Input text for make_absolute has an odd number of lines, expected pairs of lines.")

        for i in range(0, len(lines), 2):
            dent_line = lines[i]
            non_indent_line = lines[i + 1]

            dent = dent_line.rstrip("\n\r")

            cur_indent = ""
            if dent.startswith(self.marker):
                len_outdent = len(dent)
                if len(prev_indent) < len_outdent:
                     raise ValueError(f"Cannot outdent by {len_outdent} spaces from previous indent of {len(prev_indent)} spaces.")
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent

            out_line = ""
            if not non_indent_line.rstrip("\n\r"):
                out_line = non_indent_line
            else:
                out_line = cur_indent + non_indent_line

            output.append(out_line)

            prev_indent = cur_indent

        res = "".join(output)

        if self.marker in res:
            raise ValueError("Error transforming text back to absolute indents: marker found in result.")

        return res


def reverse_lines(text):
    """Reverses the order of lines in a text block."""
    if text is None:
        return None
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
--- a/original
+++ b/modified
@@ -1,5 +1,8 @@
 def hello():
-    print("Hello, World!")
+    print("Hello, Universe!")
+    print("How are you today?")

 def goodbye():
-    print("Goodbye, World!")
+    print("Farewell, Universe!")
+    print("See you next time!")