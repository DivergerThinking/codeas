from pydantic import BaseModel


class Context(BaseModel):
    batch: bool = False

    def retrieve(self, files_content: dict = None, agents_output: dict = None):
        if self.batch:
            return self.retrieve_batches(files_content, agents_output)
        else:
            return self.retrieve_single(files_content, agents_output)

    def retrieve_batches(
        self, files_content: dict = None, agents_output: dict = None
    ) -> dict:
        batch_context = {}

        if files_content:
            for path, context in files_content.items():
                batch_context[path] = [self.format_files_context(path, context)]

        if agents_output:
            for agent_name, context in agents_output.items():
                if isinstance(context, dict):
                    for path, ctx in context.items():
                        if path not in batch_context:
                            batch_context[path] = []
                        batch_context[path].append(
                            self.format_agent_path_context(agent_name, path, ctx)
                        )
                elif isinstance(context, str):
                    if files_content:
                        for path in batch_context:
                            batch_context[path].append(
                                self.format_agent_context(agent_name, context)
                            )
                    else:
                        raise ValueError(
                            "Batch cannot be retrieved without files_content or batch agents output"
                        )

        return batch_context

    def retrieve_single(self, files_content: dict = None, agents_output: dict = None):
        contexts = []
        if files_content:
            formatted_files_content = ""
            for path, context in files_content.items():
                formatted_files_content += self.format_files_context(path, context)
            contexts.append(formatted_files_content)
        if agents_output:
            formatted_agents_output = ""
            for agent_name, context in agents_output.items():
                if isinstance(context, dict):
                    for path, ctx in context.items():
                        formatted_agents_output += self.format_agent_path_context(
                            agent_name, path, ctx
                        )
                elif isinstance(context, str):
                    formatted_agents_output += self.format_agent_context(
                        agent_name, context
                    )
            contexts.append(formatted_agents_output)
        return contexts

    def format_files_context(self, path, context):
        file_context = f"<context path = {path}>\n"
        file_context += context
        file_context += "\n</context>\n"
        return file_context

    def format_agent_context(self, agent_name, context):
        agent_context = f"<context agent_name = {agent_name}>\n"
        agent_context += context
        agent_context += "\n</context>\n"
        return agent_context

    def format_agent_path_context(self, agent_name, path, context):
        agent_path_context = f"<context agent_name = {agent_name} path = {path}>\n"
        agent_path_context += context
        agent_path_context += "\n</context>\n"
        return agent_path_context
