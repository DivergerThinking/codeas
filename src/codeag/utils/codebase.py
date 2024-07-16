import os
from fnmatch import fnmatch
from pathlib import Path

from pydantic import BaseModel, PrivateAttr
from tree_sitter import Language, Parser

from codeag.configs.extensions import EXTENSIONS


class Codebase(BaseModel):
    base_dir: str = os.getcwd()
    exclude_patterns: list = [".*", "__*"]
    include_file_patterns: list = []
    _parser: Parser = PrivateAttr(None)
    _language: Language = PrivateAttr(None)

    def get_prog_files_content(self):
        prog_files_content = {}
        file_paths = self.get_file_paths()
        for path in file_paths:
            ext = os.path.splitext(path)[1]
            if EXTENSIONS.get(ext, "") == "programming":
                files_content = f"# FILE PATH: {path}\n\n{self.get_file_content(path)}"
                prog_files_content[path] = files_content
        return prog_files_content

    def get_file_paths(self):
        paths = []
        for path in self._get_paths_recursively(self.base_dir):
            paths.append(path)
        return paths

    def get_file_path(self, name: str):
        matching_paths = []
        for path in self._get_paths_recursively(self.base_dir):
            if name == os.path.split(path)[1]:
                matching_paths.append(path)
        return matching_paths if matching_paths else None

    def get_file_names(self):
        names = []
        for path in self._get_paths_recursively(self.base_dir):
            names.append(os.path.split(path)[1])
        return names

    def get_file_content(self, path: str):
        with open(path, encoding="utf-8") as source:
            return source.read()

    def get_folder_paths(self):
        paths = []
        for path in self._get_paths_recursively(self.base_dir, include_dirs=True):
            paths.append(path)
        return paths

    def _get_paths_recursively(self, path: str, include_dirs: bool = False):
        paths = self._get_matching_paths(path)
        for path in paths:
            if path.is_dir():
                if include_dirs:
                    yield str(path)
                yield from self._get_paths_recursively(path, include_dirs)
            else:
                if not include_dirs:
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

    def get_tree(self, folder_only: bool = False, folder_path: str = ""):
        if folder_only is False:
            tree = ""
            for path_element in self._get_tree_recursively(
                os.path.join(self.base_dir, folder_path)
            ):
                tree += f"{path_element}\n"
        else:
            tree = ""
            for path_element in self._get_tree_recursively(
                os.path.join(self.base_dir, folder_path)
            ):
                if path_element.endswith("/"):  # only add directories to the tree
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
