import json
from typing import Dict, List, Optional

import tokencost
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
                # if not file_usage:
                #     raise ValueError(f"File {file_path} not found in metadata")
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

    def retrieve_files_data(
        self, files_paths: list[str], metadata: Optional[RepoMetadata] = None
    ) -> Dict[str, List]:
        files_data = {
            "Incl.": [],
            "Path": [],
            "Tokens": [],
        }

        for file_path in files_paths:
            files_data["Path"].append(file_path)

            # Determine if the file should be included based on the current settings
            included = self.should_include_file(file_path, metadata)
            files_data["Incl."].append(True if included else False)

            # Count the number of tokens from the metadata
            tokens = self.count_tokens_from_metadata(file_path, metadata)
            files_data["Tokens"].append(tokens)

        return files_data

    def count_tokens_from_metadata(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> int:
        if not metadata:
            return 0

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            return 0

        # Count tokens for the file header
        file_header = f"# {file_path}"
        total_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")

        if self.use_descriptions:
            if file_usage.is_code:
                details = (
                    metadata.get_code_details(file_path)
                    if not file_usage.testing_related
                    else metadata.get_testing_details(file_path)
                )
                if details:
                    description = details.description
                    if details.external_imports:
                        description += (
                            f"\nExternal imports: {', '.join(details.external_imports)}"
                        )
                    total_tokens += tokencost.count_string_tokens(description, "gpt-4o")
            else:
                description = metadata.get_file_description(file_path)
                total_tokens += tokencost.count_string_tokens(description, "gpt-4o")
        elif self.use_details and file_usage.is_code:
            details = (
                metadata.get_code_details(file_path)
                if not file_usage.testing_related
                else metadata.get_testing_details(file_path)
            )
            if details:
                details_str = self.parse_json_response(details.model_dump_json())
                total_tokens += tokencost.count_string_tokens(details_str, "gpt-4o")
        else:
            # otherwise, return the full files number of tokens
            total_tokens = state.repo.files_tokens[file_path]

        return total_tokens

    def should_include_file(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> bool:
        if self.include_all_files:
            return True

        if not metadata:
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            return False

        return (
            (self.include_code_files and file_usage.is_code)
            or (self.include_testing_files and file_usage.testing_related)
            or (self.include_config_files and file_usage.config_related)
            or (self.include_deployment_files and file_usage.deployment_related)
            or (self.include_security_files and file_usage.security_related)
            or (self.include_ui_files and file_usage.ui_related)
            or (self.include_api_files and file_usage.api_related)
        )


if __name__ == "__main__":
    metadata = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    context = retriever.retrieve(metadata.descriptions.keys(), metadata)
    print(context)
