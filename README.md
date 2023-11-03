# codeas

codeas stands for CODEbase ASsistant. It boosts your software development processes by leveraging LLMs using your full codebase as context.

**Key features include**:
- ✅ **Flexibility**: configure the tool your way, adapting it to your codebase and setting the tone on how you want the LLM to write code for you.
- ✅ **Reusability**: configure your prompts once and reuse them without having to rewrite them each time
- ✅ **Collaboration**: share your prompts with your colleagues and the wider community
- ✅ **Transparency**: track the execution flow and cost for each prompt you execute [in progress]

## ❓ Why this tool?
There already exists many tools that use LLM for working with code (Copilot, Codeium, Cody, Bloop, just to name a few), so why bother with another you may ask? 

That's a fair question. The best answer I can give is "because each tool has its own strenghts and limitations":
- Copilot and Codeium can suggest useful code snippets on the fly without even being prompted, yet they are limited by the context they use from the codebase. 
- Cody and Bloop will use the entire codebase as context, fulfilling requests that Copilot & Codeium can’t do. However, they have their own way of processing your codebase, working well for some requests while failing for others.

Codeas also has its limitations of course (especially in these early releases), but the idea behind the tool is to let the user configure the context to use for a given request, add some guidelines to it and easily reuse these configurations whenever needed. By making the tool customisable to specific requests, tasks which couldn't be performed by other tools can now be fulfiled.

Are we there yet? No, but we intend on getting there soon. So follow us while we publish new releases that will make codeas you next go-to programming assistant.

## Releases
⚠️ **DISCLAIMER:**
We have chosen to release this application early in order to share our work with those interested in LLM application for software development. This early release means the application is not fully stable. However, we are eager to get some feedback on any issues you might face or new functionalities you would like to see. Happy coding!

### v0.1.1 (03.11.2023)
Quick patch release to add support for other languages by switching from [AST](https://docs.python.org/3/library/ast.html) to [Tree-Sitter](https://tree-sitter.github.io/tree-sitter/).

**Release Notes**:
- Add support for javascript and java codebases.

### v0.1.0 (24.10.2023)
Original release that supports simple use cases.

**Release Notes**:
- Focused on simple use cases such as adding docstrings to your code, generating tests and creating markdown documentations (feel free to try more complex use cases)
- Only supports python codebases

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

Often more than not, LLMs output code in a format which is doesn't follow your programming language conventions. We have implemented a feature to automatically format code when a file is created/modified.

Right now we have only implemented the black formatter (python): 
- configurable via the `assistant.yaml` file via `file_handler: auto_format` and `file_handler: format_command`
- by default `auto_format = False`. 
- setting `auto_format = True` and `format_command = black` every generated file will be formated by black.

### Previewing changes

By default, any changes made to the codebase is first written to files with the suffix "_preview". This allows to easily view and accept/reject changes made to the codebase:
- configurable via the `assistant.yaml` file under `file_handler: preview`. 
- by default, it is set to True.
- setting it to False means directly overwritting the original files with the changes.

## Roadmap

Future efforts will be focused on the following:
- **Multi language support**: generalize tool to parse codebase with multiple languages
- **Context retrieval configuration**: allow user to configure which context to use for a given request via prompts.yaml
- **Dynamic context retrieval**: tell LLM the context to use via prompt
- **Dynamic output generation**: tell LLM the files to create/modify via prompt
- **Smart context retrieval**: let LLM decide which context to use for the request
- **Tracking execution flow and costs**: give better transparency of LLM usage and costs
- **VS Code extension**: integrate the tool inside IDE for easier usage

