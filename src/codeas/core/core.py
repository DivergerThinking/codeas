import json
import math
from typing import Literal

from pydantic import BaseModel
from tokencost import count_string_tokens

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


def run_retrieval_agent(messages: list):
    for token in state.llm_client.stream(
        messages=messages,
        model="gpt-4o",
        tools=[tools.TOOL_RETRIEVE_RELEVANT_CONTEXT],
    ):
        yield token


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

    class RerankResultsResponse(BaseModel):
        file_paths: list[str]

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


def handle_tool_calls(tool_calls: list):
    tool_calls_messages = []
    for tool_call in tool_calls:
        function_name = tool_call["function"]["name"]
        tool_call_arguments = json.loads(tool_call["function"]["arguments"])
        tool_calls_messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": call_function(function_name, tool_call_arguments),
            }
        )
    return tool_calls_messages


def call_function(function_name: str, arguments: dict):
    return eval(f"{function_name}(**{arguments})")


def run_documentation_agent(messages: list):
    for token in state.llm_client.stream(
        messages=messages,
        model="gpt-4o",
        tools=[
            tools.TOOL_DEFINE_DOCUMENTATION_STRUCTURE,
            tools.TOOL_GENERATE_DOCUMENTATION,
        ],
    ):
        yield token


class SubSection(BaseModel):
    title: str
    query: str
    context_type: Literal["content", "description"] = "description"


class Section(BaseModel):
    title: str
    sub_sections: list[SubSection]


class DocumentationStructureResponse(BaseModel):
    sections: list[Section]


def define_documentation_structure():
    project_info = get_project_info()
    messages = [
        {
            "role": "user",
            "content": prompts.DEFINE_DOCUMENTATION_STRUCTURE_PROMPT.format(
                project_info=project_info
            ),
        }
    ]
    response = state.llm_client.run(
        messages=messages,
        model="gpt-4o-mini",
        response_format=DocumentationStructureResponse,
    )
    return response.choices[0].message.parsed


def get_project_info():
    file_paths = state.repo.get_file_paths()
    file_infos = state.storage.fetch_files_by_paths(state.repo_path, file_paths)
    file_infos_chunks = chunk_context(file_infos)
    if len(file_infos_chunks) > 1:
        summaries = summarize_file_infos(
            file_infos_chunks,
            "define relevant sections for some technical documentation covering this project",
        )
        return format_file_summaries(summaries)
    else:
        return format_file_infos(file_infos_chunks[0])


def format_file_summaries(summaries: dict):
    txt = ""
    for iter_num, summary in summaries.items():
        txt += f"# Summary of project files [part {iter_num+1}]:\n{summary}\n\n"
    return txt


def count_tokens(text: str):
    return count_string_tokens(text, model="gpt-4o-mini")


def chunk_context(file_infos: list, threshold: int = 10000):
    file_infos_txt = format_file_infos(file_infos)
    n_tokens = count_tokens(file_infos_txt)
    avg_tokens_per_file = n_tokens / len(file_infos)
    n_files_per_chunk = math.floor(threshold / avg_tokens_per_file)
    chunks = {
        iter_num: file_infos[index : index + n_files_per_chunk]
        for iter_num, index in enumerate(range(0, len(file_infos), n_files_per_chunk))
    }
    return chunks


def summarize_file_infos(file_infos_chunks: dict, task: str):
    messages = {
        key: [
            {
                "role": "user",
                "content": prompts.SUMMARIZE_FILE_INFOS_PROMPT.format(
                    file_infos=format_file_infos(file_infos_chunk), task=task
                ),
            }
        ]
        for key, file_infos_chunk in file_infos_chunks.items()
    }
    return state.llm_client.run(messages=messages, model="gpt-4o-mini")


def generate_documentation(documentation_structure: DocumentationStructureResponse):
    subsections_content = generate_subsections_content(documentation_structure)
    documentation = ""
    for section in documentation_structure.sections:
        documentation += f"# {section.title}\n\n"
        for subsection in section.sub_sections:
            documentation += f"## {subsection.title}\n\n"
            documentation += subsections_content[subsection.title]
    return documentation


def generate_subsections_content(
    documentation_structure: DocumentationStructureResponse,
):
    subsections_context = get_subsections_context(documentation_structure)
    messages = {
        subsection_title: [
            {
                "role": "user",
                "content": prompts.GENERATE_SUBSECTION_CONTENT_PROMPT.format(
                    subsection_title=subsection_title, context=context
                ),
            },
            {
                "role": "assistant",
                "content": f"## {subsection_title}\n\n",
            },
        ]
        for subsection_title, context in subsections_context.items()
    }
    return state.llm_client.run(messages=messages, model="gpt-4o-mini")


def get_subsections_context(documentation_structure: DocumentationStructureResponse):
    return {
        subsection.title: retrieve_relevant_context(
            subsection.query, context_type=subsection.context_type
        )
        for section in documentation_structure.sections
        for subsection in section.sub_sections
    }


if __name__ == "__main__":
    response = generate_documentation(define_documentation_structure())
    print(response)
