import logging
import os
from shutil import copyfile, copytree

import yaml
from pydantic import BaseModel
from rich.console import Console
from rich.live import Live

console = Console()
live = Live()


class ChatExitException(Exception):
    pass


def start_message_block(title: str, color: str):
    console.print("\n")
    console.rule(title, style=color)


def end_message_block(color: str):
    console.rule(style=color)


class File(BaseModel):
    path: str
    content: str
    line_start: int
    line_end: int


def read_yaml(path):
    try:
        with open(path, "r") as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        error_msg = f"File {path} not found."
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)


def write_yaml(path, data):
    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
    with open(path, "w") as yaml_file:
        yaml.dump(
            data,
            yaml_file,
            Dumper=SpaciousDumper,
            default_flow_style=False,
            sort_keys=False,
        )


class SpaciousDumper(yaml.SafeDumper):
    """
    HACK: insert blank lines between top-level objects (used in write_yaml)
    inspired by https://stackoverflow.com/a/44284819/3786245
    """

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()


def str_presenter(dumper, data):
    """configures yaml for dumping multiline strings
    Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
    """
    if data.count("\n") > 0:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def copy_files(source_path, target_path):
    if os.path.isdir(source_path):
        copytree(source_path, target_path)
    else:
        copyfile(source_path, target_path)
