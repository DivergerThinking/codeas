from codeas.core.state import state


def find_overlapping_files():
    selected_repo_files = state.repo.get_file_paths()
    files_with_embeddings = state.storage.fetch_files_in_chromadb(state.repo_path)
    files_overlapping = [
        filepath
        for filepath in selected_repo_files
        if filepath in files_with_embeddings
    ]
    files_missing_embeddings = [
        filepath
        for filepath in selected_repo_files
        if filepath not in files_with_embeddings
    ]
    additional_files_with_embeddings = [
        filepath
        for filepath in files_with_embeddings
        if filepath not in selected_repo_files
    ]
    return files_overlapping, files_missing_embeddings, additional_files_with_embeddings
