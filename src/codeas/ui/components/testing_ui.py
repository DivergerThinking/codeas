import os
import re

import pandas as pd
import streamlit as st

from codeas.core.state import state
from codeas.use_cases.testing import (
    TestingStrategy,
    define_testing_strategy,
    generate_tests_from_strategy,
)


def display():
    use_previous_outputs_strategy = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs_strategy"
    )

    if st.button("Define test suite", type="primary", key="define_testing_strategy"):
        with st.spinner("Defining test suite..."):
            if use_previous_outputs_strategy:
                try:
                    previous_output = state.read_output("testing_strategy.json")
                    st.session_state.outputs["testing_strategy"] = type(
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
                                                        "parsed": TestingStrategy.model_validate(
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
                            "messages": previous_output["messages"],  # Add this line
                        },
                    )
                except FileNotFoundError:
                    # st.warning(
                    #     "No previous output found for testing strategy. Running generation..."
                    # )
                    st.session_state.outputs[
                        "testing_strategy"
                    ] = define_testing_strategy(
                        state.llm_client, state.repo, state.repo_metadata
                    )
                    state.write_output(
                        {
                            "content": st.session_state.outputs["testing_strategy"]
                            .response.choices[0]
                            .message.parsed.model_dump(),
                            "cost": st.session_state.outputs["testing_strategy"].cost,
                            "tokens": st.session_state.outputs[
                                "testing_strategy"
                            ].tokens,
                            "messages": st.session_state.outputs[
                                "testing_strategy"
                            ].messages,  # Add this line
                        },
                        "testing_strategy.json",
                    )
            else:
                st.session_state.outputs["testing_strategy"] = define_testing_strategy(
                    state.llm_client, state.repo, state.repo_metadata
                )
                state.write_output(
                    {
                        "content": st.session_state.outputs["testing_strategy"]
                        .response.choices[0]
                        .message.parsed.dict(),
                        "cost": st.session_state.outputs["testing_strategy"].cost,
                        "tokens": st.session_state.outputs["testing_strategy"].tokens,
                        "messages": st.session_state.outputs[
                            "testing_strategy"
                        ].messages,  # Add this line
                    },
                    "testing_strategy.json",
                )

    if st.button("Preview", key="preview_testing_strategy"):
        preview_strategy = define_testing_strategy(
            state.llm_client, state.repo, state.repo_metadata, preview=True
        )
        with st.expander("Testing strategy", expanded=True):
            st.info(
                f"Input cost: ${preview_strategy.cost['input_cost']:.4f} ({preview_strategy.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Messages"):
                st.json(preview_strategy.messages)

    if "testing_strategy" in st.session_state.outputs:
        with st.expander("Testing strategy", expanded=True):
            output = st.session_state.outputs["testing_strategy"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            with st.expander("Messages"):
                st.json(output.messages)
            strategy = output.response.choices[0].message.parsed

            # Create a DataFrame for the data editor
            data = [
                {
                    "selected": True,
                    "type_of_test": step.type_of_test,
                    "files_to_test": step.files_paths,
                    "test_file_path": step.test_file_path,
                    "guidelines": step.guidelines,
                }
                for step in strategy.strategy
            ]

            df = pd.DataFrame(data)
            st.data_editor(
                df,
                column_config={
                    "selected": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select steps to include in test generation",
                        default=True,
                    ),
                    "type_of_test": "Type of Test",
                    "test_file_path": "Output Path",
                    "files_to_test": "Files to Test",
                    "guidelines": st.column_config.Column(
                        "Guidelines",
                        help="Click to view guidelines",
                        width="medium",
                    ),
                },
                hide_index=True,
                disabled=True,
            )

        display_generate_tests()


def display_generate_tests():
    use_previous_outputs_tests = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs_tests"
    )

    strategy = (
        st.session_state.outputs["testing_strategy"].response.choices[0].message.parsed
    )

    if st.button("Generate tests", type="primary", key="generate_tests"):
        with st.spinner("Generating tests..."):
            if use_previous_outputs_tests:
                try:
                    previous_output = state.read_output("generated_tests.json")
                    st.session_state.outputs["tests"] = type(
                        "Output",
                        (),
                        {
                            "response": previous_output["content"],
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],  # Add this line
                        },
                    )
                except FileNotFoundError:
                    # st.warning(
                    #     "No previous output found for generated tests. Running generation..."
                    # )
                    st.session_state.outputs["tests"] = generate_tests_from_strategy(
                        state.llm_client, strategy
                    )
                    # Write the output to a file
                    state.write_output(
                        {
                            "content": st.session_state.outputs["tests"].response,
                            "cost": st.session_state.outputs["tests"].cost,
                            "tokens": st.session_state.outputs["tests"].tokens,
                            "messages": st.session_state.outputs[
                                "tests"
                            ].messages,  # Add this line
                        },
                        "generated_tests.json",
                    )
            else:
                st.session_state.outputs["tests"] = generate_tests_from_strategy(
                    state.llm_client, strategy
                )
                # Write the output to a file
                state.write_output(
                    {
                        "content": st.session_state.outputs["tests"].response,
                        "cost": st.session_state.outputs["tests"].cost,
                        "tokens": st.session_state.outputs["tests"].tokens,
                        "messages": st.session_state.outputs[
                            "tests"
                        ].messages,  # Add this line
                    },
                    "generated_tests.json",
                )

    if st.button("Preview", key="preview_tests"):
        with st.expander("Tests [Preview]", expanded=True):
            preview = generate_tests_from_strategy(
                state.llm_client, strategy, preview=True
            )
            st.info(
                f"Input cost: ${preview.cost['input_cost']:.4f} ({preview.tokens['input_tokens']:,} input tokens)"
            )
            for path, messages in preview.messages.items():
                with st.expander(f"{path} [Messages]"):
                    st.json(messages)

    if "tests" in st.session_state.outputs:
        with st.expander("Tests", expanded=True):
            output = st.session_state.outputs["tests"]
            with st.expander("Messages"):
                st.json(output.messages)
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            for path, response in output.response.items():
                with st.expander(path):
                    st.markdown(response["content"])

        display_write_tests()


def display_write_tests():
    if st.button("Write tests", type="primary", key="write_tests"):
        for path, response in st.session_state.outputs["tests"].response.items():
            code = parse_code_blocks(response["content"])
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(code)
            st.success(f"{path} successfully written!")


def parse_code_blocks(markdown_content):
    # Regular expression to match code blocks
    code_block_pattern = r"```[\w\-+]*\n([\s\S]*?)\n```"
    code_blocks = re.findall(code_block_pattern, markdown_content)
    return "\n\n".join(code_blocks)
