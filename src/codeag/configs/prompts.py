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

DOCUMENT_DIRECTORIES = """
I want to document the main directories found inside a repository.
A description for each file found inside this repository has been generated.

Here are the descriptions for each file:
{get_file_descriptions}

Write a brief description for the most relevant directories found in the repository.

**IMPORTANT**:
The descriptions should be as concise as possible, with a maximum of around 50 tokens.
Include as many directories and subdirectories as you can.

Return your answer in JSON format as such:
{{
    "directory_name_1": "directory description here", 
    "directory_name_2": "directory description here"
}}
"""

DEFINE_DOCUMENTATION_SECTIONS = """
I want to generate some documentation for an entire repository.
To do so, I want to define the sections of the documentation based on some labels that were generated for each file.
Here are the labels that were generated and the number of files that have each label:
{get_labels_count}

Define the sections of the documentation that you think are most relevant to the codebase based on the labels.
Don't use all of the labels, only those you think are relevant to writing the documentation.

Return your results in JSON format as follows:
{{
    "sections": ["section1", "section2", "section3"]
}}
"""
