from pydantic import BaseModel

from codeag.core.storage import Storage


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

    def get_incl_files_info(self):
        extracted_descriptions = self.storage.read_json(
            "output/extract_file_descriptions.json"
        )
        incl_files = self.get_incl_files()
        incl_file_descriptions = ""
        for path in incl_files:
            content = extracted_descriptions[path]["contents"]
            incl_file_descriptions += f'File path: {path}\n\tDescription: {content["description"]}:\n\tDetails: {content["details"]}\n\tTechnologies used: {content["technologies"]}\n\n'
        return incl_file_descriptions

    def get_file_content(self, path: str):
        with open(path, "r") as f:
            return f.read()
