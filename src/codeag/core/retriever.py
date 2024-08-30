from pydantic import BaseModel

from codeag.agents.storage import Storage


class RetrieverError(Exception):
    pass


class Retriever(BaseModel, arbitrary_types_allowed=True):
    storage: Storage = Storage()

    def get_info_file_content(self):
        incl_files = self.get_incl_files("info")
        files_content = ""
        for path in incl_files:
            files_content += f"# FILE PATH: {path}\n{self.get_file_content(path)}\n\n"
        return files_content

    def get_info_dirs(self):
        return self.get_incl_dirs("info")

    def get_incl_files(self, category: str):
        return list(
            self.storage.read_json("repo/incl_files_tokens.json")[category].keys()
        )

    def get_incl_dirs(self, category: str):
        return str(
            list(self.storage.read_json("repo/incl_dir_tokens.json")[category].keys())
        )

    def get_info_files(self):
        return self.get_incl_files("info")

    def get_info_files_info(self):
        incl_files = self.get_incl_files("info")
        return self.get_files_info(incl_files)

    def get_files_info(self, paths: list):
        extracted_files_info = self.read_agent_output("extract_files_info")
        files_info = ""
        for path in paths:
            content = extracted_files_info["responses"][path]["content"]
            print("==========", content)
            files_info += f'File path: {path}\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'

        return files_info

    def get_folders_info(self):
        extracted_folders_info = self.read_agent_output("extract_folders_info")
        folders_info = ""
        for path, info in extracted_folders_info["responses"]["content"].items():
            folders_info += f"Folder path: {path}\n\tDescription: {info['description']}:\n\tDetails: {info['details']}\n\tTechnologies used: {info['technologies']}\n\n"
        return folders_info

    def read_agent_output(self, agent_name: str):
        try:
            return self.storage.read(agent_name)
        except FileNotFoundError:
            raise RetrieverError(f"Retrieval error. Run '{agent_name}' agent first.")

    def get_file_content(self, path: str):
        with open(path, "r") as f:
            return f.read()

    def get_root_files_info(self):
        incl_files_tokens = self.get_incl_files("info")
        root_files = [
            file_path for file_path in incl_files_tokens if "/" not in file_path
        ]
        root_files_info = self.get_files_info(root_files)
        if root_files_info == "":
            root_files_info = "No root files found."
        return root_files_info

    def get_sections_to_generate(self):
        defined_sections = self.read_agent_output("define_documentation_sections")
        return list(defined_sections["responses"]["content"].keys())

    def get_section_name(self, section_name):
        return section_name

    def get_section_file_infos(self, section_name):
        defined_sections = self.read_agent_output("define_documentation_sections")
        section_paths = defined_sections["responses"]["content"][section_name]
        section_file_paths = self.get_section_file_paths(section_paths)
        return self.get_files_info(section_file_paths)

    def get_section_file_paths(self, section_paths):
        section_file_paths = []
        incl_files = self.get_incl_files("testing")
        for file_path in incl_files:
            for section_path in section_paths:
                if file_path.startswith(section_path):
                    section_file_paths.append(file_path)
        return section_file_paths

    def get_repository_structure(self):
        folders_info = self.read_agent_output("extract_folders_info")
        repository_structure = ""
        for folder_path, folder_info in folders_info["responses"]["content"].items():
            repository_structure += f'{folder_path}:\n\t{folder_info["description"]}\n'
        return repository_structure

    def get_sections_markdown(self):
        sections = self.read_agent_output("generate_documentation_sections")
        sections_md = ""
        for response in sections["responses"].values():
            content = response["content"]
            if isinstance(content, str):
                sections_md += content + "\n\n"
            else:
                sections_md += self.parse_json_to_markdown(content)
        return sections_md

    def get_introduction_markdown(self):
        intro = self.read_agent_output("generate_introduction")
        return self.parse_json_to_markdown(intro["responses"]["content"])

    def parse_json_to_markdown(self, json_output):
        if isinstance(json_output, str):
            return json_output + "\n\n"

        markdown = ""
        for key, content in json_output.items():
            if "h1" in key:
                markdown += f"## {content}\n\n"
            elif "h2" in key:
                markdown += f"### {content}\n\n"
            elif "h3" in key:
                markdown += f"#### {content}\n"
            elif "h4" in key:
                markdown += f"##### {content}\n"
            elif "p" in key:
                markdown += f"{content}\n\n"
        return markdown

    def get_test_cases(self):
        identified_test_cases = self.read_agent_output("identify_test_cases")
        test_cases = ""
        for file_path, file_responses in identified_test_cases["responses"].items():
            test_cases += f"\nFile path: {file_path}\n"
            for test_name, test_response in file_responses["content"].items():
                test_cases += f"\tTest name: {test_name} | Test description: {test_response['description']}\n"
        return test_cases


if __name__ == "__main__":
    retriever = Retriever()
    retriever.get_info_files_info()
