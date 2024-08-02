import json
import logging

from codeag.configs.storage_configs import OUTPUTS_PATH, SETTINGS_PATH


class Retriever:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_files_content(self, file_paths: list = None):
        incl_files_tokens = self.get_incl_files_tokens()
        files_content = {}
        for path in incl_files_tokens:
            if file_paths is None or path in file_paths:
                content = f"# FILE PATH: {path}\n\n{self.read_file(path)}"
                files_content[path] = content
        return files_content

    def get_files_content_testing(self):
        selected_test_cases = self.read_selected_test_cases()
        return self.get_files_content(selected_test_cases.keys())

    def get_files_content_str(self, file_paths: list = None):
        incl_files_tokens = self.get_incl_files_tokens()
        files_content = ""
        for path in incl_files_tokens:
            if file_paths is None or path in file_paths:
                content = f"# FILE PATH: {path}\n{self.read_file(path)}\n\n"
                files_content += content
        return files_content

    def get_incl_files_tokens(self):
        with open(f"{self.repo_path}/{SETTINGS_PATH}/incl_files_tokens.json", "r") as f:
            return json.load(f)

    def read_file(self, file_path):
        with open(file_path, "r") as f:
            return f.read()

    def get_file_descriptions(self, file_paths: list = None):
        contents = self.fetch_contents("extract_file_descriptions")
        self.filter_incl_files(contents)
        file_descriptions = ""
        for path, content in contents.items():
            if file_paths is None or path in file_paths:
                file_descriptions += f'File path: {path}\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return file_descriptions

    def filter_incl_files(self, file_descriptions):
        incl_files_tokens = self.get_incl_files_tokens()
        for path in list(file_descriptions.keys()):
            if path not in incl_files_tokens:
                file_descriptions.pop(path)

    def get_file_descriptions_dict(self, file_paths: list = None):
        contents = self.fetch_contents("extract_file_descriptions")
        file_descriptions = {}
        for path, content in contents.items():
            if file_paths is None or path in file_paths:
                file_descriptions[path] = content
        return file_descriptions

    def get_directory_descriptions(self):
        contents = self.fetch_contents("extract_directory_descriptions")
        directory_descriptions = ""
        for path, content in contents.items():
            directory_descriptions += f'Directory path: {path}\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return directory_descriptions

    def get_root_files_descriptions(self):
        incl_files_tokens = self.get_incl_files_tokens()
        root_files = [
            file_path for file_path in incl_files_tokens if "/" not in file_path
        ]
        return self.get_file_descriptions(root_files)

    def get_files_relevant_sections(self):
        contents = self.fetch_contents("define_documentation_sections")
        incl_files_tokens = self.get_incl_files_tokens()

        files_relevant_sections = {}
        for file_path in incl_files_tokens:
            for section, paths in contents.items():
                for path in paths:
                    if file_path.startswith(path):
                        if file_path not in files_relevant_sections:
                            files_relevant_sections[file_path] = []
                        files_relevant_sections[file_path].append(section)
        return files_relevant_sections

    def get_files_content_for_docs(self):
        files_for_docs = self.get_files_relevant_sections()
        return self.get_files_content(files_for_docs.keys())

    def get_documentation_sections_list(self):
        contents = self.fetch_contents("define_documentation_sections")
        documentation_sections_list = ""
        for key, section in contents.items():
            documentation_sections_list += f"\t{key}: {section}\n"
        return documentation_sections_list

    def get_sections_to_generate(self):
        return {
            section_name: section_name
            for section_name in self.fetch_contents(
                "define_documentation_sections"
            ).keys()
        }

    def get_sections_file_info(self):
        sections = self.fetch_contents("define_documentation_sections")

        sections_file_info = {}
        for section_name in sections:
            self.get_files_info(section_name)
        return sections_file_info

    def get_files_info(self, section_name):
        ...

    def get_test_cases_descriptions(self):
        selected_test_cases = self.read_selected_test_cases()
        all_test_cases = self.fetch_contents("define_test_cases")

        test_cases_descriptions = ""
        for path, all_cases in all_test_cases.items():
            if path in selected_test_cases:
                test_cases_descriptions += f"File path: {path}\n"
                for test_name, test_case in all_cases.items():
                    if test_name in selected_test_cases[path]:
                        test_cases_descriptions += f"\tTest case: {test_name}\n\tDescription: {test_case['description']}\n\n"
        return test_cases_descriptions

    def get_test_cases(self):
        selected_test_cases = self.read_selected_test_cases()
        all_test_cases = self.fetch_contents("define_test_cases")

        test_cases = {}
        for path, all_cases in all_test_cases.items():
            if path in selected_test_cases:
                for test_name, test_case in all_cases.items():
                    if test_name in selected_test_cases[path]:
                        test_cases[
                            path
                        ] = f"Test case: {test_name}\n\tDescription: {test_case['description']}\n\tAsserts: {test_case['asserts']}\n\tParent: {test_case['parent_name']}\n\n"
        return test_cases

    def get_test_guidelines(self):
        return self.fetch_contents("define_testing_guidelines")

    def read_selected_test_cases(self):
        with open(
            f"{self.repo_path}/{SETTINGS_PATH}/selected_test_cases.json", "r"
        ) as f:
            return json.load(f)

    def get_sections_file_descriptions(self):
        sections_contents = self.fetch_contents("define_documentation_sections")
        incl_files_tokens = self.get_incl_files_tokens()

        sections_file_descriptions = {}
        for section, paths in sections_contents.items():
            sections_file_descriptions[section] = []
            for file_path in incl_files_tokens:
                for path in paths:
                    if file_path.startswith(path):
                        sections_file_descriptions[section].append(file_path)

            sections_file_descriptions[section] = self.get_file_descriptions(
                sections_file_descriptions[section]
            )

        return sections_file_descriptions

    #     sections_context_contents = self.fetch_contents("identify_sections_context")
    #     sections_contents = self.fetch_contents("define_documentation_sections")
    #     # remove introduction as it is generated later
    #     intro_section_name = list(sections_contents.keys())[0]
    #     sections_contents.pop(intro_section_name)

    #     sections_file_descriptions = {}
    #     for section_index, section_name in sections_contents.items():
    #         relevant_file_paths = self.get_section_relevant_files(
    #             sections_context_contents, section_index
    #         )
    #         if any(relevant_file_paths):
    #             sections_file_descriptions[section_index] = self.get_file_descriptions(
    #                 relevant_file_paths
    #             )
    #         else:
    #             logging.error(f"No relevant files found for section: {section_name}")
    #     return sections_file_descriptions

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
        file_path = f"{self.repo_path}/{OUTPUTS_PATH}/{command_name}.json"
        try:
            with open(file_path, "r") as f:
                return json.load(f)["contents"]
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")


if __name__ == "__main__":
    retriever = Retriever(repo_path=".")
    res = retriever.get_test_cases()
    print(res)
