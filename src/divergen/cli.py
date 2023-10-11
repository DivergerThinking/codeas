import typer
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
    input_preprompt,
)

app = typer.Typer()
assistant = CodebaseAssistant()


@app.command()
def set_config():
    raise NotImplementedError


@app.command()
def undo():
    raise NotImplementedError


@app.command()
def redo():
    raise


@app.command()
def run(
    prompt: Annotated[
        Optional[str], typer.Argument(help="Either the prompt OR preprompt name to run")
    ] = None,
    use_preprompt: Annotated[
        Optional[bool],
        typer.Option("-p", "--preprompt", help="whether to use preprompt"),
    ] = False,
    use_default: Annotated[Optional[bool], typer.Option("-d")] = False,
):
    if use_preprompt:
        if prompt is None:
            prompt = input_preprompt(assistant)
        modules = input_modules(assistant, use_default)
        # assistant.execute_preprompt(prompt, modules)
        print(prompt, modules)
    else:
        if prompt is None:
            prompt = input_prompt()
        modules = input_modules(assistant, use_default)
        context = input_context(use_default)
        target = input_target(use_default)
        guidelines = input_guidelines(assistant, use_default)
        print(prompt, context, target, guidelines, modules)
        # assistant.execute_prompt(prompt, context, target, guidelines, modules)

    apply = input_apply_changes()
    if apply:
        print("apply changes")
        # assistant.apply_changes()


if __name__ == "__main__":
    app()
