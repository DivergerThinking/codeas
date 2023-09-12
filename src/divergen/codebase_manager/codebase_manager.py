import ast
import glob
import os
from typing import List

from pydantic import BaseModel, PrivateAttr
from divergen.codebase_manager.module_parser import ModuleParser

class CodebaseManager(BaseModel):
    source_dir: str
    _modules: List[ModuleParser] = PrivateAttr(default_factory=list)
    
    def model_post_init(self, __context):
        self._parse_modules(self.source_dir)
            
    def get_modules(self):
        return self._modules
    
    def get_source_code(self, entity):
        return ast.unparse(entity)
    
    def modify_source_code(self, source_code, old_entity_code, new_entity_code):
        return source_code.replace(old_entity_code, new_entity_code)
        
    def get_docstrings(self, entity):
        return ast.get_docstring(entity)
    
    def _parse_modules(self, source_dir):
        file_paths = self._get_python_file_paths(source_dir)
        self._parse_python_files(file_paths)
        
    def _get_python_file_paths(self, path):
        return [
            pyfile for pyfile 
            in glob.glob(f"{path}/**/*.py", recursive=True) if 
            os.path.split(pyfile)[-1] != "__init__.py"
        ]
    
    def _parse_python_files(self, file_paths):
        for file_path in file_paths:
            module_parser = ModuleParser(path=file_path)
            with open(file_path) as source:
                content = ast.parse(source.read())
            module_parser.source_code = ast.unparse(content)
            module_parser.visit(content)
            module_parser.entities = module_parser.classes | module_parser.functions
            self._modules.append(module_parser)