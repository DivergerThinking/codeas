from prompt_toolkit import PromptSession

from codeas.chat import Chat
from codeas.utils import end_message_block, start_message_block


def start_terminal():
    chat = Chat()
    while True:
        try:
            start_message_block("User input", "bold magenta")
            session = PromptSession(message="> ")
            message = session.prompt()
        except KeyboardInterrupt:
            break

        if isinstance(message, str):
            end_message_block("bold magenta")
            chat.ask(message)


if __name__ == "__main__":
    start_terminal()
