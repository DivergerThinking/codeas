import difflib
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Iterable, Callable, Set

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
            name, version_str = full_name.rsplit(" v.", 1)
            version = int(version_str)
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

    if os.path.exists("dummy_path"):
        os.remove("dummy_path")

    try:
        current_content = file_content
        for path, hunk in edits:
            hunk = normalize_hunk(hunk)
            if not hunk:
                continue

            try:
                 updated_content = do_replace(Path("dummy_path"), current_content, hunk)
            except SearchTextNotUnique:
                if os.path.exists("dummy_path"):
                    os.remove("dummy_path")
                raise ValueError(
                    "The diff could not be applied uniquely to the file content."
                )

            if not updated_content:
                 if os.path.exists("dummy_path"):
                     os.remove("dummy_path")
                 raise ValueError("The diff failed to apply to the file content.")

            current_content = updated_content

        if os.path.exists("dummy_path"):
             os.remove("dummy_path")

        return current_content

    finally:
        if os.path.exists("dummy_path"):
            os.remove("dummy_path")


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
                edits.extend(these_edits)
                break
            line_num += 1

    # For now, just take 1!
    # edits = edits[:1]

    return edits


def _add_completed_hunk(edits, fname, hunk_lines):
    if hunk_lines:
        processed_hunk_lines = list(hunk_lines)
        while processed_hunk_lines and processed_hunk_lines[-1].strip() == "":
             processed_hunk_lines.pop()
        if processed_hunk_lines:
             edits.append((fname, processed_hunk_lines))


def process_fenced_block(lines, start_line_num):
    end_line_num = start_line_num
    while end_line_num < len(lines):
        if lines[end_line_num].strip() == "```":
            break
        end_line_num += 1

    block_lines = lines[start_line_num:end_line_num]

    edits = []
    current_fname = None
    current_hunk_lines = []

    i = 0
    while i < len(block_lines):
        line = block_lines[i]

        if line.startswith("--- "):
            if i + 1 < len(block_lines) and block_lines[i + 1].startswith("+++ "):
                _add_completed_hunk(edits, current_fname, current_hunk_lines)
                current_fname = block_lines[i + 1][4:].strip()
                current_hunk_lines = []
                i += 2
                continue

        if line.startswith("@@ "):
            _add_completed_hunk(edits, current_fname, current_hunk_lines)
            current_hunk_lines = [line]
            i += 1
            continue

        current_hunk_lines.append(line)
        i += 1

    _add_completed_hunk(edits, current_fname, current_hunk_lines)

    return end_line_num + 1, edits


def normalize_hunk(hunk):
    hunk_content_lines = hunk
    if hunk_content_lines and hunk_content_lines[0].startswith("@@ "):
         hunk_content_lines = hunk_content_lines[1:]

    if not hunk_content_lines:
        return []

    before_lines, after_lines = hunk_to_before_after(hunk_content_lines, lines=True)

    before_lines_cleaned = cleanup_pure_whitespace_lines(before_lines)
    after_lines_cleaned = cleanup_pure_whitespace_lines(after_lines)

    diff = difflib.unified_diff([l.rstrip("\r\n") for l in before_lines_cleaned],
                                [l.rstrip("\r\n") for l in after_lines_cleaned],
                                n=max(len(before_lines_cleaned), len(after_lines_cleaned)), lineterm="")

    diff_lines = list(diff)[3:]

    diff_with_newlines = []
    for line in diff_lines:
         diff_with_newlines.append(line + "\n")

    return diff_with_newlines


def cleanup_pure_whitespace_lines(lines):
    res = []
    for line in lines:
        if line.strip():
            res.append(line)
        else:
            res.append(line[-(len(line) - len(line.rstrip("\r\n"))):])
    return res


def hunk_to_before_after(hunk, lines=False):
    before = []
    after = []
    for line in hunk:
        op = " "
        content_part = ""

        if len(line) < 2:
            op = " "
            content_part = line
        else:
            op = line[0]
            content_part = line[1:]

        if op == " ":
            before.append(content_part)
            after.append(content_part)
        elif op == "-":
            before.append(content_part)
        elif op == "+":
            after.append(content_part)

    if lines:
        return before, after

    before_str = "".join(before)
    after_str = "".join(after)

    return before_str, after_str


def _apply_simple_hunk_cases(content, hunk):
     before_text, after_text = hunk_to_before_after(hunk)

     if not before_text.strip():
         if content is None:
             content = ""

         new_content = content + after_text
         return new_content

     return None


def do_replace(fname, content, hunk):
    fname = Path(fname)

    before_text_for_checks, _ = hunk_to_before_after(hunk)

    if not fname.exists() and not before_text_for_checks.strip():
        fname.touch()
        content = ""

    if content is None:
        return None

    # TODO: handle inserting into new file

    handled_content = _apply_simple_hunk_cases(content, hunk)
    if handled_content is not None:
         return handled_content

    result_content = apply_hunk(content, hunk)

    if result_content:
        return result_content

    return result_content


def apply_hunk(content, hunk):
    res = directly_apply_hunk(content, hunk)
    if res is not None:
        return res

    adjusted_hunk = make_new_lines_explicit(content, hunk)

    res = directly_apply_hunk(content, adjusted_hunk)
    if res is not None:
         return res

    preceding_context_lines_content = []
    changes_lines = []
    following_context_lines_content = []

    state = "context_before"

    for line in adjusted_hunk:
        if not line:
             continue

        prefix = line[0] if line else None
        if prefix == " ":
            content_part = line[1:]
            if state == "context_before":
                preceding_context_lines_content.append(content_part)
            elif state == "changes":
                 state = "context_after"
                 following_context_lines_content.append(content_part)
            elif state == "context_after":
                 following_context_lines_content.append(content_part)
        elif prefix in "+-":
            if state == "context_before":
                 state = "changes"
            changes_lines.append(line)

    res = apply_partial_hunk(
        content,
        preceding_context_lines_content,
        changes_lines,
        following_context_lines_content,
        hunk=adjusted_hunk
    )

    return res


def make_new_lines_explicit(content, hunk):
    before_orig, after_orig = hunk_to_before_after(hunk)

    diff = diff_lines(before_orig, content if content is not None else "")

    new_before_lines_content = []
    for line in diff:
         if len(line) > 0 and line[0] == "+":
              continue
         if len(line) > 1:
              new_before_lines_content.append(line[1:])
         elif len(line) == 1 and line[0] in " -":
              new_before_lines_content.append("")


    new_before_str = "".join(new_before_lines_content)

    if not new_before_str:
        return hunk

    if len(new_before_str.strip()) < 10:
        return hunk

    before_lines_orig = before_orig.splitlines(keepends=True)
    new_before_lines_split = new_before_str.splitlines(keepends=True)
    after_lines_split = after_orig.splitlines(keepends=True)

    if len(new_before_lines_split) < len(before_lines_orig) * 0.66:
        return hunk

    new_hunk_lines = difflib.unified_diff(
        [l.rstrip("\r\n") for l in new_before_lines_split],
        [l.rstrip("\r\n") for l in after_lines_split],
        n=max(len(new_before_lines_split), len(after_lines_split)), lineterm=""
    )
    new_hunk_list = list(new_hunk_lines)[3:]

    new_hunk_with_newlines = [line + "\n" if not line.endswith(("\n", "\r")) else line for line in new_hunk_list]

    return new_hunk_with_newlines


def diff_lines(search_text, replace_text):
    dmp = diff_match_patch()
    dmp.Diff_Timeout = 5
    # dmp.Diff_EditCost = 16

    search_lines_chars, replace_lines_chars, mapping = dmp.diff_linesToChars(
        search_text, replace_text
    )

    diff_result = dmp.diff_main(search_lines_chars, replace_lines_chars, False)
    dmp.diff_cleanupSemantic(diff_result)

    diff = list(diff_result)
    dmp.diff_charsToLines(diff, mapping)

    udiff = []
    for d_type, lines_str in diff:
        lines_list = lines_str.splitlines(keepends=True)
        if lines_str.endswith(("\n", "\r")) and lines_list and not lines_list[-1]:
            lines_list = lines_list[:-1]

        prefix = " "
        if d_type < 0:
            prefix = "-"
        elif d_type > 0:
            prefix = "+"

        for line in lines_list:
            udiff.append(prefix + line)

    return udiff


def _construct_attempt_hunk(prec_content_lines, changes_lines, foll_content_lines):
    prec_hunk_lines = [f" {line}" for line in prec_content_lines]
    foll_hunk_lines = [f" {line}" for line in foll_content_lines]
    return prec_hunk_lines + changes_lines + foll_hunk_lines


def apply_partial_hunk(content, preceding_context_lines_content, changes_lines, following_context_lines_content, hunk):
    len_prec = len(preceding_context_lines_content)
    len_foll = len(following_context_lines_content)
    use_all_context = len_prec + len_foll

    for use_total_context in range(use_all_context + 1):
        use = use_total_context
        for use_prec in range(len_prec, -1, -1):
            if use_prec > use:
                 continue

            use_foll = use - use_prec
            if use_foll > len_foll:
                 continue

            if use_prec:
                 this_prec_content_lines = preceding_context_lines_content[-use_prec:]
            else:
                 this_prec_content_lines = []

            this_foll_content_lines = following_context_lines_content[:use_foll]

            attempt_hunk = _construct_attempt_hunk(this_prec_content_lines, changes_lines, this_foll_content_lines)

            res = directly_apply_hunk(content, attempt_hunk)

            if res is not None:
                 return res

    return None


def directly_apply_hunk(content, hunk):
    before, after = hunk_to_before_after(hunk)

    if not before:
        return None

    before_lines, _ = hunk_to_before_after(hunk, lines=True)
    before_lines_stripped = "".join([line.strip() for line in before_lines])

    if content is not None and len(before_lines_stripped) < 10 and content.count(before) > 1:
        return None

    try:
        new_content = flexi_just_search_and_replace([before, after, content])
    except SearchTextNotUnique:
        new_content = None
    except Exception:
         new_content = None

    return new_content


def flexi_just_search_and_replace(texts):
    strategies = [
        (search_and_replace, all_preprocs),
    ]
    return flexible_search_and_replace(texts, strategies)


def search_and_replace(texts):
    search_text, replace_text, original_text = texts

    if original_text is None:
         return None

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
    edits.\n    """

    for strategy, preprocs in strategies:
        for preproc in preprocs:
            try:
                res = try_strategy(texts, strategy, preproc)
                if res is not None:
                    return res
            except Exception:
                 pass


def try_strategy(texts, strategy, preproc):
    preproc_strip_blank_lines, preproc_relative_indent, preproc_reverse = preproc
    ri = None

    try:
        if preproc_strip_blank_lines:
            texts = strip_blank_lines(texts)
        if preproc_relative_indent:
            ri, texts = relative_indent(texts)
        if preproc_reverse:
            texts = list(map(reverse_lines, texts))

        res = strategy(texts)

        if res is not None:
            if preproc_reverse:
                res = reverse_lines(res)

            if preproc_relative_indent:
                if ri:
                     res = ri.make_absolute(res)
                elif not ri and res is not None:
                    return None

        return res

    except ValueError:
         return None
    except Exception:
         pass
         return None


def strip_blank_lines(texts):
    """
    Removes leading and trailing newlines from each text and appends a single newline.
    Replicates original, potentially buggy, logic.
    """
    res = []
    for text in texts:
        if text is None:
             res.append(None)
             continue
        res.append(text.strip("\n") + "\n")
    return res


def relative_indent(texts):
    """
    Transforms texts to use relative indentation format using RelativeIndenter.
    Replicates original logic flow and handling of None texts.
    """
    valid_texts = [t for t in texts if t is not None]
    ri = RelativeIndenter(valid_texts) if valid_texts else None

    processed_texts = []
    for text in texts:
        if text is None:
            processed_texts.append(None)
        elif ri:
            try:
                processed_texts.append(ri.make_relative(text))
            except Exception:
                 processed_texts.append(None)
        else:
             processed_texts.append(None)

    return ri, processed_texts


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

        ARROW = "\u2190"
        if ARROW not in chars:
            self.marker = ARROW
        else:
            self.marker = self.select_unique_marker(chars)

    def select_unique_marker(self, chars):
        """Finds a unicode character not present in the given set of characters."""
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
            indent = line_without_end[:len_indent]
            change = len_indent - len(prev_indent)

            cur_indent = ""
            if change > 0:
                 cur_indent = indent[-change:]

            elif change < 0:
                cur_indent = self.marker * -change
            else:
                cur_indent = ""

            out_line = cur_indent + "\\n" + line[len_indent:]
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

            cur_indent = ""
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
            raise ValueError("Error transforming text back to absolute indents")

        return res


def reverse_lines(text):
    """Reverses the order of lines in a text string."""
    if text is None:
        return None
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