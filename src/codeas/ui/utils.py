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
    MAX_DIFF_SIZE_BYTES = 10 * 1024 * 1024 # Limit size of diff_content to prevent potential DoS
    if len(diff_content.encode('utf-8')) > MAX_DIFF_SIZE_BYTES:
        raise ValueError(f"Diff content exceeds maximum allowed size ({MAX_DIFF_SIZE_BYTES} bytes). Processing aborted.")

    edits = list(find_diffs(diff_content))

    for path, hunk in edits:
        hunk = normalize_hunk(hunk)
        if not hunk:
            continue

        try:
            file_content = do_replace(Path("dummy_path"), file_content, hunk)
        except SearchTextNotUnique:
            if os.path.exists("dummy_path"):
                os.remove("dummy_path")
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )

        if file_content is None:
            if os.path.exists("dummy_path"):
                os.remove("dummy_path")
            raise ValueError("The diff failed to apply to the file content.")

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
    end_line_num = start_line_num
    for end_line_num in range(start_line_num, len(lines)):
        line = lines[end_line_num]
        if line.startswith("```"):
            break
    else:
         end_line_num = len(lines)

    block = lines[start_line_num:end_line_num]

    fname = None
    block_start_index = 0
    if block and len(block) > 1 and block[0].startswith("--- ") and block[1].startswith("+++ "):
        fname = block[1][4:].strip()
        block_start_index = 2

    edits = []
    hunk = []
    current_fname = fname
    has_changes_in_hunk = False

    i = block_start_index
    while i < len(block):
        line = block[i]

        if line.startswith("--- ") and i + 1 < len(block) and block[i + 1].startswith("+++ "):
            if hunk and has_changes_in_hunk:
                 edits.append((current_fname, hunk))
            hunk = []
            has_changes_in_hunk = False
            current_fname = block[i + 1][4:].strip()
            i += 2
            continue

        if line.startswith("@@"):
            if hunk and has_changes_in_hunk:
                 edits.append((current_fname, hunk))
            hunk = [line]
            has_changes_in_hunk = False
            i += 1
            continue

        if line.startswith(("-", "+")):
             has_changes_in_hunk = True

        hunk.append(line)
        i += 1

    if hunk and has_changes_in_hunk:
         edits.append((current_fname, hunk))

    return end_line_num + 1, edits


def normalize_hunk(hunk):
    before, after = hunk_to_before_after(hunk, lines=True)

    before = cleanup_pure_whitespace_lines(before)
    after = cleanup_pure_whitespace_lines(after)

    diff = difflib.unified_diff(before, after, n=max(len(before), len(after)))
    diff = list(diff)[3:]
    return diff


def cleanup_pure_whitespace_lines(lines):
    res = [
        line if line.strip() else line[-(len(line) - len(line.rstrip("\r\n")))]
        for line in lines
    ]
    return res


def hunk_to_before_after(hunk, lines=False):
    before = []
    after = []
    for line in hunk:
        op = line[0] if line else ' '
        content_part = line[1:] if len(line) > 0 else ''

        if op == " ":
            before.append(content_part)
            after.append(content_part)
        elif op == "-":
            before.append(content_part)
        elif op == "+":
            after.append(content_part)

    if lines:
        return before, after

    before = "".join(before)
    after = "".join(after)

    return before, after


def do_replace(fname, content, hunk):
    fname = Path(fname)

    before_text, after_text = hunk_to_before_after(hunk)

    if not fname.exists() and not before_text.strip():
        fname.touch()
        content = ""

    if content is None:
        return None

    if not before_text.strip():
        new_content = content + after_text
        return new_content

    new_content = apply_hunk(content, hunk)
    if new_content is not None:
        return new_content

    return None


def apply_hunk(content, hunk):
    _, _ = hunk_to_before_after(hunk)

    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    hunk = make_new_lines_explicit(content, hunk)

    ops = "".join([line[0] for line in hunk if len(line) > 0])
    ops = ops.replace("-", "x")
    ops = ops.replace("+", "x")

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

    all_done = True
    for i in range(2, len(sections), 2):
        preceding_context = sections[i - 2]
        changes = sections[i - 1]
        following_context = sections[i]

        res = apply_partial_hunk(content, preceding_context, changes, following_context)
        if res is not None:
            content = res
        else:
            all_done = False
            break

    if all_done:
        return content
    else:
        return None


def make_new_lines_explicit(content, hunk):
    before, after = hunk_to_before_after(hunk)

    diff = diff_lines(before, content)

    back_diff = []
    for line in diff:
        if line[0] == "+":
            continue

        back_diff.append(line)

    new_before = directly_apply_hunk(before, back_diff)
    if new_before is None:
        return hunk

    if len(new_before.strip()) < 10:
        return hunk

    before = before.splitlines(keepends=True)
    new_before = new_before.splitlines(keepends=True)
    after = after.splitlines(keepends=True)

    if len(new_before) < len(before) * 0.66:
        return hunk

    new_hunk = difflib.unified_diff(
        new_before, after, n=max(len(new_before), len(after))
    )
    new_hunk = list(new_hunk)[3:]

    return new_hunk


def diff_lines(search_text, replace_text):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5
    search_lines, replace_lines, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    diff_lines = dmp.diff_main(search_lines, replace_lines, None)
    dmp.diff_cleanupSemantic(diff_lines)
    dmp.diff_cleanupEfficiency(diff_lines)

    diff = list(diff_lines)
    dmp.diff_charsToLines(diff, mapping)

    udiff = []
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


def _try_partial_context(content, preceding_context, changes, following_context, use_prec, use_foll):
    if use_prec:
        this_prec = preceding_context[-use_prec:]
    else:
        this_prec = []

    this_foll = following_context[:use_foll]

    res = directly_apply_hunk(content, this_prec + changes + this_foll)
    return res


def apply_partial_hunk(content, preceding_context, changes, following_context):
    len_prec = len(preceding_context)
    len_foll = len(following_context)

    use_all = len_prec + len_foll

    for drop in range(use_all + 1):
        use = use_all - drop

        for use_prec in range(len_prec, -1, -1):
            use_foll = use - use_prec

            if use_prec <= len_prec and use_foll <= len_foll:
                res = _try_partial_context(content, preceding_context, changes, following_context, use_prec, use_foll)
                if res is not None:
                    return res
    return None


def directly_apply_hunk(content, hunk):
    before, after = hunk_to_before_after(hunk)

    if not before:
        return None

    before_lines, _ = hunk_to_before_after(hunk, lines=True)
    before_lines_stripped = "".join([line.strip() for line in before_lines])

    if len(before_lines_stripped) < 10 and content.count(before) > 1:
        return None

    try:
        new_content = flexi_just_search_and_replace([before, after, content])
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
    # if num > 1:
    #    raise SearchTextNotUnique()
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
            try:
                res = try_strategy(texts, strategy, preproc)
                if res is not None:
                    return res
            except ValueError:
                 pass

    return None


def try_strategy(texts, strategy, preproc):
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None
    processed_texts = list(texts)

    if preproc_strip_blank_lines:
        processed_texts = strip_blank_lines(processed_texts)
    if preproc_relative_indent:
        ri, processed_texts = relative_indent(processed_texts)
    if preproc_reverse:
        processed_texts = list(map(reverse_lines, processed_texts))

    res = strategy(processed_texts)

    if res is not None and preproc_reverse:
        res = reverse_lines(res)

    if res is not None and preproc_relative_indent:
        res = ri.make_absolute(res)

    return res


def strip_blank_lines(texts):
    # strip leading and trailing blank lines
    texts = [text.strip("\n") + "\n" for text in texts]
    return texts


def relative_indent(texts):
    ri = RelativeIndenter(texts)
    texts = list(map(ri.make_relative, texts))

    return ri, texts


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
        """
        Based on the texts, choose a unicode character that isn't in any of them.
        """

        chars = set()
        for text in texts:
            chars.update(text)

        ARROW = "←"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars):
        for codepoint in range(0x10FFFF, 0x10000, -1):
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
            indent = line[:len_indent]
            change = len_indent - len(prev_indent)
            if change > 0:
                cur_indent = indent[-change:]
            elif change < 0:
                cur_indent = self.marker * -change
            else:
                cur_indent = ""

            out_line = cur_indent + "\n" + line[len_indent:]

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
                 raise ValueError(f"Malformed relative-indented text: Odd number of lines found. Cannot process line index {i} without a following content line.")

            dent = lines[i].rstrip("\r\n")
            non_indent = lines[i + 1]

            cur_indent = ""
            if dent.startswith(self.marker):
                len_outdent_chars = len(dent)
                if len(prev_indent) >= len_outdent_chars:
                     cur_indent = prev_indent[:-len_outdent_chars]
                else:
                     raise ValueError(f"Malformed relative-indented text: Cannot outdent {len_outdent_chars} chars from previous indent of {len(prev_indent)} chars.")
            else:
                cur_indent = prev_indent + dent

            if not non_indent.rstrip("\r\n"):
                out_line = non_indent
            else:
                out_line = cur_indent + non_indent

            output.append(out_line)
            if non_indent.rstrip("\r\n"):
                prev_indent = cur_indent

        res = "".join(output)
        if self.marker in res:
            raise ValueError("Error transforming text back to absolute indents: Marker still present")

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
]

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
"""

    try:
        result = apply_diffs(original_content, diff_content)
        print("Original content:")
        print(original_content)
        print("\nDiff content:")
        print(diff_content)
        print("\nResult after applying diffs:")
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

    print("\n--- Test case: Append/New File ---")
    original_content_empty = ""
    diff_content_append = """```diff
--- /dev/null
+++ new_file.py
@@ -0,0 +1,3 @@
+def new_function():
+    print("This is a new file.")
"""
    if os.path.exists("dummy_path"):
        os.remove("dummy_path")

    try:
        result_append = apply_diffs(original_content_empty, diff_content_append)
        print("Original content (empty):")
        print(repr(original_content_empty))
        print("\nDiff content (append):")
        print(diff_content_append)
        print("\nResult after applying diffs (append):")
        print(result_append)

    except Exception as e:
        print(f"An error occurred during append test: {e}")
    finally:
        if os.path.exists("dummy_path"):
            os.remove("dummy_path")

    print("\n--- Test case: Large Diff Content ---")
    large_diff_content = "```diff\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-line\n+newline\n" * 100000

    try:
        if os.path.exists("dummy_path"):
            os.remove("dummy_path")
        apply_diffs("initial content", large_diff_content)
        print("Large diff test passed (unexpectedly?).")
    except ValueError as e:
        print(f"Large diff test failed as expected: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during large diff test: {e}")
    finally:
        if os.path.exists("dummy_path"):
            os.remove("dummy_path")