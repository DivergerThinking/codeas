from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

GENERATE_CLASS_DOCSTRING = """
Generate docstrings for the following python code wherever necessary.
For classes, do not include private attributes and methods in the docstrings.
The docstrings should be in numpy format.
Only return the code back, no other description.

{code}
"""

ACTION_PROMPTS = {
    "generate_class_docstring": GENERATE_CLASS_DOCSTRING
}

class PromptManager:
    def build_prompt(self, action: str, inputs: dict):
        template = self.get_template(action)
        prompt_template = PromptTemplate.from_template(template)
        return prompt_template.format(**inputs)
    
    def execute_prompt(self, prompt: str):
        chat = ChatOpenAI()
        return chat([HumanMessage(content=prompt)])
    
    def get_template(self, action: str):
        try:
            return ACTION_PROMPTS[action]
        except KeyError:
            raise ValueError(f"Action {action} not supported")