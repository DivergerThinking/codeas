import logging
import os
from typing import Any, List, ClassVar

from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, PrivateAttr

from divergen.ts_codebase import ts_Codebase
from divergen.file_handler import FileHandler
from divergen.request import Request
from divergen.utils import count_tokens, read_yaml
from divergen.initializer import Initializer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class CodebaseAssistant(BaseModel, validate_assignment=True, extra="forbid"):
    codebase: ClassVar = ts_Codebase()
    # TODO: Pydantic fields doesn't seems to accept defaults with inputs. Review.
    file_handler: FileHandler = FileHandler
    max_tokens_per_module: int = 2000
    model: str = "gpt-3.5-turbo"
    _preprompts: dict = PrivateAttr(default_factory=dict)
    _guidelines: dict = PrivateAttr(default_factory=dict)
    _openai_model: object = PrivateAttr(None)

    def model_post_init(self, __context: Any) -> None:
        if os.path.exists(".divergen"):
            self._overwrite_configs()
            self._set_prompt_files()
            self._set_openai_model()
            self._parse_codebase()

    def _overwrite_configs(self):
        _configs = read_yaml(".divergen/config.yaml")
        for attr, value in _configs.items():
            if getattr(self, attr) != value:
                setattr(self, attr, value)

    def _set_prompt_files(self):
        self._preprompts = read_yaml(".divergen/prompts.yaml")
        self._guidelines = read_yaml(".divergen/guidelines.yaml")

    def _set_openai_model(self):
        self._openai_model = ChatOpenAI(
            model=self.model,
            callbacks=[StreamingStdOutCallbackHandler()],
            streaming=True,
        )

    def _parse_codebase(self):
        # TODO: add error handler for when repository is not found or is empty
        self.codebase.parse_modules()

    def init_configs(self, source_path: str = None):
        initializer = Initializer()
        initializer.init_configs(self, source_path)

    def execute_preprompt(self, name: str, modules: List[str] = None):
        logging.info(f"Executing preprompt {name}")
        user_prompt = self._preprompts[name].get("user_prompt")
        context = self._preprompts[name].get("context")
        target = self._preprompts[name].get("target")
        guidelines = self._preprompts[name].get("guidelines")
        self.execute_prompt(user_prompt, context, target, guidelines, modules)

    def execute_prompt(
        self,
        user_prompt: str,
        context: str = "code",
        target: str = "code",
        guidelines: List[str] = None,
        modules: List[str] = None,
    ):
        logging.info(f"Executing prompt {user_prompt}")
        guideline_prompt = self._read_guidelines(guidelines)
        request = Request(
            user_prompt=user_prompt,
            context=context,
            target=target,
            guideline_prompt=guideline_prompt,
            model=self._openai_model,
        )
        for module in self.codebase.get_modules(modules):
            if count_tokens(module.get(context)) > self.max_tokens_per_module:
                for entity in module.get_entities():
                    request.execute(entity)
                module.merge_entities(target)
            else:
                request.execute(module)
        self.file_handler.export_modifications(self.codebase, target)

    def _read_guidelines(self, guidelines: list):
        guideline_prompt = ""
        if guidelines is not None:
            for guideline in guidelines:
                if guideline in self._guidelines.keys():
                    guideline_prompt += self._guidelines[guideline] + "\n"
                else:
                    logging.warning(f"Guideline {guideline} not found")
            return guideline_prompt
        else:
            return None

    def apply_changes(self):
        logging.info("Applying changes")
        self.file_handler.make_backup_dir()
        self.file_handler.move_target_files_to_backup()
        self.file_handler.move_preview_files_to_target()

    def revert_changes(self):
        logging.info("Reverting changes")
        self.file_handler.move_target_files_to_preview()
        self.file_handler.move_backup_files_to_target()
        self.file_handler.reset_backup_files()

    def reject_changes(self):
        logging.info("Rejecting changes")
        self.file_handler.remove_preview_files()
