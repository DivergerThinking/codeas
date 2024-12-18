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


def run_repo_agent(messages: list):
    for token in state.llm_client.stream(
        messages=messages,
        model="gpt-4o",
        tools=[tools.TOOL_RETRIEVE_CONTEXT],
    ):
        yield token
