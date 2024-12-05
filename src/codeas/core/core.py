from codeas.core import prompts
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


if __name__ == "__main__":
    vector = state.llm_client.vectorize("testing")
    print(vector)

    from codeas.core.repo import Repo

    repo = Repo(repo_path=".")
    repo.filter_files(include_patterns=["*agent.py"])
    files_contents = repo.get_file_contents()

    # llm_client = LLMClientAzure()
    output = generate_file_infos(files_contents)
    file_infos = output.response
    embeddings = vectorize_files_infos(file_infos)
    print(file_infos)
