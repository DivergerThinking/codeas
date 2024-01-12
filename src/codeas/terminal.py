from prompt_toolkit import PromptSession

from codeas import configs
from codeas.chat import Chat
from codeas.utils import end_message_block, start_message_block, write_yaml


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
