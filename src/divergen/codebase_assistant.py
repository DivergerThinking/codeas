import logging
from typing import Any, List

from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, PrivateAttr

from divergen.codebase import Codebase
from divergen.file_handler import FileHandler
from divergen.request import Request
from divergen.utils import count_tokens, read_yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class CodebaseAssistant(BaseModel):
    config_path: str = None
    preprompts_path: str = None
    guidelines_path: str = None
    codebase: Codebase = Codebase()
    file_handler: FileHandler = FileHandler()
    max_tokens_per_module: int = 2000
    model: object = ChatOpenAI(callbacks=[StreamingStdOutCallbackHandler()])
    _preprompts: dict = PrivateAttr(default_factory=dict)
    _guidelines: dict = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.config_path:
            self._set_configs()
        if self.preprompts_path:
            self._preprompts = read_yaml(self.preprompts_path)
        if self.guidelines_path:
            self._guidelines = read_yaml(self.guidelines_path)

        # TODO: add error handler for when repository is not found
        self.codebase.parse_modules()

    def _set_configs(self):
        # TODO: overwrite self with config
        # TODO: add possibility to configure model from .yaml file
        # TODO: add model callbacks after model is initialized
        ...

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
            model=self.model,
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
        logging.info(f"Applying changes")
        self.file_handler.make_backup_dir()
        self.file_handler.move_target_files_to_backup()
        self.file_handler.move_preview_files_to_target()

    def revert_changes(self):
        logging.info(f"Reverting changes")
        self.file_handler.move_target_files_to_preview()
        self.file_handler.move_backup_files_to_target()
        self.file_handler.reset_backup_files()

    def reject_changes(self):
        logging.info(f"Rejecting changes")
        self.file_handler.remove_preview_files()
