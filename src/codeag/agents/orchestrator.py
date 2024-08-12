from typing import Any, Dict

from pydantic import BaseModel

from codeag.agents.agent import Agent, BatchAgent


class Orchestrator(BaseModel, arbitrary_types_allowed=True):
    agent_configs: dict
    agents: Dict[str, Agent] = {}
    retriever: object = None
    storage: object = None

    def model_post_init(self, __context: Any) -> None:
        self.instantiate_agents()

    def instantiate_agents(self):
        for agent_name, agent_config in self.agent_configs.items():
            if "batch_keys" in agent_config:
                self.retrieve_batch_keys(agent_config)
                self.agents[agent_name] = BatchAgent(
                    agent_name=agent_name,
                    retriever=self.retriever,
                    storage=self.storage,
                    **agent_config,
                )
            else:
                self.agents[agent_name] = Agent(
                    agent_name=agent_name,
                    retriever=self.retriever,
                    storage=self.storage,
                    **agent_config,
                )

    def retrieve_batch_keys(self, agent_config: dict):
        if isinstance(agent_config["batch_keys"], str) and agent_config[
            "batch_keys"
        ].startswith("retriever."):
            agent_config["batch_keys"] = getattr(
                self.retriever, agent_config["batch_keys"].split(".")[-1]
            )()

    def run(self, agent_name: str, write_output=True):
        return self.agents[agent_name].run(write_output)

    def preview(self, agent_name: str):
        self.agents[agent_name].preview()

    def read_output(self, agent_name: str):
        self.agents[agent_name].read_output()

    def exist_output(self, agent_name: str):
        self.agents[agent_name].exist_output()

    def write_output(self, agent_name: str, output: Any):
        self.agents[agent_name].write_output(output)


if __name__ == "__main__":
    from codeag.configs.agents_configs import AGENTS_CONFIGS
    from codeag.core.retriever import Retriever
    from codeag.core.storage import Storage

    orchestrator = Orchestrator(
        agent_configs=AGENTS_CONFIGS,
        retriever=Retriever(storage=Storage()),
        storage=Storage(),
    )
    output = orchestrator.run("extract_file_descriptions")
    ...
