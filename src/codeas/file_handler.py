import os
import subprocess

from pydantic import BaseModel, PrivateAttr

from codeas.codebase import Codebase


class FileHandler(BaseModel):
    """Class for handling files. It is used to export modifications to the codebase,
    and to apply or reject changes.

    Attributes
    ----------
    codebase : Codebase
        the codebase of the assistant
    backup_dir : str, optional
        the directory where the backup files are saved, by default ".codeas/backup"
    preview : bool, optional
        whether to make a preview of the changes, by default True
    add_test_prefix : bool, optional
        whether to add "test_" prefix to test files, by default True
    auto_format : bool, optional
        whether to auto format the files after exporting them, by default True
    format_command : str, optional
        the command used to auto format the files, by default "black"
    """

    backup_dir: str = ".codeas/backup"
    preview: bool = True
    add_test_prefix: bool = True
    auto_format: bool = True
    format_command: str = "black"
    _target_files: list = PrivateAttr(default_factory=list)
    _preview_files: list = PrivateAttr(default_factory=list)
    _backup_files: list = PrivateAttr(default_factory=list)

    def export_modifications(self, codebase: Codebase, target: str):
        """Export the modified modules to the target files.

        Parameters
        ----------
        codebase : Codebase
            the codebase of the assistant
        target : str
            the target of the modifications. It can be "code", "docs", or "tests".
        """
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
