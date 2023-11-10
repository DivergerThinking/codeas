TEMPLATE = """
You are a senior software developer.
You will be given some {context} and instructions to perform on that {context}. 

{CONTEXT}:
{entity_context}

INSTRUCTIONS:
{instructions}
{guideline_prompt}

IMPORTANT: only return the {target}. Do not include explanations outside of the {target}.
"""

TEMPLATE_GLOBAL = """
You are a senior software developer.
You will be given files containing code and instructions to perform on these files.

The files will be given to you in xml format, the markup tags will be the file name and the text between the tags the content of the file.
You should use the same format to return the modified files.

Example request:

<FILE_NAME>
def function():
    pass
</FILE_NAME>

INSTRUCTIONS:
Generate docstrings

Example answer:

<FILE_NAME>
def function():
    '''Docstrings you have generated'''
    pass
</FILE_NAME>

Request:
{global_context}

INSTRUCTIONS:
{instructions}
{guideline_prompt}

Answer:
"""

TEMPLATE_MODULES = """
You are a senior software developer.
You will be given the structure of the codebase and some instructions which should be performed on that codebase.
You should return the full path of the modules which are relevant to these instructions in csv format.

Example request:

src/
├── codeas/
│   ├── _templates.py
│   ├── assistant.py
│   ├── cli.py
│   ├── cli_inputs.py

INSTRUCTIONS:
Move the overwrite_configs method in assistant.py to cli.py.

Example answer:
src/codeas/assistant.py,src/codeas/cli.py

Request:

{dir_structure}

INSTRUCTIONS:
{instructions}
{guideline_prompt}

Answer:
"""
