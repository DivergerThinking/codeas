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

    def get_path(self, module_name, attr):
        attr_folder = getattr(self, f"{attr}_folder")
        file_format = getattr(self, f"{attr}_format")
        return os.path.join(self.root, attr_folder, module_name + file_format)

    def get_modules(self, module_names: list = None) -> List[Module]:
        if module_names is None:
            return self._modules
        else:
            return [self.get_module(module_name) for module_name in module_names]

    def get_module(self, name):
        return self.modules[name]

    def get_method(self, module_name, class_name, method_name):
        module = self.get_module(module_name)
        class_ = module.get_class(class_name)
        return class_.get_method(method_name)

    def get_class(self, module_name, class_name):
        module = self.get_module(module_name)
        return module.get_class(class_name)

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
        name = os.path.relpath(path, os.path.join(self.root, self.code_folder))
        module = Module(module_name=name, node=node)
        module.parse_entities()
        self._modules.append(module)

    def _get_modules_paths(self, dir_path):
        return [
            file_path
            for file_path in glob.glob(
                f"{dir_path}/**/*{self.code_format}", recursive=True
            )
            if os.path.split(file_path)[-1]
            != "__init__.py"  # should be generatlized to other languages
        ]

    def get_modified_modules(self):
        # TODO ADJUST TO NEW STRUCTURE WITH CODE, TESTS, DOCS
        self._set_modified_modules()
        return [module for module in self._modules if module.modified]

    def _set_modified_modules(self):
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

    def list_entities(self):
        # TODO ADJUST TO NEW STRUCTURE WITH CODE, TESTS, DOCS
        _entities = self.get_entities()
        return list(_entities.keys())

    def get_entities(self):
        # TODO ADJUST TO NEW STRUCTURE WITH CODE, TESTS, DOCS
        _entities = {}
        for module in self._modules:
            key = module.path
            _entities[key] = module
            for class_ in module._classes:
                key = f"{self._remove_extension(module.path)}.{class_.node.name}()"
                _entities[key] = class_
                for method in class_._methods:
                    key = f"{self._remove_extension(module.path)}.{class_.node.name}.{method.node.name}()"
                    _entities[key] = method
            for function in module._functions:
                key = f"{self._remove_extension(module.path)}.{function.node.name}()"
                _entities[key] = function
        return _entities

    def _remove_extension(self, path):
        # TODO ADJUST TO NEW STRUCTURE WITH CODE, TESTS, DOCS
        return path.replace(".py", "")

    def get_entity(self, name):
        _entities = self.get_entities()
        # TODO ADJUST TO NEW STRUCTURE WITH CODE, TESTS, DOCS
        return _entities[name]
