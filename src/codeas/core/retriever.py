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
            # Check if the file should be included first
            if not self.should_include_file(file_path, metadata):
                 continue # Skip if not included

            # Get file_usage if metadata exists, needed by _get_formatted_file_content
            # If file_usage is None, _get_formatted_file_content will fall back to raw content
            file_usage = metadata.get_file_usage(file_path) if metadata else None

            # Get the formatted content using the helper
            # Pass file_usage as it's already determined
            file_content = self._get_formatted_file_content(file_path, i, files_tokens, metadata, file_usage)

            # Append content
            context.append(file_content)

        return "\n\n".join(context)

    def _get_formatted_file_content(self, file_path: str, i: int, files_tokens: Optional[list[int]], metadata: Optional[RepoMetadata], file_usage) -> str:
        """Helper to get formatted file content based on retriever settings."""

        file_header = f"# {file_path}"
        # Add tokens to header only if files_tokens are provided and valid index,
        # and if descriptions or details are being used (matching original logic)
        if (self.use_details or self.use_descriptions) and files_tokens and 0 <= i < len(files_tokens):
             file_header += f" [{files_tokens[i]} tokens]"

        # Case 1: Use Details (requires metadata, file_usage, and file is code)
        if self.use_details and metadata and file_usage and file_usage.is_code:
            details = metadata.get_testing_details(file_path) if file_usage.testing_related else metadata.get_code_details(file_path)
            if details:
                return f"{file_header}:\n{self.parse_json_response(details.model_dump_json())}"

        # Case 2: Use Descriptions (requires metadata and file_usage)
        if self.use_descriptions and metadata and file_usage:
             if file_usage.is_code:
                details = metadata.get_code_details(file_path) if not file_usage.testing_related else metadata.get_testing_details(file_path)
                if details:
                    description = f"{file_header}:\n{details.description}"
                    if details.external_imports:
                        description += f"\nExternal imports: {', '.join(details.external_imports)}\n" # Added newline for consistency
                    return description
             else: # Non-code file description
                description = metadata.get_file_description(file_path)
                return f"{file_header}:\n{description}"

        # Case 3: Fallback - Get raw content
        # This covers the original 'else' block when neither use_details nor use_descriptions branches were taken,
        # or when metadata/file_usage was insufficient for those branches.
        # This always needs state.repo available.
        content = state.repo.read_file(file_path)
        return f"{file_header}:\n{content}"


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

        # Join with empty string initially and then slice to remove leading newline if it exists
        output_str = "\n".join(result)
        if output_str.startswith('\n'):
            output_str = output_str[1:]
        return output_str


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
            files_data["Incl."].append(included) # Store boolean directly

            # Count the number of tokens for ALL files in the input list, regardless of inclusion status
            # This reverts the potential regression identified in the previous iteration.
            tokens = self._get_file_token_count(file_path, metadata)
            files_data["Tokens"].append(tokens)

        return files_data

    def count_tokens_from_metadata(
        self, file_path: str, metadata: Optional[RepoMetadata]
    ) -> int:
        # This method is now simplified to call the helper
        return self._get_file_token_count(file_path, metadata)

    def _get_file_token_count(self, file_path: str, metadata: Optional[RepoMetadata]) -> int:
         """Helper to calculate token count based on retriever settings."""

         # Determine file_usage upfront if metadata is available
         file_usage = metadata.get_file_usage(file_path) if metadata else None

         # Case 1: User wants raw file content tokens (neither details nor descriptions)
         # This happens if self.use_details is False AND self.use_descriptions is False
         if not self.use_details and not self.use_descriptions:
             # Use the full file tokens from state.repo if available
             # Original code assumed it exists and would crash otherwise. Get provides safer default.
             return state.repo.files_tokens.get(file_path, 0)

         # Case 2: User wants descriptions or details tokens (requires metadata and file_usage)
         # We need metadata and file_usage to determine file type (code/test/config etc.)
         if not metadata or not file_usage:
             # If we cannot get description/details tokens (missing metadata/usage),
             # and the user *requested* description/details, we return 0 tokens
             # for this file in this mode, as no relevant content will be included.
             # This differs slightly from the raw content fallback but aligns with
             # what would likely be included in the context in description/detail mode
             # if metadata was missing for a specific file (i.e., nothing).
             return 0


         # Calculate header tokens (always included if using description/details mode and metadata/usage available)
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
                             f"\nExternal imports: {', '.join(details.external_imports)}\n" # Added newline
                         )
                     total_tokens += tokencost.count_string_tokens(description, "gpt-4o")
             else: # Non-code file description
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
         # If file_usage exists but doesn't match use_descriptions/use_details criteria (e.g., use_details=True for a non-code file),
         # total_tokens remains just the header tokens. This matches the path where
         # original method didn't enter description/details blocks but didn't hit the final else.

         return total_tokens

    def should_include_file(\
        self, file_path: str, metadata: Optional[RepoMetadata]\
    ) -> bool:\
        if self.include_all_files:\
            return True

        # If not including all files, metadata is required to check file type flags
        if not metadata:
            return False

        file_usage = metadata.get_file_usage(file_path)
        if not file_usage:
            # If metadata exists but the file isn't found in it, it cannot match any type criteria
            return False

        # This boolean expression is the core of the inclusion logic
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
    # Assuming RepoMetadata and state.repo exist and are populated for this example to work
    # Mock or ensure state.repo and metadata are available for this block
    try:
        metadata = RepoMetadata.load_metadata(".")
        # Use list() as keys() might not be list in older Python versions or specific dict implementations
        file_paths_list = list(metadata.descriptions.keys()) if metadata and hasattr(metadata, 'descriptions') and metadata.descriptions else []
        retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
        # Note: The original example calls retrieve with files_paths_list and metadata.
        # It doesn't provide files_tokens, so that part of the logic won't be tested here.
        context = retriever.retrieve(file_paths_list, metadata=metadata)
        print(context)

        # Example usage of retrieve_files_data
        # files_data = retriever.retrieve_files_data(file_paths_list, metadata)
        # print("\nFiles Data:")
        # for i in range(len(files_data["Path"])):
        #     print(f"  Path: {files_data['Path'][i]}, Included: {files_data['Incl.'][i]}, Tokens: {files_data['Tokens'][i]}")

    except Exception as e:
        print(f"Error during example execution: {e}")
        print("Please ensure RepoMetadata and state.repo are properly mocked or initialized if running this example.")