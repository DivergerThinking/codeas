import ast
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

class Entity(BaseModel):
    label: Literal["class", "function", "method"]
    source_code: str
    docstring: Optional[str]
    node: object

class ModuleParser(ast.NodeVisitor, BaseModel):
    """NOTE: currently only supports classes with one level of nested
    functions (i.e. methods) and nested functions with one level of nesting.
    Nested functions with more than one level of nesting will be ignored, as
    well as nested class methods.
    """
    source_code: str = ""
    entities: Dict[str, Entity] = Field(default_factory=dict)
    
    def parse_file(self, file_path: str):
        with open(file_path) as source:
            content = ast.parse(source.read())
            self.source_code = ast.unparse(content)
            self.visit(content)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.col_offset == 0:
            self.entities.update(
                {
                    node.name: Entity(
                        label="function", 
                        source_code=ast.unparse(node),
                        docstring=ast.get_docstring(node),
                        node=node
                    )
                }
            )
        self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef):
        if node.col_offset == 0:
            self.entities.update(
                {
                    node.name: Entity(
                        label="class", 
                        source_code=ast.unparse(node),
                        docstring=ast.get_docstring(node),
                        node=node
                    )
                }
            )
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.entities.update(
                        {
                            f"{node.name}.{item.name}": Entity(
                                label="method", 
                                source_code=ast.unparse(item),
                                docstring=ast.get_docstring(item),
                                node=item
                            )
                        }
                    )
        self.generic_visit(node)
