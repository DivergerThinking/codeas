import os
import yaml

from pydantic import BaseModel, PrivateAttr

class Prompt(BaseModel):
    request: list
    tone: list = None
    context: list = None
    additional_instructions: list = None    
    order: list = ["tone", "context", "request", "additional_instructions"]
    _prompt: str = PrivateAttr("")
    
    def build(self, prompt_library: str, add_titles: bool = True):
        for part in self.order:
            prompt_files = getattr(self, part)
            if prompt_files is not None:
                if add_titles:
                    self._prompt += "\n" + part.upper() + ":\n"
                for file_ in prompt_files:
                    path = os.path.join(prompt_library, file_ + ".txt")
                    file_content = self.read(path)
                    self._prompt += file_content + "\n"
        
        return self._prompt
        
    def read(self, path):
        with open(path, "r") as f:
            return f.read()

class PromptBuilder(BaseModel):
    prompt_library: str
    
    def build(self, template: str):
        template_path = os.path.join(self.prompt_library, template + ".yaml")
        template = self.read_template(template_path)
        prompt = Prompt(**template)
        return prompt.build(self.prompt_library)
    
    def read_template(self, path):
        with open(path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)
            return data
