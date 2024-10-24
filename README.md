# codeas

codeas stands for CODEbase ASsistant. It boosts your software development processes by leveraging LLMs using your full codebase as context.

## Why this tool ❓

There are a lot of existing AI tools for software development, each of which has its capabilities and limitations. <br>
At [Diverger](https://diverger.ai/) we decided to build our own AI tool for software development to help us where other tools can't. We chose to share it with the open-source community so that other developers can benefit from it. Any feedback and/or contribution is welcome. Happy coding!

## Demo

To view the core functionalities of codeas without setting up anything, you can check out our live demo:

[Codeas Demo](https://codeas-diverger.streamlit.app/)

This demo showcases the main features of codeas, allowing you to explore its capabilities before installation.

##  🛠️ Installation

```bash
pip install codeas
```
**NOTE**: use python version 3.9, 3.10 or 3.11 (3.12 currently not supported)
We recommend using anaconda 

#### API keys
Currently, the tool support OpenAI, Anthropic and Google Gemini.
You can add the corresponding API keys using environment variables as such:

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export GOOGLE_API_KEY="..."
```
or you can add them in the corresponding text inputs found in the Home page of the user interface.

## 💻 Usage

### Streamlit interface

Codeas provides a user-friendly Streamlit interface to interact with your codebase. To launch the interface, run the following command in your terminal:

```bash
codeas
```

The Streamlit interface offers several features:

1. **Documentation Generation**: Automatically generate comprehensive documentation for your project.
2. **Deployment Strategy**: Define deployment requirements and generate Terraform code for your infrastructure.
3. **Testing**: Create test suites and generate test cases for your codebase.
4. **Refactoring**: Identify areas for refactoring and apply changes to improve your code quality.

Each feature provides options to:
- Previewing fetched codebase context and estimated costs before executing the generation process
- Viewing each generation step and selecting only the relevant sections 
- Applying generated changes to your codebase

The user interface also includes:
- **Chat interface**: Engage in conversations with AI models about your codebase, leveraging the context of your project for more accurate and relevant responses.
- **Prompts management**: Create, edit, and manage custom prompts for various software development tasks, enhancing the efficiency of your interactions with the AI.
- **Usage tracking**: Monitor your usage of the tool, including costs, number of requests, and breakdowns by different features and models.

To get started, simply navigate through the different pages in the sidebar and follow the on-screen instructions for each feature.

## How does it work

Codeas operates by leveraging metadata generation to create a more efficient and context-specific AI-assisted development process. Here's an overview of how the application functions:

### Metadata Generation

1. **File Analysis**: The application analyzes each file in your repository to determine its type, usage, and content.

2. **Metadata Extraction**: For each file, Codeas generates metadata including:
   - File usage (e.g., code, configuration, testing)
   - File description
   - Code details (for code files)
   - Testing details (for test files)

3. **Efficient Storage**: This metadata is stored in a structured format, allowing for quick retrieval and reducing the need to re-analyze files for each operation.

### Context Retrieval

When performing operations, Codeas uses the generated metadata to retrieve relevant context:

1. **Selective Inclusion**: Based on the operation type, only relevant files are included in the context (ex. documenting the DB will only used files related to database).
2. **Detailed or Summary Information**: Depending on the task, either detailed code information or summary descriptions are used.

This approach allows Codeas to provide more specific context to the AI model while reducing the overall token count, leading to more accurate and cost-effective results.

### Use Cases

Codeas currently supports four main use cases:

1. **Documentation Generation**
   - Analyzes the codebase structure and metadata
   - Generates comprehensive documentation sections (e.g., project overview, architecture, API)
   - Allows for selective generation and preview of documentation sections
  
2. **Deployment Strategy**
   - Examines the project structure and requirements
   - Suggests an appropriate deployment strategy (currently focused on AWS)
   - Generates Terraform code based on the defined strategy

3. **Testing**
   - Analyzes the codebase to define a comprehensive testing strategy
   - Generates test cases based on the defined strategy
   - Supports various types of tests (unit, integration, etc.)

4. **Refactoring**
   - Identifies areas of the codebase that could benefit from refactoring
   - Suggests refactoring strategies for selected code groups
   - Generates detailed refactoring proposals and can apply changes

For each use case, Codeas provides options to preview the AI-generated content, estimate costs, and selectively apply changes to your codebase. This approach ensures that you have full control over the AI-assisted development process while benefiting from the efficiency and insights provided by the tool.

## 🚀 Releases

### v0.4.0

**Release notes**
- Introduces a new Streamlit-based user interface for improved user experience
- Tailored to specific software development processes: Documentation, Deployment, Testing, and Refactoring
- Improves context retrieval via metadata generation
- Implements a preview feature for viewing fetched context and estimating costs before running operations
- Adds support for applying generated changes to the codebase

### v0.3.0
Use AI agents to better interact with the codebase

**Release notes**
- Integrates agents using OpenAI tool calling to better interact with codebase 
- Adds commands to improve usability and transparency of the tool
- Improves context retrieval options with possibility to only add file structure or sections of a file
- Improves console output for better UX

### v0.2.0
Enables context retrieval and file creation to be more dynamic, making the tool act as an agent on your codebase.

**Release notes**
- Dynamic context retrieval: specify the files you want the LLM to use in your prompt
- Dynamic file creation: specify the files you want the LLM to create and where.
- Dynamic guideline selection: add guidelines in prompts.yaml and let the LLM decide which ones are relevant to each of your requests 
- Cross-language support: automatic file parsing for the most popular programming languages (.ts, .js, .py, .cs, .rb, .rs, .java, .go, .c, .php)
- Multiple file context: multiple files can be used at once within the context

### v0.1.0
First release that supports simple use cases.

**Release notes**:
- Focused on simple use cases such as adding docstrings to your code, generating tests and creating markdown documentations (feel free to try more complex use cases)
- Only supports python codebases
