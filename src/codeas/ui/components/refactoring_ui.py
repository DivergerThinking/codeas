import os

import pandas as pd
import streamlit as st

from codeas.core.state import state
from codeas.ui.utils import apply_diffs
from codeas.use_cases.refactoring import (
    ProposedChanges,
    RefactoringGroups,
    define_refactoring_files,
    generate_diffs,
    generate_proposed_changes,
)

USE_PREVIOUS_OUTPUTS_LABEL = "Use previous outputs"


def is_safe_path(base_dir, target_path):
    try:
        base_dir_realpath = os.path.realpath(base_dir)
        target_path_realpath = os.path.realpath(target_path)

        return target_path_realpath.startswith(base_dir_realpath + os.sep) or target_path_realpath == base_dir_realpath
    except OSError:
        return False


def display():
    use_previous_outputs_groups = st.toggle(
        USE_PREVIOUS_OUTPUTS_LABEL, value=True, key="use_previous_outputs_groups"
    )

    if st.button(
        "Identify refactoring files", type="primary", key="identify_refactoring_files"
    ):
        with st.spinner("Identifying refactoring files..."):
            if use_previous_outputs_groups:
                try:
                    previous_output = state.read_output("refactoring_groups.json")
                    st.session_state.outputs["refactoring_groups"] = type(
                        "Output",
                        (),
                        {
                            "response": type(
                                "Response",
                                (),
                                {
                                    "choices": [
                                        type(
                                            "Choice",
                                            (),
                                            {
                                                "message": type(
                                                    "Message",
                                                    (),
                                                    {
                                                        "parsed": RefactoringGroups.model_validate(
                                                            previous_output["content"]
                                                        )
                                                    },
                                                )
                                            },
                                        )
                                    ]
                                },
                            ),
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],
                        },
                    )
                except FileNotFoundError:
                    st.session_state.outputs[
                        "refactoring_groups"
                    ] = define_refactoring_files()
                    state.write_output(
                        {
                            "content": st.session_state.outputs["refactoring_groups"]
                            .response.choices[0]
                            .message.parsed.model_dump(),
                            "cost": st.session_state.outputs["refactoring_groups"].cost,
                            "tokens": st.session_state.outputs[
                                "refactoring_groups"
                            ].tokens,
                            "messages": st.session_state.outputs[
                                "refactoring_groups"
                            ].messages,
                        },
                        "refactoring_groups.json",
                    )
            else:
                st.session_state.outputs[
                    "refactoring_groups"
                ] = define_refactoring_files()
                state.write_output(
                    {
                        "content": st.session_state.outputs["refactoring_groups"]
                        .response.choices[0]
                        .message.parsed.model_dump(),
                        "cost": st.session_state.outputs["refactoring_groups"].cost,
                        "tokens": st.session_state.outputs["refactoring_groups"].tokens,
                        "messages": st.session_state.outputs[
                            "refactoring_groups"
                        ].messages,
                    },
                    "refactoring_groups.json",
                )

    if st.button("Preview", key="preview_refactoring_groups"):
        preview_groups = define_refactoring_files(preview=True)
        with st.expander("Refactoring groups [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_groups.cost['input_cost']:.4f} ({preview_groups.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Messages"):
                st.json(preview_groups.messages)

    if "refactoring_groups" in st.session_state.outputs:
        with st.expander("Refactoring groups", expanded=True):
            output = st.session_state.outputs["refactoring_groups"]
            with st.expander("Messages"):
                st.json(output.messages)
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            groups = output.response.choices[0].message.parsed

            data = [
                {
                    "selected": True,
                    "name": group.name,
                    "files_paths": group.files_paths,
                }
                for group in groups.groups
            ]

            df = pd.DataFrame(data)
            st.data_editor(
                df,
                column_config={
                    "selected": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select groups to include in refactoring",
                        default=True,
                    ),
                    "name": "Group Name",
                    "files_paths": st.column_config.Column(
                        "Files to Refactor",
                        help="Comma-separated list of files to refactor",
                        width="large",
                    ),
                },
                hide_index=True,
                disabled=True,
            )

        display_generate_proposed_changes()


def display_generate_proposed_changes():
    use_previous_outputs_changes = st.toggle(
        USE_PREVIOUS_OUTPUTS_LABEL, value=True, key="use_previous_outputs_changes"
    )

    groups = (
        st.session_state.outputs["refactoring_groups"]
        .response.choices[0]
        .message.parsed
    )
    if st.button(
        "Generate proposed changes", type="primary", key="generate_proposed_changes"
    ):
        with st.spinner("Generating proposed changes..."):
            if use_previous_outputs_changes:
                try:
                    previous_output = state.read_output("proposed_changes.json")
                    st.session_state.outputs["proposed_changes"] = type(
                        "Output",
                        (),
                        {
                            "response": {
                                group_name: type(
                                    "Response",
                                    (),
                                    {
                                        "choices": [
                                            type(
                                                "Choice",
                                                (),
                                                {
                                                    "message": type(
                                                        "Message",
                                                        (),
                                                        {
                                                            "parsed": ProposedChanges.model_validate(
                                                                changes
                                                            )
                                                        },
                                                    )
                                                },
                                            )
                                        ]
                                    },
                                )
                                for group_name, changes in previous_output[
                                    "content"
                                ].items()
                            },
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],
                        },
                    )
                except FileNotFoundError:
                    st.session_state.outputs[
                        "proposed_changes"
                    ] = generate_proposed_changes(groups)
                    state.write_output(
                        {
                            "content": {
                                group_name: response.choices[
                                    0
                                ].message.parsed.model_dump()
                                for group_name, response in st.session_state.outputs[
                                    "proposed_changes"
                                ].response.items()
                            },
                            "cost": st.session_state.outputs["proposed_changes"].cost,
                            "tokens": st.session_state.outputs[
                                "proposed_changes"
                            ].tokens,
                            "messages": st.session_state.outputs[
                                "proposed_changes"
                            ].messages,
                        },
                        "proposed_changes.json",
                    )
            else:
                st.session_state.outputs[
                    "proposed_changes"
                ] = generate_proposed_changes(groups)
                state.write_output(
                    {
                        "content": {
                            group_name: response.choices[0].message.parsed.model_dump()
                            for group_name, response in st.session_state.outputs[
                                "proposed_changes"
                            ].response.items()
                        },
                        "cost": st.session_state.outputs["proposed_changes"].cost,
                        "tokens": st.session_state.outputs["proposed_changes"].tokens,
                        "messages": st.session_state.outputs[
                            "proposed_changes"
                        ].messages,
                    },
                    "proposed_changes.json",
                )

    if st.button("Preview", key="preview_proposed_changes"):
        with st.expander("Proposed changes [Preview]", expanded=True):
            preview = generate_proposed_changes(groups, preview=True)
            st.info(
                f"Input cost: ${preview.cost['input_cost']:.4f} ({preview.tokens['input_tokens']:,} input tokens)"
            )
            for group_name, messages in preview.messages.items():
                with st.expander(f"{group_name} [Messages]"):
                    st.json(messages)

    if "proposed_changes" in st.session_state.outputs:
        with st.expander("Proposed changes", expanded=True):
            output = st.session_state.outputs["proposed_changes"]
            with st.expander("Messages"):
                st.json(output.messages)
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            for response in output.response.values():
                changes = response.choices[0].message.parsed
                for change in changes.changes:
                    with st.expander(change.file_path):
                        st.markdown(change.file_changes)

        display_apply_changes()


def display_apply_changes():
    use_previous_outputs_diffs = st.toggle(
        USE_PREVIOUS_OUTPUTS_LABEL, value=True, key="use_previous_outputs_diffs"
    )

    if st.button("Apply changes", type="primary", key="apply_changes"):
        groups_changes = [
            groups_changes.choices[0].message.parsed
            for groups_changes in st.session_state.outputs[
                "proposed_changes"
            ].response.values()
        ]
        with st.spinner("Generating and applying changes..."):
            if use_previous_outputs_diffs:
                try:
                    previous_output = state.read_output("generated_diffs.json")
                    st.session_state.outputs["generated_diffs"] = type(
                        "Output",
                        (),
                        {
                            "response": previous_output["content"],
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],
                        },
                    )
                except FileNotFoundError:
                    st.session_state.outputs["generated_diffs"] = generate_diffs(
                        groups_changes
                    )
                    state.write_output(
                        {
                            "content": st.session_state.outputs[
                                "generated_diffs"
                            ].response,
                            "cost": st.session_state.outputs["generated_diffs"].cost,
                            "tokens": st.session_state.outputs[
                                "generated_diffs"
                            ].tokens,
                            "messages": st.session_state.outputs[
                                "generated_diffs"
                            ].messages,
                        },
                        "generated_diffs.json",
                    )
            else:
                st.session_state.outputs["generated_diffs"] = generate_diffs(
                    groups_changes
                )
                state.write_output(
                    {
                        "content": st.session_state.outputs["generated_diffs"].response,
                        "cost": st.session_state.outputs["generated_diffs"].cost,
                        "tokens": st.session_state.outputs["generated_diffs"].tokens,
                        "messages": st.session_state.outputs[
                            "generated_diffs"
                        ].messages,
                    },
                    "generated_diffs.json",
                )

            generated_diffs_output = st.session_state.outputs["generated_diffs"]

            project_root = os.getcwd()

            for file_path, response in generated_diffs_output.response.items():
                if not is_safe_path(project_root, file_path):
                    st.error(f"Error: Original file path '{file_path}' from generated changes is outside project root. Skipping.")
                    continue

                directory, filename = os.path.split(file_path)
                name, ext = os.path.splitext(filename)
                new_file_path = os.path.join(directory, f"{name}_refactored{ext}")

                if not is_safe_path(project_root, new_file_path):
                     st.error(f"Error: Generated refactored path '{new_file_path}' is outside project root. Skipping.")
                     continue

                new_file_dir = os.path.dirname(new_file_path)
                if not is_safe_path(project_root, new_file_dir):
                     st.error(f"Error: Directory for refactored file '{new_file_dir}' is outside project root. Skipping.")
                     continue
                if not os.path.exists(new_file_dir):
                    try:
                        os.makedirs(new_file_dir, exist_ok=True)
                    except OSError as e:
                         st.error(f"Error creating directory '{new_file_dir}': {e}. Skipping.")
                         continue

                original_content = None
                try:
                    with open(file_path, "r") as f:
                        original_content = f.read()
                except OSError as e:
                    st.error(f"Error reading original file '{file_path}': {e}. Skipping.")
                    continue

                if original_content is None:
                    continue

                diff = (
                    f"```diff\n{response['content']}\n```"
                    if not response["content"].startswith("```diff")
                    else response["content"]
                )

                try:
                    patched_content = apply_diffs(original_content, diff)
                except Exception:
                    st.error(f"Error applying diff to {file_path}. Skipping.")
                    continue

                try:
                    with open(new_file_path, "w") as f:
                        f.write(patched_content)
                except OSError as e:
                     st.error(f"Error writing refactored file '{new_file_path}': {e}. Skipping.")
                     continue


                st.success(f"{new_file_path} successfully written!")
                with st.expander(f"Generated changes [{file_path}]"):
                    st.code(diff)