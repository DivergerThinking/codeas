import yaml

from tiktoken import encoding_for_model

encoder = encoding_for_model("gpt-3.5-turbo")


def count_tokens(text):
    return len(encoder.encode(text))


def read_yaml(path):
    with open(path, "r") as yaml_file:
        return yaml.safe_load(yaml_file)
