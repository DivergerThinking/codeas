# codeas

codeas stands for CODEbase ASsistant. It boosts your software development processes by leveraging LLMs using your full codebase as context.

## Why this tool ❓

There are a lot of existing AI tools for software development, each of which has its capabilities and limitations. <br>
At [Diverger](https://diverger.ai/) we decided to build our own AI tool for software development to help us where other tools can't. We chose to share it with the open-source community so that other developers can benefit from it. Any feedback and/or contribution is welcome. Happy coding!

##  🛠️ Installation

```bash
pip install codeas
```

#### OpenAI key
Currently, the tool only supports OpenAI as a provider.
To add your OpenAI key, export it as an environment variable via the terminal:

```bash
export OPENAI_API_KEY="..."
```

## 💻 Usage

### Chat interface

You can start the chat interface by running the following command in your terminal:

```bash
codeas
```

This will open a chat interface that you can use to ask questions to your assistant, interact with your codebase through agents and run commands.

```text
> [ask the assistant what you want]
```

### Agents

Agents use OpenAI's function calling to interact with the codebase. They are triggered through the use of "@" in your prompts. Example:
```text
> @add src/codeas/codebase.py structure
```
The above command adds the structure of src/codeas/codebase.py as context to the chat conversation. To view the context currently added to the conversation you can use the /view command.

The following agents are currently supported:
- `@add`: adds context from your codebase to the conversation
- `@write` - writes content to files in your codebase
- `@search` - searches through your codebase for given code

See **Agents Usage Examples** for more info on how to use agents

### Commands

Commands can be used to perform specific actions that add some functionalities to the tool yet do not require the use of LLMs. The following commands are available

- `/view`: prints the context currently used in the conversation to the console. Use this command to check that the correct context for your request was added to the conversation properly
- `/clear`: clears the context and chat history from the conversation. Use this command when you don't need the previous context anymore, this helps reduce costs by removing unnecessary tokens given to the LLM
- `/copy`: adds the last message to your clipboard.
- `/tree`: prints the tree directory currently used by the codebase parser. See codebase settings for more information. 
- `/exit`: exits the chat interface. The same can be achieved using `ctrl + C`

### Settings

Settings are stored inside ``.codeas/settings.yaml`` after the first time. <br>
**IMPORTANT NOTE**: restart the chat interface after changing. <br>

The following settings are available:
- ``chat_config``: configures model and temperature to use for chat assistant. gpt-3.5-turbo-1106 is used by default as it is faster, cheaper and produces reasonably good results.
- ``agent_configs``: configures model and temperature to use for each agent. gpt-4-1106-preview is used by default as it works best for function calls. 
- ``codebase_config``: configures which files are parsed when retrieving context from your codebase. By default, only **file extensions [.py, .java, .js, .ts, .cs, .rs, .rb, .c, .go, .php] are included** and **files starting with "." and "__" are excluded**. <br> **IMPORTANT NOTE**: parsing of the code structure of the files, functions and classes is currently only **supported for **python** files**. Use `/tree` command to check which files are included.

### Agent Usage Examples:

**`@add` examples**:

Adding a file:
```text
> @add src/codeas/codebase.py
```
Adding the code structure of a file 
```text
> @add structure of src/codeas/codebase.py
```
Adding all files in a directory 
```text
> @add files under src/codeas directory
```
Adding given lines of a file 
```text
> @add src/codeas/codebase.py l1-100
```
Adding specific class/function 
```text
> @add src/codeas/codebase Codebase class
```

NOTE: you can combine the above prompts in one request and use your own wording.

**`@write` examples**:
Writing markdown documentation to a new file:
```text
> @write markdown documentation for the given context inside docs/my_docu.md
```
Writing tests to a new file:
```text
> @write tests for the given classes using pytest. Write the tests inside tests/my_class.py
```
Writing functions to an existing file:
```text
> @write a function to read a file and append it to src/codeas/utils.py
```

NOTE: you can also first generate docs, tests, etc. without the @write and use /copy command to add the output to your clipboard

**`@search` examples**:
Searching through some functionality:
```text
> @search the sections of code related to parsing a codebase
```
Searching for a given class/function:
```text
> @search which class or function is responsible for starting the terminal interface
```

NOTE: this feature is relatively experimental and may not work so well on large codebases.

## 🚀 Releases

### v0.3.0 (15.01.2023)
Use AI agents to better interact with the codebase

**Release notes**
- Integrates agents using OpenAI tool calling to better interact with codebase 
- Adds commands to improve usability and transparency of the tool
- Improves context retrieval options with possibility to only add file structure or sections of a file
- Improves console output for better UX

### v0.2.0 (22.11.2023)
Enables context retrieval and file creation to be more dynamic, making the tool act as an agent on your codebase.

**Release notes**
- Dynamic context retrieval: specify the files you want the LLM to use in your prompt
- Dynamic file creation: specify the files you want the LLM to create and where.
- Dynamic guideline selection: add guidelines in prompts.yaml and let the LLM decide which ones are relevant to each of your requests 
- Cross-language support: automatic file parsing for the most popular programming languages (.ts, .js, .py, .cs, .rb, .rs, .java, .go, .c, .php)
- Multiple file context: multiple files can be used at once within the context

### v0.1.0 (24.10.2023)
First release that supports simple use cases.

**Release notes**:
- Focused on simple use cases such as adding docstrings to your code, generating tests and creating markdown documentations (feel free to try more complex use cases)
- Only supports python codebases