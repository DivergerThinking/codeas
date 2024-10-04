import streamlit as st

from codeas.core.state import state  # Add this import
from codeas.use_cases.deployment import define_deployment, generate_deployment


def display():
    use_previous_outputs_strategy = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs_strategy"
    )

    if st.button(
        "Define deployment requirements",
        type="primary",
        key="define_deployment_strategy",
    ):
        with st.spinner("Defining deployment requirements..."):
            if use_previous_outputs_strategy:
                try:
                    previous_output = state.read_output("deployment_strategy.json")
                    st.session_state.outputs["deployment_strategy"] = type(
                        "Output",
                        (),
                        {
                            "response": {"content": previous_output["content"]},
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],  # Add this line
                        },
                    )
                except FileNotFoundError:
                    # st.warning(
                    #     "No previous output found for deployment strategy. Running generation..."
                    # )
                    st.session_state.outputs[
                        "deployment_strategy"
                    ] = define_deployment()
                    # Write the output to a file
                    state.write_output(
                        {
                            "content": st.session_state.outputs[
                                "deployment_strategy"
                            ].response["content"],
                            "cost": st.session_state.outputs[
                                "deployment_strategy"
                            ].cost,
                            "tokens": st.session_state.outputs[
                                "deployment_strategy"
                            ].tokens,
                            "messages": st.session_state.outputs[
                                "deployment_strategy"
                            ].messages,  # Add this line
                        },
                        "deployment_strategy.json",
                    )
            else:
                st.session_state.outputs["deployment_strategy"] = define_deployment()
                # Write the output to a file
                state.write_output(
                    {
                        "content": st.session_state.outputs[
                            "deployment_strategy"
                        ].response["content"],
                        "cost": st.session_state.outputs["deployment_strategy"].cost,
                        "tokens": st.session_state.outputs[
                            "deployment_strategy"
                        ].tokens,
                        "messages": st.session_state.outputs[
                            "deployment_strategy"
                        ].messages,  # Add this line
                    },
                    "deployment_strategy.json",
                )

    if st.button("Preview", key="preview_deployment_strategy"):
        preview_strategy = define_deployment(preview=True)
        with st.expander("Deployment strategy [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_strategy.cost['input_cost']:.4f} ({preview_strategy.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Messages", expanded=False):
                st.json(preview_strategy.messages)

    if "deployment_strategy" in st.session_state.outputs:
        with st.expander("Deployment strategy", expanded=True):
            output = st.session_state.outputs["deployment_strategy"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            with st.expander("Messages", expanded=False):
                st.json(output.messages)
            st.markdown(output.response["content"])

        display_generate_deployment()


def display_generate_deployment():
    use_previous_outputs_deployment = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs_deployment"
    )

    if st.button(
        "Generate Terraform code", type="primary", key="generate_terraform_code"
    ):
        with st.spinner("Generating Terraform code..."):
            deployment_strategy = st.session_state.outputs[
                "deployment_strategy"
            ].response["content"]
            if use_previous_outputs_deployment:
                try:
                    previous_output = state.read_output("terraform_code.json")
                    st.session_state.outputs["terraform_code"] = type(
                        "Output",
                        (),
                        {
                            "response": {"content": previous_output["content"]},
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],  # Add this line
                        },
                    )
                except FileNotFoundError:
                    # st.warning(
                    #     "No previous output found for Terraform code. Running generation..."
                    # )
                    st.session_state.outputs["terraform_code"] = generate_deployment(
                        deployment_strategy
                    )
                    # Write the output to a file
                    state.write_output(
                        {
                            "content": st.session_state.outputs[
                                "terraform_code"
                            ].response["content"],
                            "cost": st.session_state.outputs["terraform_code"].cost,
                            "tokens": st.session_state.outputs["terraform_code"].tokens,
                            "messages": st.session_state.outputs[
                                "terraform_code"
                            ].messages,  # Add this line
                        },
                        "terraform_code.json",
                    )
            else:
                st.session_state.outputs["terraform_code"] = generate_deployment(
                    deployment_strategy
                )
                # Write the output to a file
                state.write_output(
                    {
                        "content": st.session_state.outputs["terraform_code"].response[
                            "content"
                        ],
                        "cost": st.session_state.outputs["terraform_code"].cost,
                        "tokens": st.session_state.outputs["terraform_code"].tokens,
                        "messages": st.session_state.outputs[
                            "terraform_code"
                        ].messages,  # Add this line
                    },
                    "terraform_code.json",
                )

    if st.button("Preview", key="preview_terraform_code"):
        deployment_strategy = st.session_state.outputs["deployment_strategy"].response[
            "content"
        ]
        preview_terraform = generate_deployment(deployment_strategy, preview=True)
        with st.expander("Terraform code [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_terraform.cost['input_cost']:.4f} ({preview_terraform.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Messages", expanded=False):
                st.json(preview_terraform.messages)

    if "terraform_code" in st.session_state.outputs:
        with st.expander("Terraform code", expanded=True):
            output = st.session_state.outputs["terraform_code"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            with st.expander("Messages", expanded=False):
                st.json(output.messages)
            st.markdown(output.response["content"])
