from typing import Any
from pydantic import BaseModel

from divergen.codebase import Codebase
from divergen.prompt_manager import PromptManager
from divergen.file_handler import FileHandler
from divergen.config import DEFAULT_CHAT_MODEL

class CodebaseAssistant(BaseModel):
    codebase: Codebase
    prompt_manager: PromptManager
    file_handler: FileHandler = FileHandler(backup_dir=".backup")
    
    def model_post_init(self, __context: Any) -> None:
        self.codebase.parse_modules()
        
    def modify_codebase(
        self, 
        template: str,
        context_args: list,
        update_method: str = "modify_code",
        preview: bool = True,
        **user_input
    ):
        entities = self.get_entities(context_args)
        prompts = self.get_prompts(entities, template, **user_input)
        update_args = self.run_llm(prompts, entities)
        self.update_codebase(update_args, update_method)
        self.file_handler.export_modules(self.codebase, preview)
    
    def generate_docs(self):
        ...
    
    def get_entities(self, context_args):
        _entities = []
        for args in context_args:
            _entities.append(self.codebase.get_entity(**args))
        return _entities
    
    def get_prompts(self, entities: list, template: str, **user_input):
        _prompts = []
        for entity in entities:
            _prompts.append(
                self.prompt_manager.build(
                    template=template, code=entity.get_code(), **user_input
                )
            )
        return _prompts
    
    def run_llm(self, prompts, entities):
        _output = []
        model = DEFAULT_CHAT_MODEL
        for entity, prompt in zip(entities, prompts):
            _output.append((entity, model.predict(prompt))) 
        return _output

    def update_codebase(self, update_args, update_method):
        for entity, update_content in update_args:
            getattr(entity, update_method)(update_content)
    
    def apply_changes(self, backup: bool = True):
        if backup:
            self.file_handler.make_backup_dir()
            self.file_handler.move_target_files_to_backup()
        
        self.file_handler.move_preview_files_to_target()
    
    def revert_changes(self):
        self.file_handler.move_target_files_to_preview()
        self.file_handler.move_backup_files_to_target()
        self.file_handler.reset_backup_files()
    
    def reject_changes(self):
        self.file_handler.remove_preview_files()