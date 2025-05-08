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
            # The commented-out code check is removed as per SonarQube S125
            if metadata:
                file_usage = metadata.get_file_usage(file_path)
            else:
                file_usage = None

            if self.should_include_file(file_path, metadata):
                # Safely get the token count for the current file if available
                file_token = files_tokens[i] if files_tokens and i < len(files_tokens) else None

                file_content_str = self._get_file_representation_string(
                    file_path,
                    file_usage,
                    metadata,
                    file_token,
                )
                if file_content_str:
                    context.append(file_content_str)

        return "\n\n".join(context)

    def _get_file_representation_string(
        self,
        file_path: str,
        file_usage,  # Type hint depends on RepoMetadata.get_file_usage return type
        metadata: Optional[RepoMetadata],
        file_token: Optional[int],
    ) -> Optional[str]:
        """Helper to get the string representation of a file based on retriever settings."""
        # Determine if we need metadata/file_usage to proceed based on settings
        needs_metadata = not self.include_all_files or self.use_details or self.use_descriptions

        if needs_metadata and (not metadata or not file_usage):
             # If metadata is required but missing for this file, cannot generate representation
             return None

        file_header = f"# {file_path}"
        if (self.use_details or self.use_descriptions) and file_token is not None:
            file_header += f" [{file_token} tokens]"

        content_string = None

        if self.use_details and file_usage and file_usage.is_code:
            details = ( metadata.get_testing_details(file_path)
                        if file_usage.testing_related
                        else metadata.get_code_details(file_path))
            if details:
                content_string = self.parse_json_response(details.model_dump_json())
        elif self.use_descriptions and file_usage:
            if file_usage.is_code:
                details = ( metadata.get_code_details(file_path)
                            if not file_usage.testing_related
                            else metadata.get_testing_details(file_path))
                if details:
                    description = details.description
                    if details.external_imports:
                        description += f"\nExternal imports: {', '.join(details.external_imports)}\n" # Added newline for clarity
                    content_string = description
            else:
                content_string = metadata.get_file_description(file_path)
        elif file_usage: # Fallback to raw content ONLY if metadata and file_usage were available AND details/descriptions are off
             # This case is for when use_details and use_descriptions are False and metadata was present
            content_string = state.repo.read_file(file_path)
        elif self.include_all_files and (not metadata or not file_usage) and not (self.use_details or self.use_descriptions): # Fallback to raw content if include_all_files is True and metadata/file_usage is missing, AND details/descriptions are OFF
             # This case is for include_all_files=True, use_details/descriptions=False, and metadata/file_usage is None
             try:
                 content_string = state.repo.read_file(file_path)
             except KeyError: # File might not be loaded into state.repo
                  content_string = None # Cannot get raw content


        if content_string is not None:
             return f"{file_header}:\n{content_string}"
        else:
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
            files_data["Incl."].append(included)

            # Count the number of tokens from the metadata
            tokens = self.count_tokens_from_metadata(file_path, metadata)
            files_data["Tokens"].append(tokens)

        return files_data

    def count_tokens_from_metadata(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> int:
        # Determine if we need metadata/file_usage to proceed based on settings for token counting
        needs_metadata_for_representation = self.use_details or self.use_descriptions

        file_usage = metadata.get_file_usage(file_path) if metadata else None

        if needs_metadata_for_representation and (not metadata or not file_usage):
             # If details/descriptions are required but metadata/file_usage is missing,
             # we cannot count tokens for that representation type.
             # If include_all_files is true, we might still count header + raw.
             if self.include_all_files and not needs_metadata_for_representation:
                  # Include header + raw tokens if include_all_files is true and we are falling back to raw
                   total_tokens = tokencost.count_string_tokens(f"# {file_path}", "gpt-4o")
                   try:
                       total_tokens += state.repo.files_tokens.get(file_path, 0)
                   except AttributeError:
                       pass # state.repo or files_tokens might not exist
                   return total_tokens
             return 0 # Otherwise, cannot count tokens meaningfully based on settings

        # Count tokens for the file header (always included if representation is generated)
        file_header = f"# {file_path}"
        total_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")

        # Add tokens for the content part based on representation setting
        content_tokens = self._count_file_representation_tokens(file_path, file_usage, metadata)
        total_tokens += content_tokens

        return total_tokens

    def _count_file_representation_tokens(
         self,
         file_path: str,
         file_usage,
         metadata: Optional[RepoMetadata]
    ) -> int:
        """Helper to count tokens for the content part of a file's representation."""
        # This helper counts tokens based on the representation type (details, descriptions, raw)
        # It assumes the caller has handled the initial checks for metadata/file_usage
        # and that file_usage and metadata (if needed) are available where required by the logic below.

        if self.use_descriptions:
            if file_usage and file_usage.is_code:
                details = ( metadata.get_code_details(file_path)
                            if not file_usage.testing_related
                            else metadata.get_testing_details(file_path))
                if details:
                    description = details.description
                    if details.external_imports:
                        description += (
                            f"\nExternal imports: {', '.join(details.external_imports)}\n" # Added newline for clarity
                        )
                    return tokencost.count_string_tokens(description, "gpt-4o")
            elif file_usage: # Not code, get description
                description = metadata.get_file_description(file_path)
                return tokencost.count_string_tokens(description, "gpt-4o")
            # If use_descriptions is True but file_usage is None, description cannot be generated/counted.
            return 0

        elif self.use_details and file_usage and file_usage.is_code:
            details = ( metadata.get_code_details(file_path)
                        if not file_usage.testing_related
                        else metadata.get_testing_details(file_path))
            if details:
                details_str = self.parse_json_response(details.model_dump_json())
                return tokencost.count_string_tokens(details_str, "gpt-4o")
            # If use_details is True and file_usage exists and is code, but no details available
            return 0

        else:
            # otherwise, return the full file's number of tokens from state (raw content)
            # This applies if use_descriptions and use_details are False
            # Assumes the file was loaded into state.repo.files_tokens
            try:
                 return state.repo.files_tokens.get(file_path, 0)
            except AttributeError: # state.repo or state.repo.files_tokens might not exist
                 return 0


    def should_include_file(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> bool:
        if self.include_all_files:
            return True

        if not metadata:
            # If filters are applied and no metadata is available, cannot include
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            # If filters are applied and file not in metadata, cannot include
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