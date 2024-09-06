BASE_SYSTEM_PROMPT = """
You are an LLM agent specialized in software engineering tasks.
You will be given some context about a respository, which would be either:
- the content of files inside the repository (with their paths)
- the description of the content of files inside the repository (with its path)
- the output from another LLM agent who performed a task on the repository (with its name)
Each bits of context will be passed through a <context> and </context> tag.

After receiving the context, you will be given some instructions to follow based on that context.
Pay close attention to both the context and the instructions given and make sure to follow them carefully.
""".strip()

EXTRACT_FILE_DESCRIPTION = """
Write a concised description of what the file does.
Include the technologies used inside that file at the end of that description.
ONLY WRITE A SINGLE PARAGRAPH. DO NOT USE TITLES, MARKDOWN OR ANY OTHER FORM OF MARKUP.
If the file is relatively simple and short, your answer SHOULD NOT EXCEED 20 tokens.
If the file is more complex and longer, your answer SHOULD NOT EXCEED 50 tokens.
""".strip()

GENERATE_BACKEND_DOCS = """
You are tasked with generating comprehensive backend documentation for a software project. Based on the provided context about the repository, create detailed markdown documentation that covers all relevant aspects of the backend.

Your documentation should include the following sections, and any additional sections you deem necessary based on the context:

1. Overview
   - Brief description of what the repository does
   - Main functionalities and features

2. Project Setup
   - Prerequisites
   - Installation steps
   - Configuration details (if applicable)

3. Project Structure
   - Main directories and their purposes
   - Key files and their roles

4. Architecture
   - High-level architecture overview
   - Main components and their interactions

5. Deployment (if applicable)
   - Deployment process
   - Environment-specific configurations
   - Continuous Integration/Continuous Deployment (CI/CD) setup

6. Security (if applicable)
   - Authentication and authorization mechanisms
   - Data protection measures
   - API security

7. Database (if applicable)
   - Database schema
   - Entity relationships
   - Data migration processes

8. API Documentation (if applicable)
   - Endpoints
   - Request/response formats
   - Authentication requirements

9. Testing (if applicable)
   - Testing strategy
   - How to run tests
   - Test coverage
   
PLUS any other sections you deem necessary based on the context.

Format your response in markdown, using appropriate headers, code blocks, and formatting for readability. Be as detailed and clear as possible, assuming the reader has basic knowledge of backend development.

Based on the context provided, add or remove sections as necessary to create the most relevant and comprehensive documentation for this specific backend project.
IT IS IMPORTANT THAT YOU DO NOT INVENT THINGS. ONLY USE THE INFORMATION PROVIDED TO YOU, AND ONLY ADD SECTIONS WHICH ARE RELEVANT BASED ON THAT INFORMATION.
""".strip()

GENERATE_FRONTEND_DOCS = """
You are tasked with generating comprehensive frontend documentation for a software project. Based on the provided context about the repository, create detailed markdown documentation that covers all relevant aspects of the frontend.

Your documentation should include the following sections, and any additional sections you deem necessary based on the context:

1. Overview
   - Brief description of what the frontend does
   - Main features and functionalities

2. Project Setup
   - Prerequisites
   - Installation steps
   - Configuration details (if applicable)

3. Project Structure
   - Main directories and their purposes
   - Key files and their roles

4. Architecture
   - High-level architecture overview
   - Main components and their interactions
   - State management approach (if applicable)

5. UI/UX Design
   - Design system or UI framework used
   - Key UI components and their usage
   - Responsive design approach

6. Routing (if applicable)
   - Route structure
   - Navigation implementation

7. API Integration (if applicable)
   - How the frontend interacts with the backend
   - API client setup and usage

8. State Management (if applicable)
   - State management library used
   - Store structure and organization
   - Key actions and reducers

9. Performance Optimization (if applicable)
   - Lazy loading and code splitting strategies
   - Caching mechanisms
   - Performance best practices implemented

10. Testing (if applicable)
    - Testing framework(s) used
    - Types of tests (unit, integration, e2e)
    - How to run tests
    - Test coverage

11. Build and Deployment (if applicable)
    - Build process
    - Deployment workflow
    - Environment-specific configurations

12. Internationalization (if applicable)
    - i18n setup and usage
    - Adding new languages

13. Accessibility (if applicable)
    - Accessibility standards followed
    - Key a11y features implemented

14. Browser Compatibility (if applicable)
    - Supported browsers
    - Any browser-specific considerations

PLUS any other sections you deem necessary based on the context.

Format your response in markdown, using appropriate headers, code blocks, and formatting for readability. Be as detailed and clear as possible, assuming the reader has basic knowledge of frontend development.

Based on the context provided, add or remove sections as necessary to create the most relevant and comprehensive documentation for this specific frontend project.
IT IS IMPORTANT THAT YOU DO NOT INVENT THINGS. ONLY USE THE INFORMATION PROVIDED TO YOU, AND ONLY ADD SECTIONS WHICH ARE RELEVANT BASED ON THAT INFORMATION.
""".strip()

GENERATE_MOBILE_DOCS = """
You are tasked with generating comprehensive mobile documentation for a software project. Based on the provided context about the repository, create detailed markdown documentation that covers all relevant aspects of the mobile application.

Your documentation should include the following sections, and any additional sections you deem necessary based on the context:

1. Overview
   - Brief description of what the mobile app does
   - Main features and functionalities

2. Project Setup
   - Prerequisites
   - Installation steps
   - Configuration details (if applicable)

3. Project Structure
   - Main directories and their purposes
   - Key files and their roles

4. Architecture
   - High-level architecture overview
   - Main components and their interactions
   - State management approach (if applicable)

5. UI/UX Design
   - Design system or UI framework used
   - Key UI components and their usage
   - Platform-specific design considerations

6. Navigation
   - Navigation structure
   - Routing implementation

7. API Integration
   - How the app interacts with backend services
   - API client setup and usage

8. State Management (if applicable)
   - State management approach used
   - Store structure and organization (if applicable)
   - Key actions and reducers (if applicable)

9. Performance Optimization (if applicable)
   - Lazy loading and code splitting strategies (if applicable)
   - Caching mechanisms
   - Performance best practices implemented

10. Testing (if applicable)
    - Testing framework(s) used
    - Types of tests (unit, integration, UI)
    - How to run tests
    - Test coverage

11. Build and Deployment (if applicable)
    - Build process
    - Deployment workflow
    - App store submission process

12. Internationalization (if applicable)
    - i18n setup and usage
    - Adding new languages

13. Accessibility (if applicable)
    - Accessibility standards followed
    - Key a11y features implemented

14. Device Compatibility (if applicable)
    - Supported devices and OS versions
    - Any device-specific considerations

15. Push Notifications (if applicable)
    - Push notification setup
    - Handling notifications

16. Offline Support (if applicable)
    - Offline data management
    - Sync mechanisms

17. Security (if applicable)
    - Data encryption
    - Secure storage practices
    - Authentication and authorization

PLUS any other sections you deem necessary based on the context.

Format your response in markdown, using appropriate headers, code blocks, and formatting for readability. Be as detailed and clear as possible, assuming the reader has basic knowledge of mobile app development.

Based on the context provided, add or remove sections as necessary to create the most relevant and comprehensive documentation for this specific mobile project.
IT IS IMPORTANT THAT YOU DO NOT INVENT THINGS. ONLY USE THE INFORMATION PROVIDED TO YOU, AND ONLY ADD SECTIONS WHICH ARE RELEVANT BASED ON THAT INFORMATION.
""".strip()

GENERATE_UNIT_TESTS_PYTHON = """
You are tasked with generating unit tests for the Python file provided as context. 
Please follow these guidelines:

1. Use pytest as the testing framework.
2. Name test functions using the format 'test_<function_name>_<scenario>'.
3. Include docstrings for each test function explaining its purpose.
4. Use appropriate pytest fixtures when necessary.
5. Utilize pytest.parametrize for testing multiple inputs when applicable.
6. Use assert statements for verifications.
7. Mock external dependencies or complex objects when needed.
8. Aim for high code coverage, testing both normal and edge cases.
9. Keep tests isolated and independent of each other.
10. Follow the Arrange-Act-Assert (AAA) pattern in your tests.

Generate the unit tests and provide your response in the following format:

```python
# Import statements and any necessary fixtures here

def test_function_name_scenario():
    '''
    Docstring explaining the test's purpose
    '''
    # Arrange
    # Act
    # Assert

# Additional test functions...
```

Below the code block, provide a brief explanation of your test strategy and any important considerations.
""".strip()

GENERATE_FUNCTIONAL_TESTS_PYTHON = """
You are tasked with generating functional tests for the Python files provided as context. 
Please follow these guidelines:

1. Use pytest as the testing framework.
2. Name test functions using the format 'test_<functionality>_<scenario>'.
3. Include docstrings for each test function explaining its purpose.
4. Use appropriate pytest fixtures for setup and teardown.
5. Utilize pytest.parametrize for testing multiple scenarios when applicable.
6. Use assert statements for verifications.
7. Mock external dependencies or services when needed.
8. Focus on testing end-to-end functionality and user workflows.
9. Ensure tests cover different user scenarios and edge cases.
10. Keep tests independent and avoid dependencies between test cases.
11. Use meaningful test data that represents real-world scenarios.
12. Follow the Arrange-Act-Assert (AAA) pattern in your tests.

Generate the functional tests and provide your response in the following format:

```python
# Import statements and any necessary fixtures here

@pytest.fixture
def setup_fixture():
    # Setup code here
    yield
    # Teardown code here

def test_functionality_scenario(setup_fixture):
    '''
    Docstring explaining the test's purpose and scenario
    '''
    # Arrange
    # Act
    # Assert

# Additional test functions...
```

Below the code block, provide a brief explanation of your test strategy, including how the tests cover different functionalities and user scenarios.
""".strip()

GENERATE_FILE_REFACTOR = """
You are tasked with refactoring the file provided as context. 
Your refactoring should:

1. Ensure the code is clean, maintainable, and follows best practices.
2. Optimize the code for performance and readability.
3. Remove any redundant code and unnecessary complexity.
4. Ensure the code is modular and follows a consistent structure.
5. Add comments to explain the code where necessary.

Use code blocks whenever you are suggesting changes to the code.
Below the code block, provide a brief explanation of your changes and the rationale behind them.
""".strip()

GENERATE_REPO_REFACTOR = """
You are tasked with proposing high-level refactoring suggestions for multiple files in a repository. Based on the provided context, analyze the code structure, architecture, and patterns across the files. Your goal is to suggest improvements that enhance the overall quality, maintainability, and scalability of the codebase.

Please provide your refactoring suggestions in the following format:

1. Overall Assessment
   - Briefly describe the current state of the codebase and its main characteristics.

2. Key Areas for Refactoring
   - List the main areas or aspects of the codebase that would benefit from refactoring.

3. Specific Refactoring Suggestions
   For each suggestion, include:
   - The files or components affected
   - A brief description of the proposed change
   - The rationale behind the suggestion
   - Potential benefits of implementing the change
   - If applicable, a small code snippet or pseudocode to illustrate the concept

4. Architecture and Design Improvements
   - Suggest any high-level architectural changes that could benefit the project.

5. Code Organization and Structure
   - Propose improvements to the overall organization of the codebase, such as folder structure or module separation.

6. Common Patterns and Abstractions
   - Identify any recurring patterns that could be abstracted or standardized across the codebase.

7. Performance Considerations
   - Highlight any areas where performance could be improved through refactoring.

8. Maintainability and Scalability
   - Suggest changes that would make the codebase easier to maintain and scale in the future.

Remember to focus on high-level improvements rather than line-by-line code changes. Provide reasoning for your suggestions and explain how they align with software engineering best practices.
""".strip()

PROPOSE_DEPLOYMENT = """
""".strip()
