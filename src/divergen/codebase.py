import ast
import glob
import os
from typing import List

from pydantic import PrivateAttr, BaseModel

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
            != "__init__.py"  # should be generatlized to other languages
        ]

    def get_modified_modules(self):
        self._set_module_modifications()
        return [module for module in self._modules if module.modified]

    def _set_module_modifications(self):
        for module in self._modules:
            for class_ in module._classes:
                for method in class_._methods:
                    if method.modified is True:
                        class_.modified = True
                if class_.modified is True:
                    module.modified = True

            for function in module._functions:
                if function.modified is True:
                    module.modified = True

    # def list_entities(self):
    #     _entities = self.get_entities()
    #     return list(_entities.keys())

    # def get_entities(self):
    #     _entities = {}
    #     for module in self._modules:
    #         key = module.path
    #         _entities[key] = module
    #         for class_ in module._classes:
    #             key = f"{module.name}.{class_.node.name}()"
    #             _entities[key] = class_
    #             for method in class_._methods:
    #                 key = f"{module.name}.{class_.node.name}.{method.node.name}()"
    #                 _entities[key] = method
    #         for function in module._functions:
    #             key = f"{module.name}.{function.node.name}()"
    #             _entities[key] = function
    #     return _entities

    # def get_entity(self, name):
    #     _entities = self.get_entities()
    #     return _entities[name]
