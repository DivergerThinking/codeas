from typing import Literal

from pydantic import BaseModel

from codeas.core import prompts, tools
from codeas.core.agent import Agent
from codeas.core.state import state


def generate_file_infos(files_contents: dict, model: str = "gpt-4o-mini"):
    messages = {
        path: [
            {
                "role": "user",
                "content": prompts.EXTRACT_FILE_INFO_PROMPT.format(
                    file_content=content
                ),
            }
        ]
        for path, content in files_contents.items()
    }
    agent = Agent(model=model)
    return agent.run(messages=messages, llm_client=state.llm_client)


def vectorize_files_infos(file_infos: dict):
    return state.llm_client.vectorize(file_infos)


def retrieve_relevant_context(
    query: str,
    n_results: int = 10,
    rerank: bool = True,
    context_type: Literal["content", "description"] = "content",
):
    results = query_repo(query, n_results)
    file_paths = results["ids"][0]
    if rerank:
        file_paths = rerank_results(query, file_paths)
    context = retrieve_context(file_paths, context_type)
    return context


def query_repo(query: str, n_results: int = 10):
    query_embeddings = state.llm_client.vectorize(query)
    return state.storage.query_files_embeddings(
        state.repo_path, query_embeddings, n_results
    )


class RerankResultsResponse(BaseModel):
    file_paths: list[str]


def rerank_results(query: str, file_paths: list):
    file_infos = state.storage.fetch_files_by_paths(state.repo_path, file_paths)
    formatted_file_infos = format_file_infos(file_infos)
    messages = [
        {
            "role": "user",
            "content": prompts.RERANK_RESULTS_PROMPT.format(
                query=query, file_infos=formatted_file_infos
            ),
        }
    ]
    response = state.llm_client.run(
        messages=messages, model="gpt-4o-mini", response_format=RerankResultsResponse
    )
    return response.choices[0].message.parsed.file_paths


def format_file_infos(file_infos: list):
    txt = ""
    for file_info in file_infos:
        txt += f"# {file_info['filepath']}\n{file_info['infos']}\n\n"
    return txt


def retrieve_context(file_paths: list, context_type: Literal["content", "description"]):
    context = ""
    if context_type == "content":
        for file_path in file_paths:
            context += f"# {file_path}\n"
            context += read_file_content(file_path)
    elif context_type == "description":
        file_infos = state.storage.fetch_files_by_paths(state.repo_path, file_paths)
        for file_info in file_infos:
            context += f"# {file_info['filepath']}\n"
            context += file_info["infos"]
    return context


def read_file_content(file_path: str):
    with open(file_path, "r") as file:
        return file.read()


def run_repo_agent(messages: list):
    for token in state.llm_client.stream(
        messages=messages,
        model="gpt-4o",
        tools=[tools.TOOL_RETRIEVE_CONTEXT],
    ):
        yield token


if __name__ == "__main__":
    response = retrieve_relevant_context("function executes LLM requests")
    print(response)
