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
                file_header = f"# {file_path}"
                if (self.use_details or self.use_descriptions) and files_tokens:
                    file_header += f" [{files_tokens[i]} tokens]"

                file_content = self._get_formatted_file_content(
                    file_path, file_usage, metadata, file_header
                )
                if file_content is not None:
                    context.append(file_content)

        return "\n\n".join(context)

    def _get_formatted_file_content(
        self,
        file_path: str,
        file_usage: Optional[any], # Use 'any' as RepoMetadata.get_file_usage return type is not specified
        metadata: Optional[RepoMetadata],
        file_header: str,
    ) -> Optional[str]:
        if self.use_details and file_usage and file_usage.is_code and metadata:
            details = (
                metadata.get_testing_details(file_path)
                if file_usage.testing_related
                else metadata.get_code_details(file_path)
            )
            if details:
                return f"{file_header}:\n{self.parse_json_response(details.model_dump_json())}"
        elif self.use_descriptions and metadata:
            if file_usage and file_usage.is_code:
                details = (
                    metadata.get_code_details(file_path)
                    if file_usage and not file_usage.testing_related
                    else metadata.get_testing_details(file_path)
                )
                if details:
                    description = f"{file_header}:\n{details.description}"
                    if details.external_imports:
                        description += f"\nExternal imports: {', '.join(details.external_imports)}"
                    return description
            elif metadata.get_file_description(file_path):
                description = metadata.get_file_description(file_path)
                return f"{file_header}:\n{description}"
        else:
            # otherwise, return the full file content
            content = state.repo.read_file(file_path)
            return f"{file_header}:\n{content}"

        return None # Should not be reached in current logic, but good practice

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

        content_tokens = self._count_content_tokens(file_path, file_usage, metadata)

        return total_tokens + content_tokens

    def _count_content_tokens(
        self,
        file_path: str,
        file_usage: any, # Use 'any' as RepoMetadata.get_file_usage return type is not specified
        metadata: RepoMetadata,
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
            return state.repo.files_tokens.get(file_path, 0) # Use .get for safety

        return 0 # Should not be reached if one of the branches is always taken

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
    # Assuming necessary setup for state and RepoMetadata exists
    # Example usage (might require mocking dependencies for execution)
    class MockRepoMetadata:
        def load_metadata(self, path):
            print(f"Loading metadata from {path}...")
            # Return a mock object with necessary attributes/methods
            mock_metadata = type('obj', (object,), {})()
            mock_metadata.descriptions = {"mock/file1.py": "Desc 1", "mock/file2.txt": "Desc 2"}
            
            class MockFileUsage:
                def __init__(self, is_code=False, testing=False, config=False, deployment=False, security=False, ui=False, api=False):
                    self.is_code = is_code
                    self.testing_related = testing
                    self.config_related = config
                    self.deployment_related = deployment
                    self.security_related = security
                    self.ui_related = ui
                    self.api_related = api

            def get_file_usage(file_path):
                if file_path == "mock/file1.py":
                    return MockFileUsage(is_code=True)
                elif file_path == "mock/file2.txt":
                    return MockFileUsage(is_code=False)
                return None
                
            def get_file_description(file_path):
                return mock_metadata.descriptions.get(file_path, "")
                
            def get_code_details(file_path):
                 if file_path == "mock/file1.py":
                     details = type('obj', (object,), {})()
                     details.description = "Details desc for file1"
                     details.external_imports = ["os", "sys"]
                     details.model_dump_json = lambda: '{"description": "Details desc for file1", "external_imports": ["os", "sys"]}'
                     return details
                 return None
            
            def get_testing_details(file_path):
                return None # Mock no testing details
            
            mock_metadata.get_file_usage = get_file_usage
            mock_metadata.get_file_description = get_file_description
            mock_metadata.get_code_details = get_code_details
            mock_metadata.get_testing_details = get_testing_details

            return mock_metadata

        # Mock necessary methods/attributes

    class MockState:
        def __init__(self):
            self.repo = type('obj', (object,), {})()
            self.repo.read_file = lambda path: f"Content of {path}"
            self.repo.files_tokens = {"mock/file1.py": 100, "mock/file2.txt": 50} # Mock token counts

    # Mock global state
    state = MockState()
    RepoMetadata.load_metadata = MockRepoMetadata().load_metadata # Monkey patch

    print("--- Test Case 1: include_all_files=True, use_descriptions=True ---")
    metadata_obj = RepoMetadata.load_metadata(".")
    retriever = ContextRetriever(include_all_files=True, use_descriptions=True)
    files_to_retrieve = list(metadata_obj.descriptions.keys()) + ["mock/file1.py", "mock/file2.txt", "nonexistent.md"] # Add some files
    context = retriever.retrieve(files_to_retrieve, None, metadata_obj)
    print(context)

    print("\n--- Test Case 2: include_code_files=True, use_details=True ---")
    retriever_details = ContextRetriever(include_code_files=True, use_details=True)
    context_details = retriever_details.retrieve(files_to_retrieve, None, metadata_obj)
    print(context_details)

    print("\n--- Test Case 3: include_all_files=False (default), raw content ---")
    retriever_raw = ContextRetriever()
    context_raw = retriever_raw.retrieve(files_to_retrieve, None, metadata_obj) # Should include nothing as include flags are false
    print(context_raw)

    print("\n--- Test Case 4: include_all_files=True, raw content ---")
    retriever_raw_all = ContextRetriever(include_all_files=True)
    context_raw_all = retriever_raw_all.retrieve(files_to_retrieve, None, metadata_obj)
    print(context_raw_all)