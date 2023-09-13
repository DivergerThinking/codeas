from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import HumanMessage, AIMessage

from divergen.prompt_manager.output_parsers import PythonOutputParser

GENERATE_DOCSTRING = """
Generate docstrings for the following python code wherever necessary.
For classes, do not include private attributes and methods in the docstrings.
The docstrings should be in numpy format.
Only return the code back, no other description.

{code}
"""

PROMPT_TEMPLATES = {
    "generate_docstring": GENERATE_DOCSTRING
}

OUTPUT_PARSERS = {
    "python_output": PythonOutputParser
}

MODELS = {
    "chat-openai": ChatOpenAI,
    "fake": FakeMessagesListChatModel
}


class PromptManager:
    def execute(
        self, 
        template_name: str, 
        template_inputs: dict,
        model_name: object = "chat-openai",
        model_params: dict = None,
        parser_name: str = None
    ):
        template = self.get_template(template_name)
        prompt_template = PromptTemplate.from_template(template)
        prompt = prompt_template.format(**template_inputs)    
        model = self.get_model(model_name, model_params)
        model_output = model([HumanMessage(content=prompt)])
        if parser_name is None:
            return model_output.content
        else:
            parser = self.get_parser(parser_name)
            return parser.parse(output=model_output.content)
    
    def get_model(self, model_name: str, model_params: dict = None):
        try:
            model = MODELS[model_name]
        except KeyError:
            raise ValueError(f"Model {model_name} not found")
        
        if model.__name__ == "FakeMessagesListChatModel":
            return model(responses=[AIMessage(content="# fake response")])
        elif model_params is not None:
            return model(**model_params)
        else:
            return model()
        
    def get_parser(self, parser_name: str):
        try:
            return OUTPUT_PARSERS[parser_name]()
        except KeyError:
            raise ValueError(f"Parser {parser_name} not found")
    
    def get_template(self, template_name: str):
        try:
            return PROMPT_TEMPLATES[template_name]
        except KeyError:
            raise ValueError(f"Template {template_name} not found")