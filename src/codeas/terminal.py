from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import Completer, Completion

from codeas.chat import Chat
from codeas.codebase import Codebase
from codeas.utils import end_message_block, start_message_block


class AutoCompleter(Completer):
    commands = ["view", "copy", "clear", "tree"]
    agents = ["search", "add", "write"]
    relative_files = Codebase().get_modules_paths()

    def get_completions(self, document, _):
        text = document.text_before_cursor
        words = text.split()
        last_word = words[-1]
        if text[0] == "/" and len(words) == 1 and text[-1] != " ":
            for completion in self.get_commands(text):
                yield Completion(completion, -len(text) + 1)
        elif last_word.startswith("@") and text[-1] != " ":
            for completion in self.get_agents(last_word):
                yield Completion(completion, -len(last_word) + 1)
        elif "/" in last_word and text[-1] != " ":
            for completion in self.get_relative_files(last_word):
                yield Completion(completion, -len(last_word))

    def get_commands(self, text):
        return [
            command for command in self.commands if ("/" + command).startswith(text)
        ]

    def get_agents(self, last_word):
        return [agent for agent in self.agents if ("@" + agent).startswith(last_word)]

    def get_relative_files(self, last_word):
        return [file_ for file_ in self.relative_files if file_.startswith(last_word)]


def start_terminal():
    chat = Chat()
    while True:
        try:
            start_message_block("User input", "bold magenta")
            session = PromptSession(message="> ", completer=AutoCompleter())
            message = session.prompt()
        # handle keyboard interrupts before prompting
        except KeyboardInterrupt:
            message = None
            answer = prompt("Are you sure you want to exit the chat interface? (y/n): ")
            if answer == "y":
                break
        try:
            if message and isinstance(message, str):
                end_message_block("bold magenta")
                chat.ask(message)
        # handle keyboard interrupts while the chat assistant is running
        except KeyboardInterrupt:
            if chat.get_last_message() == message:
                chat.remove_last_message()


if __name__ == "__main__":
    start_terminal()
