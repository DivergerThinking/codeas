import ast
from typing import List
from pydantic import PrivateAttr

from divergen._search_mixin import SearchMixin

class Entity(SearchMixin, arbitrary_types_allowed=True):
    path: str
    node: ast.AST
    modified: bool = False

    def modify_code(self, code: str):
        ast_node = ast.parse(code)
        if isinstance(self, Module):
            self.node = ast_node
        else:
            self.node = ast_node.body[0]  # ast_node is a Module node, so we get
        self.modified = True

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

    def get_method(self, name):
        return self.search_by_name(name, self._methods)


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

    def get_class(self, name):
        return self._search_by_name(name, self._classes)

    def get_function(self, name, path):
        module = self.get_module(path)
        return self._search_by_name(name, module._functions)
