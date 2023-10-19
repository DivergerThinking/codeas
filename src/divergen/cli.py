import typer
import os
from dotenv import load_dotenv
from typing import Optional
from typing_extensions import Annotated

load_dotenv()

from divergen.codebase_assistant import CodebaseAssistant
from divergen.cli_inputs import (
    input_modules,
    input_prompt,
    input_apply_changes,
    input_context,
    input_target,
    input_guidelines,
)

app = typer.Typer()
assistant = CodebaseAssistant()


def validate_run():
    if not os.path.exists(".divergen"):
        raise typer.Exit(
            "'.divergen' directory not found. Please run `divergen init` first."
        )


@app.command()
def init(
    path: Annotated[
        Optional[str],
        typer.Option(
            "-p", help="The path containing config files to use for initialization"
        ),
    ] = None,
):
    assistant.init_configs(path)


@app.command()
def undo():
    raise NotImplementedError


@app.command()
def redo():
    raise NotImplementedError


@app.command()
def run(
    prompt_name: Annotated[
        Optional[str],
        typer.Argument(help="The name of the prompt found in prompts.yaml"),
    ] = None,
    use_inputs: Annotated[
        Optional[bool],
        typer.Option("-i", "--inputs", help="whether to use CLI inputs to run prompt"),
    ] = False,
    use_default: Annotated[Optional[bool], typer.Option("-d")] = False,
):
    validate_run()
    if use_inputs:
        prompt = input_prompt()
        modules = input_modules(assistant, use_default)
        context = input_context(use_default)
        target = input_target(use_default)
        guidelines = input_guidelines(assistant, use_default)
        assistant.execute_prompt(prompt, context, target, guidelines, modules)
    else:
        modules = input_modules(assistant, use_default)
        assistant.execute_preprompt(prompt_name, modules)

    apply = input_apply_changes()
    if apply:
        assistant.apply_changes()
    else:
        assistant.reject_changes()


if __name__ == "__main__":
    app()
