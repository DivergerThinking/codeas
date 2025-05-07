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
            # Retrieve file_usage once per file if metadata is available
            file_usage = metadata.get_file_usage(file_path) if metadata else None

            # Use the existing should_include_file helper
            if self.should_include_file(file_path, metadata):
                # Extract the logic for formatting file content into a helper method
                file_string = self._format_file_for_context(file_path, i, files_tokens, metadata, file_usage)
                if file_string is not None:
                     context.append(file_string)

        return "\n\n".join(context)

    def _format_file_for_context(
        self,
        file_path: str,
        index: int,
        files_tokens: Optional[list[int]],
        metadata: Optional[RepoMetadata],
        file_usage # Type depends on RepoMetadata return type for get_file_usage
    ) -> Optional[str]:
        """Helper to format the content string for a single file based on options."""
        file_header = f"# {file_path}"
        # Add token count to header if requested and available
        if (self.use_details or self.use_descriptions) and files_tokens and index < len(files_tokens):
            file_header += f" [{files_tokens[index]} tokens]"

        content = None

        # Only attempt to get details/descriptions if metadata and file_usage are available
        if metadata and file_usage:
            if self.use_details and file_usage.is_code:
                details = metadata.get_testing_details(file_path) if file_usage.testing_related else metadata.get_code_details(file_path)
                if details:
                    content = self.parse_json_response(details.model_dump_json())
            elif self.use_descriptions:
                 if file_usage.is_code:
                      details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
                      if details:
                           description = details.description
                           if details.external_imports:
                                description += f"\nExternal imports: {', '.join(details.external_imports)}"
                           content = description
                 else: # Not code, get file description
                      description = metadata.get_file_description(file_path)
                      content = description # Can still be None if description not found

        # Fallback to reading full content if no specific formatted content was generated
        if content is None:
             try:
                content = state.repo.read_file(file_path)
             except Exception: # Catching generic Exception is broad, but matches original intent of fallback
                content = "" # Handle potential read errors gracefully

        # Combine header and content. Return None if content somehow ends up None (unlikely after fallback)
        if content is not None:
            return f"{file_header}:\n{content}"
        return None


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
        self, files_paths: list[str], metadata: Optional[RepoMetadata] = None\
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
            # Original logic: return 0 if no metadata is provided.
            # This matches the behavior before refactoring and avoids regression.
            return 0

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
             # If file not found in metadata, original returns 0. Keep this.
             # should_include_file handles the filtering based on this.
            return 0

        # Count tokens for the file header
        file_header = f"# {file_path}"
        total_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")

        # Extract the logic for calculating content tokens into a helper method
        content_tokens = self._calculate_content_tokens(file_path, file_usage, metadata)
        total_tokens += content_tokens

        return total_tokens

    def _calculate_content_tokens(
        self, file_path: str, file_usage, metadata: RepoMetadata # Assume metadata and file_usage are not None
    ) -> int:
        """Helper to calculate token count for the content part of a file based on options."""
        content_tokens = 0

        if self.use_descriptions:
            # Original logic for descriptions token count
            details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
            if details:
                description = details.description
                if details.external_imports:
                    description += f"\nExternal imports: {', '.join(details.external_imports)}"
                content_tokens = tokencost.count_string_tokens(description, "gpt-4o")
            elif not file_usage.is_code:
                 # Not code, but include_descriptions is True. Get file description tokens.
                 description = metadata.get_file_description(file_path)
                 content_tokens = tokencost.count_string_tokens(description, "gpt-4o")


        elif self.use_details and file_usage.is_code:
            # Original logic for details token count
            details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
            if details:
                details_str = self.parse_json_response(details.model_dump_json())
                content_tokens = tokencost.count_string_tokens(details_str, "gpt-4o")

        else:
            # If details/descriptions options are not used, or not applicable (e.g., not code for details),
            # the full content is used in retrieve. Calculate tokens for the full content.
            content_tokens = state.repo.files_tokens.get(file_path, 0)

        return content_tokens


    def should_include_file(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> bool:
        if self.include_all_files:
            return True

        if not metadata:
            # Cannot check specific criteria without metadata
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
             # If file not found in metadata, cannot check criteria
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
    # Example usage - requires dummy RepoMetadata and state setup
    # This part is not modified as per instructions
    metadata = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    context = retriever.retrieve(metadata.descriptions.keys(), metadata)
    print(context)