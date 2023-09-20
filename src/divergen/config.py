from langchain.chat_models import ChatOpenAI

from pydantic import BaseModel

class PromptConfig(BaseModel):
    user_prompt: str
    system_prompt: str = None
    model: object = None # langchain.LLM
    output_parser: object = None # langchain.OutputParser
    memory: object = None # langchain.Memory

DEFAULT_CHAT_MODEL = ChatOpenAI()
DEFAULT_CONFIGS = {
    "generate_docstring": PromptConfig(
        **{
            "user_prompt": "user-prompts/generate-docstring-2.yaml",
            "system_prompt": "system-prompts/code-generator.txt",
            "model": DEFAULT_CHAT_MODEL
        }
    ),
}
