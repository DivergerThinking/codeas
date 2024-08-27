import json
import os

from pydantic import BaseModel


class Storage(BaseModel):
    repo_path: str = "."
    base_path: str = ".codeas"

    def read(self, agent_name: str):
        return self.read_json(f"output/{agent_name}.json")

    def write(self, agent_name: str, output: dict):
        self.write_json(f"output/{agent_name}.json", output)

    def exists(self, agent_name: str):
        return self.exists_file(f"output/{agent_name}.json")

    def read_json(self, path):
        with open(os.path.join(self.repo_path, self.base_path, path), "r") as f:
            return json.load(f)

    def write_json(self, path, content):
        full_path = os.path.join(self.repo_path, self.base_path, path)
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        with open(full_path, "w") as f:
            json.dump(content, f)

    def exists_file(self, path):
        return os.path.exists(os.path.join(self.repo_path, self.base_path, path))
