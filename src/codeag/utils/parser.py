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
    check_readibility: bool,
    folder_only: bool,
) -> List[str]:
    """
    Recursively list contents in a repository, applying the filter function.
    """

    contents = []
    relative_path = os.path.relpath(current_path, base_path)

    if relative_path == ".":
        relative_path = ""

    should_include, should_traverse = filter_func(relative_path)

    if should_include:
        matched_files = filter_files(
            current_path, relative_path, include_files, exclude_files, check_readibility
        )
        if folder_only:
            if relative_path:
                if any(matched_files):
                    contents.append(relative_path)
        else:
            contents.extend(matched_files)

    if should_traverse:
        for item in os.listdir(current_path):
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                contents.extend(
                    list_repository_contents_recursive(
                        base_path,
                        item_path,
                        filter_func,
                        include_files,
                        exclude_files,
                        check_readibility,
                        folder_only,
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
                # file_path = os.path.join(relative_path, item_path)
                if check_readibility:
                    if is_file_readable(item_path):
                        filtered_files.append(item_path)
                else:
                    filtered_files.append(item_path)
    return filtered_files


def is_file_readable(file_path: str) -> bool:
    """
    Check if a file is readable by trying to open it.
    """
    try:
        with open(file_path, "r") as f:
            f.read()
            return True
    except Exception:
        return False


def get_repository_paths(
    path: str,
    include_dir: Optional[List[str]] = [],
    exclude_dir: Optional[List[str]] = [],
    include_files: Optional[List[str]] = [],
    exclude_files: Optional[List[str]] = [],
    check_readibility: bool = False,
    folder_only: bool = False,
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
    )

    return sorted(contents)


if __name__ == "__main__":
    dir_paths = get_repository_paths(
        "../abstreet", exclude_dir=[".*"], folder_only=True
    )
    file_paths = get_repository_paths(
        "../abstreet", exclude_dir=[".*"], folder_only=False, check_readibility=True
    )
    ...
