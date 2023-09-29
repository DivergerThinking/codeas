import logging
import os
from typing import Any
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel

from divergen.codebase import Codebase
from divergen.file_handler import FileHandler
from divergen.prompt_manager import PromptManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class CodebaseAssistant(BaseModel):
    codebase: Codebase
    prompt_manager: PromptManager = PromptManager(prompt_library="./assets/prompt-library")
    file_handler: FileHandler = FileHandler(backup_dir=".backup")

    def model_post_init(self, __context: Any) -> None:
        self.codebase.parse_modules()

    def run_action(self, action, **kwargs):
        if action == "Modify codebase":
            self.modify_codebase(**kwargs)
        elif action == "Generate markdown":
            self.generate_markdown(**kwargs)
        elif action == "Generate tests":
            self.generate_tests(**kwargs)
        elif action == "Ask LLM":
            self.ask_llm(**kwargs)

    def modify_codebase(
        self,
        template: str,
        entity_names: list,
        update_method: str = "modify_code",
        model: object = ChatOpenAI(
            streaming=True, callbacks=[StreamingStdOutCallbackHandler()]
        ),
        preview: bool = True,
        **user_input,
    ):
        logging.info(f"Modifying codebase with template: {template}")
        entities = self.get_entities(entity_names)
        prompts = self.get_prompts(entities, template, **user_input)
        update_args = self.run_llm(prompts, entities, model)
        self.update_codebase(update_args, update_method)
        self.file_handler.export_codebase(self.codebase, preview)
        return update_args

    def generate_markdown(
        self,
        template: str,
        entity_names: list,
        model: object = ChatOpenAI(
            streaming=True, callbacks=[StreamingStdOutCallbackHandler()]
        ),
        folder: str = "../docs",
        **user_input,
    ):
        logging.info(f"Modifying codebase with template: {template}")
        entities = self.get_entities(entity_names)
        prompts = self.get_prompts(entities, template, **user_input)
        docs_args = self.run_llm(prompts, entities, model)
        self.file_handler.export_markdown(docs_args, os.path.join(self.codebase.source_dir, folder))
        
    def generate_tests(
        self,
        template: str,
        entity_names: list,
        model: object = ChatOpenAI(
            streaming=True, callbacks=[StreamingStdOutCallbackHandler()]
        ),
        folder: str = "../tests",
        **user_input,
    ):
        logging.info(f"Modifying codebase with template: {template}")
        entities = self.get_entities(entity_names)
        prompts = self.get_prompts(entities, template, **user_input)
        tests_args = self.run_llm(prompts, entities, model)
        self.file_handler.export_tests(tests_args, os.path.join(self.codebase.source_dir, folder))
    
    def ask_llm(self, template: str, entity_names: list, model: object, **user_input):
        logging.info(f"Modifying codebase with template: {template}")
        entities = self.get_entities(entity_names)
        prompts = self.get_prompts(entities, template, **user_input)
        return self.run_llm(prompts, entities, model)

    def get_entities(self, entity_names):
        logging.info(f"Getting entities: {entity_names}")
        _entities = []
        for entity_name in entity_names:
            _entities.append(self.codebase.get_entity(entity_name))
        return _entities

    def get_prompts(self, entities: list, template: str, **user_input):
        logging.info(f"Getting prompts")
        _prompts = []
        for entity in entities:
            print("============")
            print(template)
            _prompts.append(
                self.prompt_manager.build(
                    template_path=template, code=entity.get_code(), **user_input
                )
            )
        return _prompts

    def run_llm(self, prompts, entities, model):
        logging.info(f"Running LLM")
        _output = []
        for entity, prompt in zip(entities, prompts):
            logging.info(f"Prompt:\n {prompt}")
            _output.append((entity, model.predict(prompt)))
        return _output

    def update_codebase(self, update_args, update_method):
        logging.info(f"Updating codebase")
        for entity, update_content in update_args:
            getattr(entity, update_method)(update_content)

    def apply_changes(self, backup: bool = True):
        logging.info(f"Applying changes")
        if backup:
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
