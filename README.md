# DIVERGEN

Set of tools to increase productivity of developers. 

## Setup

Installing via pip

```bash
pip install ...
```

Adding OPENAI_API_KEY environment variable via terminal:

```bash
export OPENAI_API_KEY="..."
```

In VSCode, it is easier to 

## Usage

### Using the python API

```python

from divergen import CodebaseAssistant

code_assist = CodebaseAssistant(
    codebase={"source_dir":...}
)
code_assist.generate_docstrings()
```

### Using the WebUI

[NOT YET IMPLEMENTED]

## Limitations

### General
- currently only designed for src/ codebase, parsing .md (/docs) and other file types /assets is not yet included.

### Docstring generation
- all classes and functions are passed to the API to ask for docstrings, even if some of them already have docstrings
- asking to generate docstring only for a specific method is currently still buggy