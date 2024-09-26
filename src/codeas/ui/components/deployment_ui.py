import streamlit as st

from codeas.use_cases.deployment import define_deployment, generate_deployment


def display():
    if st.button("Define deployment strategy", type="primary"):
        with st.spinner("Defining deployment strategy..."):
            st.session_state.outputs["deployment_strategy"] = define_deployment()

    if st.button("Preview"):
        preview_strategy = define_deployment(preview=True)
        with st.expander("Deployment strategy [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_strategy.cost['input_cost']:.4f} ({preview_strategy.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Context"):
                st.code(preview_strategy.messages[0]["content"], language="markdown")

    if "deployment_strategy" in st.session_state.outputs:
        with st.expander("Deployment strategy", expanded=True):
            output = st.session_state.outputs["deployment_strategy"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            st.markdown(output.response["content"])

        display_generate_deployment()


def display_generate_deployment():
    if st.button("Generate Terraform code", type="primary"):
        with st.spinner("Generating Terraform code..."):
            deployment_strategy = st.session_state.outputs[
                "deployment_strategy"
            ].response["content"]
            st.session_state.outputs["terraform_code"] = generate_deployment(
                deployment_strategy
            )

    if st.button("Preview"):
        deployment_strategy = st.session_state.outputs["deployment_strategy"].response[
            "content"
        ]
        preview_terraform = generate_deployment(deployment_strategy, preview=True)
        with st.expander("Terraform code [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_terraform.cost['input_cost']:.4f} ({preview_terraform.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Context"):
                st.code(preview_terraform.messages[0]["content"], language="markdown")

    if "terraform_code" in st.session_state.outputs:
        with st.expander("Terraform code", expanded=True):
            output = st.session_state.outputs["terraform_code"]
            st.info(
                f"Total cost: ${output.cost['total_cost']:.4f} "
                f"(input tokens: {output.tokens['input_tokens']:,}, "
                f"output tokens: {output.tokens['output_tokens']:,})"
            )
            st.markdown(output.response["content"])
