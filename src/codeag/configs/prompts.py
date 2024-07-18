EXTRACT_DOCUMENTATION_LABELS = """
I want to generate some documentation for an entire repository.
In order to do that, I need to define which sections the documentation should have based on the repository content.
Given that the repository is very large, I first want to give each file a label that reflects its content.
Based on these labels, I will define the sections of the documentation. 
Here are some examples of relevant labels that could be used to define the sections of the documentation:
configuration, deployment, security, authentification, front-end, back-end, database, testing, CI/CD, etc.
These are just examples, don't hesitate to include additional labels more specific to what the file does

*IMPORTANT*:
Each file can have multiple labels.
If you think a file is not relevant for the documentation, don't give it any label. 

Define the labels for the following file:
{get_files_content}

Return your answer in JSON format as such:
{{
    "labels": ["label1", "label2", "label3"]
}}
"""

EXTRACT_FILE_DESCRIPTIONS = """
I want to generate some documentation for an entire repository.
In order to do that, I need to define which sections the documentation should have based on the repository content.
Given that the repository is very large, I first want to extract some information about what each file in the repo does.
Based on this information and technologies used, I will define the sections of the documentation.

File to extract information from:
{get_files_content}

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
{get_file_descriptions}

**IMPORTANT**:
Include AS MANY directories and subdirectories as you can.
Only ignore directories and subdirectories that you think are ABSOLUTELY NOT RELEVANT for the documentation.

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

Define sections based on the following repositories' directories:
{get_directory_descriptions}

**IMPORTANT**: 
Keep these sections at the high level. EXAMPLES of documentation sections: 
"Introduction", "Getting started", "Architecture Overview", "Configuration", "API Reference", "Database Schema", "Testing", "Deployment", "Performance", "Security", "Monitoring and logging", "Dependencies", "Accessibility", "Integration", "Data Management", "Integration", etc.
ALWAYS START WITH "Introduction" as the first section

Return your results in JSON format using indices (starting as 0) as keys and section names as values:
{{
    0: Introduction,
    1: ...,
    2: ...
}}
"""

IDENTIFY_SECTIONS_CONTEXT = """
I want to generate some documentation for an entire repository.
I have already defined the different sections I want to generate for the repository, and now want to retrieve the necessary context to generate each section.
For each file in the repository, I need you to identify the sections of the documentation where this file should be used as context.

Here are the different sections of the documentation:
{get_documentation_sections_list}

Identify in which of these sections the following file should be used as context:
{get_files_content}

**IMPORTANT**:
The file can be used as context in multiple sections. 
As an example, a configuration file used for setting up the project could be used in both "Configuration" and "Getting Started" section.

Return your answer in JSON format as follows, using the indexes of the section you identified:
{{
    "relevant_sections": [0, 1]
}}
where [0, 1] would be the sections with index 0 and 1
"""

GENERATE_DOCUMENTATION_SECTIONS = """
I want to generate some documentation for an entire repository.
I have already defined the different sections I want to generate for the repository and identified the relevant files to use as context for generating each section.

Based on the context of the files, I want you to generate the content for the following section:
{get_sections_to_generate}

Here is the relevant context I have identified for this section:
{get_sections_file_descriptions}

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
