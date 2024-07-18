from pydantic import BaseModel

from codeag.configs import api_params, prompts


class CommandArg(BaseModel):
    prompt: str
    api_params: dict
    multiple_requests: bool
    estimate_multiplier: int


COMMAND_ARGS = {
    "extract_file_descriptions": CommandArg(
        prompt=prompts.EXTRACT_FILE_DESCRIPTIONS,
        api_params=api_params.GPT35_BASE_PARAMS,
        multiple_requests=True,
        estimate_multiplier=100,
    ),
    "extract_directory_descriptions": CommandArg(
        prompt=prompts.EXTRACT_DIRECTORY_DESCRIPTIONS,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=False,
        estimate_multiplier=1000,
    ),
    "define_documentation_sections": CommandArg(
        prompt=prompts.DEFINE_DOCUMENTATION_SECTIONS,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=False,
        estimate_multiplier=200,
    ),
    "identify_sections_context": CommandArg(
        prompt=prompts.IDENTIFY_SECTIONS_CONTEXT,
        api_params=api_params.GPT35_BASE_PARAMS,
        multiple_requests=True,
        estimate_multiplier=15,
    ),
    "generate_documentation_sections": CommandArg(
        prompt=prompts.GENERATE_DOCUMENTATION_SECTIONS,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=True,
        estimate_multiplier=200,
    ),
    "generate_introduction": CommandArg(
        prompt=prompts.GENERATE_INTRODUCTION,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=False,
        estimate_multiplier=100,
    ),
}
