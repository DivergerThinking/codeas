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
            # Use the dedicated method to check if file should be included
            if self.should_include_file(file_path, metadata):
                # Extract the logic for generating file content string to a helper method
                file_context_string = self._generate_file_context_string(
                    file_path, i, files_tokens, metadata
                )
                if file_context_string:
                    context.append(file_context_string)

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
            "Incl.\": [],
            "Path": [],
            "Tokens": [],
        }

        for file_path in files_paths:
            files_data["Path"].append(file_path)

            # Determine if the file should be included based on the current settings
            included = self.should_include_file(file_path, metadata)
            files_data["Incl.\"].append(True if included else False)

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

        content_tokens = 0
        # Determine content type and calculate its tokens using helper methods
        if self.use_descriptions:
            content_tokens = self._count_description_tokens(file_path, file_usage, metadata)
        elif self.use_details and file_usage.is_code:
            content_tokens = self._count_details_tokens(file_path, file_usage, metadata)
        else:
            # otherwise, return the full files number of tokens
            content_tokens = state.repo.files_tokens.get(file_path, 0)

        return total_tokens + content_tokens

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

    # Helper method to generate the content string for a file
    def _generate_file_context_string(
        self,
        file_path: str,
        index: int,
        files_tokens: Optional[list[int]],
        metadata: Optional[RepoMetadata]
    ) -> Optional[str]:
        file_header = f"# {file_path}"

        if (self.use_details or self.use_descriptions) and files_tokens and index < len(files_tokens):
            file_header += f" [{files_tokens[index]} tokens]"

        file_usage = None
        if metadata:
             file_usage = metadata.get_file_usage(file_path)

        content_string = None

        if self.use_details and file_usage and file_usage.is_code:
             content_string = self._get_detailed_content_string(file_path, file_usage, metadata)
        elif self.use_descriptions and file_usage:
             content_string = self._get_described_content_string(file_path, file_usage, metadata)
        else:
             # Fallback to full content
             content_string = state.repo.read_file(file_path)

        if content_string is not None:
             return f"{file_header}:\\n{content_string}"
        else:
             # This case implies the specific method called returned None, meaning details/description
             # couldn't be retrieved or didn't exist, and fallback wasn't used for this mode.
             return None


    # Helper method to get description content string
    def _get_described_content_string(self, file_path, file_usage, metadata) -> Optional[str]:
        if not metadata or not file_usage:
            return None
        if file_usage.is_code:
            details = self._get_code_or_testing_details(file_path, file_usage, metadata)
            if details:
                description = details.description
                if details.external_imports:
                     description += f"\\nExternal imports: {', '.join(details.external_imports)}"
                return description
        else:
            # For non-code files, just get the file description
            description = metadata.get_file_description(file_path)
            return description # Assume get_file_description always returns a string

        return None # Should only happen if details for code file not found


    # Helper method to get detailed (JSON parsed) content string
    def _get_detailed_content_string(self, file_path, file_usage, metadata) -> Optional[str]:
        if not metadata or not file_usage or not file_usage.is_code:
            return None # Details are only for code files

        details = self._get_code_or_testing_details(file_path, file_usage, metadata)
        if details:
            return self.parse_json_response(details.model_dump_json())

        return None # Details not found


    # Helper method to get code or testing details based on file type
    def _get_code_or_testing_details(self, file_path, file_usage, metadata):
        if not metadata or not file_usage:
            return None
        if file_usage.is_code:
            return (
                metadata.get_code_details(file_path)
                if not file_usage.testing_related
                else metadata.get_testing_details(file_path)
            )
        return None # Not a code file


    # Helper method to count description tokens
    def _count_description_tokens(self, file_path, file_usage, metadata) -> int:
        content_string = self._get_described_content_string(file_path, file_usage, metadata)
        if content_string is not None:
            # Add newline and header tokens if they were added in retrieve.
            # In count_tokens_from_metadata, header tokens are counted separately.
            # We only need to count the content string itself here.
            return tokencost.count_string_tokens(content_string, "gpt-4o")
        return 0 # Description not found or not applicable


    # Helper method to count details tokens
    def _count_details_tokens(self, file_path, file_usage, metadata) -> int:
         content_string = self._get_detailed_content_string(file_path, file_usage, metadata)
         if content_string is not None:
             # Add newline and header tokens if they were added in retrieve.
             # In count_tokens_from_metadata, header tokens are counted separately.
             # We only need to count the content string itself here.
             return tokencost.count_string_tokens(content_string, "gpt-4o")
         return 0 # Details not found or not applicable


if __name__ == "__main__":
    metadata = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    context = retriever.retrieve(metadata.descriptions.keys(), metadata)
    print(context)