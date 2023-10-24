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
            yaml.dump(
                {"PROMPT_NAME": {"instructions": "YOUR INSTRUCTIONS HERE"}},
                yaml_file,
                default_flow_style=False,
                sort_keys=False,
            )
            yaml_file.write(
                "  # target: code\n  # context: code\n  # guidelines:\n  #   - GUIDELINE_NAME\n\n"
            )
            yaml.dump(
                {"guidelines": {"GUIDELINE_NAME": "YOUR GUIDELINE HERE"}},
                yaml_file,
                default_flow_style=False,
                sort_keys=False,
            )
