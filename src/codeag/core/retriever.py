from typing import List

from pydantic import BaseModel, PrivateAttr


class FileUsage(BaseModel):
    is_code: bool
    db_related: bool
    ai_related: bool
    ui_related: bool
    api_related: bool
    config_related: bool
    testing_related: bool
    security_related: bool
    deployment_related: bool


prompt_identify_file_usage = """

"""


def identify_file_usage(file_path: str) -> FileUsage:
    ...


class CodeDetails(BaseModel):
    external_imports: List[str]
    internal_imports: List[str]
    classes: List[str]
    relationships: List[str]
    functionalities: List[str]


def generate_code_details(file_path: str) -> CodeDetails:
    ...


# if file_usage.code_related and not file_usage.testing_related:


class TestingDetails(BaseModel):
    imports: List[str]
    test_cases: List[str]


def generate_testing_details() -> TestingDetails:
    ...


# if file_usage.code_related and file_usage.testing_related:


def generate_descriptions() -> list[str]:
    ...


class ContextRetriever(BaseModel):
    include_all_files: bool = False
    include_code_files: bool = False
    include_testing_files: bool = False
    include_config_files: bool = False
    include_deployment_files: bool = False
    previous_outputs: list[str] = PrivateAttr(default=[])
    use_descriptions: bool = False
    use_details: bool = False
    _descriptions: list[str] = PrivateAttr(default=[])
    _files_types: list[FileUsage] = PrivateAttr(default=[])
    _code_details: list[CodeDetails] = PrivateAttr(default=[])
    _testing_details: list[TestingDetails] = PrivateAttr(default=[])

    def retrieve() -> str:
        ...


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

prompt_generate_docs_ai = """
Generate a comprehensive AI documentation section.

Start with the title '## AI'.

Include subsections using '### [Subsection Name]' format. Examples of subsections may include (but are not limited to):
- AI/ML Model Architecture
- Training Process
- Data Preprocessing
- Feature Engineering
- Model Evaluation Metrics
- AI Integration Points
- Ethical AI Considerations

Provide detailed technical information about AI/ML components, methodologies, and integration within the project.

IMPORTANT: The output should be directly suitable for a markdown file without any additional explanations or markdown code block tags.
"""
