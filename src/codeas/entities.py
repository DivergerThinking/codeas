from typing import Any, List, Optional

from pydantic import BaseModel, PrivateAttr


class BaseEntity(BaseModel):
    """Base class for all entities, such as modules, classes, and functions.
    Each base entity is attached not only to its source code (self.code) but also to its
    documentation (self.docs) and tests (self.tests). This makes it easy to modify the
    source code, documentation, and tests of an entity at the same time.

    Attributes
    ----------
    node : object
        the ast node
    code : str, optional
        the code, by default ""
    docs : str, optional
        the docs, by default ""
    tests : str, optional
        the tests, by default ""
    modified : bool, optional
        flag to indicate if the entity has been modified, by default False
    """

    content: str = ""
    node: object = None
    parser: object = None
    modified: bool = False
    body: list = []

    def modify(self, content):
        """Modify the attribute and update the node.

        Parameters
        ----------
        attr : str
            the attribute to modify
        value : str
            the value to set
        """
        self.content = content
        self.modified = True
        if self.node is not None:
            self.update_node(content)

    def update_node(self, code: str):
        """Update the ast node with the new code.
        If the entity is not a module, we also update the module node.

        Parameters
        ----------
        code : str
            the new code
        """
        if isinstance(self, Module):
            node = self.parser.parse(bytes(code, "utf8")).root_node
            self.node = node
            self.set_content()
        elif isinstance(self, Entity):
            # TODO: With this node update, all start/end bytes references breaks. To review.
            self.node = self.parser.parse(bytes(code, "utf8")).root_node
            self.update_module_node()

    def set_content(self):
        if self.node is not None:
            self.content = self.node.text.decode()

    def set_body(self):
        if self.node is not None:
            self.body = [child for child in self.node.children]


class Entity(BaseEntity, arbitrary_types_allowed=True):
    """Entity class for classes and functions.

    Attributes
    ----------
    module : object
        the parent module
    body_idx : int
        the index of the node in the parent module's body
    """

    module: object
    body_idx: int

    def model_post_init(self, __context: Any) -> None:
        self.set_code()

    def update_module_node(self):
        self.module.body[self.body_idx] = self.node


class Module(BaseEntity):
    """Module class containing a list of entities."""

    name: str
    _entities: List[Entity] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self.set_content()
        self.set_body()

    def get_entities(self, entity_names: Optional[list] = None) -> List[Entity]:
        """Return a list of entities. If entity_names is None, return all entities."""
        if entity_names is None:
            return self._entities
        else:
            return [self.get_entity(entity_name) for entity_name in entity_names]

    def get_entity(self, name: str):
        """Return an entity by name.

        Parameters
        ----------
        name : str
            the name of the entity
        """
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
        """Parse the entities in the module."""
        # TODO: Right now this is useless, but should be adapted to each language.
        for idx, node in enumerate(self.body):
            if node.type in [
                "package_declaration",
                "line_comment",
                "class_declaration",
                "block_comment",
                "class_declaration",
            ]:
                self._entities.append(
                    Entity(node=node, parser=self.parser, module=self, body_idx=idx)
                )
