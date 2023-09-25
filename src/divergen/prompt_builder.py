import os
import yaml

from pydantic import BaseModel, PrivateAttr

def read_yaml(path):
    with open(path, 'r') as yaml_file:
        data = yaml.safe_load(yaml_file)
        return data

class Prompt(BaseModel):
    prompt_library: str
    request: list
    tone: list = None
    context: list = None
    additional_instructions: list = None    
    order: list = ["tone", "context", "request", "additional_instructions"]
    _prompt: str = PrivateAttr("")
    
    def build(self, add_titles: bool = True):
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

class PromptBuilder(BaseModel):
    prompt_library: str
    
    def build(self, template: str):
        template_path = os.path.join(self.prompt_library, template + ".yaml")
        template = read_yaml(template_path)
        prompt = Prompt(prompt_library=self.prompt_library, **template)
        return prompt.build()        
