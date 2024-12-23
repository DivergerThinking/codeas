import streamlit as st

from codeas.core import core
from codeas.core.state import state
from codeas.ui.components import repo_ui
from codeas.ui.components.shared import find_overlapping_files


def repo_page():
    st.subheader("📚 Embeddings")
    repo_ui.display_repo_path()
    display_files()
    display_files_in_collection()


def display_files():
    state.load_page_filters()
    state.apply_filters()
    repo_ui.display_files()


def display_files_in_collection():
    filepaths = state.storage.fetch_files_in_chromadb(state.repo_path)
    if not any(filepaths):
        st.info("No embeddings found in this collection. Generate embeddings.")
        display_generate_embeddings()
    else:
        (
            files_overlapping,
            files_missing_embeddings,
            additional_files_with_embeddings,
        ) = find_overlapping_files()
        st.info(
            f"{len(files_overlapping)}/{len(state.repo.get_file_paths())} files with embeddings."
        )
        if any(files_missing_embeddings):
            st.warning(
                f"{len(files_missing_embeddings)} files missing embeddings. Generate missing embeddings."
            )
            display_generate_embeddings(files_missing_embeddings)
        if any(additional_files_with_embeddings):
            st.error(
                f"{len(additional_files_with_embeddings)} files with embeddings not found in selected files. Update collection."
            )
            display_update_collection(additional_files_with_embeddings)


def display_generate_embeddings(file_paths: list[str] = []):
    if st.button("Generate embeddings", type="primary"):
        with st.spinner("Generating embeddings..."):
            output = core.generate_file_infos(state.repo.get_file_contents(file_paths))
            file_infos = output.response
            embeddings = core.vectorize_files_infos(file_infos)
            state.storage.store_file_infos_in_chromadb(
                repo_path=state.repo_path,
                file_infos=file_infos,
                embeddings=embeddings,
            )
            state.storage.store_file_infos_in_tinydb(
                repo_path=state.repo_path,
                file_infos=file_infos,
            )
            st.rerun()


def display_update_collection(filepaths: list[str]):
    if st.button("Update collection", type="primary"):
        state.storage.update_collection(state.repo_path, filepaths)
        st.write("Collection updated")
        # st.rerun()


repo_page()
