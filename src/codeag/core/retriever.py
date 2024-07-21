import json
import logging

from codeag.configs.db_configs import STORAGE_PATH


class Retriever:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_files_content(self):
        ...

    # files_content = {}
    # file_paths = self.codebase.get_file_paths()
    # for path in file_paths:
    #     ext = os.path.splitext(path)[1]
    #     if EXTENSIONS.get(ext, "") == "programming":
    #         content = (
    #             f"# FILE PATH: {path}\n\n{self.codebase.get_file_content(path)}"
    #         )
    #         files_content[path] = content
    # return files_content

    def get_file_descriptions(self, file_paths: list = None):
        contents = self.fetch_contents("extract_file_descriptions")
        file_descriptions = ""
        for path, content in contents.items():
            if file_paths is None or path in file_paths:
                file_descriptions += f'File: {path}:\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return file_descriptions

    def get_directory_descriptions(self):
        contents = self.fetch_contents("extract_directory_descriptions")
        directory_descriptions = ""
        for path, content in contents.items():
            directory_descriptions += f'Directory: {path}:\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return directory_descriptions

    def get_documentation_sections_list(self):
        contents = self.fetch_contents("define_documentation_sections")
        documentation_sections_list = ""
        for key, section in contents.items():
            documentation_sections_list += f"\t{key}: {section}\n"
        return documentation_sections_list

    def get_sections_to_generate(self):
        contents = self.fetch_contents("define_documentation_sections")
        sections_file_descriptions = self.get_sections_file_descriptions()
        return {
            section_index: section_name
            for section_index, section_name in contents.items()
            if section_index in sections_file_descriptions.keys()
        }

    def get_sections_file_descriptions(self):
        sections_context_contents = self.fetch_contents("identify_sections_context")
        sections_contents = self.fetch_contents("define_documentation_sections")
        # remove introduction as it is generated later
        intro_section_name = list(sections_contents.keys())[0]
        sections_contents.pop(intro_section_name)

        sections_file_descriptions = {}
        for section_index, section_name in sections_contents.items():
            relevant_file_paths = self.get_section_relevant_files(
                sections_context_contents, section_index
            )
            if any(relevant_file_paths):
                sections_file_descriptions[section_index] = self.get_file_descriptions(
                    relevant_file_paths
                )
            else:
                logging.error(f"No relevant files found for section: {section_name}")
        return sections_file_descriptions

    def get_section_relevant_files(self, sections_context_contents, section_index):
        relevant_file_paths = []
        for file_path, relevant_sections in sections_context_contents.items():
            if int(section_index) in relevant_sections["relevant_sections"]:
                relevant_file_paths.append(file_path)
        return relevant_file_paths

    def get_repository_structure(self):
        contents = self.fetch_contents("extract_directory_descriptions")
        repository_structure = ""
        for path, content in contents.items():
            repository_structure += f'{path}:\n\t{content["description"]}\n'
        return repository_structure

    def get_sections_markdown(self):
        contents = self.fetch_contents("generate_documentation_sections")
        sections_markdown = ""
        for section_content in contents.values():
            for markdown, content in section_content.items():
                if "h1" in markdown:
                    sections_markdown += f"## {content}\n\n"
                elif "h2" in markdown:
                    sections_markdown += f"### {content}\n\n"
                elif "h3" in markdown:
                    sections_markdown += f"#### {content}\n"
                elif "h4" in markdown:
                    sections_markdown += f"##### {content}\n"
                elif "p" in markdown:
                    sections_markdown += f"{content}\n\n"
        return sections_markdown

    def fetch_contents(self, command_name):
        file_path = f"{STORAGE_PATH}/{command_name}.json"
        try:
            with open(file_path, "r") as f:
                return json.load(f)["contents"]
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
