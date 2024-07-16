import json
import logging
import os

from codeag.configs.command_args import COMMAND_ARGS
from codeag.configs.extensions import EXTENSIONS
from codeag.utils.codebase import Codebase


class Retriever:
    def __init__(self, codebase: Codebase):
        self.codebase = codebase

    def get_files_content(self):
        files_content = {}
        file_paths = self.codebase.get_file_paths()
        for path in file_paths:
            ext = os.path.splitext(path)[1]
            if EXTENSIONS.get(ext, "") == "programming":
                content = (
                    f"# FILE PATH: {path}\n\n{self.codebase.get_file_content(path)}"
                )
                files_content[path] = content
        return files_content

    def get_file_descriptions(self):
        descriptions_contents = self.read_output_contents(
            COMMAND_ARGS["extract_file_descriptions"].output_path
        )
        descriptions_str = ""
        for path, content in descriptions_contents.items():
            descriptions_str += f'File: {path}:\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return descriptions_str

    def get_directory_descriptions(self):
        descriptions_contents = self.read_output_contents(
            COMMAND_ARGS["extract_directory_descriptions"].output_path
        )
        descriptions_str = ""
        for path, content in descriptions_contents.items():
            descriptions_str += f'Directory: {path}:\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return descriptions_str

    def get_labels_count(self):
        labels_contents = self.read_output_contents(
            COMMAND_ARGS["extract_documentation_labels"].output_path
        )
        labels_count = self.count_labels(labels_contents)
        sorted_labels_count = self.sort_count(labels_count)
        return str(sorted_labels_count)

    def count_labels(self, labels_contents):
        label_counts = {}
        for labels in labels_contents.values():
            for label in labels["labels"]:
                if label in label_counts:
                    label_counts[label] += 1
                else:
                    label_counts[label] = 1
        return label_counts

    def sort_count(self, labels_count):
        return {
            k: v
            for k, v in sorted(
                labels_count.items(), key=lambda item: item[1], reverse=True
            )
        }

    def read_output_contents(self, output_path):
        try:
            with open(output_path, "r") as f:
                return json.load(f)["contents"]
        except FileNotFoundError:
            logging.error(f"File not found: {output_path}")
