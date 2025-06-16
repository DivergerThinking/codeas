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
        """
        Retrieves context strings for the given file paths based on retriever settings.
        """
        context = []
        for i, file_path in enumerate(files_paths):
            # Removed commented out code: # if not file_usage: # raise ValueError(...)

            if self.should_include_file(file_path, metadata):
                file_entry = self._build_file_entry(file_path, i, files_tokens, metadata)
                if file_entry is not None:
                    context.append(file_entry)

        return "\n\n".join(context)

    def _build_file_entry(self, file_path: str, index: int, files_tokens: Optional[list[int]], metadata: Optional[RepoMetadata]) -> Optional[str]:
        """
        Builds the formatted string entry for a single file based on settings.
        Returns the string or None if the file content mode yielded no content.
        """
        file_usage = metadata.get_file_usage(file_path) if metadata else None

        file_header = f"# {file_path}"
        token_info = None
        if (self.use_details or self.use_descriptions) and files_tokens and index < len(files_tokens):
             token_info = files_tokens[index]
        if token_info is not None:
             file_header += f" [{token_info} tokens]"

        content_part = None # Use None to signify that no relevant content was found/generated in description/details mode

        is_metadata_mode = self.use_descriptions or self.use_details

        if self.use_descriptions and metadata and file_usage:
            if file_usage.is_code:
                details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
                if details and details.description:
                    content_part = details.description
                    if details.external_imports:
                        content_part += f"\nExternal imports: {', '.join(details.external_imports)}"
            elif metadata.get_file_description(file_path):
                 content_part = metadata.get_file_description(file_path)

        elif self.use_details and metadata and file_usage and file_usage.is_code:
            details = metadata.get_testing_details(file_path) if file_usage.testing_related else metadata.get_code_details(file_path)
            if details:
                content_part = self.parse_json_response(details.model_dump_json())

        if is_metadata_mode and content_part is None:
            # Metadata mode but couldn't get description/details content
            return None

        if not is_metadata_mode:
            # Fallback to full content mode
            try:
                content_part = state.repo.read_file(file_path)
            except Exception: # Catch potential file reading errors
                 print(f"Warning: Could not read file {file_path}")
                 content_part = "" # Add header + :\n even if content is empty

        if content_part is not None:
            return f"{file_header}:\\n{content_part}"
        else:
            # This case should ideally not be reached if the logic is correct,
            # but serves as a final safeguard.
            return None


    def parse_json_response(self, json_str: str) -> str:
        """
        Parses a JSON string and formats it into a human-readable string.
        """
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

    def retrieve_files_data(\n        self, files_paths: list[str], metadata: Optional[RepoMetadata] = None\n    ) -> Dict[str, List]:
        """
        Retrieves data about files including inclusion status, path, and token count.
        """
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

            # Count the number of tokens for the content that would be included
            tokens = self.count_tokens_from_metadata(file_path, metadata)
            files_data["Tokens"].append(tokens)

        return files_data

    def count_tokens_from_metadata(\n        self, file_path: str, metadata: Optional[RepoMetadata]\n    ) -> int:
        """
        Counts tokens for the content that would be included for a file based on settings.
        """
        file_usage = metadata.get_file_usage(file_path) if metadata else None

        # Determine the mode: description, details, or full content fallback
        use_descriptions_mode = self.use_descriptions and metadata and file_usage
        use_details_mode = self.use_details and metadata and file_usage and file_usage.is_code

        if use_descriptions_mode or use_details_mode:
            # Calculate tokens for metadata-based content
            file_header = f"# {file_path}"
            header_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")

            if use_descriptions_mode:
                 content_tokens = self._calculate_description_tokens(file_path, file_usage, metadata)
            elif use_details_mode:
                 content_tokens = self._calculate_details_tokens(file_path, file_usage, metadata)
            else: # Should not be reached
                content_tokens = 0

            return header_tokens + content_tokens
        else:
            # Fallback to full content tokens (happens if not metadata mode or metadata/file_usage is missing)
            file_header = f"# {file_path}"
            header_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")
            full_content_tokens = state.repo.files_tokens.get(file_path, 0)
            return header_tokens + full_content_tokens

    def _calculate_description_tokens(self, file_path, file_usage, metadata):
        """Helper to calculate tokens for description content."""
        description = ""
        if file_usage.is_code:
            details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
            if details and details.description:
                description = details.description
                if details.external_imports:
                    description += f"\nExternal imports: {', '.join(details.external_imports)}"
        elif metadata.get_file_description(file_path):
             description = metadata.get_file_description(file_path)

        return tokencost.count_string_tokens(description, "gpt-4o") if description else 0


    def _calculate_details_tokens(self, file_path, file_usage, metadata):
        """Helper to calculate tokens for details content (JSON parsed)."""
        details = metadata.get_testing_details(file_path) if file_usage.testing_related else metadata.get_code_details(file_path)
        if details:
            details_str = self.parse_json_response(details.model_dump_json())
            return tokencost.count_string_tokens(details_str, "gpt-4o")
        return 0


    def should_include_file(\n        self, file_path: str, metadata: Optional[RepoMetadata]\n    ) -> bool:
        """
        Determines if a file should be included based on the current settings.
        """
        if self.include_all_files:
            return True

        if not metadata:
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            return False

        return (\n            (self.include_code_files and file_usage.is_code)\n            or (self.include_testing_files and file_usage.testing_related)\n            or (self.include_config_files and file_usage.config_related)\n            or (self.include_deployment_files and file_usage.deployment_related)\n            or (self.include_security_files and file_usage.security_related)\n            or (self.include_ui_files and file_usage.ui_related)\n            or (self.include_api_files and file_usage.api_related)\n        )


if __name__ == "__main__":
    # Example usage - requires mocking RepoMetadata and state.repo
    # For testing purposes, ensure state and RepoMetadata are properly initialized or mocked
    try:
        # Attempt to use actual objects if available in the environment
        metadata = RepoMetadata.load_metadata(".")
        # Assuming state.repo is available globally from codeas.core.state
        if not hasattr(state, 'repo'):
             print("Warning: state.repo not available. Skipping __main__ example.")
        else:
            retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
            # Ensure metadata.descriptions is not None/empty before calling .keys()
            if metadata and hasattr(metadata, 'descriptions') and metadata.descriptions:
                 context = retriever.retrieve(list(metadata.descriptions.keys()), metadata=metadata)
                 print(context)
            else:
                 print("Warning: No metadata descriptions found. Skipping context retrieval.")

    except ImportError:
        print("Could not import necessary modules for __main__ example.")
    except Exception as e:
        print(f"An error occurred during __main__ execution: {e}")