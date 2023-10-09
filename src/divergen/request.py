from pydantic import BaseModel
from langchain.chat_models import ChatOpenAI
from divergen.templates import TEMPLATES


class Request(BaseModel):
    user_prompt: str
    context: str
    guideline_prompt: str
    model: ChatOpenAI
    target: str

    def execute(self, entity: object):
        prompt_context = entity.get(self.context)
        prompt = TEMPLATES[self.target].format(
            self.user_prompt, prompt_context, self.guideline_prompt
        )
        output = self.model.run(prompt)
        if self.target in ["code", "tests"]:
            output = self._parse_output(output)
        entity.modify(self.target, output)

    def _parse_output(self, output: str):
        return output.replace("```python", "").replace("```", "")
