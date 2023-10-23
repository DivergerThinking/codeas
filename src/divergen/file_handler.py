import os
import subprocess

from pydantic import BaseModel, PrivateAttr

from divergen.codebase import Codebase


class FileHandler(BaseModel):
    backup_dir: str = ".divergen/backup"
    preview: bool = True
    add_test_prefix: bool = True
    auto_format: bool = True
    format_command: str = "black"
    _target_files: list = PrivateAttr(default_factory=list)
    _preview_files: list = PrivateAttr(default_factory=list)
    _backup_files: list = PrivateAttr(default_factory=list)

    def export_modifications(self, codebase: Codebase, target: str):
        # mechanism for adding test_ prefix to test files is not ideal. To be reviewed.
        prefix = "test_" if (self.add_test_prefix and target == "tests") else ""
        for module in codebase.get_modified_modules():
            path = codebase.get_path(module.name, target, prefix)
            self._target_files.append(path)
            if self.preview:
                path = codebase.get_path(module.name, target, prefix, "_preview")
                self._preview_files.append(path)
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            self._write_file(path, module.get(target))
            if self.auto_format:
                self._format_file(path)

    def _write_file(self, file_path: str, content: str):
        with open(file_path, "w") as f:
            f.write(content)

    def _format_file(self, file_path: str):
        if file_path.endswith(".py"):
            subprocess.run(f"{self.format_command} {file_path}", shell=True, check=True)

    def reset_target_files(self):
        self._target_files = []

    def reset_backup_files(self):
        self._backup_files = []

    def remove_backup_files(self):
        for file_path in self._backup_files:
            os.remove(file_path)
        self._backup_files = []

    def remove_preview_files(self):
        for file_path in self._preview_files:
            os.remove(file_path)
        self._preview_files = []

    def move_target_files_to_preview(self):
        for target_path, preview_path in zip(self._target_files, self._preview_files):
            os.rename(target_path, preview_path)

    def move_backup_files_to_target(self):
        for backup_path, target_path in zip(self._backup_files, self._target_files):
            os.rename(backup_path, target_path)

    def make_backup_dir(self):
        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)

    def move_target_files_to_backup(self):
        for target_path in self._target_files:
            backup_path = os.path.join(self.backup_dir, os.path.split(target_path)[-1])
            os.rename(target_path, backup_path)
            self._backup_files.append(backup_path)

    def move_preview_files_to_target(self):
        for preview_path, target_path in zip(self._preview_files, self._target_files):
            os.rename(preview_path, target_path)
