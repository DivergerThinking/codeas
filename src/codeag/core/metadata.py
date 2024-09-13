from typing import List

from pydantic import BaseModel, Field

from codeag.core.agent import Agent
from codeag.core.llms import LLMClient
from codeag.core.repo import Repo


class FileUsage(BaseModel):
    is_code: bool
    db_related: bool
    ui_related: bool
    api_related: bool
    config_related: bool
    testing_related: bool
    security_related: bool
    deployment_related: bool


class CodeDetails(BaseModel):
    description: str
    external_imports: List[str]
    internal_imports: List[str]
    classes: List[str]
    relationships: List[str]
    functionalities: List[str]


class TestingDetails(BaseModel):
    description: str
    external_imports: List[str]
    internal_imports: List[str]
    classes: List[str]
    test_cases: List[str]


class RepoMetadata(BaseModel):
    files_usage: dict[str, FileUsage] = Field(default={})
    descriptions: dict[str, str] = Field(default={})
    code_details: dict[str, CodeDetails] = Field(default={})
    testing_details: dict[str, TestingDetails] = Field(default={})

    def generate_repo_metadata(self, llm_client: LLMClient, files_paths: list[str]):
        self.generate_files_usage(llm_client, files_paths)
        self.generate_descriptions(llm_client)
        self.generate_code_details(llm_client)
        self.generate_testing_details(llm_client)

    def generate_files_usage(self, llm_client: LLMClient, files_paths: list[str]):
        context = get_files_contents(files_paths)
        agent = Agent(
            instructions=prompt_identify_file_usage,
            model="gpt-4o-mini",
            response_format=FileUsage,
        )
        output = agent.run(llm_client, context)
        self.files_usage = {
            file_path: parse_response(output.response[file_path])
            for file_path in files_paths
        }

    def generate_descriptions(self, llm_client: LLMClient):
        files_to_generate_descriptions = [
            file_path
            for file_path, usage in self.files_usage.items()
            if not usage.is_code
        ]
        context = get_files_contents(files_to_generate_descriptions)
        agent = Agent(instructions=prompt_generate_descriptions, model="gpt-4o-mini")
        output = agent.run(llm_client, context)
        self.descriptions = {
            file_path: output.response[file_path]["content"]
            for file_path in files_to_generate_descriptions
        }

    def generate_code_details(self, llm_client: LLMClient):
        files_to_generate_code_details = [
            file_path
            for file_path, usage in self.files_usage.items()
            if usage.is_code and not usage.testing_related
        ]
        context = get_files_contents(files_to_generate_code_details)
        agent = Agent(
            instructions=prompt_generate_code_details,
            model="gpt-4o-mini",
            response_format=CodeDetails,
        )
        output = agent.run(llm_client, context)
        self.code_details = {
            file_path: parse_response(output.response[file_path])
            for file_path in files_to_generate_code_details
        }

    def generate_testing_details(self, llm_client: LLMClient):
        files_to_generate_testing_details = [
            file_path
            for file_path, usage in self.files_usage.items()
            if usage.is_code and usage.testing_related
        ]
        context = get_files_contents(files_to_generate_testing_details)
        agent = Agent(
            instructions=prompt_generate_testing_details,
            model="gpt-4o-mini",
            response_format=TestingDetails,
        )
        output = agent.run(llm_client, context)
        self.testing_details = {
            file_path: parse_response(output.response[file_path])
            for file_path in files_to_generate_testing_details
        }

    def get_file_metadata(self, file_path: str):
        return {
            "usage": self.get_file_usage(file_path),
            "description": self.get_file_description(file_path),
            "code_details": self.get_code_details(file_path),
            "testing_details": self.get_testing_details(file_path),
        }

    def get_file_usage(self, file_path: str) -> FileUsage:
        return self.files_usage.get(file_path)

    def get_file_description(self, file_path: str) -> str:
        return self.descriptions.get(file_path)

    def get_code_details(self, file_path: str) -> CodeDetails:
        return self.code_details.get(file_path)

    def get_testing_details(self, file_path: str) -> TestingDetails:
        return self.testing_details.get(file_path)


def get_files_contents(file_paths: list[str]) -> str:
    contents = {}
    for file_path in file_paths:
        with open(file_path, "r") as f:
            contents[file_path] = f"# path = {file_path}:\n{f.read()}"
    return contents


def parse_response(response: object):
    return response.choices[0].message.parsed


prompt_identify_file_usage = """
Analyze the given file path and content to determine its usage and type. Respond with boolean values for the following properties:

- is_code: Set to true if the file is a programming file (.py, .js, .java, etc.) AND contains some logic (classes, functions, etc.). IMPORTANT: Data, configuration, markdown, and text files should be set to false.
- db_related: Set to true if the file is related to database operations or configuration.
- ui_related: Set to true if the file is related to user interface components or styling.
- api_related: Set to true if the file is related to API endpoints or functionality.
- config_related: Set to true if the file contains configuration settings.
- testing_related: Set to true if the file is related to testing or test cases.
- security_related: Set to true if the file is related to security measures or authentication.
- deployment_related: Set to true if the file is related to deployment processes or settings.

A file can have multiple related aspects, so multiple properties can be true.

Examples:
1. A database configuration file would have both db_related and config_related set to true.
2. A React component file would have both is_code and ui_related set to true.
3. A test file for API endpoints would have is_code, api_related, and testing_related set to true.

IMPORTANT
Analyze the file path and content carefully to make accurate determinations.
Review your response. Pay particular attention to the **is_code** property.
Programming files which only contain data, configurations, or documentation should have the **is_code** property set to false.
""".strip()


prompt_generate_code_details = """
Analyze the given code and provide the following details:
1. Description: A single sentence describing what the file does.
2. External imports: List of external library used (only list the library name).
3. Internal imports: List of internal modules used (only list the module name). !! These internal modules should not appear in the external imports list.
4. Classes: List all class names defined in the file.
5. Relationships: Show dependencies between classes in this file and modules/classes from internal imports. Use -> for "depends on", <- for "is depended on by", and <> for bidirectional dependencies. Avoid repeating the same relationship in multiple directions.
6. Functionalities: List the main functionalities present in the file. DO NOT name specific methods or functions.

IMPORTANT:
Pay particular attention to what are considered internal vs external imports. 
External imports are standard external libraries used in the project, while internal imports are modules which are found in the same repository.
The internal imports are those you should use to generate the relationships between the given file and other files in the repository, which will later on be used to generate the system architecture.

Be concise and focus on key information. Do not write any explanations.
""".strip()


prompt_generate_testing_details = """
Analyze the given test file and provide the following details:
1. Description: A single sentence describing what the test file covers.
2. External imports: List of external libraries used (only list the library name).
3. Internal imports: List of internal modules being tested (only list the module name). !! These internal modules should not appear in the external imports list.
4. Classes: List the classes tested in this file.
5. Test cases: List the main test cases or test groups present in the file. Use general descriptions rather than specific method names.

IMPORTANT:
Pay particular attention to what are considered internal vs external imports. 
External imports are standard testing libraries or external dependencies, while internal imports are modules from the project being tested.

Be concise and focus on key information. Do not write any explanations.
""".strip()


prompt_generate_descriptions = """
Write a single sentence describing what the given file does.
Add the technologies mentioned inside that file (and their versions if present) after that description.
"""

if __name__ == "__main__":
    llm_client = LLMClient()
    repo = Repo(repo_path=".")
    incl = repo.filter_files()
    files_paths = [file_path for file_path, incl in zip(repo.files_paths, incl) if incl]

    metadata = RepoMetadata()
    metadata.generate_repo_metadata(llm_client, files_paths)

    print(metadata.get_file_metadata("src/codeag/core/agents.py"))
