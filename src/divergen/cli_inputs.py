from __future__ import annotations
from typing import TYPE_CHECKING

from termcolor import colored

if TYPE_CHECKING:
    from divergen.codebase_assistant import CodebaseAssistant


DEFAULT = {
    "modules": "all",
    "context": "0",
    "target": "0",
    "guidelines": "None",
}


def input_prompt():
    return input(
        colored("\nEnter instructions for the model to perform: \n input: ", "red")
    )


def input_preprompt(assistant: CodebaseAssistant):
    options = list(assistant._preprompts.keys())
    selected_option = input(
        colored("\nSelect the preprompt you want to use. \n", "red")
        + _display_options(options, multi=False)
    )
    return options[int(selected_option)]


def input_modules(assistant: CodebaseAssistant, use_default: bool):
    if use_default:
        selected_options = DEFAULT["modules"]
    else:
        options = assistant.codebase.get_module_names()
        selected_options = input(
            colored("\nSelect the modules you want to use. \n", "red")
            + _display_options(options, multi=True, default=DEFAULT["modules"])
        )

    if selected_options == "all" or selected_options == "":
        return options
    else:
        return [options[int(idx)] for idx in selected_options.split(",")]

def input_guidelines(assistant: CodebaseAssistant, use_default: bool):
    if use_default:
        selected_options = DEFAULT["guidelines"]
    else:
        options = assistant._guidelines.keys()
        selected_options = input(
            colored("\nSelect the guidelines you want to use. \n", "red")
            + _display_options(options, multi=True, default=DEFAULT["guidelines"])
        )

    if selected_options == "":
        return DEFAULT["guidelines"]
    else:
        return [options[int(idx)] for idx in selected_options.split(",")]

def input_context(use_default: bool):
    if use_default:
        selected_option = DEFAULT["context"]
    else:
        options = ["code", "docs", "tests"]
        selected_option = input(
            colored("\nSelect the context to use for these modules. \n", "red")
            + _display_options(options, multi=False, default=DEFAULT["context"])
        )
    if selected_option == "":
        return options[int(DEFAULT["context"])]
    else:
        return options[int(selected_option)]


def input_target(use_default: bool):
    if use_default:
        selected_option = DEFAULT["target"]
    else:
        options = ["code", "docs", "tests"]
        selected_option = input(
            colored("\nSelect the target to use for these the modules. \n", "red")
            + _display_options(options, multi=False, default=DEFAULT["context"])
        )
    if selected_option == "":
        return options[int(DEFAULT["target"])]
    else:
        return options[int(selected_option)]


def input_apply_changes():
    selected_option = input(
        colored("\nDo you want to apply the changes? [yes/no]\ninput: [yes]", "red")
    )
    return (selected_option == "yes" or selected_option == "y" or selected_option == "")


def _display_options(options: list, multi: bool = False, default: str = None):
    options_display = "Choose from the following options: \n"
    for idx, option in enumerate(options):
        options_display += f"{str(idx)} = {option}\n"
    options_display += "Enter the option number. "
    if multi:
        options_display += "To select multiple options, use csv format. Ex.: 1,2,3\n"
        options_display += "To select all options, type 'all' \n"
    options_display += f"\ninput: {f'[{default}] ' if default else ''}"
    return options_display
