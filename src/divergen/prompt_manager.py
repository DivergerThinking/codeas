import os

import pyperclip
import yaml
from pydantic import BaseModel, PrivateAttr


def read_yaml(path):
    with open(path, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        return data


class TemplateBuilder(BaseModel):
    prompt_library: str
    request: list
    tone: list = None
    context: list = None
    additional_instructions: list = None
    order: list = ["tone", "context", "request", "additional_instructions"]
    _prompt: str = PrivateAttr("")

    def build_template(self, add_titles: bool = True):
        for component in self.order:
            prompt_component = getattr(self, component)
            if prompt_component is not None:
                if add_titles:
                    self._prompt += "\n" + component.upper() + ":\n"

                prompt_chunks = read_yaml(
                    os.path.join(self.prompt_library, "components", component + ".yaml")
                )

                for chunk_name in prompt_component:
                    self._prompt += prompt_chunks[chunk_name] + "\n"

        return self._prompt


class PromptManager(BaseModel):
    prompt_library: str
    add_titles: bool = True
    copy_to_clipboard: bool = False

    def build(self, template_path: str, **user_input):
        template_args = read_yaml(os.path.join(self.prompt_library, template_path))
        template_builder = TemplateBuilder(prompt_library=self.prompt_library, **template_args)
        template = template_builder.build_template(self.add_titles)
        prompt = template.format(**user_input)
        if self.copy_to_clipboard:
            pyperclip.copy(prompt)
        return prompt

    def list_templates(self, _action: str = None):
        if _action == "Modify codebase":
            path = os.path.join(self.prompt_library, "prebuilt", "modify_codebase")
        elif _action == "Generate markdown":
            path = os.path.join(self.prompt_library, "prebuilt", "generate_markdown")
        elif _action == "Generate tests":
            path = os.path.join(self.prompt_library, "prebuilt", "generate_tests")
        else:
            raise ValueError(f"Action {_action} not recognized")
        return [
            os.path.relpath(os.path.join(path, file_name), self.prompt_library)
            for file_name in os.listdir(path)
            if file_name.endswith(".yaml")
        ]
