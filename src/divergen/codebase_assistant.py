import logging
from typing import Any
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

from divergen.codebase import Codebase
from divergen.file_handler import FileHandler
from divergen.utils import count_tokens, read_yaml
from divergen.request import Request

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
    preprompts: dict = Field(default_factory=dict)
    guidelines: dict = Field(default_factory=dict)
    # TODO: make preprompts and guidelines private attributes

    def model_post_init(self, __context: Any) -> None:
        if self.config_path:
            self._set_configs()
        if self.preprompts_path:
            self.preprompts = read_yaml(self.preprompts_path)
        if self.guidelines_path:
            self.guidelines = read_yaml(self.guidelines_path)

        # TODO: add error handler for when repository is not found
        self.codebase.parse_modules()

    def _set_configs(self):
        # TODO: implement this method
        # TODO: add possibility to configure model from .yaml file
        # TODO: add model callbacks after model is initialized
        ...

    def execute_preprompt(self, name: str, module_names: list = None):
        logging.info(f"Executing preprompt {name}")
        user_prompt = self.preprompts[name].get("user_prompt")
        context = self.preprompts[name].get("context")
        target = self.preprompts[name].get("target")
        guidelines = self.preprompts[name].get("guidelines")
        self.execute_prompt(user_prompt, context, target, guidelines, module_names)

    def execute_prompt(
        self,
        user_prompt: str,
        context: str = "code",
        target: str = "code",
        guidelines: list = None,
        module_names: list = None,
    ):
        guideline_prompt = self._read_guidelines(guidelines)
        request = Request(
            user_prompt=user_prompt,
            context=context,
            target=target,
            guideline_prompt=guideline_prompt,
            model=self.model,
        )
        modules = self.codebase.get_modules(module_names)
        for module in modules:
            if count_tokens(module.get(context)) > self.max_tokens_per_module:
                entities = module.get_entities()
                for entity in entities:
                    request.execute(entity)
                module.merge_entities(target)
            else:
                request.execute(module)
        self.file_handler.export_modifications(self.codebase, target)

    def _read_guidelines(self, guidelines: list):
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
