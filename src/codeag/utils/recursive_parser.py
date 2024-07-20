import os
from typing import Callable, List, Optional, Tuple


def match_path(path: str, pattern: str) -> bool:
    """
    Check if a path matches the given pattern.

    If pattern includes '*', use startswith() for the part before '*'.
    Otherwise, check if the path starts with the pattern (for subdirectory support).
    """
    if pattern.endswith("/"):
        pattern = pattern[:-1]  # remove trailing slash

    if pattern.endswith("*"):
        prefix = pattern.split("*")[0]
        return path.startswith(prefix)
    elif pattern.startswith("*"):
        suffix = pattern.split("*")[1]
        return path.endswith(suffix)
    else:
        return path == pattern or path.startswith(pattern + os.path.sep)


def create_filter(
    base_path: str, include_patterns: List[str], exclude_patterns: List[str]
) -> Callable[[str], Tuple[bool, bool]]:
    """
    Create a filter function based on include and exclude patterns.
    Returns a tuple (should_include, should_traverse)
    """

    def filter_func(path: str) -> Tuple[bool, bool]:
        if exclude_patterns and any(
            match_path(path, pattern) for pattern in exclude_patterns
        ):
            return False, False

        if not include_patterns:
            return True, True

        for pattern in include_patterns:
            if match_path(path, pattern):
                return True, True
            elif any(
                match_path(os.path.join(path, subdir), pattern)
                for subdir in os.listdir(os.path.join(base_path, path))
                if os.path.isdir(os.path.join(base_path, path, subdir))
            ):
                return False, True

        return False, False

    return filter_func


def list_repository_contents_recursive(
    base_path: str,
    current_path: str,
    filter_func: Callable[[str], Tuple[bool, bool]],
    include_files: list,
    exclude_files: list,
    check_readability: bool,
    folder_only: bool,
    as_dict: bool,
):
    """
    Recursively list contents in a repository, applying the filter function.
    """
    if as_dict:
        contents = {"dirs": {}, "files": []}
    elif check_readability:
        contents = {}
    else:
        contents = []

    relative_path = os.path.relpath(current_path, base_path)

    if relative_path == ".":
        relative_path = ""

    should_include, should_traverse = filter_func(relative_path)

    if should_include:
        matched_files = filter_files(
            current_path, relative_path, include_files, exclude_files, check_readability
        )
        if as_dict:
            contents["files"].extend(matched_files)
        elif folder_only:
            if relative_path and any(matched_files):
                contents.append(relative_path)
        else:
            if isinstance(matched_files, dict):
                contents.update(matched_files)
            else:
                contents.extend(matched_files)

    if should_traverse:
        for item in os.listdir(current_path):
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                if as_dict:
                    sub_contents = list_repository_contents_recursive(
                        base_path,
                        item_path,
                        filter_func,
                        include_files,
                        exclude_files,
                        check_readability,
                        folder_only,
                        as_dict,
                    )
                    if sub_contents["dirs"] or sub_contents["files"]:
                        contents["dirs"][item] = sub_contents
                else:
                    if check_readability:
                        contents.update(
                            list_repository_contents_recursive(
                                base_path,
                                item_path,
                                filter_func,
                                include_files,
                                exclude_files,
                                check_readability,
                                folder_only,
                                as_dict,
                            )
                        )
                    else:
                        contents.extend(
                            list_repository_contents_recursive(
                                base_path,
                                item_path,
                                filter_func,
                                include_files,
                                exclude_files,
                                check_readability,
                                folder_only,
                                as_dict,
                            )
                        )

    return contents


def filter_files(
    current_path: str,
    relative_path: str,
    include_files: list,
    exclude_files: list,
    check_readibility: bool,
) -> List[str]:
    """
    Filter files in the specified path based on the include and exclude patterns.
    """
    if check_readibility:
        filtered_files = {}
    else:
        filtered_files = []
    for item in os.listdir(current_path):
        item_path = os.path.join(current_path, item)
        if os.path.isfile(item_path):
            if include_files and not any(
                match_path(item, pattern) for pattern in include_files
            ):
                continue
            if exclude_files and any(
                match_path(item, pattern) for pattern in exclude_files
            ):
                continue
            else:
                file_path = os.path.join(relative_path, item)
                if check_readibility:
                    try:
                        filtered_files[file_path] = read_file(item_path)
                    except Exception:
                        pass
                else:
                    filtered_files.append(os.path.join(relative_path, item))
    return filtered_files


def read_file(file_path: str) -> bool:
    """
    Check if a file is readable by trying to open it.
    """
    with open(file_path, "r") as f:
        return f.read()


def get_repository_paths(
    path: str,
    include_dir: Optional[List[str]] = [],
    exclude_dir: Optional[List[str]] = [],
    include_files: Optional[List[str]] = [],
    exclude_files: Optional[List[str]] = [],
    check_readibility: bool = False,
    folder_only: bool = False,
    as_dict: bool = False,
) -> List[str]:
    """
    List contents in a repository, with optional filtering and folder-only mode.

    Args:
    path (str): The path of the repository.
    include_dir (Optional[List[str]]): List of directories to include.
        Use '*' for wildcard matching (e.g., '.*', '_*'), supports subdirectory paths.
    exclude_dir (Optional[List[str]]): List of directories to exclude.
        Use '*' for wildcard matching (e.g., '.*', '_*'), supports subdirectory paths.
    folder_only (bool): If True, return only directory names. Defaults to False.

    Returns:
    List[str]: A list of file or directory paths found in the repository.
    """
    if not os.path.isdir(path):
        raise ValueError(f"The specified path '{path}' is not a valid directory.")

    filter_func = create_filter(path, include_dir, exclude_dir)

    contents = list_repository_contents_recursive(
        path,
        path,
        filter_func,
        include_files,
        exclude_files,
        check_readibility,
        folder_only,
        as_dict,
    )
    if as_dict:
        contents
    elif check_readibility:
        return dict(sorted(contents.items()))
    else:
        return sorted(contents)


def extract_folders_up_to_level(repo_path, file_paths, max_level, as_lists=True):
    folders = {}
    for path, n_tokens in file_paths.items():
        parts = os.path.normpath(path).split(os.sep)
        for level in range(1, min(len(parts), max_level) + 1):
            folder = os.sep.join(parts[:level])
            full_folder_path = os.path.join(repo_path, folder)
            if os.path.isdir(full_folder_path):
                if folder not in folders:
                    folders[folder] = {"n_files": 0, "n_tokens": 0}
                folders[folder]["n_files"] += 1
                folders[folder]["n_tokens"] += n_tokens

    # Sort the dictionary by folder names
    sorted_folders = dict(sorted(folders.items()))

    if as_lists:
        paths = list(sorted_folders.keys())
        n_files = [folder_info["n_files"] for folder_info in sorted_folders.values()]
        n_tokens = [folder_info["n_tokens"] for folder_info in sorted_folders.values()]
        return paths, n_files, n_tokens
    else:
        return sorted_folders


def count_tokens_per_files(files):
    return {path: int(len(content) / 4) for path, content in files.items()}


if __name__ == "__main__":
    # dir_paths = get_repository_paths(
    #     "../abstreet", exclude_dir=[".*"], folder_only=True
    # )
    file_paths = get_repository_paths(
        "../abstreet",
        exclude_dir=[".*"],
        folder_only=False,
        check_readibility=True,
    )
    file_chars = count_tokens_per_files(file_paths)
    folders = extract_folders_up_to_level("../abstreet", file_chars, 0, True)
    ...
