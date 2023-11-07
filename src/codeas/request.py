import logging
import re
from typing import List, Optional, Union

from pydantic import BaseModel

from codeas._templates import TEMPLATE, TEMPLATE_GLOBAL
from codeas.codebase import Codebase
from codeas.entities import Entity, Module


class Request(BaseModel):
    """Class for executing LLM requests on entities and modules.

    Attributes
    ----------
    instructions : str
        the instructions for the request
    context : str
        the context of the request. It can be "code", "docs", or "tests".
    guideline_prompt : Optional[str]
        the prompt to be used as a guideline for the model, by default None
    model : object
        the model to use for executing the request
    target : str
        the target of the request. It can be "code", "docs", or "tests".
    """

    instructions: str
    context: str
    guideline_prompt: Optional[str]
    model: object
    target: str

    def execute_globally(
        self, codebase: Codebase, modules: List[str], verbose: bool = True
    ):
        logging.info("Executing request globally")

        global_context = ""
        for module in codebase.get_modules(modules):
            global_context += f"<{module.name}>"
            global_context += module.get(self.context)
            global_context += f"</{module.name}>\n"

        prompt = TEMPLATE_GLOBAL.format(
            global_context=global_context,
            instructions=self.instructions,
            guideline_prompt=self.guideline_prompt,
        )
        if verbose:
            logging.info(f"Prompt:\n {prompt}")

        logging.info("Model output: \n")
        output = self.model.predict(prompt)

        for module_name, module_content in self._parse_markup_string(output):
            module = codebase.get_module(module_name)
            module.modify(self.target, module_content)

    def _parse_markup_string(input_string):
        pattern = r"<([^<>]+)>\n(.*?)\n</\1>"
        matches = re.findall(pattern, input_string, re.DOTALL)
        return [(match[0], match[1]) for match in matches]

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
