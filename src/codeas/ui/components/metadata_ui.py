import streamlit as st

from codeas.ui.state import state


def display():
    st.subheader("Metadata")

    # Display number of files with generated metadata
    files_with_metadata = [
        f
        for f in state.repo.included_files_paths
        if f in state.repo_metadata.files_usage
    ]
    files_missing_metadata = [
        f
        for f in state.repo.included_files_paths
        if f not in state.repo_metadata.files_usage
    ]

    with st.expander("Metadata"):
        st.write("Files missing metadata")
        st.json(files_missing_metadata, expanded=False)

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

        st.write("Metadata")
        st.json(state.repo_metadata.model_dump(), expanded=False)

        if st.button("Update metadata"):
            with st.spinner("Generating metadata..."):
                state.repo_metadata.generate_repo_metadata(
                    state.llm_client, state.repo, state.repo.included_files_paths
                )
                state.repo_metadata.export_metadata(state.repo_path)
            st.success("Metadata updated!")
            st.rerun()

        if st.button("Estimate cost", key="estimate_update_metadata"):
            with st.spinner("Estimating cost..."):
                preview = state.repo_metadata.generate_repo_metadata(
                    state.llm_client,
                    state.repo,
                    state.repo.included_files_paths,
                    preview=True,
                )
                input_cost = preview.cost["input_cost"]
                input_tokens = preview.tokens["input_tokens"]
                estimated_cost = input_cost * 3
                estimated_input_tokens = input_tokens * 2
                estimated_output_tokens = input_tokens // 3
                st.caption(
                    f"Estimated cost: ${estimated_cost:.4f} (input tokens: {estimated_input_tokens:,} + output tokens: {estimated_output_tokens:,})"
                )

        st.caption("This will re-generate metadata for all selected files")

    st.info(
        f"{len(files_with_metadata)}/{len(state.repo.included_files_paths)} selected files have metadata"
    )
