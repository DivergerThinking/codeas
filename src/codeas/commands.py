import os
from typing import List

from codeas.utils import File, console, count_tokens


def view_context(context: List[File]):
    console.rule("Context", style="yellow")
    if any(context):
        for file_ in context:
            context_path = os.path.join(os.getcwd(), f".codeas/{file_.path}")
            dir_path = os.path.dirname(context_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(context_path, "w") as f:
                f.write(file_.content)

            lines = (
                f"l.{file_.line_start}-{file_.line_end}"
                if file_.line_end != -1
                else "structure"
            )

            console.print(
                f"{file_.path} | {lines} | {count_tokens(file_.content)} tokens"
            )
    else:
        console.print("No files in context")
    console.rule(style="yellow")
