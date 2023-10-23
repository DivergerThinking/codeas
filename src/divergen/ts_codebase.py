import os
from tree_sitter import Language, Parser
from divergen.ts_entities import ts_Module

JAVA_LANGUAGE = Language("build/my-languages.so", "java")


class ts_Codebase:
    def __init__(self) -> None:
        JAVA_LANGUAGE = Language("build/my-languages.so", "java")
        self.parser = Parser()
        self.parser.set_language(JAVA_LANGUAGE)
        self._modules: list[ts_Module] = []
        self.code_format: str = ".java"
        self.code_folder: str = "./src/"

    def parse_module(
        self, module_name: str, dir_path: str, verbose: bool = False
    ):
        module_path = os.path.join(dir_path, module_name)
        with open(module_path, "r") as file:
            code = file.read()

        tree = self.parser.parse(bytes(code, "utf8"))
        module = ts_Module(
            name=module_name.strip(".java"), node=tree.root_node, parser=self.parser
        )
        module.parse_entities()

        return module

    def parse_modules(self, codebase=".", verbose=False):
        # TODO: Adapt to just walk over self.code_folder
        for dirpath, _, files in os.walk(codebase):
            for filename in files:
                if filename.endswith(self.code_format):
                    if verbose:
                        print(f"**** PARSING {filename} ****")
                    self._modules.append(self.parse_module(filename, dirpath))

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

    def get_path(self, module_name: str, target: str, preview: bool = False):
        target_folder = getattr(self, f"{target}_folder")
        target_format = getattr(self, f"{target}_format")
        preview_str = "_preview" if preview else ""
        return os.path.join(
            target_folder,
            module_name.replace(".", "/") + preview_str + target_format,
        )
