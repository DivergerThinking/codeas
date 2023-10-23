import logging
from typing import Optional, Union

from pydantic import BaseModel

from divergen._templates import TEMPLATE
from divergen.entities import Entity, Module


class Request(BaseModel):
    instructions: str
    context: str
    guideline_prompt: Optional[str]
    model: object
    target: str

    def execute(self, entity: Union[Entity, Module], verbose: bool = True):
        if isinstance(entity, Entity):
            logging.info(f"Executing request for {entity.node.name}")
        elif isinstance(entity, Module):
            logging.info(f"Executing request for {entity.name}")

        entity_context = entity.get(self.context)
        prompt = TEMPLATE.format(
            context=self.context,
            CONTEXT=self.context.upper(),
            entity_context=entity_context,
            instructions=self.instructions,
            guideline_prompt=self.guideline_prompt,
            target=self.target,
        )
        if verbose:
            logging.info(f"Prompt:\n {prompt}")

        logging.info("Model output: \n")
        output = self.model.predict(prompt)

        if self.target in ["code", "tests"]:
            output = self._parse_output(output)

        entity.modify(self.target, output)

    def _parse_output(self, output: str):
        return output.replace("```python", "").replace("```", "").replace("CODE:", "")
