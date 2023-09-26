import os
import yaml

import pyperclip
from pydantic import BaseModel, PrivateAttr

def read_yaml(path):
    with open(path, 'r') as yaml_file:
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
        for sequence in self.order:
            prompt_sequence = getattr(self, sequence)
            if prompt_sequence is not None:
                if add_titles:
                    self._prompt += "\n" + sequence.upper() + ":\n"
                
                prompt_chunks = read_yaml(
                    os.path.join(self.prompt_library, sequence + ".yaml")
                )

                for chunk_name in prompt_sequence:
                    self._prompt += prompt_chunks[chunk_name] + "\n"
        
        return self._prompt

class PromptManager(BaseModel):
    prompt_library: str
    add_titles: bool = True
    copy_to_clipboard: bool = False
    
    def build(self, template: str, **user_input):
        template_path = os.path.join(self.prompt_library, template + ".yaml")
        template_args = read_yaml(template_path)
        template_builder = TemplateBuilder(prompt_library=self.prompt_library, **template_args)
        template = template_builder.build_template(self.add_titles)
        prompt = template.format(**user_input)
        if self.copy_to_clipboard:
            pyperclip.copy(prompt)
        return prompt
