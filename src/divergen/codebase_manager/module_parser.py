import ast
from typing import List

from pydantic import BaseModel, Field

from divergen.codebase_manager.entity import Entity

class ModuleParser(ast.NodeVisitor, BaseModel):
    """NOTE: currently only supports classes with one level of nested
    functions (i.e. methods) and nested functions with one level of nesting.
    Nested functions with more than one level of nesting will be ignored, as
    well as nested class methods.
    """
    path: str = ""
    source_code: str = ""
    entities: List[Entity] = Field(default_factory=list)
    
    def model_post_init(self, __context):
        with open(self.path) as source:
            content = ast.parse(source.read())
            self.source_code = ast.unparse(content)
            self.visit(content)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.col_offset == 0:
            self.entities.append(
                Entity(
                    name=node.name, 
                    label="function", 
                    source_code=ast.unparse(node),
                    docstring=ast.get_docstring(node),
                    node=node
                )
            )
        self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef):
        if node.col_offset == 0:
            self.entities.append(
                Entity(
                    name=node.name, 
                    label="class", 
                    source_code=ast.unparse(node),
                    docstring=ast.get_docstring(node),
                    node=node
                )
            )
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.entities.append(
                        Entity(
                            name=f"{node.name}.{item.name}", 
                            label="method", 
                            source_code=ast.unparse(node),
                            docstring=ast.get_docstring(node),
                            node=item
                        )
                    )
        self.generic_visit(node)
