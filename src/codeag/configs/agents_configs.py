from codeag.configs import prompts

AGENTS_CONFIGS = {
    "generate_docs_backend": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_BACKEND_DOCS,
        "model": "gpt-4o",
        "context": "files_info",
    },
    "generate_docs_frontend": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FRONTEND_DOCS,
        "model": "gpt-4o",
        "context": "files_info",
    },
    "generate_docs_mobile": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_MOBILE_DOCS,
        "model": "gpt-4o",
        "context": "files_info",
    },
    "generate_unit_tests_python": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_UNIT_TESTS_PYTHON,
        "model": "gpt-4o",
        "context": "files_content",
        "batch": True,
    },
    "generate_functional_tests_python": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FUNCTIONAL_TESTS_PYTHON,
        "model": "gpt-4o",
        "context": "files_content",
        "batch": True,
    },
    "generate_file_refactor": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FILE_REFACTOR,
        "model": "gpt-4o",
        "context": "files_content",
        "batch": True,
    },
    "generate_repo_refactor": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_REPO_REFACTOR,
        "model": "gpt-4o",
        "context": "files_content",
    },
    "extract_files_info": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.EXTRACT_FILE_DESCRIPTION,
        "model": "gpt-4o-mini",
        "context": "files_content",
        "batch": True,
    },
}
