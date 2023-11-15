import logging
import re
from typing import List, Optional, Union

from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from codeas._templates import SYSTEM_PROMPT_GLOBAL, TEMPLATE, TEMPLATE_MODULES
from codeas.codebase import Codebase
from codeas.entities import Entity, Module
from codeas.utils import tree


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

    def get_modules_from_instructions(self, codebase: Codebase, verbose: bool = True):
        logging.info("Getting modules from instructions")
        prompt = TEMPLATE_MODULES.format(
            dir_structure=tree(".", exclude=codebase.exclude),
            instructions=self.instructions,
            guideline_prompt=self.guideline_prompt,
        )
        if verbose:
            logging.info(f"Prompt:\n {prompt}")

        logging.info("Model output: \n")
        output = self.model.predict(prompt)
        return self._parse_modules(output)

    def _parse_modules(self, input_string):
        return [module.replace("/", ".") for module in input_string.split(",")]

    def execute_globally(
        self, codebase: Codebase, modules: List[str] = None, verbose: bool = True
    ):
        logging.info("Executing request globally")
        modules_content = ""
        for module in codebase.get_modules(modules):
            modules_content += f"\n<{module.name}>\n"
            modules_content += module.get(self.context)
            modules_content += f"</{module.name}>\n"

        messages = [
            SystemMessage(content=SYSTEM_PROMPT_GLOBAL),
            HumanMessage(content=modules_content),
            HumanMessage(content=self.instructions),
        ]

        logging.info("Model output: \n")
        output = self.model(messages).content

        for module_name, module_content in self._parse_markup_string(output):
            try:
                module = codebase.get_module(module_name)
                module.modify
                (self.target, module_content)
            except ValueError:
                codebase.add_module(module_name, module_content)

    def _parse_markup_string(self, input_string):
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
