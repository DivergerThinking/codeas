"""
This outlines the following 

Codebase
    _modules (Module)
        _functions (FunctionDef)
        _classes (ClassDef)
            _methods (FunctionDef) (methods)
"""

import ast
from typing import List
from pydantic import BaseModel, PrivateAttr

class Entity(BaseModel):
    node: ast.AST
    
    def add_docstring(self, text: str):
        self.remove_docstring()
        docstring = ast.Expr(value=ast.Str(s=text))
        self.node.body = [docstring] + self.node.body
    
    def remove_docstring(self):
        if self.has_docstring():
            self.node.body.pop(0)
    
    def has_docstring(self):
        return self.get_docstring() is not None
    
    def get_docstring(self):
        return ast.get_docstring(self.node)
    
    def get_sourcecode(self):
        return ast.unparse()
        
class Function(Entity):
    node: ast.FunctionDef

class Class(Entity):
    node: ast.ClassDef
    _methods: List[Function] = PrivateAttr(default_factory=list)
    
    def parse_methods(self):
        for node in self.node.body:
            if isinstance(node, ast.FunctionDef):
                self._methods.append(Function(node))

class Module(Entity):
    path: str
    node: ast.Module
    _classes: List[Class] = PrivateAttr(default=list)
    _functions: List[Function] = PrivateAttr(default=list)
    
    def parse_elements(self):
        for node in self.node.body:
            if node.col_offset == 0:
                if isinstance(node, ast.FunctionDef):
                    self._functions.append(Function(node))
                elif isinstance(node, ast.ClassDef):
                    self._classes.append(Class(node))

class Codebase(BaseModel):
    source_dir: str
    _modules: List[Module] = PrivateAttr(default=list)
    
    def parse_modules(self):
        modules_paths = self.get_modules_paths(self.source_dir)
        for module_path in modules_paths:
            self.parse_module(module_path)
    
    def parse_module(self, module_path):
        with open(module_path) as source:
            module_content = source.read()
        node = ast.parse(module_content)
        module = Module(path=module_path, node=node)
        module.parse_entities()
        self._modules.append(module)
    
    def get_modules(self):
        return self._modules

    def get_module(self, path): 
        # TODO: path = self._get_exact_path(path)
        return self._search_by_attr("path", path, self._modules)
    
    def get_class(self, name, path):
        module = self.get_module(path)
        return self._search_by_attr("name", name, module._classes)
    
    def get_function(self, name, path):
        module = self.get_module(path)
        return self._search_by_attr("name", name, module._functions)
    
    def _search_by_attr(self, attr, value, entities):
        result = [
            entity for entity in entities
            if getattr(entity, attr) == value
        ]
        self._check_search(result, value)
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
    
    def get_functions(self, module_path):
        ...
    
    def get_classes(self, module_path): 
        ...