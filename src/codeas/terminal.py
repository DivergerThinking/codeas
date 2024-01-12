from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion

from codeas import configs
from codeas.chat import Chat
from codeas.codebase import Codebase
from codeas.utils import end_message_block, start_message_block, write_yaml


class AutoCompleter(Completer):
    commands = ["view", "copy", "clear"]
    agents = ["search", "context", "write"]
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
        except KeyboardInterrupt:
            break

        if isinstance(message, str):
            end_message_block("bold magenta")
            chat.ask(message)


def write_settings():
    write_yaml(".codeas/codeas.yaml", get_configs(["model", "temperature"]))


def get_configs(attrs: list = []):
    if any(attrs):
        return {
            config_name: {
                attr: value
                for attr, value in getattr(configs, config_name).items()
                if attr in attrs
            }
            for config_name in vars(configs)
            if "_config" in config_name
        }
    else:
        return {
            config_name: getattr(configs, config_name)
            for config_name in vars(configs)
            if "_config" in config_name
        }


if __name__ == "__main__":
    start_terminal()
