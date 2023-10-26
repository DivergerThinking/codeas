import glob
import os
from typing import Literal

from tree_sitter import Language, Parser

from codeas.ts_entities import ts_Module

LANG_EXTENSION_MAP = {"python": ".py", "java": ".java", "javascript": ".js"}


class ts_Codebase:
    def __init__(self, language: Literal["python", "java", "javascript"]) -> None:
        "TS Changed."
        current_dir = os.path.dirname(os.path.realpath(__file__))
        LANGUAGE_GRAMMAR = Language(f"{current_dir}/tree-sitter-grammars.so", language)
        self.parser = Parser()
        self.parser.set_language(LANGUAGE_GRAMMAR)
        self._modules: list[ts_Module] = []
        self.code_format: str = LANG_EXTENSION_MAP[language]
        self.code_folder: str = "./src/"

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

    def parse_module(self, module_path: str):
        """TS. Changed."""
        with open(module_path, "r") as file:
            module_content = file.read()

        tree = self.parser.parse(bytes(module_content, "utf8"))
        rel_path = os.path.relpath(module_path, self.code_folder)
        name = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
        module = ts_Module(
            name=name.strip(self.code_format), node=tree.root_node, parser=self.parser
        )
        module.parse_entities()
        self._modules.append(module)

    def get_module(self, name):
        for module in self._modules:
            if module.name == name:
                return module
        raise ValueError(f"Module {name} not found")

    def get_modules(self, module_names: list = None) -> list[ts_Module]:
        if module_names is None:
            return self._modules
        else:
            return [self.get_module(module_name) for module_name in module_names]

    def get_modified_modules(self):
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
