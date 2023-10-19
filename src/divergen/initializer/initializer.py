from __future__ import annotations

import os

from typing import TYPE_CHECKING
from pydantic import BaseModel

from divergen.utils import write_yaml, copy_files
from divergen.initializer._default_prompts import DEFAULT_PROMPTS

if TYPE_CHECKING:
    from divergen.codebase_assistant import CodebaseAssistant


class Initializer(BaseModel):
    def init_configs(self, assistant: CodebaseAssistant, source_path: str = None):
        self._create_divergen_dir()
        if source_path:
            copy_files(source_path, ".divergen")
        else:
            write_yaml(".divergen/assistant.yaml", assistant.model_dump())
            write_yaml(".divergen/prompts.yaml", DEFAULT_PROMPTS)

    def _create_divergen_dir(self):
        if not os.path.exists(".divergen"):
            os.mkdir(".divergen")
