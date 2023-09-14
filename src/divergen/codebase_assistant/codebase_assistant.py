import os
from pydantic import BaseModel, PrivateAttr

from divergen.codebase_manager import CodebaseManager
from divergen.prompt_manager import PromptManager

class CodebaseAssistant(BaseModel, arbitrary_types_allowed=True):
    source_dir: str
    backup_dir: str = ".backup"
    prompt_manager: PromptManager
    codebase_manager: CodebaseManager = CodebaseManager()
    _target_files: list = PrivateAttr(default_factory=list)
    _preview_files: list = PrivateAttr(default_factory=list)
    _backup_files: list = PrivateAttr(default_factory=list)
    
    def generate_docstrings(
        self,
        model_name: str = "chat-openai",
        model_params: dict = None,
        parser_name: str = "python_output",
        preview: bool = True
    ):
        self.reset_codebase()
        for module in self.codebase_manager.parse_modules(self.source_dir):
            for entity in module.entities:
                model_output = self.prompt_manager.execute(
                    template_name="generate-docstring.yaml", 
                    template_inputs={"code": entity.source_code},
                    model_name=model_name,
                    model_params=model_params,
                    parser_name=parser_name
                )
                module.source_code = module.source_code.replace(
                    entity.source_code, model_output
                )
            self.write_to_file(module.source_code, module.file_path, preview)
            break
    
    def reset_codebase(self):
        self.remove_backup_files()
        self.remove_preview_files()
        self._target_files = []
    
    def remove_backup_files(self):
        for file_path in self._backup_files:
            os.remove(file_path)
        self._backup_files = []
    
    def remove_preview_files(self):
        for file_path in self._preview_files:
            os.remove(file_path)
        self._preview_files = []
    
    def parse_model_output(self, model_output: str):
        return model_output.replace("```python", "").replace("```", "")

    def write_to_file(self, code: str, file_path: str, preview: bool = True):
        self._target_files.append(file_path)
        
        if preview:
            file_path = file_path.replace(".py", "_preview.py")
            self._preview_files.append(file_path)

        with open(file_path, "w") as f:
            f.write(code)
    
    def apply_changes(self, backup: bool = True):
        if backup:
            self._make_backup_dir()
            self._move_target_files_to_backup()
        
        self._move_preview_files_to_target()
    
    def revert_changes(self):
        self._move_target_files_to_preview()
        self._move_backup_files_to_target()
        self._backup_files = []
    
    def reject_changes(self):
        self.remove_preview_files()
    
    def _move_target_files_to_preview(self):
        for target_path, preview_path in zip(self._target_files, self._preview_files):
            os.rename(target_path, preview_path)
    
    def _move_backup_files_to_target(self):
        for backup_path, target_path in zip(
            self._backup_files, self._target_files
        ):
            os.rename(backup_path, target_path)

    def _make_backup_dir(self):
        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)
    
    def _move_target_files_to_backup(self):
        for target_path in self._target_files:
            backup_path = os.path.join(
                self.backup_dir, os.path.split(target_path)[-1]
            )
            os.rename(target_path, backup_path)
            self._backup_files.append(backup_path)
    
    def _move_preview_files_to_target(self):
        for preview_path, target_path in zip(self._preview_files, self._target_files):
            os.rename(preview_path, target_path)
        