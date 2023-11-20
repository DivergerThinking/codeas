import logging
import re
from typing import Optional

from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from codeas._templates import (
    SYSTEM_PROMPT_FILES,
    SYSTEM_PROMPT_GUIDELINES,
    SYSTEM_PROMPT_REQUEST,
)
from codeas.codebase import Codebase


class Request(BaseModel):
    """Class for executing LLM requests on entities and modules.

    Attributes
    ----------
    instructions : str
        the instructions for the request
    model : object
        the model to use for executing the request
    guidelines : Optional[list]
        the guidelines which can be identified belonging to a prompt, by default None
    """

    instructions: str
    model: object
    guidelines: Optional[dict] = None

    def execute(self, codebase: Codebase):
        logging.info("\n=======\ADDING RELEVANT GUIDELINES\n=======\n")
        self.add_relevant_guidelines()

        logging.info("\n=======\nIDENTIFYING RELEVANT FILES\n=======\n")
        relevant_files = self.identify_relevant_files(codebase)

        logging.info("\n=======\nEXECUTING REQUEST\n=======\n")
        self.execute_request(codebase, relevant_files)

    def add_relevant_guidelines(self) -> list:
        if self.guidelines is not None:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT_GUIDELINES),
                HumanMessage(content=str(self.guidelines)),
                HumanMessage(content=self.instructions),
            ]
            logging.info("\nMODEL OUTPUT:\n\n")
            model_output = self.model(messages).content
            guideline_names = self._parse_csv_string(model_output)
            for guideline_name in guideline_names:
                try:
                    self.instructions += f"\n{self.guidelines[guideline_name]}"
                except Exception:
                    logging.info(f"Guideline {guideline_name} not found in guidelines")

    def identify_relevant_files(self, codebase: Codebase) -> dict:
        tree = codebase.get_tree()
        logging.info(f"\nDIRECTORY TREE: {tree}")
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_FILES),
            HumanMessage(content=tree),
            HumanMessage(content=self.instructions),
        ]
        logging.info("\nMODEL OUTPUT:\n\n")
        model_output = self.model(messages).content
        return self._parse_markup_string(model_output)

    def execute_request(self, codebase, relevant_files):
        modules_to_read = self._parse_csv_string(relevant_files["read"])
        modules_content = ""
        for module in codebase.get_modules(modules_to_read):
            modules_content += f"\n<{module.name}>\n"
            modules_content += module.content
            modules_content += f"</{module.name}>\n"
        logging.info(f"\nCODEBASE CONTEXT:\n\n{modules_content}")

        user_message = self._get_user_message(relevant_files)
        logging.info(f"\nPROMPT:\n\n{user_message}")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT_REQUEST),
            HumanMessage(content=modules_content),
            HumanMessage(content=user_message),
        ]

        logging.info("\nMODEL OUTPUT:\n\n")
        output = self.model(messages).content

        for module_name, module_content in self._parse_markup_string(output).items():
            try:
                # TODO: refactor error handling
                module = codebase.get_module(module_name)
                module.modify(module_content)
            except ValueError:
                codebase.add_module(module_name, module_content)

    def _parse_csv_string(self, input_string):
        return input_string.split(",")

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
