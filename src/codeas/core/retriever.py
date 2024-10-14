import json
from typing import Optional

from pydantic import BaseModel

from codeas.core.metadata import RepoMetadata
from codeas.core.state import state


class ContextRetriever(BaseModel):
    include_all_files: bool = False
    include_code_files: bool = False
    include_testing_files: bool = False
    include_config_files: bool = False
    include_deployment_files: bool = False
    include_security_files: bool = False
    include_ui_files: bool = False
    include_api_files: bool = False
    use_descriptions: bool = False
    use_relationships: bool = False
    use_details: bool = False

    def retrieve(
        self,
        files_paths: list[str],
        files_tokens: Optional[list[int]] = None,
        metadata: Optional[RepoMetadata] = None,
    ) -> str:
        context = []
        for i, file_path in enumerate(files_paths):
            if metadata:
                file_usage = metadata.get_file_usage(file_path)
                if not file_usage:
                    raise ValueError(f"File {file_path} not found in metadata")
            else:
                file_usage = None

            if self.include_all_files or (
                (self.include_code_files and file_usage.is_code)
                or (self.include_testing_files and file_usage.testing_related)
                or (self.include_config_files and file_usage.config_related)
                or (self.include_deployment_files and file_usage.deployment_related)
                or (self.include_security_files and file_usage.security_related)
                or (self.include_ui_files and file_usage.ui_related)
                or (self.include_api_files and file_usage.api_related)
            ):
                file_header = f"# {file_path}"
                if (self.use_details or self.use_descriptions) and files_tokens:
                    file_header += f" [{files_tokens[i]} tokens]"

                if self.use_details and file_usage.is_code:
                    if file_usage.testing_related:
                        details = metadata.get_testing_details(file_path)
                    else:
                        details = metadata.get_code_details(file_path)
                    if details:
                        context.append(
                            f"{file_header}:\n{self.parse_json_response(details.model_dump_json())}"
                        )
                elif self.use_descriptions:
                    if file_usage.is_code:
                        details = (
                            metadata.get_code_details(file_path)
                            if not file_usage.testing_related
                            else metadata.get_testing_details(file_path)
                        )
                        if details:
                            description = f"{file_header}:\n{details.description}"
                            if details.external_imports:
                                description += f"\nExternal imports: {', '.join(details.external_imports)}"
                            context.append(description)
                    else:
                        description = metadata.get_file_description(file_path)
                        context.append(f"{file_header}:\n{description}")
                elif self.use_relationships:
                    if file_usage.is_code:
                        details = (
                            metadata.get_code_details(file_path)
                            if not file_usage.testing_related
                            else metadata.get_testing_details(file_path)
                        )
                        if details:
                            description = f"{file_header}:\n{details.description}"
                            if details.internal_imports:
                                description += f"\nInternal imports: {', '.join(details.internal_imports)}"
                            if details.functionalities:
                                description += f"\nFunctionalities: {', '.join(details.functionalities)}"
                            context.append(description)
                    else:
                        description = metadata.get_file_description(file_path)
                        context.append(f"{file_header}:\n{description}")
                else:
                    content = state.repo.read_file(file_path)
                    context.append(f"{file_header}:\n{content}")

        return "\n\n".join(context)

    def parse_json_response(self, json_str: str) -> str:
        data = json.loads(json_str)
        result = []
        for key, value in data.items():
            if value:
                result.append(f"\n{key.replace('_', ' ').title()}:")
                if isinstance(value, list):
                    result.extend(f"- {item}" for item in value)
                else:
                    result.append(str(value))

        return "\n".join(result)


if __name__ == "__main__":
    metadata = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    context = retriever.retrieve(metadata.descriptions.keys(), metadata)
    print(context)
