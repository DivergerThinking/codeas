from codeas.core.agent import Agent
from codeas.core.retriever import ContextRetriever
from codeas.core.state import state

prompt_identify_modules = """
Analyze the given codebase and identify small, focused modules. Each module should represent a specific functionality or feature and typically consist of only a few closely related files. Avoid grouping files based solely on their directory structure.

For each module you identify:
1. Provide a concise module name that reflects its specific functionality
2. List only the few files that directly contribute to this functionality
3. Describe the module's specific purpose and main functionality in 1-2 sentences

Use the following format for your response:

- Module Name: [Specific Functionality Name]
  Files:
  - [File path 1]
  - [File path 2]
  - [File path 3] (rarely more than 3-5 files)
  Description: [Brief, focused description of the module's specific purpose]

Guidelines:
- Aim for small, cohesive modules focused on a single responsibility
- Modules should typically contain 2-5 files, rarely more
- Prioritize functional relationships over directory structure
- It's okay if some files appear in multiple modules if they contribute to different functionalities
- Not every file needs to be in a module; focus on identifying clear, specific functionalities

Ensure your analysis results in numerous small, focused modules rather than a few large, generic groupings.
"""


def identify_modules(preview: bool = False):
    retriever = ContextRetriever(include_code_files=True, use_relationships=True)
    context = retriever.retrieve(
        state.repo.included_files_paths,
        state.repo.included_files_tokens,
        state.repo_metadata,
    )
    agent = Agent(
        instructions=prompt_identify_modules,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=context)
    else:
        return agent.run(state.llm_client, context=context)


prompt_identify_c4_components_and_containers = """
Analyze the given codebase and identify the components and containers according to the C4 model:

1. Components:
   - Identify groupings of related functionality encapsulated behind well-defined interfaces.
   - These could be collections of implementation classes or modules behind an interface.
   - Components are not separately deployable units.

2. Containers:
   - Identify applications or data stores that need to be running for the system to work.
   - These represent runtime boundaries and are typically deployable units.
   - Examples: web applications, desktop applications, mobile apps, databases, file systems, serverless functions, etc.

For each component and container you identify:
1. Provide a concise name that reflects its nature
2. Describe its purpose and main functionality in 1-2 sentences
3. List the technologies used by the component or container
4. List the relationships with other components or containers

Use the following format for your response:

## Containers:

#### [Container Name]
[Description, technologies and relationships]

#### [Container Name]
[Description, technologies and relationships]

## Components:

#### [Component Name]
[Description, technologies and relationships]

#### [Component Name]
[Description, technologies and relationships]

NOTE: If the project doesn't have distinct containers, focus solely on identifying components.
"""


def identify_c4_components_and_containers(preview: bool = False):
    retriever = ContextRetriever(include_code_files=True, use_relationships=True)
    context = retriever.retrieve(
        state.repo.included_files_paths,
        state.repo.included_files_tokens,
        state.repo_metadata,
    )
    agent = Agent(
        instructions=prompt_identify_c4_components_and_containers,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=context)
    else:
        return agent.run(state.llm_client, context=context)


prompt_generate_c4_diagrams = """
Generate graphs in mermaid for the given components and containers.
The graphs show clearly how the components and containers are related to each other.
Include some styling to clearly differentiate between components, containers and systems.

Example of container graph for an Internet Banking System:
```mermaid
graph TB
  classDef person fill:#08427b,stroke:#052e56,color:#ffffff
  classDef system fill:#999999,stroke:#6b6b6b,color:#ffffff
  classDef container fill:#438dd5,stroke:#2e6295,color:#ffffff

  1["Personal Banking Customer [person]"]:::person
  4["Mainframe Banking System"]:::system
  5["E-mail System"]:::system

  subgraph 7["Internet Banking System"]
    style 7 stroke:#0b4884,color:#0b4884
    10["Web Application [container]"]:::container
    11["API Application [container]"]:::container
    18["Database [container]"]:::container
    8["Single-Page Application [container]"]:::container
    9["Mobile App [container]"]:::container
  end

  5--"Sends e-mails to"-->1
  1--"Visits bigbank.com/ib using"-->10
  1--"Views account balances, and makes payments using"-->8
  1--"Views account balances, and makes payments using"-->9
  10--"Delivers to the customer's web browser"-->8
  8--"Makes API calls to"-->11
  9--"Makes API calls to"-->11
  11--"Reads from and writes to"-->18
  11--"Makes API calls to"-->4
  11--"Sends e-mail using"-->5
```

Example of the component graph for the same Internet Banking System:
```mermaid
graph TB
  classDef system fill:#999999,stroke:#6b6b6b,color:#ffffff
  classDef container fill:#438dd5,stroke:#2e6295,color:#ffffff
  classDef component fill:#85bbf0,stroke:#5d82a8,color:#000000

  4["Mainframe Banking System"]:::system
  5["E-mail System"]:::system
  8["Single-Page Application [container]"]:::container
  9["Mobile App [container]"]:::container
  18["Database [container]"]:::container

  subgraph 11["API Application"]
    style 11 stroke:#2e6295,color:#2e6295
    12["Sign In Controller [component]"]:::component
    13["Accounts Summary Controller [component]"]:::component
    14["Reset Password Controller [component]"]:::component
    15["Security Component [component]"]:::component
    16["Mainframe Banking System Facade [component]"]:::component
    17["E-mail Component [component]"]:::component
  end

  8--"Makes API calls to"-->12
  8--"Makes API calls to"-->13
  8--"Makes API calls to"-->14
  9--"Makes API calls to"-->12
  9--"Makes API calls to"-->13
  9--"Makes API calls to"-->14
  12--"Uses"-->15
  13--"Uses"-->16
  14--"Uses"-->15
  14--"Uses"-->17
  15--"Reads from and writes to"-->18
  16--"Makes API calls to"-->4
  17--"Sends e-mail using"-->5
```

Output format:
## Container graph:
```mermaid
graph TB
   ...
```

## Component graph:
```mermaid
graph TB
   ...
```

"""


def generate_c4_diagrams(c4_model: str, preview: bool = False):
    agent = Agent(
        instructions=prompt_generate_c4_diagrams,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=c4_model)
    else:
        return agent.run(state.llm_client, context=c4_model)
