import json
from typing import List

from pydantic import BaseModel


class FileContent(BaseModel):
    info_only: bool = False
    batch: bool = False

    def retrieve(self, paths: List[str]) -> list:
        if self.batch:
            return self.retrieve_batches(paths)
        else:
            return self.retrieve_single(paths)

    def retrieve_batches(self, paths: List[str]) -> dict:
        batches = {}
        for path in paths:
            batches[path] = self.get_context(path)
        return batches

    def retrieve_single(self, paths: List[str]) -> str:
        context = ""
        for path in paths:
            context += self.get_context(path)
            context += "\n"
        return context

    def get_context(self, path: str) -> str:
        if self.info_only:
            file_content = (
                f"<context-start / file_path = {path} / context_type = file_info >\n"
            )
            file_content += self.read_file_info(path)
            file_content += (
                f"\n<context-end / file_path = {path} / context_type = file_info >\n"
            )
        else:
            file_content = (
                f"<context-start / file_path = {path} / context_type = file_content>\n"
            )
            file_content += self.read_file(path)
            file_content += (
                f"\n<context-end / file_path = {path} / context_type = file_content >\n"
            )
        return file_content

    def read_file(self, path: str) -> str:
        with open(path, "r") as f:
            return f.read()

    def read_file_info(self, path: str) -> str:
        with open("./.codeas/outputs/extract_file_info.json", "r") as f:
            return json.load(f)["response"][path]["content"]


class AgentOutput(BaseModel):
    agent_name: str
    batch: bool = False

    def retrieve(self):
        if self.batch:
            output = self.retrieve_batches()
        else:
            output = self.retrieve_single()
        return self.format_output(output)

    def retrieve_batches(self):
        output = self.read_output()
        if isinstance(output, dict):
            return output
        else:
            raise ValueError(
                f"Context retrieval error: '{self.agent_name}' output is not a dictionary. Set batch = False"
            )

    def retrieve_single(self):
        output = self.read_output()
        if isinstance(output, str):
            return output
        else:
            output_str = ""
            for key, value in output.items():
                output_str += f"{key}:\n{value}\n\n"
            return output_str

    def read_output(self):
        with open(f"./codeas/agent_outputs/{self.agent_name}.json", "r") as f:
            return json.load(f)

    def format_output(self, output: str):
        return f"<context-start / agent_name = {self.agent_name} / context_type = agent_output>\n{output}\n<context-end / agent_name = {self.agent_name} / context_type = agent_output>\n"


class Context(BaseModel):
    file_content: FileContent = None
    agent_output: AgentOutput = None

    def retrieve(self, **kwargs) -> List[str]:
        contexts = self._retrieve_contexts(**kwargs)
        return self._format_contexts(contexts)

    def _retrieve_contexts(self, **kwargs):
        contexts = []
        if self.file_content:
            contexts.append(self.file_content.retrieve(kwargs["paths"]))
        if self.agent_output:
            contexts.append(self.agent_output.retrieve())
        return contexts

    def _format_contexts(self, contexts):
        if any([isinstance(context, dict) for context in contexts]):
            return self._merge_dicts(contexts)
        else:
            return contexts

    def _merge_dicts(self, contexts):
        """
        Merge multiple contexts into a single dictionary.

        This function is designed to handle both dictionary and string contexts,
        combining them in a way that's compatible with the agent's message structure.
        It's implemented to support batch processing of contexts while maintaining
        consistency across different context types.

        The function does the following:
        1. Merges dictionary contexts by matching keys.
        2. Appends string contexts to all keys in the merged dictionary.
        3. Ensures all dictionary contexts have matching keys to prevent inconsistencies.

        """
        merged = {}
        dict_contexts = [ctx for ctx in contexts if isinstance(ctx, dict)]

        if not dict_contexts:
            raise ValueError("No dictionary contexts found to merge")

        keys = set(dict_contexts[0].keys())

        for ctx in dict_contexts[1:]:
            if set(ctx.keys()) != keys:
                raise ValueError("Retrieval error: batches keys don't match")

        for key in keys:
            merged[key] = [ctx[key] for ctx in dict_contexts]

        for ctx in contexts:
            if isinstance(ctx, str):
                for key in merged:
                    merged[key].append(ctx)

        return merged
