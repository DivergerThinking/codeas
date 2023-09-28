# DIVERGEN

Improve your codebase with LLMs using the right context for the right prompts.

## Setup

### Dependencies

#### Installing from github:

```bash
pip install ...
```

#### Installing from local repository (after cloning)

```bash
git clone ...
cd divergen
pip install -e .
```

### OpenAI key

Adding OPENAI_API_KEY environment variable via terminal:

```bash
export OPENAI_API_KEY="..."
```

OR

Using .env file with `OPENAI_API_KEY="..."` defined inside.


## Usage

### Using the Streamlit UI

**NOTE**: this requires cloning the repository beforehand.

After installing the dependencies and setting up the OpenAI API key, run the following from the root of the repository:

```bash
streamlit run ui.py
```

This will open a window in your default browser at port 8501 with the streamlit app.

### Using the python API

```python

from divergen import CodebaseAssistant

assistant = CodebaseAssistant(codebase={"source_dir":...})
assistant.modify_codebase(
    template="...",
    entity_names=[...]
    **user_input
)
```
