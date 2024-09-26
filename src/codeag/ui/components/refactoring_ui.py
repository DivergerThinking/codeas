import os

import streamlit as st

from codeag.ui.utils import apply_diffs
from codeag.use_cases.refactoring import (
    define_refactoring_files,
    generate_diffs,
    generate_proposed_changes,
)


def display():
    if st.button("Define refactoring groups", type="primary"):
        with st.spinner("Defining refactoring groups..."):
            st.session_state.outputs["refactoring_groups"] = define_refactoring_files()

    if st.button("Preview"):
        preview_groups = define_refactoring_files(preview=True)
        with st.expander("Refactoring groups [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_groups.cost['input_cost']:.4f} ({preview_groups.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Context"):
                st.code(preview_groups.messages[0]["content"], language="markdown")

    if "refactoring_groups" in st.session_state.outputs:
        with st.expander("Refactoring groups", expanded=True):
            output = st.session_state.outputs["refactoring_groups"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            groups = output.response.choices[0].message.parsed

            for i, group in enumerate(groups.groups):
                col1, col2 = st.columns([0.95, 0.05])
                with col1:
                    with st.expander(f"{group.name}"):
                        st.write("**Files to be refactored:**")
                        st.json(group.files_paths)
                with col2:
                    st.button(
                        "🗑️",
                        key=f"delete_group_{i}",
                        type="primary",
                        on_click=remove_group,
                        args=(i,),
                    )

        display_generate_proposed_changes()


def remove_group(i):
    groups = (
        st.session_state.outputs["refactoring_groups"]
        .response.choices[0]
        .message.parsed
    )
    del groups.groups[i]
    st.session_state.outputs["refactoring_groups"].response.choices[
        0
    ].message.parsed = groups


def display_generate_proposed_changes():
    groups = (
        st.session_state.outputs["refactoring_groups"]
        .response.choices[0]
        .message.parsed
    )
    if st.button("Generate proposed changes", type="primary"):
        with st.spinner("Generating proposed changes..."):
            st.session_state.outputs["proposed_changes"] = generate_proposed_changes(
                groups
            )

    if st.button("Preview", key="preview_proposed_changes"):
        with st.expander("Proposed changes [Preview]", expanded=True):
            preview = generate_proposed_changes(groups, preview=True)
            st.info(
                f"Input cost: ${preview.cost['input_cost']:.4f} ({preview.tokens['input_tokens']:,} input tokens)"
            )
            for group_name, messages in preview.messages.items():
                with st.expander(f"Context [{group_name}]"):
                    st.code(messages[0]["content"], language="markdown")

    if "proposed_changes" in st.session_state.outputs:
        with st.expander("Proposed changes", expanded=True):
            output = st.session_state.outputs["proposed_changes"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            for group_name, response in output.response.items():
                with st.expander(f"{group_name}"):
                    changes = response.choices[0].message.parsed
                    for change in changes.changes:
                        with st.expander(f"File: {change.file_path}"):
                            st.markdown(change.file_changes)

        display_generate_diffs()


def display_generate_diffs():
    if st.button("Generate diffs", type="primary"):
        groups_changes = [
            groups_changes.choices[0].message.parsed
            for groups_changes in st.session_state.outputs[
                "proposed_changes"
            ].response.values()
        ]
        with st.spinner("Generating diffs..."):
            st.session_state.outputs["generated_diffs"] = generate_diffs(groups_changes)

    if "generated_diffs" in st.session_state.outputs:
        with st.expander("Generated diffs", expanded=True):
            output = st.session_state.outputs["generated_diffs"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )

            for file_path, response in output.response.items():
                with st.expander(f"Diff for file: {file_path}"):
                    st.code(response["content"])

        display_apply_diffs()


def display_apply_diffs():
    if st.button("Apply diffs", type="primary"):
        generated_diffs_output = st.session_state.outputs["generated_diffs"]

        for file_path, response in generated_diffs_output.response.items():
            # Split the file path into directory, filename, and extension
            directory, filename = os.path.split(file_path)
            name, ext = os.path.splitext(filename)

            # Create the new file path with "_refactored" added
            new_file_path = os.path.join(directory, f"{name}_refactored{ext}")

            # Read the original file content
            with open(file_path, "r") as f:
                original_content = f.read()

            # Apply the diff to the original content
            diff = (
                f"```diff\n{response['content']}\n```"
                if not response["content"].startswith("```diff")
                else response["content"]
            )

            try:
                patched_content = apply_diffs(original_content, diff)
            except Exception as e:
                st.error(f"Error applying diff to {file_path}: {e}")
                continue

            # Write the patched content to the new file
            if not os.path.exists(os.path.dirname(new_file_path)):
                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
            with open(new_file_path, "w") as f:
                f.write(patched_content)

            st.success(f"{new_file_path} successfully written!")
