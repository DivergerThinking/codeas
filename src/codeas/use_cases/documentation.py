from codeas.configs import prompts
from codeas.core.agent import Agent
from codeas.core.llm import LLMClient
from codeas.core.metadata import RepoMetadata
from codeas.core.repo import Repo
from codeas.core.retriever import ContextRetriever
from codeas.core.usage_tracker import usage_tracker

DOCS_MODEL = "gpt-4o"
SECTION_CONFIG = {
    "project_overview": {
        "context": {"include_all_files": True, "use_descriptions": True},
        "prompt": prompts.generate_docs_project_overview,
        "model": DOCS_MODEL,
    },
    "setup_and_development": {
        "context": {"include_config_files": True, "include_deployment_files": True},
        "prompt": prompts.generate_docs_setup_and_development,
        "model": DOCS_MODEL,
    },
    "architecture": {
        "context": {"include_code_files": True, "use_details": True},
        "prompt": prompts.generate_docs_architecture,
        "model": DOCS_MODEL,
    },
    "ui": {
        "context": {"include_ui_files": True, "use_details": True},
        "prompt": prompts.generate_docs_ui,
        "model": DOCS_MODEL,
    },
    "db": {
        "context": {"include_db_files": True, "use_details": True},
        "prompt": prompts.generate_docs_db,
        "model": DOCS_MODEL,
    },
    "api": {
        "context": {"include_api_files": True, "use_details": True},
        "prompt": prompts.generate_docs_api,
        "model": DOCS_MODEL,
    },
    "testing": {
        "context": {"include_testing_files": True, "use_details": True},
        "prompt": prompts.generate_docs_testing,
        "model": DOCS_MODEL,
    },
    "deployment": {
        "context": {"include_deployment_files": True, "use_details": True},
        "prompt": prompts.generate_docs_deployment,
        "model": DOCS_MODEL,
    },
    "security": {
        "context": {"include_security_files": True, "use_details": True},
        "prompt": prompts.generate_docs_security,
        "model": DOCS_MODEL,
    },
}


def generate_docs_section(
    llm_client: LLMClient,
    section: str,
    repo: Repo,
    metadata: RepoMetadata,
    preview: bool = False,
) -> str:
    config = SECTION_CONFIG.get(section)
    if not config:
        return f"Error: Section '{section}' not found in configuration."

    retriever = ContextRetriever(**config["context"])
    context = retriever.retrieve(
        repo.included_files_paths, repo.included_files_tokens, metadata
    )
    agent = Agent(instructions=config["prompt"], model=config["model"])
    if preview:
        return agent.preview(context=context)
    else:
        result = agent.run(llm_client, context=context)
        usage_tracker.record_usage(f"generate_{section}", result.cost["total_cost"])
        return result


if __name__ == "__main__":
    from codeas.core.metadata import RepoMetadata
    from codeas.core.repo import Repo

    llm_client = LLMClient()
    repo = Repo(repo_path=".")
    metadata = RepoMetadata.load_metadata(repo_path=".")
    docs = generate_docs_section(llm_client, "project_overview", repo, metadata)
    print(docs)
