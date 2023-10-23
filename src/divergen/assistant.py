import logging
import os
from typing import Any, List

from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import AIMessage
from pydantic import BaseModel, PrivateAttr

from divergen.codebase import Codebase
from divergen.file_handler import FileHandler
from divergen.initializer import Initializer
from divergen.request import Request
from divergen.utils import count_tokens, read_yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class CodebaseAssistant(BaseModel, validate_assignment=True, extra="forbid"):
    codebase: Codebase = Codebase()
    file_handler: FileHandler = FileHandler()
    max_tokens_per_module: int = 2000
    model: str = "gpt-3.5-turbo"
    _prompts: dict = PrivateAttr(default_factory=dict)
    _openai_model: object = PrivateAttr(None)

    def model_post_init(self, __context: Any) -> None:
        if os.path.exists(".divergen"):
            self._overwrite_configs()
            self._set_prompts()
            self._set_openai_model()
            self._parse_codebase()

    def _overwrite_configs(self):
        _configs = read_yaml(".divergen/assistant.yaml")
        for attr, value in _configs.items():
            if getattr(self, attr) != value:
                setattr(self, attr, value)

    def _set_prompts(self):
        self._prompts = read_yaml(".divergen/prompts.yaml")
        self._add_guideline_prompts(self._prompts)

    def _add_guideline_prompts(self, prompts: dict):
        guidelines = prompts.get("guidelines")
        for prompt in prompts.values():
            prompt_guidelines = prompt.get("guidelines")
            if prompt_guidelines is not None:
                prompt["guideline_prompt"] = ""
                for prompt_guideline in prompt_guidelines:
                    if prompt_guideline in guidelines.keys():
                        prompt["guideline_prompt"] += (
                            guidelines[prompt_guideline] + "\n"
                        )
                    else:
                        err_msg = f"Guideline {prompt_guideline} not found"
                        logging.error(err_msg)
                        raise ValueError(err_msg)

    def _set_openai_model(self):
        if self.model == "fake":
            dummy_func = """def dummy_func():\n    pass"""
            msg = AIMessage(content=dummy_func)
            self._openai_model = FakeMessagesListChatModel(responses=[msg])
        else:
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
        instructions = self._prompts[name]["instructions"]
        target = self._prompts[name].get("target", "code")
        context = self._prompts[name].get("context", "code")
        guideline_prompt = self._prompts[name].get("guideline_prompt", "")
        self.execute_prompt(instructions, target, context, guideline_prompt, modules)

    def execute_prompt(
        self,
        instructions: str,
        target: str = "code",
        context: str = "code",
        guideline_prompt: List[str] = None,
        modules: List[str] = None,
    ):
        logging.info(f"Executing prompt {instructions}")
        request = Request(
            instructions=instructions,
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

    def apply_changes(self):
        logging.info("Applying changes")
        self.file_handler.make_backup_dir()
        # handling the case when we generate files for the first time
        # TODO: need to think about how to better handle this in general
        try:
            self.file_handler.move_target_files_to_backup()
        except FileNotFoundError:
            pass
        self.file_handler.move_preview_files_to_target()

    def revert_changes(self):
        # this mechanism for undoing is not valid under the new CLI logic and should be reviewed
        logging.info("Reverting changes")
        self.file_handler.move_target_files_to_preview()
        self.file_handler.move_backup_files_to_target()
        self.file_handler.reset_backup_files()

    def reject_changes(self):
        logging.info("Rejecting changes")
        self.file_handler.remove_preview_files()
