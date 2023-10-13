import yaml
from tiktoken import encoding_for_model
import logging

encoder = encoding_for_model("gpt-3.5-turbo")


def count_tokens(text):
    return len(encoder.encode(text))


def read_yaml(path):
    try:
        with open(path, "r") as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        error_msg = f"File {path} not found."
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
