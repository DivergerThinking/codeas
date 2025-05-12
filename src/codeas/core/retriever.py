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

    def _get_file_content_string(
        self, file_path, file_usage, metadata, files_tokens, i
    ) -> str:
        """Helper to get the content string for an included file."""
        file_header = f"# {file_path}"
        if (self.use_details or self.use_descriptions) and files_tokens:
            file_header += f" [{files_tokens[i]} tokens]"

        if self.use_details and file_usage and file_usage.is_code:
            details = metadata.get_testing_details(
                file_path
            ) if file_usage.testing_related else metadata.get_code_details(file_path)
            if details:
                return f"{file_header}:\\n{self.parse_json_response(details.model_dump_json())}"
        elif self.use_descriptions and file_usage:
            if file_usage.is_code:
                details = metadata.get_code_details(
                    file_path
                ) if not file_usage.testing_related else metadata.get_testing_details(
                    file_path
                )
                if details:
                    description = f"{file_header}:\\n{details.description}"
                    if details.external_imports:
                        description += f"\\nExternal imports: {', '.join(details.external_imports)}"
                    return description
            else:
                description = metadata.get_file_description(file_path)
                return f"{file_header}:\\n{description}"
        else:
            content = state.repo.read_file(file_path)
            return f"{file_header}:\\n{content}"

        # Return empty string if file_usage is None or no details/descriptions used/found
        # and not falling into the 'else' (read file content) case.
        # This can happen if metadata/file_usage is None, but should_include_file allows inclusion
        # based on include_all_files=True. In such cases, _get_file_content_string might be called
        # but return an empty string if there's no file_usage to guide content retrieval.
        return ""

    def retrieve(
        self,
        files_paths: list[str],
        files_tokens: Optional[list[int]] = None,
        metadata: Optional[RepoMetadata] = None,
    ) -> str:
        context = []
        for i, file_path in enumerate(files_paths):
            # Removed the commented-out code check here
            if metadata:
                file_usage = metadata.get_file_usage(file_path)
            else:
                file_usage = None

            if self.should_include_file(file_path, metadata):
                 file_content = self._get_file_content_string(
                     file_path, file_usage, metadata, files_tokens, i
                 )
                 if file_content:
                     context.append(file_content)

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

    def _get_countable_content_string(self, file_path, file_usage, metadata) -> Optional[str]:
        """Helper to get the string content to be token counted (excluding header)."""
        if not file_usage:
            return None

        if self.use_descriptions:
            if file_usage.is_code:
                details = metadata.get_code_details(
                    file_path
                ) if not file_usage.testing_related else metadata.get_testing_details(
                    file_path
                )
                if details:
                    description = details.description
                    if details.external_imports:
                        description += (
                            f"\\nExternal imports: {', '.join(details.external_imports)}"
                        )
                    return description
            else:
                return metadata.get_file_description(file_path)
        elif self.use_details and file_usage.is_code:
            details = metadata.get_code_details(
                file_path
            ) if not file_usage.testing_related else metadata.get_testing_details(
                file_path
            )
            if details:
                return self.parse_json_response(details.model_dump_json())

        return None # If neither descriptions nor details are used or file type doesn't match


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

        countable_content = self._get_countable_content_string(file_path, file_usage, metadata)

        if countable_content is not None:
             total_tokens += tokencost.count_string_tokens(countable_content, "gpt-4o")
        else:
            # otherwise, return the full files number of tokens
            # Reverted the check to restore original KeyError behavior
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
    # Reverted __main__ block to a minimal state similar to original
    # or just 'pass' if execution setup is complex and not relevant to the fix.
    # Assuming metadata and state.repo are properly initialized elsewhere
    # for the class to function.
    metadata = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    # Provide dummy list for files_tokens as it's optional but used in logic
    context = retriever.retrieve(list(metadata.descriptions.keys()), files_tokens=[0] * len(metadata.descriptions), metadata=metadata)
    print(context)