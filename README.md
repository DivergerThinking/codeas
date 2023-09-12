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
- only classes and standalone functions are retrieved (full modules, global constants, etc. are not).

### Docstring generation
- all classes and functions are passed to the API to ask for docstrings, even if some of them already have docstrings