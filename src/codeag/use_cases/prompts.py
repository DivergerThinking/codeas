generate_docs_project_overview = """
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

generate_docs_setup_and_development = """
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

generate_docs_architecture = """
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

generate_docs_ui = """
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

generate_docs_db = """
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

generate_docs_api = """
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

generate_docs_testing = """
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

generate_docs_deployment = """
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

generate_docs_security = """
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

define_testing_strategy = """
Analyze the given repository structure and create a comprehensive testing strategy by breaking down the test generation process into different steps. 
Consider the following aspects when defining the steps:
1. Types of tests: Each step should focus on a specific type of test, such as unit tests, integration tests, functional tests, etc.
2. File relationships: Group related files together to ensure that all of the necessary context is included.
3. Token limits: Aim to keep each step's input tokens count (the sum of the tokens count of the file paths) under 10,000 tokens unless it is absolutely necessary to exceed it.
4. Existing tests: If there already exist tests for a given file/class/method, do not include it in the testing step.

For each testing step, provide:
- files_paths: A list of file paths to be included for the test generation process
- type_of_test: The type of test to be performed
- guidelines: The guidelines to follow for the test generation process (testing framework, focus areas, etc.)
- test_file_path: The path of the file where the generated tests will be saved. **IMPORTANT**: make sure that the path doesn't already exist.

Consider the following when creating the strategy:
- Ensure critical components and core functionality are well-covered
- Balance between different types of tests
- Prioritize tests that will provide the most value and coverage
- Consider the complexity and importance of different parts of the codebase
"""

generate_tests_from_guidelines = """
Generate comprehensive tests based on the provided guidelines and file contents. 
Follow these instructions carefully:
1. Create tests according to the 'type of test' and 'guidelines' provided.
2. Write the complete test code, including all necessary imports, in code blocks.
3. Provide a brief explanation for each test or group of tests you generate.

IMPORTANT:
- All code must be contained within code blocks.
- The code blocks should contain the full, runnable test code in the correct order.
- Include ALL necessary imports at the beginning of the code.
- Do not include any code outside of the code blocks.
- The entire content of the code blocks will be extracted and written to a file, so ensure it's complete and correct.

Begin with a brief overview of the tests you're creating, then proceed with the test code and explanations.
"""
