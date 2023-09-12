from pydantic import BaseModel

from divergen.codebase_manager import CodebaseManager
from divergen.prompt_manager import PromptManager

class CodebaseAssistant(BaseModel, arbitrary_types_allowed=True):
    code_manager: CodebaseManager
    prompt_manager: PromptManager = PromptManager()
    
    def generate_docstrings(self):
        for module in self.code_manager.get_modules():
            for entity in module.entities.values():
                # TODO: Modify module.entities to be a list of entities.name, entities.source_code, entities.docstring, etc.
                entity_source_code = self.code_manager.get_source_code(entity)
                prompt = self.prompt_manager.build_prompt(
                    "generate_class_docstring", {"code": entity_source_code}
                )
                model_output = self.prompt_manager.execute_prompt(prompt)
                # TODO parse model_output to remove the ```python and ``` from the beginning and end
                new_module_source_code = self.code_manager.modify_source_code(
                    module.source_code, entity_source_code, model_output.content
                )
                preview_path = module.path.replace(".py", "_preview.py")
                self.write_new_source_code(new_module_source_code, preview_path)
                break # TODO: Remove this break. This is only for testing purposes.
    
    def write_new_source_code(self, code: str, output_path: str):
        with open(output_path, "w") as f:
            f.write(code)
        