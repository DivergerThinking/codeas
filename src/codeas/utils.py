import logging
import os
from pathlib import Path
from shutil import copyfile, copytree
from typing import List

import yaml
from tiktoken import encoding_for_model

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


def tree(dir_path: str, ignore_startswith: List[str] = None):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """
    # prefix components:
    space = "    "
    branch = "│   "
    # pointers:
    tee = "├── "
    last = "└── "

    def _tree(dir_path: str, prefix: str = "", ignore_startswith: List[str] = None):
        contents = list(
            path
            for path in Path(dir_path).iterdir()
            if _not_startswith(path, ignore_startswith)
        )
        # contents each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            yield prefix + pointer + path.name + "/" if path.is_dir() else prefix + pointer + path.name
            if path.is_dir():  # extend the prefix and recurse:
                extension = branch if pointer == tee else space
                # i.e. space because last, └── , above so no more |
                yield from _tree(
                    path, prefix=prefix + extension, ignore_startswith=ignore_startswith
                )

    def _not_startswith(path: Path, ignore_startswith: List[str] = None):
        if ignore_startswith is None:
            return True
        else:
            for char in ignore_startswith:
                if path.name.startswith(char):
                    return False
            return True

    tree_str = ""
    for line in _tree(dir_path, ignore_startswith=ignore_startswith):
        tree_str += f"{line}\n"
    return tree_str
