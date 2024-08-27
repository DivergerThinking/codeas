from pydantic import BaseModel

from codeag.agents.storage import Storage


class Retriever(BaseModel, arbitrary_types_allowed=True):
    storage: Storage = Storage()

    def get_incl_files_content(self):
        incl_files = self.get_incl_files()
        files_content = ""
        for path in incl_files:
            files_content += f"# FILE PATH: {path}\n{self.get_file_content(path)}\n\n"
        return files_content

    def get_incl_files(self):
        return list(self.storage.read_json("state/incl_files_tokens.json").keys())

    def get_incl_dirs(self):
        return str(list(self.storage.read_json("state/incl_dir_tokens.json").keys()))

    def get_incl_files_info(self):
        incl_files = self.get_incl_files()
        return self.get_files_info(incl_files)

    def get_files_info(self, paths: list):
        extracted_files_info = self.storage.read("extract_files_info")
        files_info = ""
        for path in paths:
            content = extracted_files_info["responses"][path]["content"]
            files_info += f'File path: {path}\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'

        if files_info == "":
            files_info = "No root files found."

        return files_info

    def get_file_content(self, path: str):
        with open(path, "r") as f:
            return f.read()

    def get_dirs_info(self):
        extracted_folders_info = self.storage.read("extract_folders_info")
        dirs_info = ""
        for path, info in extracted_folders_info["responses"]["content"].items():
            dirs_info += f"Folder path: {path}\n\tDescription: {info['description']}:\n\tDetails: {info['details']}\n\n"
        return dirs_info

    def get_root_files_info(self):
        incl_files_tokens = self.get_incl_files()
        root_files = [
            file_path for file_path in incl_files_tokens if "/" not in file_path
        ]
        return self.get_files_info(root_files)

    def get_sections_to_generate(self):
        defined_sections = self.storage.read("define_documentation_sections")
        return list(defined_sections["responses"]["content"].keys())

    def get_section_name(self, section_name):
        return section_name

    def get_section_file_infos(self, section_name):
        defined_sections = self.storage.read("define_documentation_sections")
        section_paths = defined_sections["responses"]["content"][section_name]
        section_file_paths = self.get_section_file_paths(section_paths)
        return self.get_files_info(section_file_paths)

    def get_section_file_paths(self, section_paths):
        section_file_paths = []
        incl_files = self.get_incl_files()
        for file_path in incl_files:
            for section_path in section_paths:
                if file_path.startswith(section_path):
                    section_file_paths.append(file_path)
        return section_file_paths

    def get_repository_structure(self):
        folders_info = self.storage.read("extract_folders_info")
        repository_structure = ""
        for folder_path, folder_info in folders_info["responses"]["content"].items():
            repository_structure += f'{folder_path}:\n\t{folder_info["description"]}\n'
        return repository_structure

    def get_sections_markdown(self):
        sections = self.storage.read("generate_documentation_sections")
        sections_md = ""
        # print("========",sections["responses"].keys())
        for response in sections["responses"].values():
            sections_md += self.parse_json_to_markdown(response["content"])
        return sections_md

    def get_introduction_markdown(self):
        intro = self.storage.read("generate_introduction")
        return self.parse_json_to_markdown(intro["responses"]["content"])

    def parse_json_to_markdown(self, json_output):
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


if __name__ == "__main__":
    retriever = Retriever()
    retriever.get_incl_files_info()
