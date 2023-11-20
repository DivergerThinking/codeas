from __future__ import annotations

import os
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel

from codeas.utils import copy_files, write_yaml

if TYPE_CHECKING:
    from codeas.assistant import Assistant


class Initializer(BaseModel):
    def init_configs(self, assistant: Assistant, source_path: str = None):
        self._create_codeas_dir()
        if source_path:
            copy_files(source_path, ".codeas")
        else:
            write_yaml(".codeas/assistant.yaml", assistant.model_dump())
            self._write_default_prompts(".codeas/prompts.yaml")

    def _create_codeas_dir(self):
        if not os.path.exists(".codeas"):
            os.mkdir(".codeas")

    def _write_default_prompts(self, file_path: str):
        with open(file_path, "w") as yaml_file:
            yaml_file.write("# Example prompts you can use\n")
            yaml.dump(
                {
                    "generate_docstrings": "Generate docstrings for all files under src/",
                    "generate_tests": "Generate tests for all files under src/",
                    "generate_documentation": "Generate usage documentation for all files under src/",
                },
                yaml_file,
                default_flow_style=False,
                sort_keys=False,
            )
            yaml_file.write("# Example guidelines you can use\n")
            yaml.dump(
                {
                    "guidelines": {
                        "documentation": "Documentation should be written in docs/ folder in markdown format.",
                        "tests": "Tests should be written in tests/ folder using pytest, with file name starting with 'test_'.",
                        "docstrings": "Docstrings should use numpy style.",
                    }
                },
                yaml_file,
                default_flow_style=False,
                sort_keys=False,
            )
