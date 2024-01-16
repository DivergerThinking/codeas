from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

import pyperclip

from codeas.codebase import Codebase
from codeas.utils import ChatExitException, console

if TYPE_CHECKING:
    from codeas.chat import Chat


def exit_chat():
    raise ChatExitException


def tree_display():
    console.rule("Codebase Tree", style="blue")
    codebase = Codebase()
    console.print(codebase.get_tree())
    console.rule(style="blue")


def copy_last_message(chat: Chat):
    pyperclip.copy(chat.thread._messages[-1]["content"])


def clear_chat(chat: Chat):
    chat.thread._messages = []
    chat.thread._context = []
    chat.context = []


def view_context(chat: Chat):
    console.rule("Context", style="blue")
    if any(chat.context):
        if os.path.exists(".codeas/context"):
            shutil.rmtree(".codeas/context")

        for file_ in chat.context:
            context_path = os.path.join(os.getcwd(), f".codeas/context/{file_.path}")
            dir_path = os.path.dirname(context_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(context_path, "w") as f:
                f.write(file_.content)

            if hasattr(file_, "line_end"):
                section = (
                    f"l.{file_.line_start}-{file_.line_end}"
                    if file_.line_end != -1
                    else "structure"
                )
            else:
                section = file_.name

            console.print(
                f"{file_.path} | {section} | {chat.thread.count_tokens(file_.content)} tokens"
            )
    else:
        console.print("No files in context")
    console.rule(style="blue")
