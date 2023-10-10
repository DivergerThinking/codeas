import ast
import glob
import os
from typing import List

from pydantic import BaseModel, PrivateAttr

from divergen.entities import Module


class Codebase(BaseModel):
    root: str = "."
    code_folder: str = "src"
    docs_folder: str = "docs"
    tests_folder: str = "tests"
    code_format: str = ".py"
    docs_format: str = ".md"
    tests_format: str = ".py"
    _modules: List[Module] = PrivateAttr(default_factory=list)

    def get_path(self, module_name: str, target: str, preview: bool = False):
        target_folder = getattr(self, f"{target}_folder")
        target_format = getattr(self, f"{target}_format")
        preview_str = "_preview" if preview else ""
        return os.path.join(
            self.root,
            target_folder,
            module_name.replace(".", "/") + preview_str + target_format,
        )

    def get_modules(self, module_names: list = None) -> List[Module]:
        if module_names is None:
            return self._modules
        else:
            return [self.get_module(module_name) for module_name in module_names]

    def get_module(self, name):
        for module in self._modules:
            if module.name == name:
                return module
        raise ValueError(f"Module {name} not found")

    def parse_modules(self):
        modules_paths = self._get_modules_paths(
            os.path.join(self.root, self.code_folder)
        )
        for module_path in modules_paths:
            self.parse_module(module_path)

    def parse_module(self, path):
        with open(path) as source:
            module_content = source.read()
        node = ast.parse(module_content)
        rel_path = os.path.relpath(path, os.path.join(self.root, self.code_folder))
        name = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
        module = Module(name=name, node=node)
        module.parse_entities()
        self._modules.append(module)

    def _get_modules_paths(self, path):
        return [
            file_path
            for file_path in glob.glob(f"{path}/**/*{self.code_format}", recursive=True)
            if os.path.split(file_path)[-1]
            != "__init__.py"  # TODO: should be generalized to other languages
        ]

    def get_modified_modules(self):
        self._set_module_modifications()
        return [module for module in self._modules if module.modified]

    def _set_module_modifications(self):
        for module in self._modules:
            for entity in module._entities:
                if entity.modified is True:
                    module.modified = True
