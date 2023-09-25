import pyperclip
from pydantic import BaseModel

from divergen.config import DEFAULT_CHAT_MODEL
from divergen.prompt_builder import PromptBuilder

class PromptManager(BaseModel):
    prompt_library: str
    
    def execute(self, template, **user_input):
        prompt = self.build(template, **user_input)
        model = DEFAULT_CHAT_MODEL
        return model.predict(prompt)
    
    def build(self, template, **user_input):
        builder = PromptBuilder(prompt_library=self.prompt_library)
        prompt_template = builder.build(template)
        return prompt_template.format(**user_input)
    
    def copy(self, template, **user_inputs):
        prompt = self.build(template, **user_inputs)
        pyperclip.copy(prompt)