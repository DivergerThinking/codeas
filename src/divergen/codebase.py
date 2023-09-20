"""
The below outlines the codebase hierarchy of attributes:

Codebase:
    Entities (Entity):
    _modules (Module(Entity))
        Elements:
        _functions (Entity)
        _classes (Class(Entity))
            _methods (Function)
"""
import os
import glob
import ast
from typing import List
from pydantic import BaseModel, PrivateAttr

class SearchMixin(BaseModel):
    def _search_by_path(self, path, entities):
        result = [
            entity for entity in entities
            if entity.path == path
        ]
        self._check_search(result, path)
        return result[0]

    def _search_by_name(self, name, entities):
        result = [
            entity for entity in entities
            if entity.node.name == name
        ]
        self._check_search(result, name)
        return result[0]
    
    def _search_by_line(self, line_no):
        ...
    
    def _check_search(self, result, value):
        if len(result) == 0:
            raise ValueError(f"{value} not found")
        elif len(result) > 1:
            raise ValueError(f"Multiple {value} found ")
        else:
            return result

class Entity(SearchMixin, arbitrary_types_allowed=True):
    path: str
    node: ast.AST
    modified: bool = False
    
    def add_docstring(self, text: str):
        self.remove_docstring()
        docstring = ast.Expr(value=ast.Str(s=text))
        self.node.body = [docstring] + self.node.body
        self.modified = True
    
    def remove_docstring(self):
        if self.has_docstring():
            self.node.body.pop(0)
            self.modified = True
    
    def has_docstring(self):
        return self.get_docstring() is not None
    
    def get_docstring(self):
        return ast.get_docstring(self.node)
    
    def get_code(self):
        return ast.unparse(self.node)
    
class Class(Entity):
    _methods: List[Entity] = PrivateAttr(default_factory=list)
    
    def parse_methods(self):
        for node in self.node.body:
            if isinstance(node, ast.FunctionDef):
                method = Entity(path=self.path, node=node)
                self._methods.append(method)

class Module(Entity):
    _classes: List[Class] = PrivateAttr(default_factory=list)
    _functions: List[Entity] = PrivateAttr(default_factory=list)
    
    def parse_elements(self):
        for node in self.node.body:
            if node.col_offset == 0:
                if isinstance(node, ast.FunctionDef):
                    function = Entity(path=self.path, node=node)
                    self._functions.append(function)
                elif isinstance(node, ast.ClassDef):
                    class_ = Class(path=self.path, node=node)
                    class_.parse_methods()
                    self._classes.append(class_)
    
    def get_class(self, name, path):
        module = self.get_module(path)
        return self._search_by_name(name, module._classes)
    
    def get_function(self, name, path):
        module = self.get_module(path)
        return self._search_by_name(name, module._functions)

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
            os.path.relpath(file_path, dir_path) for file_path
            in glob.glob(f"{dir_path}/**/*.py", recursive=True) if 
            os.path.split(file_path)[-1] != "__init__.py"
        ]
        
    def set_modules_modified_by_elements(self):
        for entity in self.get_elements():
            if entity.modified is True:
                module = self.get_module(entity.path)
                module.modified = True
    
    def get_modified_modules(self):
        self.set_modules_modified_by_elements()
        return [
            module for module in self._modules if module.modified
        ]
    
    def get_modules(self):
        return self._modules

    def get_module(self, path):
        return self._search_by_path(path, self._modules)
    
    def get_elements(self, classes=True, functions=True, methods=True) -> List[Entity]:
        elements = []
        for module in self._modules:
            if classes or methods:
                for class_ in module._classes:
                    if classes:
                        elements.append(class_)
                    if methods:
                        for method in class_._methods:
                            elements.append(method)

            if functions:
                for function in module._functions:
                    elements.append(function)

        return elements
    
    def get_element_names(self):
        return [element.node.name for element in self.get_elements()]

    def get_element(self, name) -> Entity:
        elements = [
            element for element_name, element 
            in zip(self.get_element_names(), self.get_elements())
            if element_name == name
        ]
        self._check_search(elements, name)
        return elements[0]