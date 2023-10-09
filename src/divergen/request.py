from pydantic import BaseModel
from typing import Optional
from divergen.templates import TEMPLATES
from divergen.entities import Entity
import logging


class Request(BaseModel):
    user_prompt: str
    context: str
    guideline_prompt: Optional[str]
    model: object
    target: str

    def execute(self, entity: Entity):
        logging.info(f"Executing prompt {self.user_prompt}")
        entity_context = entity.get(self.context)
        prompt = TEMPLATES[self.target].format(
            self.user_prompt, entity_context, self.guideline_prompt
        )
        output = self.model.predict(prompt)
        if self.target in ["code", "tests"]:
            output = self._parse_output(output)
        entity.modify(self.target, output)

    def _parse_output(self, output: str):
        return output.replace("```python", "").replace("```", "")
