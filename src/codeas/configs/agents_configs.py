from codeas.configs import prompts
from codeas.core.agent import FileDetailsOutput, FilePathsOutput

AGENTS_CONFIGS = {
    "custom": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": "",
        "model": "gpt-4o-2024-08-06",
        "context": "files_content",
    },
    "generate_docs_backend": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_BACKEND_DOCS,
        "model": "gpt-4o-2024-08-06",
        "context": "files_description",
    },
    "generate_docs_frontend": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FRONTEND_DOCS,
        "model": "gpt-4o-2024-08-06",
        "context": "files_description",
    },
    "generate_docs_mobile": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_MOBILE_DOCS,
        "model": "gpt-4o-2024-08-06",
        "context": "files_description",
    },
    "generate_detailed_technical_docs": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_DETAILED_TECHNICAL_DOCS,
        "model": "gpt-4o-2024-08-06",
        "context": "files_detail",
    },
    "generate_config_docs": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_CONFIG_DOCS,
        "model": "gpt-4o-2024-08-06",
        "context": "files_content",
        "auto_select": True,
    },
    "generate_unit_tests_python": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_UNIT_TESTS_PYTHON,
        "model": "gpt-4o-2024-08-06",
        "context": "files_content",
        "batch": True,
    },
    "generate_functional_tests_python": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FUNCTIONAL_TESTS_PYTHON,
        "model": "gpt-4o-2024-08-06",
        "context": "files_content",
    },
    "generate_file_refactor": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FILE_REFACTOR,
        "model": "gpt-4o-2024-08-06",
        "context": "files_content",
        "batch": True,
    },
    "generate_repo_refactor": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_REPO_REFACTOR,
        "model": "gpt-4o-2024-08-06",
        "context": "files_content",
    },
    "suggest_aws_deployment": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.SUGGEST_AWS_DEPLOYMENT,
        "model": "gpt-4o-2024-08-06",
        "context": "files_detail",
    },
    "generate_aws_terraform": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_AWS_TERRAFORM,
        "model": "gpt-4o-2024-08-06",
        "context": "files_detail",
        "use_previous_outputs": True,
    },
    "extract_files_description": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.EXTRACT_FILE_DESCRIPTION,
        "model": "gpt-4o-mini",
        "context": "files_content",
        "batch": True,
    },
    "extract_files_detail": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.EXTRACT_FILE_DETAIL,
        "model": "gpt-4o-mini",
        "context": "files_content",
        "response_format": FileDetailsOutput,
        "batch": True,
    },
    "auto_select_files": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.AUTO_SELECT_FILES,
        "model": "gpt-4o-2024-08-06",
        "context": "files_description",
        "response_format": FilePathsOutput,
    },
}
