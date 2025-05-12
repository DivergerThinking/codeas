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
            # Use dedicated method to check if file should be included
            if not self.should_include_file(file_path, metadata):
                continue

            file_usage = metadata.get_file_usage(file_path) if metadata else None

            # Build file header
            file_header = f"# {file_path}"
            # Add tokens to header if needed and available
            if (self.use_details or self.use_descriptions) and files_tokens is not None and i < len(files_tokens):
                file_header += f" [{files_tokens[i]} tokens]"

            # Determine the content string based on settings and file type
            content_string = None
            if metadata and file_usage:
                if self.use_details and file_usage.is_code:
                    details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
                    if details:
                        # Use the parse_json_response method to format details
                        content_string = self.parse_json_response(details.model_dump_json())
                elif self.use_descriptions:
                    if file_usage.is_code:
                        details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
                        if details:
                            content_string = details.description
                            if details.external_imports:
                                content_string += f"\\nExternal imports: {', '.join(details.external_imports)}"
                    else: # Non-code file description
                        description = metadata.get_file_description(file_path)
                        if description: # Only add if description exists
                           content_string = description

            # Append header and content (either specific or full)
            if content_string is not None:
                 context.append(f"{file_header}:\\n{content_string}")
            else: # Fallback to full content if no specific content generated or applicable
                # Ensure state.repo exists before accessing
                if hasattr(state, 'repo') and state.repo:
                    full_content = state.repo.read_file(file_path)
                    context.append(f"{file_header}:\\n{full_content}")


        return "\\n\\n".join(context)

    def parse_json_response(self, json_str: str) -> str:
        data = json.loads(json_str)
        result = []
        for key, value in data.items():
            if value:
                result.append(f"\\n{key.replace('_', ' ').title()}:")
                if isinstance(value, list):
                    result.extend(f"- {item}" for item in value)
                else:
                    result.append(str(value))

        return "\\n".join(result)

    def retrieve_files_data(
        self, files_paths: list[str], metadata: Optional[RepoMetadata] = None
    ) -> Dict[str, List]:
        files_data: Dict[str, List] = {
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
        # If metadata is needed for description/details but not provided,
        # or if file_usage is missing, we cannot count tokens for those specific types.
        # The original code seems to return 0 in these metadata-dependent cases.
        if not metadata:
             return 0

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
             # If file_usage is missing, we cannot check file types/usage.
             return 0

        # Determine the content string based on settings for token counting
        content_string_for_counting = ""
        use_specific_content = False # Flag to indicate if we should count specific content

        if self.use_descriptions:
            use_specific_content = True
            if file_usage.is_code:
                details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
                if details:
                    content_string_for_counting = details.description
                    if details.external_imports:
                         content_string_for_counting += f"\\nExternal imports: {', '.join(details.external_imports)}"
            else: # Non-code file description
                 description = metadata.get_file_description(file_path)
                 if description:
                    content_string_for_counting = description
                 else:
                     # If description is None, effectively no specific content to count
                     use_specific_content = False
        elif self.use_details and file_usage.is_code:
             use_specific_content = True
             details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
             if details:
                 # For details, the raw content string for counting is the JSON string
                 content_string_for_counting = details.model_dump_json()
             else:
                 # If details are None, no specific content to count
                 use_specific_content = False

        # Count tokens based on whether specific content was determined,
        # otherwise fall back to full file tokens if state.repo is available.
        if use_specific_content:
            file_header = f"# {file_path}"
            total_tokens = tokencost.count_string_tokens(file_header, "gpt-4o")
            total_tokens += tokencost.count_string_tokens(content_string_for_counting, "gpt-4o")
            return total_tokens
        else:
            # otherwise, return the full files number of tokens if state.repo is available
            if hasattr(state, 'repo') and state.repo:
                # Use .get() for safety in case file_path is not in files_tokens
                return state.repo.files_tokens.get(file_path, 0)
            else:
                # Cannot get full file tokens without state.repo
                return 0


    def should_include_file(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> bool:
        if self.include_all_files:
            return True

        if not metadata:
            # If metadata is missing, we cannot check file types/usage,
            # so we cannot apply the specific include flags.
            # Only include_all_files works without metadata.
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
             # If file_usage is missing for a file, we cannot check its type/usage.
             # We cannot apply specific include flags.
             return False

        # Check specific include flags based on file_usage
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
    # Basic example usage - requires a mock or actual state/metadata setup
    # This block is for demonstration and is not run in a standard import.
    # Replace with actual setup or mock objects for testing if needed.
    try:
        # Assuming state and RepoMetadata are properly initialized elsewhere
        # For simple execution demonstration, we just show the call structure
        metadata = RepoMetadata.load_metadata(".") # Requires actual implementation
        retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
        # metadata.descriptions.keys() should return iterable of file paths
        file_paths_example = list(metadata.descriptions.keys()) # Example paths
        # files_tokens_example = [state.repo.files_tokens.get(f, 0) for f in file_paths_example] # Example tokens if state.repo exists

        # context = retriever.retrieve(file_paths_example, files_tokens_example, metadata)
        # print(context)

        # print("\n--- Retrieve Files Data Example ---")
        # files_data = retriever.retrieve_files_data(file_paths_example, metadata)
        # print(files_data)

        print("ContextRetriever methods defined. Add mock objects or run in environment with state/metadata for full execution.")

    except NameError:
        print("Skipping __main__ execution: state or RepoMetadata not available.")
    except Exception as e:
        print(f"An error occurred during __main__ execution: {e}")