import logging
import re
from typing import Optional

from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from codeas._templates import SYSTEM_PROMPT_GLOBAL, SYSTEM_PROMPT_MODULES
from codeas.codebase import Codebase


class Request(BaseModel):
    """Class for executing LLM requests on entities and modules.

    Attributes
    ----------
    instructions : str
        the instructions for the request
    guideline_prompt : Optional[str]
        the prompt to be used as a guideline for the model, by default None
    model : object
        the model to use for executing the request
    """

    instructions: str
    guideline_prompt: Optional[str]
    model: object

    def execute(self, codebase: Codebase):
        logging.info("\n=======\nIDENTIFYING RELEVANT FILES\n=======\n")
        relevant_files = self._identify_relevant_files(codebase)

        logging.info("\n=======\nEXECUTING REQUEST\n=======\n")
        modules_to_read = self._parse_csv_string(relevant_files["read"])
        modules_content = ""
        for module in codebase.get_modules(modules_to_read):
            modules_content += f"\n<{module.name}>\n"
            modules_content += module.get("code")
            modules_content += f"</{module.name}>\n"
        logging.info(f"\nCODEBASE CONTEXT:\n\n{modules_content}")

        user_message = self._get_user_message(relevant_files)
        logging.info(f"\nPROMPT:\n\n{user_message}")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT_GLOBAL),
            HumanMessage(content=modules_content),
            HumanMessage(content=user_message),
        ]

        logging.info("\nMODEL OUTPUT:\n\n")
        output = self.model(messages).content

        for module_name, module_content in self._parse_markup_string(output).items():
            try:
                module = codebase.get_module(module_name)
                module.modify("new_content", module_content)
            except ValueError:
                codebase.add_module(module_name, module_content)

    def _identify_relevant_files(self, codebase: Codebase):
        tree = codebase.get_tree()
        logging.info(f"\nDIRECTORY TREE: {tree}")
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_MODULES),
            HumanMessage(content=tree),
            HumanMessage(content=self.instructions),
        ]
        logging.info("\nMODEL OUTPUT:\n\n")
        model_output = self.model(messages).content
        return self._parse_markup_string(model_output)

    def _parse_csv_string(self, input_string):
        return [module.replace("/", ".") for module in input_string.split(",")]

    def _parse_markup_string(self, input_string):
        pattern = r"<([^<>]+)>\n(.*?)\n</\1>"
        return dict(re.findall(pattern, input_string, re.DOTALL))

    def _get_user_message(self, relevant_files: dict):
        user_message = ""
        user_message += f"Instructions:\n{self.instructions}\n"

        output_format = ""
        if "modify" in relevant_files:
            for module_name in self._parse_csv_string(relevant_files["modify"]):
                output_format += f"<{module_name}>\n"
                output_format += "[FILE_CONTENT]\n"
                output_format += f"</{module_name}>\n"
        if "create" in relevant_files:
            for module_name in self._parse_csv_string(relevant_files["create"]):
                output_format += f"<{module_name}>\n"
                output_format += "[FILE_CONTENT]\n"
                output_format += f"</{module_name}>\n"

        user_message += f"Output format:\n{output_format}"
        return user_message
