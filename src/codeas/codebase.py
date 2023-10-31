import glob
import os
from typing import Any, List

from pydantic import BaseModel, PrivateAttr, SkipValidation
from tree_sitter import Language, Parser

from codeas.entities import Module

LANG_EXTENSION_MAP = {"python": ".py", "java": ".java", "javascript": ".js"}


class Codebase(BaseModel):
    """Codebase is a collection of modules, while a module is a collection of entities,
    such as functions and classes, which are parsed from source code files.
    See the Module class for more information.

    Attributes
    ----------
    language : str
        code language name
    code_folder : str, optional
        folder where the source code is found, by default "./src/"
    docs_folder : str, optional
        folder where the documentation is found, by default "./docs/"
    tests_folder : str, optional
        folder where the tests are found, by default "./tests/"
    code_format : str, optional
        the source code format, by default ".py"
    docs_format : str, optional
        the documnetation format, by default ".md"
    tests_format : str, optional
        the tests format, by default ".py"
    """

    language: str
    parser: SkipValidation = None
    code_folder: str = "./src/"
    docs_folder: str = "./docs/"
    tests_folder: str = "./tests/"
    code_format: str = ""
    docs_format: str = ".md"
    tests_format: str = ""
    _modules: List[Module] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self.code_format = LANG_EXTENSION_MAP[self.language]
        self.tests_format = LANG_EXTENSION_MAP[self.language]
        self.parser = self._create_parser(self.language)

    def _create_parser(self, language) -> object:
        """Reads the tree sitter grammar file and sets the selected language.
        The grammar file is hardcoded by now. Pending test on different OS."""
        current_dir = os.path.dirname(os.path.realpath(__file__))
        language_grammar = Language(f"{current_dir}/tree-sitter-grammars.so", language)
        parser = Parser()
        parser.set_language(language_grammar)
        return parser

    def parse_modules(self):
        """Parse all the modules in the code folder and save them in the modules list."""
        self._check_code_folder()
        modules_paths = self._get_modules_paths(self.code_folder)
        for module_path in modules_paths:
            self.parse_module(module_path)

    def _check_code_folder(self):
        if not os.path.exists(self.code_folder):
            raise ValueError(
                f"Source code folder {self.code_folder} not found. Check your configurations in the assistant.yaml file."
            )

    def _get_modules_paths(self, path):
        return [
            file_path
            for file_path in glob.glob(f"{path}/**/*{self.code_format}", recursive=True)
            if os.path.split(file_path)[-1]
            != "__init__.py"  # TODO: should be generalized to other languages
        ]

    def parse_module(self, path: str):
        """Parse a module from a source code file.

        Parameters
        ----------
        path : str
            The path to the source code file
        """
        with open(path) as source:
            module_content = source.read()
        node = self.parser.parse(bytes(module_content, "utf8")).root_node
        rel_path = os.path.relpath(path, self.code_folder)
        name = (
            os.path.splitext(rel_path)[0]
            .replace(os.path.sep, ".")
            .strip(self.code_format)
        )
        module = Module(name=name, node=node, parser=self.parser)
        module.parse_entities()
        self._modules.append(module)

    def get_modules(self, module_names: list = None) -> List[Module]:
        """Return a list of modules. If module_names is None, return all modules."""
        if module_names is None:
            return self._modules
        else:
            return [self.get_module(module_name) for module_name in module_names]

    def get_module_names(self):
        """Return a list of module names."""
        return [module.name for module in self._modules]

    def get_module(self, name):
        for module in self._modules:
            if module.name == name:
                return module
        raise ValueError(f"Module {name} not found")

    def get_modified_modules(self):
        """Return a list of modules that have been modified."""
        self._set_module_modifications()
        return [module for module in self._modules if module.modified]

    def _set_module_modifications(self):
        for module in self._modules:
            for entity in module._entities:
                if entity.modified is True:
                    module.modified = True

    def get_path(
        self, module_name: str, target: str, prefix: str = "", suffix: str = ""
    ):
        """Return the path for a target file of a module.

        Parameters
        ----------
        module_name : str
            The name of the module
        target : str
            The target of the file. Options: "code", "docs", "tests"
        prefix : str, optional
            The prefix to add to the module name, by default ""
        suffix : str, optional
            The suffix to add to the module name, by default ""

        Returns
        -------
        str
            The path of the target file
        """
        target_folder = getattr(self, f"{target}_folder")
        target_format = getattr(self, f"{target}_format")
        module_path = module_name.replace(".", "/")
        module_head, module_tail = os.path.split(module_path)
        return os.path.join(
            target_folder,
            module_head,
            prefix + module_tail + suffix + target_format,
        )
