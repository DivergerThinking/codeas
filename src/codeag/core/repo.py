import glob
import os
from typing import List

from pydantic import BaseModel


class Repo(BaseModel):
    repo_path: str
    files_paths: List[str] = []
    files_tokens: dict = {}
    folders_paths: List[str] = []
    folders_tokens: dict = {}

    def __init__(self, **data):
        super().__init__(**data)
        self.repo_path = os.path.abspath(self.repo_path)
        self.get_files_paths()
        self.get_folders_paths()
        self.calculate_files_tokens()
        self.calculate_folders_tokens()

    def get_files_paths(self):
        absolute_paths = glob.glob(os.path.join(self.repo_path, "**"), recursive=True)
        self.files_paths = [
            os.path.relpath(path, self.repo_path)
            for path in absolute_paths
            if os.path.isfile(path)
        ]

    def get_folders_paths(self):
        absolute_paths = glob.glob(os.path.join(self.repo_path, "**"), recursive=True)
        self.folders_paths = [
            os.path.relpath(path, self.repo_path)
            for path in absolute_paths
            if os.path.isdir(path) and path != self.repo_path
        ]

    def calculate_files_tokens(self):
        for rel_file_path in self.files_paths:
            abs_file_path = os.path.join(self.repo_path, rel_file_path)
            try:
                content = self._read_file(abs_file_path)
                self.files_tokens[rel_file_path] = int(len(content) / 4)
            except Exception:
                self.files_tokens[rel_file_path] = None

    def _read_file(self, path):
        with open(path, "r") as f:
            return f.read()

    def calculate_folders_tokens(self):
        self.folders_tokens = {folder: 0 for folder in self.folders_paths}
        for file_path, tokens in self.files_tokens.items():
            if tokens is not None:
                folder = os.path.dirname(file_path)
                while folder and folder != ".":
                    if folder in self.folders_tokens:
                        self.folders_tokens[folder] += tokens
                    folder = os.path.dirname(folder)


class Filters(BaseModel):
    include_files: list = []
    exclude_files: list = []
    include_folders: list = []
    exclude_folders: list = []


class RepoSelector(BaseModel):
    repo: Repo

    def filter_files(self, filters: Filters) -> List[bool]:
        incl_files = []
        for file_path in self.repo.files_paths:
            tokens = self.repo.files_tokens.get(file_path)
            if tokens is None or tokens == 0:
                incl_files.append(False)
                continue

            if filters.include_files and not any(
                self._match_path(file_path, pattern)
                for pattern in filters.include_files
            ):
                incl_files.append(False)
                continue

            if filters.exclude_files and any(
                self._match_path(file_path, pattern)
                for pattern in filters.exclude_files
            ):
                incl_files.append(False)
                continue

            incl_files.append(True)

        return incl_files

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

    def filter_folders(self, incl_files: List[bool]) -> List[bool]:
        incl_folders = []
        folder_files_map = {}

        # Create a mapping of folders to their files
        for file_path, include in zip(self.repo.files_paths, incl_files):
            folder_path = os.path.dirname(file_path)
            if folder_path not in folder_files_map:
                folder_files_map[folder_path] = []
            folder_files_map[folder_path].append(include)

        # Determine whether to include each folder
        for folder_path in self.repo.folders_paths:
            if folder_path in folder_files_map and any(folder_files_map[folder_path]):
                incl_folders.append(True)
            else:
                incl_folders.append(False)

        return incl_folders


if __name__ == "__main__":
    repo = Repo(repo_path=".")
    selector = RepoSelector(repo=repo)
    filters = Filters(include_files=["*.py", "*.txt"])
    print(selector.filter_files(filters))
