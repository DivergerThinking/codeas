import glob
import os

from pydantic import BaseModel
from divergen.codebase_manager.module_parser import ModuleParser

class CodebaseManager(BaseModel):            
    def parse_modules(self, source_dir: str):
        file_paths = self._get_python_file_paths(source_dir)
        return self._parse_python_files(file_paths)
        
    def _get_python_file_paths(self, path):
        return [
            pyfile for pyfile 
            in glob.glob(f"{path}/**/*.py", recursive=True) if 
            os.path.split(pyfile)[-1] != "__init__.py"
        ]
    
    def _parse_python_files(self, file_paths):
        modules = []
        for file_path in file_paths:
            module_parser = ModuleParser(file_path=file_path)
            module_parser.parse_file()
            modules.append(module_parser)
        return modules