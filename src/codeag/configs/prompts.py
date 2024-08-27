EXTRACT_FILE_DESCRIPTIONS = """
I want to generate some documentation for an entire repository.
In order to do that, I need to define which sections the documentation should have based on the repository content.
Given that the repository is very large, I first want to extract some information about what each file in the repo does.
Based on this information and technologies used, I will define the sections of the documentation.

File to extract information from:
{get_file_content}

The information you should extract is the following:
- "description": a brief and concise description of what the file does, with a maximum of around 50 tokens.
- "details": some additional detail about what the file does, use bullet points to list this information.
- "technologies": the key technologies used in the file, such as programming languages, frameworks, libraries, etc.

Return your answer in JSON format as such:
{{
    "description": "description as string",
    "details": "details as string",
    "technologies": ["technology1, technology2, technology3"]
}}

**IMPORTANT**: Only return a single JSON response with description, details and technologies.
"""

EXTRACT_DIRECTORY_DESCRIPTIONS = """
I want to generate some documentation for an entire repository.
In order to do that, I need to define which sections the documentation should have based on the repository content.
Given that the repository is very large and including the content from all files doesn't fit into context, I want to extract some information about the main directories and subdirectories found in the repository.

I have already extracted some information about what each of the file in the repository does:
- "description": a brief and concise description of what each file does, with a maximum of around 50 tokens.
- "details": some additional detail about what each file does.
- "technologies": the key technologies used in each file.

Use this information to extract the same information but at the directory level.

FILES INFORMATION:
{get_incl_files_info}

**IMPORTANT**:
Only include the following directories and subdirectories:
{get_incl_dirs}

Return your answer in JSON format as such:
{{
    "directory_or_subdirectory_name_1": {{
        "description": "description as string",
        "details": "details as string",
        "technologies": ["technology1, technology2, technology3"]
    }},
    "directory_or_subdirectory_name_2": {{
        ...
    }},
}}
"""

DEFINE_DOCUMENTATION_SECTIONS = """
I want to generate some documentation for an entire repository.
To do so, I need you to define the sections that should be included in the documentation based on the content of the repository.
You should keep these sections at the high level. Examples of documentation sections include: 
"Getting started", "Configuration", "API Reference", "Database Schema", "Testing", "Deployment", "Performance", "Security", "Monitoring and logging", "Dependencies", "Accessibility", "Integration", "Data Management", "Integration", etc.
You don't need to limit yourself to those examples, feel free to define other sections if you see fit.

Here is some information about the directories in the repository:
{get_dirs_info}

Here is some information about the files in the root of the repository:
{get_root_files_info}

For each section you define, include the relevant root files and directory paths to use as context for generating this section.

Return the sections in the following JSON format:
{{
    section_name1: [path1, path2],
    section_name2: [path2, path3],
}}

**IMPORTANT**:
The same directory and file paths can be used for multiple sections. Example: some configuration file used for deployments can be relevant to both "Configuration" and "Deployment" sections.
DO NOT include an "Introduction" section, this one will be generated separately at the end.
ONLY ADD SECTIONS WHICH APPEAR TO BE RELEVANT FROM THE GIVEN REPOSITORY CONTENT 
"""

IDENTIFY_SECTIONS_CONTEXT = """
I want to generate some documentation for an entire repository.
I have already defined the different sections I want to generate for the repository, and now want to retrieve the necessary context to generate each section.

Here is the content of the file:
<file-content-start>
{get_files_content_for_docs}
<file-content-end>

This file will be used as context for generating the following documentation sections:
{get_files_relevant_sections}

Extract the key information found inside the file that should be used as context for documenting those sections.

Return your answer in JSON format as follows:
{{
    "key_info": "extracted key information here"
}}

**IMPORTANT**:
You are not asked to actually document the files, but to EXTRACT INFORMATION FROM THEM.
BE AS CONCISE AS POSSIBLE. The idea is to capture as much information as possible in as little tokens possible.
Have another look at the sections that will need to be documented, and make sure you only extract relevant information.
Try not to exceed 100 tokens unless you think the file contains a large amount of important information and details.
"""

GENERATE_DOCUMENTATION_SECTIONS = """
I want to generate some documentation for an entire repository.
I have already defined the different sections I want to generate for the repository and identified the relevant files to use as context for generating each section.

Generate the content for the following section: "{get_section_name}"

Here is the relevant context I have identified for this section:
{get_section_file_infos}

**IMPORTANT**:
Not all files are necessarily relevant to the section.
Don't try to include all of the file's information inside the documentation, only focus on those that are relevant.
The documentation you generate should be broken down into different subsections whenever necessary.
Follow an html-like structure for the documentation, using "h1", "h2", "h3" as section titles and "p" as content.

Return your answer in JSON format following this structure:
{{
    "0 - h1": "section title here",
    "1 - h2": "subsection title here",
    "2 - p": "content here"
    "3 - h2": "subsection title here",
    "4 - h3": "subsubsection title here",
    "5 - p": "content here"
}}

NOTE: the 0 - 1 - 2 - 3 - 4 - 5 are just indexes to make the JSON keys unique.
"""

GENERATE_INTRODUCTION = """
I have generated a documentation for an entire repository but it misses an introduction.
Generate the "Project overview" and "Purpose and scope" subsections for the documentation.

Here is the generated documentation any content for these sections, including the "..." placeholders which you should generate:
<documentation-start>
## Introduction

### Project overview

...

### Purpose and scope

...

### Repository structure

{get_repository_structure}

{get_sections_markdown}
<documentation-end>

Follow an html-like structure using "h1", "h2" as section titles and "p" as content.
Return your answer in JSON format following this structure:
{{
    0 - h1: "Introduction",
    1 - h2: "Project overview",
    2 - p: ...,
    3 - h2: "Purpose and scope",
    4 - p: ...
}}

NOTE: the 0 - 1 - 2 - 3 - 4 are just indexes to make the JSON keys unique.
"""

CATEGORIZE_FILE_USAGE = """
I want to generate documentation, tests and refactor code at a repository level.
To do so, I want you to categorize the usage of the following file in the repository:
{get_files_content_short}

*note: only the top 10 and bottom 10 lines of the file are shown to give you an idea of the file content.

Return your answer in JSON format as such:
{{
    "use_for_testing": boolean,
    "use_for_documentation": boolean,
    "use_for_refactoring": boolean
}}

**IMPORTANT**:
A file could be used for multiple purposes (multiple True values) or none of them (all False values).
Before categorizing the file, you need to pay particular attention to additional instructions provided by the user for each purpose.

GENERAL INSTRUCTIONS:
{get_general_instructions}

INSTRUCTIONS FOR TESTING:
{get_test_instructions}

INSTRUCTIONS FOR DOCUMENTATION:
{get_documentation_instructions}

INSTRUCTIONS FOR REFACTORING:
{get_refactoring_instructions}

These are some obvious but important rules you should also consider:
- Testing and refactoring should only be done on files that contain code.
- Files that already contain tests should not be used for testing.
- Documentation should also include non-code files (configs, READMEs, etc.) but some files might not be relevant, such as files containing some data or logs.

READ AGAIN the above instructions CAREFULLY before categorizing the file.
"""

CATEGORIZE_TEST_FILES = """
I want to generate some tests for a repository.
In order to do that, I first need to identify which files from the repository are relevant for testing.

The relevance of these tests should be categorized into three main categories:
- High: files that are critical for the application and should be tested thoroughly
- Medium: files that are important for the application but not critical
- Low: files that don't necessarily need to be tested or are difficult to test

Here are some key information about each file in the repository:
{get_file_descriptions}

**IMPORTANT**:
Focus on files which are relevant for testing and relatively easy to test (example: unit testing).
Files that are more difficult to test (UI, integration tests, scripts, etc.) ranked as low priority.
Ignore files which are already test files.

Return your answer in JSON format as such:
{{
    High: ["path1", "path2"],
    Medium: ["path3", "path4", "path5"],
    Low: ["path6", "path7"]
}}
"""

IDENTIFY_TEST_CASES = """
I want to generate some tests for an entire repository.
For each of the file in the repository, I first want to define the different test cases (i.e. behaviors to cover) that should be implemented.
The tests will then be generated based on these test cases.

Define some test cases for the following file:
{get_files_content}

Return your answer in JSON format as such:
{{
    "test_name1": {{
        "description": "description of the test case",
        "asserts": "assertions to be made in the test case"
        "importance": int (from 10 highest importance, to 1 lowest importance)"
        "parent_name": "the class or function name the test case belongs to",
    }},
    "test_name2": {{
        ...
    }},
}}

**IMPORTANT**:
Test case names should reflect the name that would be given to the test function.
Test case descriptions and asserts should be as concise as possible.
The test cases should be sorted by order of importance.
"""

DEFINE_TESTING_GUIDELINES = """
I want to generate a set of tests for an entire code repository.
In order for these tests to be somewhat standardized, I first want to define some guidelines on how to generate these tests.
These guidelines should include the testing framework to be used as well as any other information you think is relevant (naming, structure, etc.).

Define the guidelines for the following files:
{get_test_cases_descriptions}

**IMPORTANT**:
ONLY WRITE THE GUIDELINES. Be as concised as possible. Write the guidelines as bullet points. Try and limit them to 5-10 points.
If you think multiple frameworks or guidelines should be used for different types of files, explain when each should be used.
DO NOT write guidelines for each file separately, write them as general guidelines for the entire repository.
Try not to exceed 200-300 tokens.
"""

GENERATE_TESTS = """
I want to generate a set of tests for a code repository.
I have already generated the test cases for each file in the repository.

Here is the file I want to write the tests for:
{get_files_content_testing}

Generate tests that cover the following test cases:
{get_test_cases}

Use the following testing guidelines:
{get_test_guidelines}

Return your answer in JSON format with the test_file's name as key and the content of the test file as value:
{{
    "path_of_test_file": "test_file_content"
}}

**IMPORTANT**:
Include the full path of the test file. Make sure to follow the testing guidelines.
Include the test case as docsctring in the corresponding test.
Ignore testing guidelines that are not relevant for the current task at hand (i.e. if they focus on aspects that are outside of the scope of generating the tests).
THE CONTENT OF THE FILE SHOULD ONLY BE CODE
"""
# ONLY WRITE THE CODE. Your output will directly be written to files as part of the repository, and will be executed as such.
