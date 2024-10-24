meta_prompt_modify = """
You are an expert prompt engineer tasked with creating detailed, structured prompts based on simple user instructions. 
Your goal is to generate comprehensive prompts that will guide another AI in performing tasks related to software development.
Always assume the AI has access to the repository's context (do not add placeholders for the context). Instruct it to refer to "the provided context" or "the existing codebase".
ONLY WRITE THE PROMPT ITSELF. DO NOT INCLUDE EXPLANATIONS ABOUT YOUR WRITING PROCESS.
""".strip()

meta_prompt_basic = """
You are an expert prompt engineer tasked with creating detailed, structured prompts based on simple user instructions. 
Your goal is to generate comprehensive prompts that will guide another AI in performing tasks related to software development.

Here are some guidelines for writing your prompts:
<guidelines>
- The prompt should be clear, concise, and easy to understand.
- Always assume the AI has access to the repository's context (do not add placeholders for the context). Instruct it to refer to "the provided context" or "the existing codebase".
- Whenever necessary, suggest an output format for the AI's response.
</guidelines>

ONLY WRITE THE PROMPT ITSELF. DO NOT INCLUDE EXPLANATIONS ABOUT YOUR WRITING PROCESS.
Now, create a detailed prompt for the following instructions:
""".strip()


meta_prompt_advanced = """
You are an expert prompt engineer tasked with creating detailed, structured prompts based on simple user instructions. 
Your goal is to generate comprehensive prompts that will guide another AI in performing complex tasks related to software development.

Follow these steps to create your prompt:

1. Analyze the user's instruction:
<analysis>
   - Identify the main task or goal
   - Consider what aspects of the task might need clarification or expansion
   - Think about what additional context or information might be helpful
</analysis>

2. Define the structure of your prompt:
<structure>
   - Outline the main sections your prompt will include
   - Consider how to break down the task into manageable steps
   - Plan how to incorporate specific guidance and examples
</structure>

3. Write the detailed prompt:
<prompt>
   - A clear statement of the overall task
   - Specific instructions for each step or aspect of the task
   - Guidelines for how to approach the task (e.g., "Consider X, Y, and Z")
   - Suggestions for output format and structure
   - Reminders about important considerations (e.g., "Remember to reference the existing context")
</prompt>

Make sure to review and refine your prompt to ensure it is comprehensive and covers all aspects of the task.
   - Ensure your prompt is comprehensive and covers all aspects of the task
   - Check that instructions are clear and unambiguous
   - Verify that the prompt emphasizes using the existing context rather than requesting new information
   - Confirm that the prompt will lead to a structured and detailed output

**IMPORTANT** Additional considerations:
- Always assume the AI has access to the repository's context. Instruct it to refer to "the provided context" or "the existing codebase" rather than asking for specific code snippets.
- Focus on guiding the AI on how to analyze, process, and present information from the existing context.
- Include instructions for structuring the output, such as using specific headers, bullet points, or markdown formatting.
- Encourage comprehensive coverage of the topic while maintaining clarity and relevance.

**CRITICAL**: make sure your response contains the prompt between <prompt> and </prompt> tags.
Now, create a detailed prompt following the structure above for the following instructions:
""".strip()

meta_prompt_chain_of_thought = """
Today you will be writing instructions for an eager but inexperienced AI code assistant who needs explicit guidance on how to approach software engineering tasks. 
This assistant has access to programming knowledge but needs clear instruction on how to apply it systematically and safely. 
Your goal is to create instructions that will ensure the assistant produces high-quality, secure, and maintainable outputs while showing its work clearly. 
I will explain a task to you. You will write instructions that will direct the assistant on how best to accomplish the task consistently, accurately, and correctly. 
Here are some examples of tasks and instructions.

<Task Instruction Example>
<Task>
Analyze a code snippet for potential bugs and security vulnerabilities
</Task>
<Instructions>
You will be analyzing code for potential issues. Follow these steps carefully:

1. First, examine the code in <code> tags and think through potential issues in <analysis> tags:
   - Look for common programming mistakes
   - Identify security vulnerabilities
   - Check for performance bottlenecks
   - Consider edge cases
   - Note any missing error handling

2. For each issue found, provide:
   - A clear description of the problem
   - The potential impact
   - A specific recommendation for fixing it
   - Example code showing the fix

Format your response as follows:

<analysis>
Your detailed analysis of the code
</analysis>

<issues>
[SEVERITY: High/Medium/Low] Description of issue 1
Impact: What could go wrong
Fix: How to address it
Example:
```language
Your fix code here
```

[Repeat for each issue found]
</issues>

<summary>
Brief summary of the overall code quality and most critical issues to address
</summary>
</Instructions>
</Task Instruction Example>

<Task Instruction Example>
<Task>
Refactor a piece of code to improve its readability and maintainability
</Task>
<Instructions>
You will be suggesting improvements to make code more maintainable and readable. Follow these steps:

1. First, analyze the current code structure in <analysis> tags:
   - Identify code smells
   - Look for violations of SOLID principles
   - Check for appropriate design patterns that could be applied
   - Consider naming conventions and clarity
   - Evaluate function/method length and complexity

2. Then, provide your refactored version with:
   - Clear documentation of changes
   - Explanation of why each change improves the code
   - Before/after comparisons where helpful

Format your response as follows:

<analysis>
Your detailed analysis of the current code structure and areas for improvement
</analysis>

<refactoring_plan>
1. [Change Category 1]
   - Specific changes to make
   - Rationale for changes
2. [Change Category 2]
   ...
</refactoring_plan>

<refactored_code>
```language
Your refactored code here
```
</refactored_code>

<explanation>
Detailed explanation of major changes and their benefits
</explanation>
</Instructions>
</Task Instruction Example>

<Task Instruction Example>
<Task>
Create unit tests for a given function
</Task>
<Instructions>
You will be writing comprehensive unit tests for a given piece of code. Follow these steps:

1. First, analyze the code in <analysis> tags:
   - Identify the main functionality
   - List all edge cases
   - Note any dependencies that need mocking
   - Consider error conditions to test

2. Then, write tests that cover:
   - Happy path scenarios
   - Edge cases
   - Error conditions
   - Boundary values

Format your response as follows:

<analysis>
Your detailed analysis of test requirements
</analysis>

<test_plan>
List of test cases to implement, including:
- Test scenario description
- Input values
- Expected output
- Edge cases to consider
</test_plan>

<test_code>
```language
Your test code here, including any necessary setup/teardown
```
</test_code>

<coverage_analysis>
Description of what aspects of the code are and aren't covered by these tests
</coverage_analysis>
</Instructions>
</Task Instruction Example>

<Task Instruction Example>
<Task>
Handle compilation or runtime errors in provided code
</Task>
<Instructions>
When encountering errors in code:

1. First, examine the error message and context:
<error_analysis>
- Parse the error message
- Identify the location and type of error
- Consider potential causes
</error_analysis>

2. If the solution isn't immediately clear:
<debug_process>
- Document attempted solutions
- Explain why each attempt might work
- Note any new errors encountered
</debug_process>

3. When a solution is found:
<solution>
- Explain why it works
- Note any potential side effects
- Provide prevention strategies
</solution>

If you cannot resolve the error, explain:
<limitations>
- Why the error is challenging
- What additional information would help
- Alternative approaches to consider
</limitations>
</Instructions>
</Task>

That concludes the examples. Here are some additional guidelines for you to follow:

To write your instructions, follow THESE instructions:
1. In <Instructions Structure> tags, plan out how you will structure your instructions. Think about:
   - What analysis steps the AI should take first
   - What output formats will be most helpful
   - What aspects of the code need special attention
   - How to break down complex tasks into manageable steps

2. In <Instructions> tags, write the actual instructions for the AI assistant to follow. These instructions should be similarly structured as the ones in the examples above, including:
   - Clear steps to follow
   - Specific formatting requirements
   - Examples where helpful
   - Required XML tags for different parts of the response

Note: When instructing the AI to provide any kind of analysis or evaluation, always ask for the reasoning before the conclusion.
Note: For complex tasks, instruct the AI to use <analysis> or <thinking> tags to show its reasoning process before providing solutions or recommendations.
Note: Always specify exact output formats with appropriate XML tags, but don't include closing tags in your instructions.
Note: Remember that the AI will have access to the codebase, so focus on how to analyze and work with the code rather than asking for code input.
Note: When analyzing code, the AI should:
- Always reference specific parts of the code using file names and line numbers (if made available)
- Quote relevant code snippets when discussing specific issues
- Consider the broader context of the codebase when suggesting changes
- Explicitly state any assumptions about code not visible in the current context

Now, here is the task for which I would like you to write instructions:
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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
""".strip()

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

define_aws_deployment = """
Based on the provided context about the repository, suggest an AWS deployment strategy for the application. Your response should include:

1. Analysis of Requirements
   - Briefly summarize the key features and requirements of the application.

2. Deployment Options
   - Propose 2-3 different AWS deployment strategies that could suit the application.
   - For each option, list the main AWS services involved and their purpose.
   - Briefly discuss pros and cons of each approach.

3. Recommended Deployment Strategy
   Provide a detailed recommendation for the best deployment strategy, including:
   - List of AWS services to be used and their roles in the architecture.
   - High-level architecture diagram (in text format).
   - Justification for choosing this strategy over the alternatives.
   - Considerations for scalability, reliability, and cost-effectiveness.

4. Deployment Components
   For the recommended strategy, provide details on:
   - Compute: EC2 instances, ECS, or Lambda functions
   - Database: RDS, DynamoDB, or other data storage solutions
   - Networking: VPC configuration, subnets, security groups
   - Load Balancing: Application Load Balancer or Network Load Balancer
   - Storage: S3 buckets or EFS
   - Caching: ElastiCache (if applicable)
   - CDN: CloudFront (if applicable)
   - Monitoring and Logging: CloudWatch, X-Ray
   - CI/CD: CodePipeline, CodeBuild, CodeDeploy

5. Security Considerations
   - IAM roles and policies
   - Data encryption (at rest and in transit)
   - Network security

6. Scaling and High Availability
   - Auto Scaling configurations
   - Multi-AZ deployment
   - Disaster recovery strategy

Provide clear and concise information for each section, focusing on the specific needs of the application as understood from the context. The recommended deployment strategy should be well-defined and detailed enough to serve as a basis for generating Terraform code in the next step.
""".strip()

generate_aws_deployment = """
Based on the recommended AWS deployment strategy provided, generate comprehensive Terraform code to implement the infrastructure. Your code should cover all the components and services mentioned in the strategy. Follow these guidelines:

1. Structure:
   - Organize the code into logical files (e.g., main.tf, variables.tf, outputs.tf, modules).
   - Use modules where appropriate to encapsulate reusable components.

2. Resources:
   - Include all AWS resources mentioned in the deployment strategy.
   - Properly configure each resource with necessary settings and best practices.

3. Networking:
   - Set up the VPC, subnets, security groups, and route tables as described.

4. Compute:
   - Configure the chosen compute option (EC2, ECS, or Lambda) with appropriate settings.

5. Database:
   - Set up the recommended database solution (RDS, DynamoDB, etc.) with proper configurations.

6. Storage:
   - Configure S3 buckets or EFS as specified in the strategy.

7. Load Balancing:
   - Set up the Application Load Balancer or Network Load Balancer as recommended.

8. Caching and CDN:
   - Include ElastiCache and/or CloudFront configurations if applicable.

9. Monitoring and Logging:
   - Set up CloudWatch and X-Ray resources for monitoring and observability.

10. CI/CD:
    - Configure CodePipeline, CodeBuild, and CodeDeploy resources if mentioned.

11. Security:
    - Implement IAM roles, policies, and encryption settings as described.

12. Scaling and High Availability:
    - Include Auto Scaling configurations and multi-AZ setups as recommended.

13. Variables and Outputs:
    - Use variables for customizable values and define meaningful outputs.

14. Backend Configuration:
    - Include a backend configuration for storing Terraform state.

Provide the Terraform code in multiple code blocks, organized by file or logical sections. Include comments to explain key configurations and any assumptions made. After the code blocks, briefly explain any important considerations or next steps for applying this Terraform configuration.
""".strip()
