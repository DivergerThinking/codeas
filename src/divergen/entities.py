import ast
from typing import Any, List

from pydantic import PrivateAttr, BaseModel


class _SearchMixin(BaseModel):
    def _search_by_name(self, name, entities):
        result = [entity for entity in entities if entity.node.name == name]
        self._check_search(result, name)
        return result[0]

    def _check_search(self, result, value):
        if len(result) == 0:
            raise ValueError(f"{value} not found")
        elif len(result) > 1:
            raise ValueError(f"Multiple {value} found: {result}")
        else:
            return result


class Entity(_SearchMixin, arbitrary_types_allowed=True):
    node: ast.AST
    code: str = ""
    docs: str = ""
    tests: str = ""
    code_modified: bool = False
    docs_modified: bool = False
    tests_modified: bool = False

    def model_post_init(self, __context: Any) -> None:
        self.code = self.get_code()

    def get(self, attr):
        return getattr(self, attr)

    def modify(self, attr, value):
        setattr(self, attr, value)
        setattr(self, f"{attr}_modified", True)
        if attr == "code":
            self.update_node(value)

    def update_node(self, code: str):
        ast_node = ast.parse(code)
        if isinstance(self, Module):
            self.node = ast_node
        else:
            self.node = ast_node.body[0]
        # ast_node is ast.Module, so we get body[0] to get the ClassDef or FunctionDef

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
    module_name: str
    _classes: List[Class] = PrivateAttr(default_factory=list)
    _functions: List[Entity] = PrivateAttr(default_factory=list)

    def get_entities(self) -> List[Entity]:
        return self._classes + self._functions

    def get_class(self, name):
        return self._search_by_name(name, self._classes)

    def get_function(self, name):
        return self._search_by_name(name, self._functions)

    def parse_entities(self):
        for node in self.node.body:
            if node.col_offset == 0:
                if isinstance(node, ast.FunctionDef):
                    function = Entity(node=node)
                    self._functions.append(function)
                elif isinstance(node, ast.ClassDef):
                    class_ = Class(node=node)
                    class_.parse_methods()
                    self._classes.append(class_)
