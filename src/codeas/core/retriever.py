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
            file_usage = None
            if metadata:
                file_usage = metadata.get_file_usage(file_path)
                # if not file_usage:
                #     raise ValueError(f"File {file_path} not found in metadata")

            if self.should_include_file(file_path, metadata):
                file_header = f"# {file_path}"

                # Add token estimate to header only if specified and available
                if (self.use_details or self.use_descriptions) and files_tokens:
                     file_header += f" [{files_tokens[i]} tokens]"


                # --- Original content determination logic in retrieve ---
                if self.use_details and file_usage and file_usage.is_code:
                    details = (
                        metadata.get_code_details(file_path)
                        if not file_usage.testing_related
                        else metadata.get_testing_details(file_path)
                    )
                    if details:
                         context.append(
                             f"{file_header}:\n{self.parse_json_response(details.model_dump_json())}"
                         )
                elif self.use_descriptions and file_usage:
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
                    else: # Not code file
                        description = metadata.get_file_description(file_path)
                        context.append(f"{file_header}:\n{description}\n") # Added newline for consistency
                else: # Default case: include full file content
                    content = state.repo.read_file(file_path)
                    context.append(f"{file_header}:\n{content}")
                # --- End original content determination logic ---


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

            # Count the number of tokens using the refactored method
            tokens = self.count_tokens_from_metadata(file_path, metadata)
            files_data["Tokens"].append(tokens)

        return files_data

    # Helper method to get details/description string content based on settings
    # Returns the string content or None if full file content should be used.
    # Requires metadata and file_usage to be not None.
    def _get_specific_content_string(self, file_path: str, file_usage, metadata: RepoMetadata) -> Optional[str]:
        """Helper to get the specific content string (description or details) or None. Requires metadata and file_usage."""
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
                        description += f"\nExternal imports: {', '.join(details.external_imports)}"
                    return description
                else:
                     # use_descriptions=True, is_code=True but no details -> return empty string
                     return ""
            else: # Not code file, use file description
                description = metadata.get_file_description(file_path)
                # Use description if found, else empty string
                return description if description is not None else ""

        elif self.use_details and file_usage.is_code:
             details = (
                 metadata.get_code_details(file_path)
                 if not file_usage.testing_related
                 else metadata.get_testing_details(file_path)
             )
             if details:
                 return self.parse_json_response(details.model_dump_json())
             else:
                 # use_details=True, is_code=True but no details -> return empty string
                 return ""

        return None # Indicates full file content should be used based on flags


    # Helper method to count tokens for specific content (description/details)
    # Returns the total token count (header + content) or -1 if full file content should be used.
    # Requires metadata and file_usage to be not None.
    def _count_specific_content_tokens_helper(self, file_path: str, file_usage, metadata: RepoMetadata) -> int:
        """Helper to calculate tokens for specific content (description/details) including header. Returns -1 if full content is used. Requires metadata and file_usage."""
        content_string = self._get_specific_content_string(file_path, file_usage, metadata)

        # _get_specific_content_string returns None only if the flags combination
        # doesn't trigger specific content (i.e., not use_descriptions and not (use_details and is_code))
        if content_string is not None:
            total_tokens = tokencost.count_string_tokens(f"# {file_path}", "gpt-4o")
            total_tokens += tokencost.count_string_tokens(content_string, "gpt-4o")
            return total_tokens
        else:
            # This case corresponds to the final 'else' in the original count_tokens_from_metadata
            # where full file content tokens are used.
            return -1


    def count_tokens_from_metadata(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> int:
        if not metadata:
            return 0

        file_usage = metadata.get_file_usage(file_path)

        # If file_usage exists, we might use specific content based on flags
        if file_usage:
             specific_content_tokens = self._count_specific_content_tokens_helper(file_path, file_usage, metadata)

             if specific_content_tokens != -1:
                 # Specific content was requested and found (includes header tokens)
                 return specific_content_tokens
             # else: Specific content was requested but not found/applicable -> fall through to full file tokens

        # If file_usage is None OR specific content was not used/found, return full file tokens
        # This matches the original 'else' block behavior.
        # Use .get() for safe access in case the file_path is not in files_tokens
        return state.repo.files_tokens.get(file_path, 0)


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
    context = retriever.retrieve(list(metadata.descriptions.keys()), metadata)
    print(context)