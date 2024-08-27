from codeag.configs import llm_params, prompts

AGENTS_CONFIGS = {
    "extract_files_info": {
        "prompt": prompts.EXTRACT_FILE_DESCRIPTIONS,
        "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
        "batch_keys": "retriever.get_incl_files",
    },
    "extract_folders_info": {
        "prompt": prompts.EXTRACT_DIRECTORY_DESCRIPTIONS,
        "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
    },
    "define_documentation_sections": {
        "prompt": prompts.DEFINE_DOCUMENTATION_SECTIONS,
        "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
    },
    "generate_documentation_sections": {
        "prompt": prompts.GENERATE_DOCUMENTATION_SECTIONS,
        "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
        "batch_keys": "retriever.get_sections_to_generate",
    },
    "generate_introduction": {
        "prompt": prompts.GENERATE_INTRODUCTION,
        "llm_params": llm_params.GPT4_BASE_PARAMS,
    },
    "categorize_test_files": {
        "prompt": prompts.CATEGORIZE_TEST_FILES,
        "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
    },
    "identify_test_cases": {
        "prompt": prompts.IDENTIFY_TEST_CASES,
        "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
    },
    "define_testing_guidelines": {
        "prompt": prompts.DEFINE_TESTING_GUIDELINES,
        "llm_params": llm_params.GPT4MINI_NO_JSON,
    },
    "generate_tests": {
        "prompt": prompts.GENERATE_TESTS,
        "llm_params": llm_params.GPT4_BASE_PARAMS,
    },
    # "generate_code_snippets": {
    #     "prompt":prompts.GENERATE_CODE_SNIPPETS,
    #     "api_params":api_params.GPT4_BASE_PARAMS,
    # },
    # "generate_code_comments": {
    #     "prompt":prompts.GENERATE_CODE_COMMENTS,
    #     "api_params":api_params.GPT4_BASE_PARAMS,
    # },
    # "generate_code_documentation": {
    #     "prompt":prompts.GENERATE_CODE_DOCUMENTATION,
    #     "api_params":api_params.GPT4_BASE_PARAMS,
    # },
}
