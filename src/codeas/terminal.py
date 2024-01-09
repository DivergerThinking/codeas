from prompt_toolkit import PromptSession
from rich.console import Console

from codeas.chat import Chat


def start_terminal():
    chat = Chat()
    console = Console()
    while True:
        try:
            console.print("\n")
            console.rule("User input", style="bold magenta")
            session = PromptSession(message="> ")
            message = session.prompt()
        except KeyboardInterrupt:
            break

        if isinstance(message, str):
            console.rule(style="bold magenta")
            chat.ask(message)


if __name__ == "__main__":
    start_terminal()
