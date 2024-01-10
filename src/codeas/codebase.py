import os
from collections import namedtuple
from fnmatch import fnmatch
from pathlib import Path

import tree_sitter_languages
from pydantic import BaseModel, PrivateAttr
from tree_sitter import Language, Parser

LANG_EXTENSION_MAP = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".cs": "c_sharp",
    ".rs": "rust",
    ".rb": "ruby",
    ".c": "c",
    ".go": "go",
    ".php": "php",
}
DEFAULT_FILE_PATTERNS = [f"*{ext}" for ext in LANG_EXTENSION_MAP.keys()]
DEFAULT_EXCLUDE_PATTERNS = [".*", "__*"]


class Codebase(BaseModel):
    base_dir: str = "."
    exclude_patterns: list = DEFAULT_EXCLUDE_PATTERNS
    include_file_patterns: list = DEFAULT_FILE_PATTERNS
    _parser: Parser = PrivateAttr(None)
    _language: Language = PrivateAttr(None)

    def get_modules_paths(self):
        paths = []
        for path in self._get_paths_recursively(self.base_dir):
            paths.append(path)
        return paths

    def _get_paths_recursively(self, path: str):
        paths = self._get_matching_paths(path)
        for path in paths:
            if path.is_dir():
                yield from self._get_paths_recursively(path)
            else:
                yield str(path)

    def _get_matching_paths(self, path):
        return list(
            path
            for path in Path(path).iterdir()
            if self._not_match(path, self.exclude_patterns)
            and self._match(path, self.include_file_patterns)
        )

    def _not_match(self, path: Path, patterns: list):
        if any(patterns):
            for pattern in patterns:
                if fnmatch(path.name, pattern):
                    return False
            return True
        else:
            return True

    def _match(self, path: Path, file_patterns: list, match_dir: bool = False):
        if any(file_patterns):
            if path.is_file():
                return any([fnmatch(path.name, pattern) for pattern in file_patterns])
            if match_dir and path.is_dir():
                return any(
                    [any(list(path.glob(f"**/{pattern}"))) for pattern in file_patterns]
                )
        return True

    def parse_root_node(self, path: str):
        self._set_parser(path)
        with open(path) as source:
            module_content = source.read()
        return self._parser.parse(bytes(module_content, "utf8")).root_node

    def _set_parser(self, path: str):
        """Reads the tree sitter grammar file and sets the selected language.
        The grammar file is hardcoded by now. Pending test on different OS."""
        language_ext = os.path.splitext(path)[1]
        language = LANG_EXTENSION_MAP[language_ext]
        self._language = tree_sitter_languages.get_language(language)
        self._parser = Parser()
        self._parser.set_language(self._language)

    def get_tree(self):
        tree = ""
        for path_element in self._get_tree_recursively(self.base_dir):
            tree += f"{path_element}\n"
        return tree

    def _get_tree_recursively(self, path: str, prefix: str = ""):
        paths = self._get_matching_paths(path)
        space = "    "
        branch = "│   "
        tee = "├── "
        last = "└── "
        # paths each get pointers that are ├── with a final └── :
        pointers = [tee] * (len(paths) - 1) + [last]
        for pointer, path in zip(pointers, paths):
            if path.is_dir() and self._match(path, self.include_file_patterns, True):
                yield prefix + pointer + path.name + "/"
            elif path.is_file():
                yield prefix + pointer + path.name

            if path.is_dir():  # extend the prefix and recurse:
                extension = branch if pointer == tee else space
                # i.e. space because last, └── , above so no more |
                yield from self._get_tree_recursively(path, prefix=prefix + extension)

    def get_standalone_functions(self, path: str, name: str = None):
        functions = self.get_functions(path, name)
        methods = self.get_methods(path, name)
        return list(set(functions).difference(methods))

    def get_functions(self, path: str, name: str = None):
        root_node = self.parse_root_node(path)
        if name and "." in name:
            class_name, function_name = name.split(".")
            return self.get_methods(path, function_name, class_name)
        else:
            query_scm = """
            (function_definition
            name: (identifier) @function_name) 
            """.strip()
            query = self._language.query(query_scm)
            Function = namedtuple("Function", "name code node")
            functions = []
            for node, _ in query.captures(root_node):
                if name:
                    if node.text.decode() == name:
                        functions.append(
                            Function(
                                name=node.text.decode(),
                                code=node.parent.text.decode(),
                                node=node.parent,
                            )
                        )
                else:
                    functions.append(
                        Function(
                            name=node.text.decode(),
                            code=node.parent.text.decode(),
                            node=node.parent,
                        )
                    )
            return functions

    def get_methods(self, path: str, name: str = None, class_name: str = None):
        root_node = self.parse_root_node(path)
        query_scm = """
        (class_definition
            name: (identifier) @class_name
            body: (_
            (function_definition
                name: (identifier) @method_name))
        )
        """.strip()
        if class_name:
            query_scm = "(" + query_scm + f"(eq? @class_name {class_name}))"
        query = self._language.query(query_scm)
        Function = namedtuple("Function", "name code node")
        functions = []
        for node, tag in query.captures(root_node):
            if tag == "method_name":  # filter out the class_name tags
                if name:
                    if node.text.decode() == name:
                        functions.append(
                            Function(
                                name=node.text.decode(),
                                code=node.parent.text.decode(),
                                node=node.parent,
                            )
                        )
                else:
                    functions.append(
                        Function(
                            name=node.text.decode(),
                            code=node.parent.text.decode(),
                            node=node.parent,
                        )
                    )
        return functions

    def get_classes(self, path: str, name: str = None):
        root_node = self.parse_root_node(path)
        query_scm = """
        (class_definition
        name: (identifier) @class_name) 
        """.strip()
        query = self._language.query(query_scm)
        Class = namedtuple("Class", "name code node")
        classes = []
        for node, _ in query.captures(root_node):
            if name:
                if node.text.decode() == name:
                    classes.append(
                        Class(
                            name=node.text.decode(),
                            code=node.parent.text.decode(),
                            node=node.parent,
                        )
                    )
            else:
                classes.append(
                    Class(
                        name=node.text.decode(),
                        code=node.parent.text.decode(),
                        node=node.parent,
                    )
                )
        return classes

    def get_imports(self, path: str):
        root_node = self.parse_root_node(path)
        Import = namedtuple("Import", "name code node")
        imports = []
        for node in root_node.children:
            if node.type in ["import_statement", "import_from_statement"]:
                imports.append(Import(code=node.text.decode(), node=node))
        return imports

    def get_imports_lines(self, path: str):
        root_node = self.parse_root_node(path)
        imports_lines = []
        for node in root_node.children:
            if node.type in ["import_statement", "import_from_statement"]:
                imports_lines.append(node.start_point[0])
        return imports_lines

    def get_file_structure(self, path: str):
        relevant_lines = set()
        for class_ in self.get_classes(path):
            relevant_lines.update(self._get_definition_lines(class_.node))
        for function_ in self.get_functions(path):
            relevant_lines.update(self._get_definition_lines(function_.node))
        relevant_lines.update(self.get_imports_lines(path))
        file_lines = self._read_files_lines(path)
        file_subset = self._read_subset_from_lines(file_lines, relevant_lines)
        return f"# {path}\n" + "".join(file_subset)

    def _get_definition_lines(self, node):
        lines = set()
        for child_node in node.children:
            if child_node.type in ["parameters", "identifier", "argument_list"]:
                lines.update([child_node.start_point[0]])
        return lines

    def _read_files_lines(self, path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines

    def _read_subset_from_lines(self, lines, subset_lines):
        subset = []
        for i, line in enumerate(lines):
            if i in subset_lines:
                subset.append(line)
        return subset
