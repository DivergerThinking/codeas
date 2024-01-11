from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pyperclip

from codeas.utils import console, count_tokens

if TYPE_CHECKING:
    from codeas.chat import Chat


def copy_last_message(chat: Chat):
    pyperclip.copy(chat.thread.messages[-1]["content"])


def clear_chat(chat: Chat):
    chat.thread.messages = []
    chat.context = []


def view_context(chat: Chat):
    console.rule("Context", style="blue")
    if any(chat.context):
        for file_ in chat.context:
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
    console.rule(style="blue")
