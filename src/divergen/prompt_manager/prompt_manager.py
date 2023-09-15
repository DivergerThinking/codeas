import os

from pydantic import BaseModel
from langchain.chat_models import ChatOpenAI
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import load_prompt

from divergen.prompt_manager.output_parsers import PythonOutputParser


OUTPUT_PARSERS = {
    "python_output": PythonOutputParser
}

MODELS = {
    "chat-openai": ChatOpenAI,
    "fake": FakeMessagesListChatModel
}


class PromptManager(BaseModel):
    prompt_library: str

    def execute_template(
        self,
        template_name: str, 
        template_inputs: dict,
        model_name: object = "chat-openai",
        model_params: dict = None,
        parser_name: str = None
    ):
        prompt_template = load_prompt(os.path.join(self.prompt_library, template_name))
        prompt = prompt_template.format(**template_inputs)    
        model = self.get_model(model_name, model_params)
        model_output = model([HumanMessage(content=prompt)])
        if parser_name is None:
            return model_output.content
        else:
            parser = self.get_parser(parser_name)
            return parser.parse(output=model_output.content)
    
    def build_template(self, template_name, template_inputs):
        prompt_template = load_prompt(os.path.join(self.prompt_library, template_name))
        return prompt_template.format(**template_inputs)  
    
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