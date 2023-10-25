# CODEAS

CODEAS stands for CODEbase ASsistant.
It uses your codebase as context and helps you to automate the generation of code, documentation, and tests by leveraging the power of LLMs.

**Key features include**:
- **Flexible**: configure the tool your way, adapting it to your codebase and setting the tone on how you want code to be generated.
- **Easy to use**: execute your prompts easily from the CLI application
- **Reusable**: configure your prompts once and reuse them without having to rewrite them each time
- **Collaborative**: share your prompts with your colleagues and the wider community
- **Transparent**: track the execution flow and cost for each prompt you execute [in progress]

#### ⚠️ **DISCLAIMER**: 24.10.2023. (v0.1.0) 
We have chosen to release this application early in order to share our work with those interested in LLM application for software development. However, this early release means the application is not yet stable nor fully documented. However, we are eager to get some feedback on any issues you might face or functionalities you would like to see. Happy coding!

## Installation

#### Pypi

```bash
pip install codeas
```

#### Development

```
git clone git@github.com:DivergerThinking/codeas.git
cd codeas
pip install -e .
```

#### OpenAI key

Currently the tool only supports OpenAI models, but will soon be extended to other models.

To add you OpenAI key, export it as environment variable via terminal:

```bash
export OPENAI_API_KEY="..."
```

OR add it to a .env file at the root of your repository

## Usage

### How does it work

Before running the tool, it is important to first understand its main components and how they interact with each other.

<img src="docs/images/how-does-it-work.png" alt="drawing" width="800"/>
`CLI App`: This is your entry point to the tool. We use it to initialize our config files and run the prompts we configure.

#### `Configs`: 
the application configurations are stored inside .yaml files generated which are generated when running `codeas init`
- `assistant.yaml`: contains the configurations for the Assistant class (see codeas.assistant.py)
- `prompts.yaml`: contains the prompts to run through the CLI. See next point for more information.

#### `Prompt`: 
we refer to prompt as single entry inside the prompts.yaml containing the following
- `instructions`: the instructions for the LLM to perform
- `context`: the context we pass to the LLM from the module. By default this is the module's code. Options are "code", "tests" or "docs".
- `target`: the target we want to modify from the module. By default this is the module's code. Options are "code", "tests" or "docs".
- `guidelines` [optional]: some additional guidelines the LLM should follow when performing the instructions

Prompt example:
```yaml
# .codeas/prompts.yaml
generate_docs:
  instructions: Generate usage documentation in markdown format.
  context: code
  target: docs
  guidelines:
  - docs_guideline
```

#### `Modules`: 
we refer to modules as units of code stored inside a file. The particularity of our definition is that a single module can refer to three files: source code, tests and documentation files. This makes it easier for us to retrieve or modify source code, tests and documentation of a given module:

<img src="docs/images/modules.png" alt="drawing" width="500"/>

#### `Codebase`: 
we refer to a codebase as a collection of modules and their corresponding source code, test and documentation files. Even though a more comprehensive definition of a codebase should include other files such as configurations, dependency and environment files, we are not including them (yet) to simplify our application.

**IMPORTANT NOTE**: it is therefore important that our codebase is structured in such a way that documentation, tests and source code are found in three different folders.

<img src="docs/images/codebase.png" alt="drawing" width="300"/>

In the above example, the ``/src`` folder contains the source_code in python files, the ``docs/`` folder the documentation files in markdown format, and the ``tests/`` folder the test files in python format. This structure is reflected in the `assistant.yaml` file 

```yaml
# .codeas/assistant.yaml
codebase:
  code_folder: ./src/
  code_format: .py
  docs_folder: ./docs/
  docs_format: .md
  tests_folder: ./tests/
  tests_format: .py
```

If your repository follows a different structure, you must adjust the ``assistant.yaml`` file accordingly.

### CLI app

**The application uses your current directory as codebase** to work with. Make sure you first `cd` to the root of the repository you want to work with.

If you run the tool for the first time on the repository, you must first inititalize the configuration files.

#### Initializing configs

Run the following command at the root of the repository you want to work with.

```bash
codeas init
```

This will generate the following config files

```
├── .codeas
│   ├── assistant.yaml
│   ├── prompts.yaml
```

If you wan to re-use the same configs you have from another project, you can add the `-p` or `--path` with the path to the project.

```bash
codeas init -p ../another-project/.codeas
```

#### Configuring prompts

Inside the `.codeas/prompts.yaml` are the prompts and their attributes.

```yaml
generate_tests:
    instructions: Generate tests using pytest.
    target: tests
```

#### Executing prompts

Use `codeas run` followed by the prompt name you want to execute:

```bash
codeas run generate_tests
```

If you don't don't want to use the yaml file, you can enter the instructions and guidelines via the CLI using the `-i` option:

```bash
codeas run -i
```

## Additional features

### Chunking large context

Due to the **limitation of the context size** of LLMs, we have implemented a feature to chunk the size of context given from the codebase to the LLM for each request. 

This is **handled by the parameter "max_tokens_per_module" found in the `assistant.yaml`** config file. By default it is 8000 tokens, meaning any modules that amounts to more tokens than that will by chunked into entities (classes and functions) and each entity will be given as request to the LLM. All responses from the LLM are then merged back together.

**IMPORTANT NOTE**: this feature has not been tested much so it is likely not to work well in some cases, but we are working on it and are open to suggestions for improvements.

### Formatting generated files (auto_format)

Often more than not, LLMs output code in a format which is doesn't follow your programming language conventions. As our tool is focused on python right now, we have implemented a feature to automatically format code when a file is written/modified. Right now we are using black to achieve this. This is configurable via the `assistant.yaml` file under `file_handler: auto_format` and `file_handler: format_command`. By default `auto_format = True` and `format_command = black`. By setting `auto_format = False` no formatting will take place, or a different formatter can be run via the ``format_command``.

### Previewing changes

By default, any changes made to the codebase is first written to files with the suffix "_preview". This allows to easily view and accept/reject changes made to the codebase. This is configurable via the `assistant.yaml` file under `file_handler: preview`. By default, it is set to True. Setting it to False means directly overwritting the original files with the changes.

## Roadmap

Future efforts will be focused on the following:
- **Multi language support**: run tool on any codebase you want
- **Tracking execution flow and costs**: give better transparency of LLM usage
- **Smart context retrieval & codebase modification**: use LLM to identify what to retrieve and modify in the codebase
- **VS Code extension**: integrate the tool inside IDE for easier usage

