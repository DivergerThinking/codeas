import ast

from pydantic import BaseModel, Field

class ModuleParser(ast.NodeVisitor, BaseModel):
    """NOTE: currently only supports classes with one level of nested
    functions (i.e. methods) and nested functions with one level of nesting.
    Nested functions with more than one level of nesting will be ignored, as
    well as nested class methods.
    """
    path: str = ""
    source_code: str = ""
    functions: dict = Field(default_factory=dict)
    classes: dict = Field(default_factory=dict)
    methods: dict = Field(default_factory=dict)
    entities: dict = Field(default_factory=dict)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.col_offset == 0:
            self.functions[node.name] = node
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.functions[node.name + "." + item.name] = item
        self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef):
        if node.col_offset == 0:
            self.classes[node.name] = node
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.methods[node.name + "." + item.name] = item
        self.generic_visit(node)
