import os
from typing import Optional

import typer
from dotenv import load_dotenv
from typing_extensions import Annotated

load_dotenv()

from codeas.assistant import Assistant
from codeas.cli_inputs import input_apply_changes
from codeas.utils import read_yaml

app = typer.Typer()


def validate_run():
    if not os.path.exists(".codeas/assistant.yaml"):
        raise typer.Exit(
            "'.codeas/assistant.yaml' not found. Please run `codeas init` first."
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
    assistant = Assistant()
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
    prompt: Annotated[
        Optional[str],
        typer.Option("-p", "--prompt", help="whether to use CLI inputs to run prompt"),
    ] = None,
):
    validate_run()
    assistant_args = read_yaml(".codeas/assistant.yaml")
    assistant = Assistant(**assistant_args)
    if prompt is not None:
        assistant.execute_prompt(prompt)
    else:
        assistant.execute_preprompt(prompt_name)

    apply = input_apply_changes()
    if apply:
        assistant.apply_changes()
    else:
        assistant.reject_changes()


if __name__ == "__main__":
    app()
