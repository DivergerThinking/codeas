import os
import re

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

    if st.button(
        "Define testing strategy", type="primary", key="define_testing_strategy"
    ):
        with st.spinner("Defining testing strategy..."):
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
                        },
                    )
                except FileNotFoundError:
                    st.warning(
                        "No previous output found for testing strategy. Running generation..."
                    )
                    st.session_state.outputs[
                        "testing_strategy"
                    ] = define_testing_strategy(
                        state.llm_client, state.repo, state.repo_metadata
                    )
                    # Write the output to a file
                    state.write_output(
                        {
                            "content": st.session_state.outputs["testing_strategy"]
                            .response.choices[0]
                            .message.parsed.model_dump(),
                            "cost": st.session_state.outputs["testing_strategy"].cost,
                            "tokens": st.session_state.outputs[
                                "testing_strategy"
                            ].tokens,
                        },
                        "testing_strategy.json",
                    )
            else:
                st.session_state.outputs["testing_strategy"] = define_testing_strategy(
                    state.llm_client, state.repo, state.repo_metadata
                )
                # Write the output to a file
                state.write_output(
                    {
                        "content": st.session_state.outputs["testing_strategy"]
                        .response.choices[0]
                        .message.parsed.dict(),
                        "cost": st.session_state.outputs["testing_strategy"].cost,
                        "tokens": st.session_state.outputs["testing_strategy"].tokens,
                    },
                    "testing_strategy.json",
                )

    if st.button("Preview", key="preview_testing_strategy"):
        preview_strategy = define_testing_strategy(
            state.llm_client, state.repo, state.repo_metadata, preview=True
        )
        with st.expander("Testing strategy [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_strategy.cost['input_cost']:.4f} ({preview_strategy.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Context"):
                st.code(preview_strategy.messages[0]["content"], language="markdown")

    if "testing_strategy" in st.session_state.outputs:
        with st.expander("Testing strategy", expanded=True):
            output = st.session_state.outputs["testing_strategy"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            strategy = output.response.choices[0].message.parsed

            for i, step in enumerate(strategy.strategy):
                col1, col2 = st.columns([0.95, 0.05])
                with col1:
                    with st.expander(f"{step.test_file_path} [{step.type_of_test}]"):
                        st.write("**Guidelines:**")
                        st.code(step.guidelines, language="markdown")
                        st.write("**Files to be tested:**")
                        st.json(step.files_paths)
                with col2:
                    st.button(
                        "🗑️",
                        key=f"delete_step_{i}",
                        type="primary",
                        on_click=remove_step,
                        args=(i,),
                    )

        display_generate_tests()


def remove_step(i):
    strategy = (
        st.session_state.outputs["testing_strategy"].response.choices[0].message.parsed
    )
    del strategy.strategy[i]
    st.session_state.outputs["testing_strategy"].response.choices[
        0
    ].message.parsed = strategy


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
                        },
                    )
                except FileNotFoundError:
                    st.warning(
                        "No previous output found for generated tests. Running generation..."
                    )
                    st.session_state.outputs["tests"] = generate_tests_from_strategy(
                        state.llm_client, strategy
                    )
                    # Write the output to a file
                    state.write_output(
                        {
                            "content": st.session_state.outputs["tests"].response,
                            "cost": st.session_state.outputs["tests"].cost,
                            "tokens": st.session_state.outputs["tests"].tokens,
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
                with st.expander(f"Context [{path}]"):
                    st.code(messages[0]["content"], language="markdown")

    if "tests" in st.session_state.outputs:
        with st.expander("Tests", expanded=True):
            output = st.session_state.outputs["tests"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            for path, response in output.response.items():
                with st.expander(f"Context [{path}]"):
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
