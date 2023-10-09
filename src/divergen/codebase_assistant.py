import logging
from typing import Any, Union, List
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

from divergen.codebase import Codebase
from divergen.entities import Module
from divergen.file_handler import FileHandler
from divergen.utils import count_token, read_yaml
from divergen.request import Request

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class CodebaseAssistant(BaseModel):
    codebase: Codebase = Codebase()
    preprompts_path: str = "./configs/preprompts.yaml"
    preprompts: dict = Field(default_factory=dict)
    guidelines_path: str = "./configs/guidelines.yaml"
    guidelines: dict = Field(default_factory=dict)
    max_tokens_per_module = 2000
    model: ChatOpenAI = ChatOpenAI(callbacks=[StreamingStdOutCallbackHandler()])
    file_handler: FileHandler = FileHandler(backup_dir=".backup")

    def model_post_init(self, __context: Any) -> None:
        self.codebase.parse_modules()
        self._read_config_files()

    def _read_config_files(self):
        if isinstance(self.preprompts, str):
            self.preprompts = read_yaml(self.preprompts)
        if isinstance(self.guidelines, str):
            self.guidelines = read_yaml(self.guidelines)

    def execute_preprompt(self, name: str, module_names: list = None):
        prompt = self.preprompts[name].get("prompt")
        context = self.preprompts[name].get("context")
        target = self.preprompts[name].get("target")
        guidelines = self.preprompts[name].get("guidelines")
        self.execute_prompt(prompt, context, target, guidelines, module_names)

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
            if count_token(module.get_context(context)) > self.max_tokens_per_module:
                entities = module.get_entities()
                for entity in entities:
                    request.execute(entity)
                module.merge_entities(target)
            else:
                request.execute(module)
        self.file_handler.export_modifications(target, self.codebase)

    def _read_guidelines(self, guidelines: list):
        ...

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
