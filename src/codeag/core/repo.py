import copy
import os
from glob import glob
from typing import Dict, List

from pydantic import BaseModel


class Repo(BaseModel, extra="forbid"):
    repo_path: str = "."
    files_paths: List[str] = []
    files_tokens: Dict[str, int] = {}
    filters: Dict[str, List[str]] = {
        "include_dir": [],
        "exclude_dir": [],
        "include_files": [],
        "exclude_files": [],
    }
    incl_files_tokens: Dict[str, int] = {}
    excl_files_tokens: Dict[str, int] = {}
    dir_depth: int = 3
    incl_dir_tokens: Dict[str, int] = {}
    excl_dir_tokens: Dict[str, int] = {}
    incl_dir_nfiles: Dict[str, int] = {}
    excl_dir_nfiles: Dict[str, int] = {}

    def model_post_init(self, __context):
        self.get_files_paths()
        self.calculate_files_tokens()
        self.apply_filters()

    def get_files_paths(self):
        self.files_paths = glob(os.path.join(f"{self.repo_path}", "**"), recursive=True)

    def calculate_files_tokens(self):
        for file_path in self.files_paths:
            rel_file_path = os.path.relpath(file_path, self.repo_path)
            try:
                content = self._read_file(file_path)
                self.files_tokens[rel_file_path] = int(len(content) / 4)
            except Exception:
                self.files_tokens[rel_file_path] = None

    def _read_file(self, path):
        with open(path, "r") as f:
            return f.read()

    def apply_filters(self):
        self.filter_files_tokens()
        self.filter_dirs()

    def filter_files_tokens(self):
        self.incl_files_tokens = copy.deepcopy(self.files_tokens)
        for file_path, tokens in self.files_tokens.items():
            dir_path = os.path.split(file_path)[0]

            if tokens is None or tokens == 0:
                self.excl_files_tokens[file_path] = self.incl_files_tokens.pop(
                    file_path
                )
                continue

            if any(self.filters["include_files"]) and not any(
                self._match_path(file_path, pattern)
                for pattern in self.filters["include_files"]
            ):
                self.excl_files_tokens[file_path] = self.incl_files_tokens.pop(
                    file_path
                )
                continue

            if any(self.filters["exclude_files"]) and any(
                self._match_path(file_path, pattern)
                for pattern in self.filters["exclude_files"]
            ):
                self.excl_files_tokens[file_path] = self.incl_files_tokens.pop(
                    file_path
                )
                continue

            if any(self.filters["include_dir"]) and not any(
                self._match_path(dir_path, pattern)
                for pattern in self.filters["include_dir"]
            ):
                self.excl_files_tokens[file_path] = self.incl_files_tokens.pop(
                    file_path
                )
                continue

            if any(self.filters["exclude_dir"]) and any(
                self._match_path(dir_path, pattern)
                for pattern in self.filters["exclude_dir"]
            ):
                self.excl_files_tokens[file_path] = self.incl_files_tokens.pop(
                    file_path
                )
                continue

    def _match_path(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches the given pattern.

        If pattern includes '*', use startswith() for the part before '*'.
        Otherwise, check if the path starts with the pattern (for subdirectory support).
        """
        if pattern.endswith("/"):
            pattern = pattern[:-1]  # remove trailing slash

        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1] in path
        elif pattern.endswith("*"):
            prefix = pattern.split("*")[0]
            return path.startswith(prefix)
        elif pattern.startswith("*"):
            suffix = pattern.split("*")[1]
            return path.endswith(suffix)
        else:
            return path == pattern or path.startswith(pattern + os.path.sep)

    def filter_dirs(self):
        self.incl_dir_tokens, self.incl_dir_nfiles = {}, {}
        self._process_dirs(
            self.incl_files_tokens, self.incl_dir_tokens, self.incl_dir_nfiles
        )
        self.excl_dir_tokens, self.excl_dir_nfiles = {}, {}
        self._process_dirs(
            self.excl_files_tokens, self.excl_dir_tokens, self.excl_dir_nfiles
        )

    def _process_dirs(self, files_tokens, dir_tokens, dir_nfiles):
        for file_path, tokens in files_tokens.items():
            dir_parts = os.path.normpath(file_path).split(os.sep)
            for level in range(1, min(len(dir_parts), self.dir_depth) + 1):
                folder = os.sep.join(dir_parts[:level])
                folder_path = os.path.join(self.repo_path, folder)
                if os.path.isdir(folder_path):
                    if folder not in dir_tokens:
                        dir_tokens[folder] = 0
                        dir_nfiles[folder] = 0
                    dir_tokens[folder] += tokens if tokens else 0
                    dir_nfiles[folder] += 1

        # sorted_folders = dict(sorted(self.incl_dir_tokens.items()))

        # paths = list(sorted_folders.keys())
        # n_files = [folder_info["n_files"] for folder_info in sorted_folders.values()]
        # n_tokens = [folder_info["n_tokens"] for folder_info in sorted_folders.values()]
        # return paths, n_files, n_tokens
