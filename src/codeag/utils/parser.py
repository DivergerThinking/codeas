import copy
import os
from glob import glob


def match_path(path: str, pattern: str) -> bool:
    """
    Check if a path matches the given pattern.

    If pattern includes '*', use startswith() for the part before '*'.
    Otherwise, check if the path starts with the pattern (for subdirectory support).
    """
    if pattern.endswith("/"):
        pattern = pattern[:-1]  # remove trailing slash

    if pattern.startswith("*") and pattern.endswith("*"):
        return pattern[1:-1] in path
    elif pattern.endswith("*"):
        prefix = pattern.split("*")[0]
        return path.startswith(prefix)
    elif pattern.startswith("*"):
        suffix = pattern.split("*")[1]
        return path.endswith(suffix)
    else:
        return path == pattern or path.startswith(pattern + os.path.sep)


def filter_files(
    files_tokens, include_dir=[], exclude_dir=[], include_files=[], exclude_files=[]
):
    included_files = copy.deepcopy(files_tokens)
    excluded_files = {}
    for path, tokens in files_tokens.items():
        dir_path, file_name = os.path.split(path)

        if any(include_files) and not any(
            match_path(path, pattern) for pattern in include_files
        ):
            excluded_files[path] = included_files.pop(path)
            continue

        if any(exclude_files) and any(
            match_path(path, pattern) for pattern in exclude_files
        ):
            excluded_files[path] = included_files.pop(path)
            continue

        if any(include_dir) and not any(
            match_path(dir_path, pattern) for pattern in include_dir
        ):
            excluded_files[path] = included_files.pop(path)
            continue

        if any(exclude_dir) and any(
            match_path(dir_path, pattern) for pattern in exclude_dir
        ):
            excluded_files[path] = included_files.pop(path)
            continue

        if tokens is None or tokens == 0:
            excluded_files[path] = included_files.pop(path)

    return included_files, excluded_files


def estimate_tokens_from_files(repo_path, file_paths):
    files_tokens = {}
    for path in file_paths:
        rel_path = os.path.relpath(path, repo_path)
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    files_tokens[rel_path] = int(len(f.read()) / 4)
            except Exception:
                files_tokens[rel_path] = None
    return files_tokens


def list_files(repo_path: str):
    return glob(os.path.join(f"{repo_path}", "**"), recursive=True)


def extract_folders_up_to_level(repo_path, files_tokens, max_level, as_lists=True):
    folders = {}
    for path, n_tokens in files_tokens.items():
        parts = os.path.normpath(path).split(os.sep)
        for level in range(1, min(len(parts), max_level) + 1):
            folder = os.sep.join(parts[:level])
            full_folder_path = os.path.join(repo_path, folder)
            if os.path.isdir(full_folder_path):
                if folder not in folders:
                    folders[folder] = {"n_files": 0, "n_tokens": 0}
                folders[folder]["n_files"] += 1
                folders[folder]["n_tokens"] += n_tokens if n_tokens else 0

    sorted_folders = dict(sorted(folders.items()))

    if as_lists:
        paths = list(sorted_folders.keys())
        n_files = [folder_info["n_files"] for folder_info in sorted_folders.values()]
        n_tokens = [folder_info["n_tokens"] for folder_info in sorted_folders.values()]
        return paths, n_files, n_tokens
    else:
        return sorted_folders


if __name__ == "__main__":
    # dir_paths = get_repository_paths(
    #     "../abstreet", exclude_dir=[".*"], folder_only=True
    # )
    repo_path = "."
    file_paths = list_files(repo_path)
    file_tokens = estimate_tokens_from_files(repo_path, file_paths)
    included_files, excluded_files = filter_files(
        file_tokens, include_dir=[], exclude_dir=[], include_files=[], exclude_files=[]
    )
    folders = extract_folders_up_to_level("../abstreet", included_files, 1, True)
    print(folders)
