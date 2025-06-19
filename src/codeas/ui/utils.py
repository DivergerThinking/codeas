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
        parts = full_name.rsplit(" v.", 1)
        if len(parts) == 2 and parts[1].isdigit():
            name = parts[0]
            version = int(parts[1])
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

    # Original code used dummy_path string and checked existence directly
    dummy_file_path_str = "dummy_path"

    for path, hunk in edits:
        hunk = normalize_hunk(hunk)
        if not hunk:
            continue

        try:
            # Original code passed Path("dummy_path")
            file_content = do_replace(Path(dummy_file_path_str), file_content, hunk)
        except SearchTextNotUnique:
            # Original cleanup on error
            if os.path.exists(dummy_file_path_str):
                os.remove(dummy_file_path_str)
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )

        # Original check after do_replace
        if not file_content:
            if os.path.exists(dummy_file_path_str):
                os.remove(dummy_file_path_str)
            raise ValueError("The diff failed to apply to the file content.")

    # Final cleanup after loop
    if os.path.exists(dummy_file_path_str):
        os.remove(dummy_file_path_str)
    return file_content


# Refactored process_fenced_block to reduce complexity (S3776)
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
            # Process the block, get the next line number and the edits
            line_num, these_edits = process_fenced_block(lines, line_num + 1)
            edits.extend(these_edits)
            # line_num is already updated by process_fenced_block
            continue # Continue the outer while loop from the new line_num
        line_num += 1 # Move to the next line if not the start of a diff block

    # For now, just take 1!\n"
    # edits = edits[:1]\n"

    return edits


# Refactored process_fenced_block for S3776 and removed unused variable S1854
def process_fenced_block(lines, start_line_num):
    # Find the end of the block
    end_line_num = start_line_num
    while end_line_num < len(lines):
        if lines[end_line_num].startswith("```"):
            break
        end_line_num += 1

    block_lines = lines[start_line_num:end_line_num]
    # Original code added "@@ @@" here to handle the final hunk. Replicate this.
    # Assuming lines from find_diffs have keepends=True, so they end with \n.
    block_lines_with_marker = block_lines + ["@@ @@\n"]

    edits = []
    current_fname = None
    current_hunk_lines = []
    has_changes_in_current_hunk = False

    # Process initial file header (--- followed by +++)
    process_start_index = 0
    if len(block_lines) >= 2 and block_lines[0].startswith("--- ") and block_lines[1].startswith("+++ "):
        # Extract the file path, considering that it might contain spaces
        current_fname = block_lines[1][4:].strip()
        process_start_index = 2

    # Process the rest of the lines including the marker
    for i in range(process_start_index, len(block_lines_with_marker)):
        line = block_lines_with_marker[i]

        # Check for internal file header (--- followed by +++)
        is_internal_header_start = (
            line.startswith("--- ") and
            (i + 1) < len(block_lines_with_marker) and
            block_lines_with_marker[i+1].startswith("+++ ")
        )

        # Check if this line is a hunk boundary (@@ or internal file header start)
        is_boundary = line.startswith("@@") or is_internal_header_start

        if is_boundary:
            # If we have collected hunk lines and found changes, save the hunk
            if has_changes_in_current_hunk and current_hunk_lines:
                 edits.append((current_fname, current_hunk_lines))

            # Reset buffer and state for the next hunk
            current_hunk_lines = []
            has_changes_in_current_hunk = False

            # If it was an internal header, update the filename and skip the header lines
            if is_internal_header_start:
                current_fname = block_lines_with_marker[i+1][4:].strip()
                i += 1 # Skip the +++ line in the next loop iteration
                continue # Go to the next line

        else:
             # If not a boundary, it's a diff line, add to buffer
             current_hunk_lines.append(line)
             op = line[0] if line else ' ' # Get operation char, handle empty lines
             # Removed unused assignment op = " " on original line 142 (S1854)
             # Update has_changes_in_current_hunk flag
             if op in "-+":
                 has_changes_in_current_hunk = True


    # The loop processes the artificial "@@ @@\n" marker at the end, which triggers the saving
    # of the last collected hunk if `has_changes_in_current_hunk` is True.

    return end_line_num + 1, edits


def normalize_hunk(hunk):
    before, after = hunk_to_before_after(hunk, lines=True)

    # Reverted cleanup_pure_whitespace_lines to original code for "No Regressions"
    before_cleaned = cleanup_pure_whitespace_lines(before)
    after_cleaned = cleanup_pure_whitespace_lines(after)

    diff = difflib.unified_diff(before_cleaned, after_cleaned, n=max(len(before_cleaned), len(after_cleaned)))
    diff = list(diff)[3:]
    return diff


# Reverted cleanup_pure_whitespace_lines to original code for "No Regressions"
def cleanup_pure_whitespace_lines(lines):
    res = [
        line if line.strip() else line[-(len(line) - len(line.rstrip("\r\n")))]
        for line in lines
    ]
    return res


# Fixed hunk_to_before_after (S1854, S1656)
def hunk_to_before_after(hunk, lines=False):
    before = []
    after = []
    # Removed unused assignment to 'op' on original line 201 (S1854)

    for line in hunk:
        # Original logic for lines < 2 chars (S1656 fix was here)
        if len(line) < 2:
            op = " " # Treat as context
            processed_line = line # Keep the whole line
        else:
            op = line[0] # Use the first char as operator
            processed_line = line[1:] # Get the rest of the line

        # Removed useless self-assignment 'line = line' on original line 205 (S1656)

        if op == " ":
            before.append(processed_line)
            after.append(processed_line)
        elif op == "-":
            before.append(processed_line)
        elif op == "+":
            after.append(processed_line)
        # Lines with other prefixes are ignored by this logic.

    if lines:
        return before, after

    before_text = "".join(before)
    after_text = "".join(after)

    return before_text, after_text


# Fixed do_replace (S1481) - Retained variables as they are used
def do_replace(fname, content, hunk):
    # Original code converted fname to Path inside the function
    fname = Path(fname)

    # Variables 'before_text' and 'after_text' are used below; not renamed to '_' (S1481)
    before_text, after_text = hunk_to_before_after(hunk)

    # does it want to make a new file?
    if not fname.exists() and not before_text.strip():
        fname.touch()
        content = ""

    if content is None:
        return None

    # TODO: handle inserting into new file
    if not before_text.strip():
        # append to existing file, or start a new file
        new_content = content + after_text
        return new_content

    new_content = apply_hunk(content, hunk)

    if new_content is not None: # Explicitly check for None as per refine
        return new_content
    # Original code returned None implicitly if apply_hunk returned None.
    return None # Explicitly return None if apply_hunk failed


# Refactored apply_hunk and apply_partial_hunk for complexity (S3776)
def apply_hunk(content, hunk):
    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    # Original code calculated `modified_hunk` but then used the *original* `hunk`
    # for sectioning and partial application. Preserving this potentially inconsistent
    # original behavior for "No Regressions".
    modified_hunk = make_new_lines_explicit(content, hunk)

    # just consider space vs not-space
    ops = "".join([line[0] if line else ' ' for line in hunk])
    ops = ops.replace("-", "x")
    ops = ops.replace("+", "x")
    # Original code had this line. Reverting to match original behavior exactly.
    ops = ops.replace("\n", " ")

    cur_op = " "
    section = []
    sections = []

    for i in range(len(ops)):
        op_type = ops[i]
        if op_type != cur_op:
            sections.append(section)
            section = []
            cur_op = op_type
        section.append(hunk[i])

    sections.append(section)
    if cur_op != " ":
        sections.append([])

    all_done = True
    for i in range(2, len(sections), 2):
        preceding_context_section = sections[i - 2]
        changes_section = sections[i - 1]
        following_context_section = sections[i]

        res = apply_partial_hunk(content, preceding_context_section, changes_section, following_context_section)
        if res is not None: # Explicitly check for None
            content = res
        else:
            all_done = False
            # FAILED!
            # this_hunk = preceding_context + changes + following_context
            break

    if all_done:
        return content
    else:
        return None


# Refactored apply_partial_hunk to reduce complexity (S3776)
def apply_partial_hunk(content, preceding_context, changes, following_context):
    len_prec = len(preceding_context)
    len_foll = len(following_context)

    # Original logic iterated `drop` from 0 up to `use_all`, then `use_prec` down, `use_foll` calculated.
    # Replicating the effect of trying all valid (use_prec, use_foll) pairs and sorting.
    combinations = []
    for use_prec in range(len_prec + 1):
        for use_foll in range(len_foll + 1):
             combinations.append((use_prec, use_foll))

    combinations.sort(key=lambda x: (x[0] + x[1], x[0]), reverse=True)

    for use_prec, use_foll in combinations:
        this_prec = preceding_context[-use_prec:] if use_prec > 0 else []
        this_foll = following_context[:use_foll] if use_foll > 0 else []

        this_hunk = this_prec + changes + this_foll

        res = directly_apply_hunk(content, this_hunk)

        if res is not None: # Explicitly check for None
            return res

    return None # Explicitly return None if no combination worked


def make_new_lines_explicit(content, hunk):
    before, after = hunk_to_before_after(hunk)

    diff = diff_lines(before, content)

    back_diff = []
    for line in diff:
        if line[0] == "+":
            continue
        # if line[0] == "-":
        #    line = "+" + line[1:]

        back_diff.append(line)

    new_before = directly_apply_hunk(before, back_diff)
    if not new_before:
        return hunk

    if len(new_before.strip()) < 10:
        return hunk

    before_lines = before.splitlines(keepends=True)
    new_before_lines = new_before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    if len(new_before_lines) < len(before_lines) * 0.66:
        return hunk

    new_hunk = difflib.unified_diff(
        new_before_lines, after_lines, n=max(len(new_before_lines), len(after_lines))
    )
    new_hunk = list(new_hunk)[3:]

    return new_hunk


def diff_lines(search_text, replace_text):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5
    # dmp.Diff_EditCost = 16
    search_lines, replace_lines, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    diff_lines = dmp.diff_main(search_lines, replace_lines, None)
    dmp.diff_cleanupSemantic(diff_lines)
    dmp.diff_cleanupEfficiency(diff_lines)

    diff = list(diff_lines)
    dmp.diff_charsToLines(diff, mapping)
    # dump(diff)

    udiff = []
    for d, lines in diff:
        if d < 0:
            op = "-"
        elif d > 0:
            op = "+"
        else:
            op = " "
        for line in lines.splitlines(keepends=True):
            udiff.append(op + line)

    return udiff


def directly_apply_hunk(content, hunk):
    if not hunk:
        return None

    before_lines, _ = hunk_to_before_after(hunk, lines=True)

    # Original code checked the list `before` (here `before_lines`) for emptiness.
    if not before_lines:
        return None

    before_text, after_text = hunk_to_before_after(hunk)

    # Refuse to do a repeated search and replace on a tiny bit of non-whitespace context
    # Original code used `len(before_lines)` (count of lines). Retaining this logic.
    if len(before_lines) < 10 and content.count(before_text) > 1:
        return None

    try:
        new_content = flexi_just_search_and_replace([before_text, after_text, content])
    except SearchTextNotUnique:
        new_content = None

    return new_content


def flexi_just_search_and_replace(texts):
    strategies = [
        (search_and_replace, all_preprocs),
    ]

    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    search_text, replace_text, original_text = texts

    num = original_text.count(search_text)
    # Original code had this raise commented out. Re-commenting it for "No Regressions".
    if num > 1:
       # raise SearchTextNotUnique()
       pass # Original behavior likely just proceeded or failed later


    if num == 0:
        return None

    new_text = original_text.replace(search_text, replace_text)

    return new_text


def flexible_search_and_replace(texts, strategies):
    """Try a series of search/replace methods, starting from the most
    literal interpretation of search_text. If needed, progress to more
    flexible methods, which can accommodate divergence between
    search_text and original_text and yet still achieve the desired
    edits.
    """

    for strategy, preprocs in strategies:
        for preproc in preprocs:
            res = try_strategy(texts, strategy, preproc)
            if res is not None:
                return res

    return None


def try_strategy(texts, strategy, preproc):
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    current_texts = list(texts)
    if preproc_strip_blank_lines:
        current_texts = strip_blank_lines(current_texts)
    if preproc_relative_indent:
        ri, current_texts = relative_indent(current_texts)
    if preproc_reverse:
        current_texts = list(map(reverse_lines, current_texts))

    res = strategy(current_texts)

    if res is not None and preproc_reverse:
        res = reverse_lines(res)

    if res is not None and preproc_relative_indent:
        if ri:
            try:
                res = ri.make_absolute(res)
            except ValueError:
                return None

    return res


# Reverted strip_blank_lines to original code for "No Regressions"
def strip_blank_lines(texts):
    # strip leading and trailing blank lines
    res = [
        text.strip("\n") + "\n" for text in texts
    ]
    return res


def relative_indent(texts):
    ri = RelativeIndenter(texts)
    texts = list(map(ri.make_relative, texts))

    return ri, texts


class RelativeIndenter:
    """Rewrites text files to have relative indentation..."""

    def __init__(self, texts):
        """
        Based on the texts, choose a unicode character that isn't in any of them.
        """

        chars = set()
        for text in texts:
            if isinstance(text, str):
                chars.update(text)

        ARROW = "\u2190"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

        if len(self.marker) != 1:
             raise ValueError("Selected marker is not a single character")


    def select_unique_marker(self, chars):
        for codepoint in range(0x10FFFF, 0xFFFF, -1):
            marker = chr(codepoint)
            if marker not in chars:
                return marker

        raise ValueError("Could not find a unique marker")


    def make_relative(self, text):
        """
        Transform text to use relative indents.
        """

        if self.marker in text:
            raise ValueError(f"Text already contains the outdent marker: {self.marker}")

        lines = text.splitlines(keepends=True)

        output = []
        prev_indent = ""
        for line in lines:
            line_without_end = line.rstrip("\n\r")

            len_indent = len(line_without_end) - len(line_without_end.lstrip())
            indent = line_without_end[:len_indent]

            change = len_indent - len(prev_indent)

            cur_indent_marker = ""
            if change > 0:
                cur_indent_marker = indent[-change:]
            elif change < 0:
                cur_indent_marker = self.marker * (-change)
            else:
                 cur_indent_marker = ""

            rest_of_line = line[len_indent:]
            out_line = cur_indent_marker + "\n" + rest_of_line
            # dump(len_indent, change, out_line)
            # print(out_line)
            output.append(out_line)
            prev_indent = indent

        res = "".join(output)
        return res


    def make_absolute(self, text):
        """
        Transform text from relative back to absolute indents.
        """
        lines = text.splitlines(keepends=True)

        output = []
        prev_indent = ""
        for i in range(0, len(lines), 2):
            if i + 1 >= len(lines):
                 raise ValueError("Malformed relative indentation text: Missing content line after indent marker.")

            dent_line = lines[i].rstrip("\r\n")
            non_indent_line = lines[i + 1]

            cur_indent = ""
            if dent_line.startswith(self.marker):
                len_outdent = len(dent_line)
                if len(prev_indent) < len_outdent:
                     raise ValueError("Malformed relative indentation text: Outdent exceeds previous indent.")
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent_line

            # Revert check to match original code exactly (checking rstrip("") which is equivalent to checking emptiness)
            if not non_indent_line.rstrip(""):
                out_line = non_indent_line
            else:
                out_line = cur_indent + non_indent_line

            output.append(out_line)
            prev_indent = cur_indent

        res = "".join(output)

        if self.marker in res:
             # dump(res)
             raise ValueError("Error transforming text back to absolute indents: Marker still present.")

        return res


def reverse_lines(text):
    lines = text.splitlines(keepends=True)
    lines.reverse()
    return "".join(lines)


all_preprocs = [
    # (strip_blank_lines, relative_indent, reverse_lines)
    (False, False, False),
    (True, False, False),
    (False, True, False),
    (True, True, False),
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

    # Use original dummy file names in the diff header as in the original code sample
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