import os
from pydantic import PrivateAttr
import pyperclip

from divergen.codebase_manager import CodebaseManager
from divergen.prompt_manager import PromptManager

class CodebaseAssistant(CodebaseManager):
    backup_dir: str = ".backup"
    prompt_manager: PromptManager
    _target_files: list = PrivateAttr(default_factory=list)
    _preview_files: list = PrivateAttr(default_factory=list)
    _backup_files: list = PrivateAttr(default_factory=list)
    
    def explain_codebase(
        self,
        entity_name: str = None,
        module_name: str = None,
        copy_to_clipboard: bool = True
    ):
        self.reset_codebase()
        self.parse_modules()
        if entity_name is not None:
            source_code = self.get_entity_source_code(entity_name, module_name)
        elif module_name is not None:
            source_code = self.get_module_source_code(module_name)
        else:
            source_code = self.get_codebase_source_code()
        
        if copy_to_clipboard:
            prompt = self.prompt_manager.build_template(
                template_name="explain-codebase.yaml", 
                template_inputs={"code":source_code}
            )
            pyperclip.copy(prompt)
        else:
            return self.execute_generate_docstring_template(
                template_inputs={"code":source_code}
            )
            
    
    def generate_docstrings(
        self,
        entity_name: str = None,
        module_name: str = None,
        preview: bool = True
    ):
        self.reset_codebase()
        self.parse_modules()
        if entity_name is not None:
            self.generate_entity_docstrings(entity_name, module_name, preview)
        elif module_name is not None:
            self.generate_module_docstrings(module_name, preview)
        else:
            self.generate_codebase_docstrings(preview)
    
    def generate_entity_docstrings(self, entity_name, module_name=None, preview=True):
        if module_name is not None:
            module_path = self.get_module_path(module_name)
            module_source_code = self.get_module_source_code(module_name)
            entity_source_code = self.get_entity_source_code(entity_name, module_name)
        else:
            module_path = self.get_entity_module_path(entity_name)
            module_source_code = self._modules[module_path].source_code
            entity_source_code = self.get_entity_source_code(entity_name)
        model_output = self.execute_generate_docstring_template(
            template_inputs={"code": entity_source_code}
        )
        self.write_to_file(
            content=module_source_code.replace(entity_source_code, model_output),
            file_path=module_path,
            preview=preview
        )
        
    def generate_module_docstrings(self, module_name, preview=True):
        module_path = self.get_module_path(module_name)
        module_source_code = self.get_module_source_code(module_name)
        model_output = self.execute_generate_docstring_template(
            template_inputs={"code": module_source_code}
        )
        self.write_to_file(
            content=module_source_code.replace(module_source_code, model_output),
            file_path=module_path,
            preview=preview
        )
        
    def generate_codebase_docstrings(self, preview):
        for module_name in self.get_modules_names():
            self.generate_module_docstrings(module_name, preview)
    
    def execute_generate_docstring_template(self, template_inputs):
        return self.prompt_manager.execute_template(
            template_name="generate-docstring.yaml", 
            template_inputs=template_inputs,
            # model_name="fake",
            model_name = "chat-openai",
            model_params=None,
            parser_name="python_output"
        )
    
    def execute_explain_codebase_template(self, template_inputs):
        return self.prompt_manager.execute_template(
            template_name="explain-codebase.yaml", 
            template_inputs=template_inputs,
            # model_name="fake", 
            model_name = "chat-openai",
            model_params=None,
            parser_name=None
        )
    
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

    def write_to_file(self, content: str, file_path: str, preview: bool = True):
        self._target_files.append(file_path)
        
        if preview:
            file_path = file_path.replace(".py", "_preview.py")
            self._preview_files.append(file_path)

        with open(file_path, "w") as f:
            f.write(content)
    
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
        