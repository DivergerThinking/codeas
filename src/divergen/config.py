from langchain.chat_models import ChatOpenAI

from pydantic import BaseModel
from divergen.output_parsers import PythonOutputParser 
from divergen.retrievers import CodeRetriever, Retriever

class PromptConfig(BaseModel):
    user_prompt: str
    system_prompt: str = None
    model: object = None
    retriever: Retriever = None
    output_parser: object = None #OutputParser
    memory: object = None

SOURCE_DIR = "./src-test"
DEFAULT_CHAT_MODEL = ChatOpenAI()
DEFAULT_CONFIGS = {
    "generate_docstrings": PromptConfig(
        **{
            "user_prompt": "user-prompts/generate-docstring-2.yaml",
            "system_prompt": "system-prompts/code-generator.txt",
            "model": DEFAULT_CHAT_MODEL,
            "retriever": CodeRetriever(source_dir=SOURCE_DIR),
            "output_parser": PythonOutputParser(),
            # "memory": ...,
        }
    ),
}

# Usage api

codebase = Codebase()

retriever = CodeRetriever(codebase)
# codebase.get_code(entity_name, module_name)
# codebase.get_code(module_name)
user_input = retriever.retrieve(**user_input)


output_parser = CodeExporter(codebase)

prompt = "Generate docstings for all functions"
prompt = "Generate docstings for functions without docstrings"
prompt = "Generate docstings for functions without docstrings in module X"

def generate_docstrings(self):
    codebase.parse_modules()
    if "all-functions":
        ...
    elif "functions-without-docstrings":
        ...
    elif "functions-in-module-X":
        ...
        
# params without docstrings

def _generate_docstings(self, entities):
    for entity in codebase.get_entity_names():
        ...

    

# multiple modules can have the same name, what to do then?
    # use paths instead of names
# multiple classes can have the same name, what to do then?
    # specify which module the class is in
# what about when methods have the same name within a module (i.e. method overloading)
    # use the line number to specify which method
