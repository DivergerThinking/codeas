import typer
from dotenv import load_dotenv
from typing import Optional
from typing_extensions import Annotated

load_dotenv()
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import AIMessage
from divergen.codebase_assistant import CodebaseAssistant
from divergen.cli_inputs import (
    input_modules,
    input_prompt,
    input_apply_changes,
    input_context,
    input_target,
    input_guidelines
)

dummy_func = """
def dummy_func():
    pass
"""
msg = AIMessage(content=dummy_func)
dummy_model = FakeMessagesListChatModel(responses=[msg])

app = typer.Typer()
assistant = CodebaseAssistant(
    codebase={"root": "./ml_repo_xs"},
    preprompts_path="./configs/preprompts.yaml",
    guidelines_path="./configs/guidelines.yaml",
    # model=dummy_model,
    max_tokens_per_module=2000
)


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
    prompt_name: Annotated[
        Optional[str], typer.Argument(help="The name of the prompt found in prompts.yaml")
    ] = None,
    use_inputs: Annotated[
        Optional[bool],
        typer.Option("-i", "--inputs", help="whether to use CLI inputs to run prompt"),
    ] = False,
    use_default: Annotated[Optional[bool], typer.Option("-d")] = False,
):
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


if __name__ == "__main__":
    app()
