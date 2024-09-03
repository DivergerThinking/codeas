from typing import Any, Dict

from pydantic import BaseModel

from codeag.agents.agent import Agent, BatchAgent
from codeag.agents.storage import Storage
from codeag.core.llms import LLMClient


class Orchestrator(BaseModel, arbitrary_types_allowed=True):
    agent_configs: dict
    retriever: object = None
    storage: Storage = Storage()
    write_to_storage: bool = True
    agents: Dict[str, Agent] = {}

    def model_post_init(self, __context: Any) -> None:
        self.instantiate_agents()

    def instantiate_agents(self):
        llm_client = LLMClient()  # instantiate single client for all agents
        for agent_name, agent_config in self.agent_configs.items():
            if "batch_keys" in agent_config:
                self.agents[agent_name] = BatchAgent(
                    agent_name=agent_name,
                    retriever=self.retriever,
                    storage=self.storage,
                    llm_client=llm_client,
                    write_to_storage=self.write_to_storage,
                    **agent_config,
                )
            else:
                self.agents[agent_name] = Agent(
                    agent_name=agent_name,
                    retriever=self.retriever,
                    storage=self.storage,
                    llm_client=llm_client,
                    write_to_storage=self.write_to_storage,
                    **agent_config,
                )

    def run(self, agent_name: str):
        return self.agents[agent_name].run()

    def ask(self, agent_name: str, prompt: str, key: str = None):
        if key:
            return self.agents[agent_name].ask(prompt, key)
        else:
            return self.agents[agent_name].ask(prompt)

    def preview(self, agent_name: str):
        return self.agents[agent_name].preview()

    def read_output(self, agent_name: str):
        return self.agents[agent_name].read_output()

    def exist_output(self, agent_name: str):
        return self.agents[agent_name].exist_output()


if __name__ == "__main__":
    from codeag.agents.storage import Storage
    from codeag.configs.agents_configs import AGENTS_CONFIGS
    from codeag.core.retriever import Retriever

    orchestrator = Orchestrator(
        agent_configs=AGENTS_CONFIGS,
        retriever=Retriever(storage=Storage()),
        storage=Storage(),
        write_to_storage=False,
    )
    output = orchestrator.read_output("generate_documentation_sections")
    output = orchestrator.ask(
        "generate_documentation_sections",
        "add some additional details",
        "Getting Started",
    )
    ...
