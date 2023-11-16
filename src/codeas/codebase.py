import os
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Union

import tree_sitter_languages
from pydantic import BaseModel, PrivateAttr
from tree_sitter import Parser

from codeas.entities import Module

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
    """Codebase is a collection of modules, while a module is a collection of entities,
    such as functions and classes, which are parsed from source code files.
    See the Module class for more information.
    """

    exclude_patterns: list = DEFAULT_EXCLUDE_PATTERNS
    include_file_patterns: list = DEFAULT_FILE_PATTERNS
    _modules: List[Module] = PrivateAttr(default_factory=list)
    _parser: Parser = PrivateAttr(None)

    def parse_modules(self):
        """Parse all the modules in the code folder and save them in the modules list."""
        for module_path in self.get_modules_paths():
            self.parse_module(module_path)

    def get_modules_paths(self):
        paths = []
        for path in self._get_paths_recursively("."):
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

    def parse_module(self, path: str):
        """Parse a module from a source code file.

        Parameters
        ----------
        path : str
            The path to the source code file
        """
        language_ext = os.path.splitext(path)[1]
        Language = LANG_EXTENSION_MAP[language_ext]
        self._set_parser(Language)
        with open(path) as source:
            module_content = source.read()
        node = self._parser.parse(bytes(module_content, "utf8")).root_node
        name = path.replace(os.path.sep, ".")
        module = Module(name=name, node=node, parser=self._parser)
        module.parse_entities()
        self._modules.append(module)

    def _set_parser(self, language) -> object:
        """Reads the tree sitter grammar file and sets the selected language.
        The grammar file is hardcoded by now. Pending test on different OS."""
        self._parser = Parser()
        self._parser.set_language(tree_sitter_languages.get_language(language))

    def get_tree(self):
        tree = ""
        for path_element in self._get_tree_recursively("."):
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

    def get_modules(self, module_names: Union[list, str] = None) -> List[Module]:
        """Return a list of modules. If module_names is None, return all modules."""
        if module_names is None:
            return self._modules
        elif isinstance(module_names, list):
            modules = []
            for module_name in module_names:
                try:
                    modules.append(self.get_module(module_name))
                except ValueError:
                    pass
            return modules
        elif isinstance(module_names, str):
            return [self.get_module(module_names)]

    def get_module(self, name):
        for module in self._modules:
            if module.name == name:
                return module
        raise ValueError(f"Module {name} not found")

    def get_module_names(self):
        """Return a list of module names."""
        return [module.name for module in self._modules]

    def add_module(self, name, content):
        self._modules.append(Module(name=name, new_content=content, modified=True))

    def get_modified_modules(self):
        """Return a list of modules that have been modified."""
        self._set_module_modifications()
        return [module for module in self._modules if module.modified]

    def _set_module_modifications(self):
        for module in self._modules:
            for entity in module._entities:
                if entity.modified is True:
                    module.modified = True
