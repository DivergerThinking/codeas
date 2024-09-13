import json

from pydantic import BaseModel

from codeag.core.metadata import RepoMetadata


class ContextRetriever(BaseModel):
    include_all_files: bool = False
    include_code_files: bool = False
    include_testing_files: bool = False
    include_config_files: bool = False
    include_deployment_files: bool = False
    include_security_files: bool = False
    include_ui_files: bool = False
    include_api_files: bool = False
    use_descriptions: bool = False
    use_details: bool = False

    def retrieve(self, files_paths: list[str], metadata: RepoMetadata) -> str:
        context = []
        for file_path in files_paths:
            file_usage = metadata.get_file_usage(file_path)
            if not file_usage:
                raise ValueError(f"File {file_path} not found in metadata")

            if self.include_all_files or (
                (self.include_code_files and file_usage.is_code)
                or (self.include_testing_files and file_usage.testing_related)
                or (self.include_config_files and file_usage.config_related)
                or (self.include_deployment_files and file_usage.deployment_related)
                or (self.include_security_files and file_usage.security_related)
                or (self.include_ui_files and file_usage.ui_related)
                or (self.include_api_files and file_usage.api_related)
            ):
                if self.use_details and file_usage.is_code:
                    if file_usage.testing_related:
                        details = metadata.get_testing_details(file_path)
                    else:
                        details = metadata.get_code_details(file_path)
                    if details:
                        context.append(
                            f"# {file_path}:\n{self.parse_json_response(details.model_dump_json())}"
                        )
                elif self.use_descriptions:
                    if file_usage.is_code:
                        details = (
                            metadata.get_code_details(file_path)
                            if not file_usage.testing_related
                            else metadata.get_testing_details(file_path)
                        )
                        if details:
                            description = f"# {file_path}:\n{details.description}"
                            if details.external_imports:
                                description += f"\nExternal imports: {', '.join(details.external_imports)}"
                            context.append(description)
                    else:
                        description = metadata.get_file_description(file_path)
                        context.append(f"# {file_path}:\n{description}")
                else:
                    with open(file_path, "r") as f:
                        content = f.read()
                    context.append(f"# {file_path}:\n{content}")

        return "\n\n".join(context)

    def parse_json_response(self, json_str: str) -> str:
        data = json.loads(json_str)
        result = [
            "(the below text is a generated representation of the code present in the file)"
        ]

        for key, value in data.items():
            if value:
                result.append(f"\n{key.replace('_', ' ').title()}:")
                if isinstance(value, list):
                    result.extend(f"- {item}" for item in value)
                else:
                    result.append(str(value))

        return "\n".join(result)


def generate_docs_project_overview() -> str:
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    context = retriever.retrieve()
    return context


def generate_docs_setup_and_development() -> str:
    retriever = ContextRetriever(
        include_config_files=True,
        include_deployment_files=True,
    )
    context = retriever.retrieve()
    return context


def generate_docs_architecture() -> str:
    retriever = ContextRetriever(include_code_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_ui() -> str:
    retriever = ContextRetriever(include_ui_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_db() -> str:
    retriever = ContextRetriever(include_db_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_api() -> str:
    retriever = ContextRetriever(include_api_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_testing() -> str:
    retriever = ContextRetriever(include_testing_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_deployment() -> str:
    retriever = ContextRetriever(include_deployment_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_security() -> str:
    retriever = ContextRetriever(include_security_files=True, use_details=True)
    context = retriever.retrieve()
    return context


def generate_docs_ai() -> str:
    retriever = ContextRetriever(include_ai_files=True, use_details=True)
    context = retriever.retrieve()
    return context


prompt_generate_docs_project_overview = """
Generate a comprehensive project overview documentation section.

Start with the title '## Project Overview'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Purpose and Goals
- Target Audience
- Key Features
- Technology Stack
- System Architecture Overview
- Repository Structure

Provide detailed information for each subsection.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_setup_and_development = """
Create a detailed setup and development documentation section.

Start with the title '## Setup and Development'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Prerequisites
- Environment Setup
- Dependencies
- Build Process
- Configuration Files
- Code Style and Standards

Provide clear, step-by-step instructions and explanations for each subsection.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_architecture = """
Produce a thorough architecture documentation section.

Start with the title '## Architecture'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Detailed System Architecture
- Core Components
- Main Modules/Classes
- Key Algorithms
- Data Structures
- Design Patterns
- Business Logic
- Core Functions
- Workflow Processes
- Data Flow

Provide in-depth technical details and explanations for each subsection.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_ui = """
Generate a comprehensive UI documentation section.

Start with the title '## User Interface'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Component Hierarchy
- State Management
- Styling Approach
- Responsive Design
- Accessibility Features
- User Interaction Flows

Provide detailed explanations and examples for each aspect of the UI.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_db = """
Create a detailed database documentation section.

Start with the title '## Database'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Schema Design
- Entity-Relationship Diagrams
- Indexing Strategy
- Query Optimization
- Data Models
- Database Migrations

Provide comprehensive information about the database structure, optimization techniques, and management processes.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_api = """
Produce a thorough API documentation section.

Start with the title '## API'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Endpoints
- Request/Response Formats
- Authentication Methods
- Rate Limiting
- API Versioning
- Error Handling for API Responses

Provide detailed descriptions of each API endpoint, including request methods, parameters, response formats, and examples.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_testing = """
Generate a comprehensive testing documentation section.

Start with the title '## Testing'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Unit Tests
- Integration Tests
- End-to-End Tests
- Test Coverage
- Mocking Strategies
- Test Data Management
- Continuous Integration Testing

Provide detailed information about testing methodologies, tools used, and best practices.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_deployment = """
Create a detailed deployment documentation section.

Start with the title '## Deployment'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Deployment Process
- Continuous Integration/Continuous Deployment (CI/CD)
- Environment-Specific Configurations
- Scaling Strategies
- Server Setup
- Containerization
- Cloud Service Configurations

Provide step-by-step deployment instructions, configuration details, and best practices.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

prompt_generate_docs_security = """
Produce a thorough security documentation section.

Start with the title '## Security'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- Authentication Mechanisms
- Authorization Rules
- Data Encryption
- Input Validation
- CSRF Protection
- XSS Prevention
- Security Best Practices
- Compliance and Regulations

Provide detailed explanations of security measures, implementation details, and compliance requirements.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""

if __name__ == "__main__":
    metadata = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    context = retriever.retrieve(metadata.descriptions.keys(), metadata)
    print(context)
