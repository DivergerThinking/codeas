from codeag.configs import prompts

AGENTS_CONFIGS = {
    "extract_file_info": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.EXTRACT_FILE_DESCRIPTION,
        "model": "gpt-4o-mini",
        "context": {"file_content": {"batch": True}},
        "args": {"paths": "selected_file_paths"},
        "output_func": "display_json",
    },
    "generate_docs_overview": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_DOCUMENTATION_OVERVIEW,
        "model": "gpt-4o-mini",
        "context": {"file_content": {"info_only": True}},
        "args": {"paths": "selected_file_paths"},
        "output_func": "display_text",
    },
    "generate_docs_deployment": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_DOCUMENTATION_DEPLOYMENT,
        "model": "gpt-4o-mini",
        "context": {"file_content": {"info_only": True}},
        "args": {"paths": "auto_select"},
        "output_func": "display_text",
    },
    "define_unit_tests": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.DEFINE_UNIT_TESTS,
        "model": "gpt-4o-mini",
        "context": {
            "file_info": "file_selector",
        },
    },
    "generate_unit_tests": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_UNIT_TESTS,
        "model": "gpt-4o-mini",
        "context": {
            "file_info": "file_selector",
        },
    },
    "generate_functional_tests": {
        "system_prompt": prompts.BASE_SYSTEM_PROMPT,
        "instructions": prompts.GENERATE_FUNCTIONAL_TESTS,
        "model": "gpt-4o-mini",
        "context": {
            "file_info": "file_selector",
        },
    },
}
#     "extract_folders_info": {
#         "prompt": prompts.EXTRACT_DIRECTORY_DESCRIPTIONS,
#         "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
#     },
#     "define_documentation_sections": {
#         "prompt": prompts.DEFINE_DOCUMENTATION_SECTIONS,
#         "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
#     },
#     "generate_documentation_sections": {
#         "prompt": prompts.GENERATE_DOCUMENTATION_SECTIONS,
#         "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
#         "batch_keys": "retriever.get_sections_to_generate",
#     },
#     "generate_introduction": {
#         "prompt": prompts.GENERATE_INTRODUCTION,
#         "llm_params": llm_params.GPT4_BASE_PARAMS,
#     },
#     "categorize_test_files": {
#         "prompt": prompts.CATEGORIZE_TEST_FILES,
#         "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
#     },
#     "identify_test_cases": {
#         "prompt": prompts.IDENTIFY_TEST_CASES,
#         "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
#         "batch_keys": "retriever.get_incl_files",
#     },
#     "prioritize_test_cases": {
#         "prompt": prompts.PRIORITIZE_TEST_CASES,
#         "llm_params": llm_params.GPT4MINI_BASE_PARAMS,
#     },
#     "define_testing_guidelines": {
#         "prompt": prompts.DEFINE_TESTING_GUIDELINES,
#         "llm_params": llm_params.GPT4MINI_NO_JSON,
#     },
#     "generate_tests": {
#         "prompt": prompts.GENERATE_TESTS,
#         "llm_params": llm_params.GPT4_BASE_PARAMS,
#     },
#     # "generate_code_snippets": {
#     #     "prompt":prompts.GENERATE_CODE_SNIPPETS,
#     #     "api_params":api_params.GPT4_BASE_PARAMS,
#     # },
#     # "generate_code_comments": {
#     #     "prompt":prompts.GENERATE_CODE_COMMENTS,
#     #     "api_params":api_params.GPT4_BASE_PARAMS,
#     # },
#     # "generate_code_documentation": {
#     #     "prompt":prompts.GENERATE_CODE_DOCUMENTATION,
#     #     "api_params":api_params.GPT4_BASE_PARAMS,
#     # },
# }
