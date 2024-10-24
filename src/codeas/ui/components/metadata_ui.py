import streamlit as st

from codeas.core.state import state


def display():
    files_missing_metadata = [
        f
        for f in state.repo.included_files_paths
        if f not in state.repo_metadata.files_usage
    ]
    if len(files_missing_metadata) > 0:
        st.warning(f"{len(files_missing_metadata)} files are missing metadata")
        st.dataframe(
            {"Missing metadata": files_missing_metadata},
            use_container_width=True,
            height=300,
        )
        display_generate_missing_metadata(files_missing_metadata)
    return files_missing_metadata


def display_generate_missing_metadata(files_missing_metadata):
    if st.button("Generate Missing Metadata", type="primary"):
        with st.spinner("Generating missing metadata..."):
            state.repo_metadata.generate_missing_repo_metadata(
                state.llm_client, state.repo, files_missing_metadata
            )
            state.repo_metadata.export_metadata(state.repo_path)
        st.success("Missing metadata generated and exported successfully!")
        st.rerun()

    if st.button("Estimate cost", key="estimate_missing_metadata"):
        with st.spinner("Estimating cost..."):
            preview = state.repo_metadata.generate_missing_repo_metadata(
                state.llm_client, state.repo, files_missing_metadata, preview=True
            )
            input_cost = preview.cost["input_cost"]
            input_tokens = preview.tokens["input_tokens"]
            estimated_cost = input_cost * 3
            estimated_input_tokens = input_tokens * 2
            estimated_output_tokens = input_tokens // 3
            st.caption(
                f"Estimated cost: ${estimated_cost:.4f} (input tokens: {estimated_input_tokens:,} + output tokens: {estimated_output_tokens:,})"
            )
