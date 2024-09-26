from codeas.core.agent import Agent
from codeas.core.retriever import ContextRetriever
from codeas.ui.state import state

prompt_define_deployment = """
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


def define_deployment(preview: bool = False) -> str:
    retriever = ContextRetriever(include_code_files=True, use_descriptions=True)
    context = retriever.retrieve(
        state.repo.included_files_paths,
        state.repo.included_files_tokens,
        state.repo_metadata,
    )

    agent = Agent(
        instructions=prompt_define_deployment,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=context)
    else:
        return agent.run(state.llm_client, context=context)


prompt_generate_deployment = """
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


def generate_deployment(deployment_strategy: str, preview: bool = False) -> str:
    retriever = ContextRetriever(include_code_files=True, use_descriptions=True)
    context = [
        retriever.retrieve(
            state.repo.included_files_paths,
            state.repo.included_files_tokens,
            state.repo_metadata,
        )
    ]
    context.append(deployment_strategy)
    agent = Agent(
        instructions=prompt_generate_deployment,
        model="gpt-4o",
    )
    if preview:
        return agent.preview(context=context)
    else:
        return agent.run(state.llm_client, context=context)
