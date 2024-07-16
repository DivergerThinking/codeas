from pydantic import BaseModel

from codeag.configs import api_params, prompts


class CommandArg(BaseModel):
    prompt: str
    api_params: dict
    multiple_requests: bool
    output_path: str
    estimate_multiplier: int


COMMAND_ARGS = {
    "extract_documentation_labels": CommandArg(
        prompt=prompts.EXTRACT_DOCUMENTATION_LABELS,
        api_params=api_params.GPT35_BASE_PARAMS,
        multiple_requests=True,
        output_path=".codeas/documentation_labels.json",
        estimate_multiplier=15,
    ),
    "extract_file_descriptions": CommandArg(
        prompt=prompts.EXTRACT_FILE_DESCRIPTIONS,
        api_params=api_params.GPT35_BASE_PARAMS,
        multiple_requests=True,
        output_path=".codeas/file_descriptions.json",
        estimate_multiplier=100,
    ),
    "extract_directory_descriptions": CommandArg(
        prompt=prompts.EXTRACT_DIRECTORY_DESCRIPTIONS,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=False,
        output_path=".codeas/directory_descriptions.json",
        estimate_multiplier=1000,
    ),
    "document_directories": CommandArg(
        prompt=prompts.DOCUMENT_DIRECTORIES,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=False,
        output_path=".codeas/directories.json",
        estimate_multiplier=300,
    ),
    "define_documentation_sections": CommandArg(
        prompt=prompts.DEFINE_DOCUMENTATION_SECTIONS,
        api_params=api_params.GPT4_BASE_PARAMS,
        multiple_requests=False,
        output_path=".codeas/documentation_sections.json",
        estimate_multiplier=200,
    ),
}
