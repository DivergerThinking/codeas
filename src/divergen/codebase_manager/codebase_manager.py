import glob
import os
from typing import Dict

from pydantic import BaseModel, PrivateAttr
from divergen.codebase_manager.module_parser import ModuleParser

class CodebaseManager(BaseModel):
    source_dir: str
    _modules: Dict[str, ModuleParser] = PrivateAttr(default_factory=dict)
    
    def get_codebase_source_code(self):
        codebase_source_code = ''
        for module_path, module_content in self._modules.items():
            codebase_source_code += (
                f"\n\n===========================\n"
                + f"Code for module {module_path}:\n"
                + "===========================\n\n"
                + f"{module_content.source_code}"
            )
        return codebase_source_code
    
    def get_module_source_code(self, module_name):
        module_path = self.get_module_path(module_name)
        module_content = self._modules[module_path]
        return module_content.source_code
    
    def get_entity_source_code(self, entity_name, module_name=None):
        if module_name is not None:
            module_path = self.get_module_path(module_name)
        else:
            module_path = self.get_entity_module_path(entity_name)
        module_content = self._modules[module_path]
        entity = module_content.entities[entity_name]
        return entity.source_code
    
    def parse_modules(self):
        modules_paths = self.get_modules_paths(self.source_dir)
        for module_path in modules_paths:
            self.parse_module(module_path)
    
    def parse_module(self, module_path):
        module_parser = ModuleParser()
        module_parser.parse_file(module_path)
        self._modules[module_path] = module_parser
        
    def get_modules_paths(self, dir_path):
        return [
            file_path for file_path
            in glob.glob(f"{dir_path}/**/*.py", recursive=True) if 
            os.path.split(file_path)[-1] != "__init__.py"
        ]
    
    def get_modules_names(self, dir_path):
        return [
            os.path.split(file_path)[-1] for file_path
            in glob.glob(f"{dir_path}/**/*.py", recursive=True) if 
            os.path.split(file_path)[-1] != "__init__.py"
        ]
    
    def get_module_path(self, module_name):
        modules_containing_module_name = [
            module_path 
            for module_path in self.get_modules_paths(self.source_dir)
            if os.path.split(module_path)[-1] == module_name
        ]
        if len(modules_containing_module_name) == 0:
            raise ValueError(f"Module {module_name} not found")
        elif len(modules_containing_module_name) > 1:
            raise ValueError(
                f"""Module {module_name} appears in more than one module: 
                {modules_containing_module_name}
                """
            )
        else:
            return modules_containing_module_name[0]
    
    def get_entity_module_path(self, entity_name):
        modules_containing_entity_name = [
            module_path
            for module_path, module_content in self._modules.items()
            if entity_name in module_content.entities.keys()
        ]
        if len(modules_containing_entity_name) == 0:
            raise ValueError(f"Entity {entity_name} not found")
        elif len(modules_containing_entity_name) > 1:
            raise ValueError(
                f"""Entity {entity_name} appears in more than one module: 
                {modules_containing_entity_name}
                """
            )
        else:
            return modules_containing_entity_name[0]