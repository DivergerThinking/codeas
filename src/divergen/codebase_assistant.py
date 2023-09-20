from typing import Any
from pydantic import BaseModel

from divergen.codebase import Codebase
from divergen.prompt_manager import PromptManager
from divergen.file_handler import FileHandler

class CodebaseAssistant(BaseModel):
    codebase: Codebase
    prompt_manager: PromptManager
    file_handler: FileHandler = FileHandler(backup_dir=".backup")
    
    def model_post_init(self, __context: Any) -> None:
        self.codebase.parse_modules()
    
    def generate_docstrings(self, **user_input):
        for element in self.codebase.get_elements(classes=False):
            if not element.has_docstring():
                code = element.get_code()
                docstring = self._get_docstring(code, **user_input)
                docstring = self._clean_docstring(docstring)
                element.add_docstring(docstring)
        self.file_handler.export_modules(self.codebase)
    
    def _get_docstring(self, code, **user_input):
        return self.prompt_manager.execute_prompt(
            "generate_docstring", code=code, **user_input
        )
    
    def _clean_docstring(self, docstring):
        return docstring.replace("'''", "").replace('"""', "")
    
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