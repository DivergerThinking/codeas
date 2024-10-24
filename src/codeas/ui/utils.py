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
            file_content = do_replace(Path("dummy_path"), file_content, hunk)
        except SearchTextNotUnique:
            if os.path.exists("dummy_path"):
                os.remove("dummy_path")
            raise ValueError(
                "The diff could not be applied uniquely to the file content."
            )

        if not file_content:
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

    # For now, just take 1!
    # edits = edits[:1]

    return edits


def process_fenced_block(lines, start_line_num):
    for line_num in range(start_line_num, len(lines)):
        line = lines[line_num]
        if line.startswith("```"):
            break

    block = lines[start_line_num:line_num]
    block.append("@@ @@")

    if block[0].startswith("--- ") and block[1].startswith("+++ "):
        # Extract the file path, considering that it might contain spaces
        fname = block[1][4:].strip()
        block = block[2:]
    else:
        fname = None

    edits = []

    keeper = False
    hunk = []
    op = " "
    for line in block:
        hunk.append(line)
        if len(line) < 2:
            continue

        if line.startswith("+++ ") and hunk[-2].startswith("--- "):
            if hunk[-3] == "\n":
                hunk = hunk[:-3]
            else:
                hunk = hunk[:-2]

            edits.append((fname, hunk))
            hunk = []
            keeper = False

            fname = line[4:].strip()
            continue

        op = line[0]
        if op in "-+":
            keeper = True
            continue
        if op != "@":
            continue
        if not keeper:
            hunk = []
            continue

        hunk = hunk[:-1]
        edits.append((fname, hunk))
        hunk = []
        keeper = False

    return line_num + 1, edits


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
    op = " "
    for line in hunk:
        if len(line) < 2:
            op = " "
            line = line
        else:
            op = line[0]
            line = line[1:]

        if op == " ":
            before.append(line)
            after.append(line)
        elif op == "-":
            before.append(line)
        elif op == "+":
            after.append(line)

    if lines:
        return before, after

    before = "".join(before)
    after = "".join(after)

    return before, after


def do_replace(fname, content, hunk):
    fname = Path(fname)

    before_text, after_text = hunk_to_before_after(hunk)

    # does it want to make a new file?
    if not fname.exists() and not before_text.strip():
        fname.touch()
        content = ""

    if content is None:
        return

    # TODO: handle inserting into new file
    if not before_text.strip():
        # append to existing file, or start a new file
        new_content = content + after_text
        return new_content

    new_content = None

    new_content = apply_hunk(content, hunk)
    if new_content:
        return new_content


def apply_hunk(content, hunk):
    before_text, after_text = hunk_to_before_after(hunk)

    res = directly_apply_hunk(content, hunk)
    if res:
        return res

    hunk = make_new_lines_explicit(content, hunk)

    # just consider space vs not-space
    ops = "".join([line[0] for line in hunk])
    ops = ops.replace("-", "x")
    ops = ops.replace("+", "x")
    ops = ops.replace("\n", " ")

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
        if res:
            content = res
        else:
            all_done = False
            # FAILED!
            # this_hunk = preceding_context + changes + following_context
            break

    if all_done:
        return content


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
            d = "-"
        elif d > 0:
            d = "+"
        else:
            d = " "
        for line in lines.splitlines(keepends=True):
            udiff.append(d + line)

    return udiff


def apply_partial_hunk(content, preceding_context, changes, following_context):
    len_prec = len(preceding_context)
    len_foll = len(following_context)

    use_all = len_prec + len_foll

    # if there is a - in the hunk, we can go all the way to `use=0`
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
            if res:
                return res


def directly_apply_hunk(content, hunk):
    before, after = hunk_to_before_after(hunk)

    if not before:
        return

    before_lines, _ = hunk_to_before_after(hunk, lines=True)
    before_lines = "".join([line.strip() for line in before_lines])

    # Refuse to do a repeated search and replace on a tiny bit of non-whitespace context
    if len(before_lines) < 10 and content.count(before) > 1:
        return

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
        return

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
            if res:
                return res


def try_strategy(texts, strategy, preproc):
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    if preproc_strip_blank_lines:
        texts = strip_blank_lines(texts)
    if preproc_relative_indent:
        ri, texts = relative_indent(texts)
    if preproc_reverse:
        texts = list(map(reverse_lines, texts))

    res = strategy(texts)

    if res and preproc_reverse:
        res = reverse_lines(res)

    if res and preproc_relative_indent:
        try:
            res = ri.make_absolute(res)
        except ValueError:
            return

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
            raise ValueError("Text already contains the outdent marker: {self.marker}")

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
            dent = lines[i].rstrip("\r\n")
            non_indent = lines[i + 1]

            if dent.startswith(self.marker):
                len_outdent = len(dent)
                cur_indent = prev_indent[:-len_outdent]
            else:
                cur_indent = prev_indent + dent

            if not non_indent.rstrip("\r\n"):
                out_line = non_indent  # don't indent a blank line
            else:
                out_line = cur_indent + non_indent

            output.append(out_line)
            prev_indent = cur_indent

        res = "".join(output)
        if self.marker in res:
            # dump(res)
            raise ValueError("Error transforming text back to absolute indents")

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
