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
            file_usage = metadata.get_file_usage(file_path) if metadata else None

            if self.should_include_file(file_path, metadata):
                file_content_str = self._get_file_content_string(
                    file_path, file_usage, files_tokens, i, metadata
                )
                if file_content_str:
                    context.append(file_content_str)

        return "\n\n".join(context)

    def _get_file_content_string(
        self,
        file_path: str,
        file_usage: Optional[any], # Replace 'any' with actual type if known
        files_tokens: Optional[list[int]],
        index: int,
        metadata: Optional[RepoMetadata],
    ) -> Optional[str]:
        file_header = f"# {file_path}"
        if (self.use_details or self.use_descriptions) and files_tokens:
            file_header += f" [{files_tokens[index]} tokens]"

        if self.use_details and file_usage and file_usage.is_code and metadata:
            details = (
                metadata.get_testing_details(file_path)
                if file_usage.testing_related
                else metadata.get_code_details(file_path)
            )
            if details:
                return f"{file_header}:\n{self.parse_json_response(details.model_dump_json())}"
        elif self.use_descriptions and file_usage and metadata:
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
                    return description
            else:
                description = metadata.get_file_description(file_path)
                return f"{file_header}:\n{description}"
        else:
            # otherwise, return the full files content
            content = state.repo.read_file(file_path)
            return f"{file_header}:\n{content}"
        return None # Return None if no content type matched/data missing


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

    def retrieve_files_data(\
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
            files_data["Incl."].append(included)

            # Count the number of tokens from the metadata
            tokens = self.count_tokens_from_metadata(file_path, metadata)
            files_data["Tokens"].append(tokens)

        return files_data

    def count_tokens_from_metadata(\
        self, file_path: str, metadata: Optional[RepoMetadata]\
    ) -> int:
        if not metadata:
            return 0

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            return 0

        # Count tokens for the file header
        file_header = f"# {file_path}"
        header_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")

        content_tokens = self._count_file_content_tokens(file_path, metadata, file_usage)

        return header_tokens + content_tokens

    def _count_file_content_tokens(
        self,
        file_path: str,
        metadata: RepoMetadata,
        file_usage: any # Replace 'any' with actual type if known
    ) -> int:
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
                    return tokencost.count_string_tokens(description, "gpt-4o")
            else:
                description = metadata.get_file_description(file_path)
                return tokencost.count_string_tokens(description, "gpt-4o")
        elif self.use_details and file_usage.is_code:
            details = (
                metadata.get_code_details(file_path)
                if not file_usage.testing_related
                else metadata.get_testing_details(file_path)
            )
            if details:
                details_str = self.parse_json_response(details.model_dump_json())
                return tokencost.count_string_tokens(details_str, "gpt-4o")
        else:
            # otherwise, return the full files number of tokens
            # Assuming state.repo.files_tokens is available and correct
            return state.repo.files_tokens.get(file_path, 0)

        return 0 # Default return if none of the above branches hit

    def should_include_file(\
        self, file_path: str, metadata: Optional[RepoMetadata]\
    ) -> bool:
        if self.include_all_files:
            return True

        if not metadata:
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            return False

        return (\
            (self.include_code_files and file_usage.is_code)\
            or (self.include_testing_files and file_usage.testing_related)\
            or (self.include_config_files and file_usage.config_related)\
            or (self.include_deployment_files and file_usage.deployment_related)\
            or (self.include_security_files and file_usage.security_related)\
            or (self.include_ui_files and file_usage.ui_related)\
            or (self.include_api_files and file_usage.api_related)\
        )


if __name__ == "__main__":
    # This block requires the actual RepoMetadata and state objects to run
    # Skipping execution as required by instructions
    pass