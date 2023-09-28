import ast
import glob
import os
from typing import List

from pydantic import PrivateAttr

from divergen._search_mixin import SearchMixin
from divergen.entities import Module


class Codebase(SearchMixin):
    source_dir: str
    _modules: List[Module] = PrivateAttr(default_factory=list)

    def parse_modules(self):
        modules_paths = self.get_modules_paths(self.source_dir)
        for module_path in modules_paths:
            self.parse_module(module_path)

    def parse_module(self, path):
        with open(os.path.join(self.source_dir, path)) as source:
            module_content = source.read()
        node = ast.parse(module_content)
        module = Module(path=path, node=node)
        module.parse_elements()
        self._modules.append(module)

    def get_modules_paths(self, dir_path):
        return [
            os.path.relpath(file_path, dir_path)
            for file_path in glob.glob(f"{dir_path}/**/*.py", recursive=True)
            if os.path.split(file_path)[-1] != "__init__.py"
        ]

    def get_modified_modules(self):
        self.set_modified_modules()
        return [module for module in self._modules if module.modified]

    def set_modified_modules(self):
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
        _entities = self.get_entities()
        return list(_entities.keys())

    def get_entities(self):
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
        return path.replace(".py", "")

    def get_entity(self, name):
        _entities = self.get_entities()
        return _entities[name]

    def get_module(self, path):
        return self._search_by_path(path, self._modules)

    def get_method(self, module_path, class_name, method_name):
        module = self.get_module(module_path)
        class_ = module.get_class(class_name)
        return class_.get_method(method_name)

    def get_class(self, module_path, class_name):
        module = self.get_module(module_path)
        return module.get_class(class_name)
