import glob
import os
from typing import List

import tokencost
from pydantic import BaseModel


class Repo(BaseModel):
    repo_path: str
    files_paths: List[str] = []
    files_tokens: dict = {}
    included: List[bool] = []
    included_files_paths: List[str] = []
    included_files_tokens: List[int] = []

    def __init__(self, **data):
        super().__init__(**data)
        self.repo_path = os.path.abspath(self.repo_path)
        self.files_paths = self.get_files_paths()
        self.calculate_files_tokens()
        self.filter_files()

    def get_files_paths(self):
        absolute_paths = glob.glob(os.path.join(self.repo_path, "**"), recursive=True)
        return [
            os.path.relpath(path, self.repo_path)
            for path in absolute_paths
            if os.path.isfile(path)
        ]

    def calculate_files_tokens(self):
        for rel_file_path in self.files_paths:
            abs_file_path = os.path.join(self.repo_path, rel_file_path)
            try:
                content = self._read_file(abs_file_path)
                self.files_tokens[rel_file_path] = tokencost.count_string_tokens(
                    content, "gpt-4o-mini"
                )
            except Exception:
                self.files_tokens[rel_file_path] = None

    def _read_file(self, path):
        with open(path, "r") as f:
            return f.read()

    def filter_files(
        self, include_patterns: List[str] = [], exclude_patterns: List[str] = []
    ) -> List[bool]:
        self.included = []
        self.included_files_paths = []
        self.included_files_tokens = []
        for file_path in self.files_paths:
            tokens = self.files_tokens.get(file_path)
            if tokens is None or tokens == 0:
                self.included.append(False)
                continue

            if include_patterns and not any(
                self._match_path(file_path, pattern) for pattern in include_patterns
            ):
                self.included.append(False)
                continue

            if exclude_patterns and any(
                self._match_path(file_path, pattern) for pattern in exclude_patterns
            ):
                self.included.append(False)
                continue

            self.included.append(True)
            self.included_files_paths.append(file_path)
            self.included_files_tokens.append(tokens)

    def _match_path(self, path: str, pattern: str) -> bool:
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

    def read_file(self, file_path: str) -> str:
        with open(os.path.join(self.repo_path, file_path), "r") as f:
            return f.read()
