import ast
from typing import Any, List, Optional

from pydantic import BaseModel, PrivateAttr


class BaseEntity(BaseModel):
    node: object
    code: str = ""
    docs: str = ""
    tests: str = ""
    modified: bool = False

    def get(self, attr):
        return getattr(self, attr)

    def modify(self, attr, value):
        setattr(self, attr, value)
        self.modified = True
        if attr == "code":
            self.update_node(value)

    def update_node(self, code: str):
        ast_node = ast.parse(code)
        if isinstance(self, Module):
            self.node = ast_node
        elif isinstance(self, Entity):
            # ast_node is ast.Module, so we get body[0] to get the ClassDef/FunctionDef
            self.node = ast_node.body[0]
            self.update_module_node()

    def set_code(self):
        self.code = ast.unparse(self.node)


class Entity(BaseEntity, arbitrary_types_allowed=True):
    module: object
    body_idx: int

    def model_post_init(self, __context: Any) -> None:
        self.set_code()

    def update_module_node(self):
        self.module.node.body[self.body_idx] = self.node


class Module(BaseEntity):
    name: str
    _entities: List[Entity] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self.set_code()

    def get_entities(self, entity_names: Optional[list] = None) -> List[Entity]:
        if entity_names is None:
            return self._entities
        else:
            return [self.get_entity(entity_name) for entity_name in entity_names]

    def get_entity(self, name: str):
        results = [entity for entity in self.entities if entity.node.name == name]
        self._check_search(results, name)
        return results[0]

    def _check_search(self, result, value):
        if len(result) == 0:
            raise ValueError(f"{value} not found")
        elif len(result) > 1:
            raise ValueError(f"Multiple {value} found: {result}")
        else:
            return result

    def parse_entities(self):
        for idx, node in enumerate(self.node.body):
            if node.col_offset == 0 and isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                self._entities.append(Entity(node=node, module=self, body_idx=idx))

    def merge_entities(self, attr: str):
        if attr == "code":
            # since nodes are updated, we reset the code
            self.set_code()
        else:
            # reset the attribute to empty string and then add the attribute of each entity
            self.modify(attr, "")
            for entity in self.get_entities():
                module_attr = self.get(attr)
                module_attr += entity.get(attr)
