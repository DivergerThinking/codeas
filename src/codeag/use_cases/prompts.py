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

define_refactoring_files = """
You are an expert software architect tasked with grouping related files for a refactoring project. Your goal is to create logical groups of files that are closely related and should be refactored together. Follow these guidelines:

1. Analyze the given files and their contents to understand their relationships and dependencies.
2. Group files based on their functional similarities, shared responsibilities, and interdependencies.
3. Ensure that each file is placed in exactly one group - no file should appear in multiple groups.
4. Create as many groups as necessary to logically organize all the files.
5. Consider the following factors when grouping files:
   - Shared imports or dependencies
   - Similar naming conventions or prefixes
   - Files that implement related features or functionality
   - Files that belong to the same module or package
   - Files that operate on the same data structures or models

Ensure that all files from the input are included in the groups, and that the grouping is logical and conducive to efficient refactoring.

Return the groups as a list of FileGroup objects, each FileGroup containing a list of the file paths contained in the group and a unique descriptive name for that group.
""".strip()

generate_proposed_changes = """
As an expert software architect, your task is to propose refactoring changes for a group of related files. Analyze the provided files and suggest improvements to enhance code quality, maintainability, and adherence to best practices. Follow these guidelines:

1. Examine the code structure, design patterns, and overall architecture of the files.
2. Identify areas for improvement, such as:
   - Code duplication
   - Overly complex methods or classes
   - Poorly named variables, functions, or classes
   - Violation of SOLID principles
   - Inefficient algorithms or data structures
   - Lack of proper error handling
   - Inconsistent coding style
3. Propose specific refactoring changes for each file.
4. Provide a brief explanation for each proposed change, highlighting its benefits.

Return your response in a structured format with
- file_path: <path to the file>
- changes: <proposed changes for that file>

EXAMPLE STRUCTURE FOR PROPOSED CHANGES:

1. <Refactoring suggestion 1>
   Explanation: <Brief explanation of the issue and proposed solution>
   ```<language>
   // Original code
   <problematic code snippet>

   // Refactored code
   <improved code snippet>
   ```
2. <Refactoring suggestion 2>
   Explanation: <Brief explanation of the issue and proposed solution>
   ...

Only include code snippets if you think it is relevant. The above is only an example of what the structure of your response might look like.
IMPORTANT: Remember to consider the context of the entire group of files when making suggestions, as some refactoring changes may have implications across multiple files.
""".strip()

generate_diffs = """
As an expert software architect, your task is to implement the proposed refactoring changes for a single file. You will be provided with the original file content and the proposed changes. Your goal is to generate a diff that represents the necessary changes.

Follow these guidelines:

1. Carefully review the original file content and the proposed changes.
2. Generate a diff that accurately represents the proposed changes.
3. Use unified diff format for the file.
4. Include only the changed parts of the file in the diff.
5. Ensure that applying this diff will result in the desired refactored code.

EXAMPLE OF PROPOSED CHANGES:

1. Add an imports of sympy.
2. Remove the is_prime() function.
3. Replace the existing call to is_prime() with a call to sympy.isprime().

EXAMPLE OF DIFF OUTPUT:

```diff
--- mathweb/flask/app.py
+++ mathweb/flask/app.py
@@ ... @@
-class MathWeb:
+import sympy
+
+class MathWeb:
@@ ... @@
-def is_prime(x):
-    if x < 2:
-        return False
-    for i in range(2, int(math.sqrt(x)) + 1):
-        if x % i == 0:
-            return False
-    return True
@@ ... @@
-@app.route('/prime/<int:n>')
-def nth_prime(n):
-    count = 0
-    num = 1
-    while count < n:
-        num += 1
-        if is_prime(num):
-            count += 1
-    return str(num)
+@app.route('/prime/<int:n>')
+def nth_prime(n):
+    count = 0
+    num = 1
+    while count < n:
+        num += 1
+        if sympy.isprime(num):
+            count += 1
+    return str(num)
```

FILE EDITING RULES:
- Include the first 2 lines with the file paths.
- Don't include timestamps with the file paths.
- Start a new hunk for each section of the file that needs changes.
- Start each hunk of changes with a `@@ ... @@` line. (Don't include line numbers like `diff -U0` does.)
- Mark all new or modified lines with `+`.
- Mark all lines that need to be removed with `-`.
- Only output hunks that specify changes with `+` or `-` lines.
- IMPORTANT: MAKE SURE THAT ALL CHANGES START WITH A `+` OR `-`!
- Indentation matters in the diffs!
- When editing a function, method, loop, etc use a hunk to replace the *entire* code block. Delete the entire existing version with `-` lines and then add a new, updated version with `+` lines.
-To move code within a file, use 2 hunks: 1 to delete it from its current location, 1 to insert it in the new location.
- Your output should be ONLY the unified diff, without any explanations or additional text.
""".strip()