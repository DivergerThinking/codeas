import streamlit as st

from codeas.core.state import state  # Add this import
from codeas.use_cases.architecture import (
    generate_c4_diagrams,
    identify_c4_components_and_containers,
)


def display():
    use_previous_outputs = st.toggle(
        "Use previous outputs", value=True, key="use_previous_outputs_c4_model"
    )

    if st.button("Define C4 Model", type="primary"):
        with st.spinner("Defining C4 Model..."):
            if use_previous_outputs:
                try:
                    previous_output = state.read_output("c4_model.json")
                    st.session_state.outputs["c4_model"] = type(
                        "Output",
                        (),
                        {
                            "response": {"content": previous_output["content"]},
                            "cost": previous_output["cost"],
                            "tokens": previous_output["tokens"],
                            "messages": previous_output["messages"],
                        },
                    )
                except FileNotFoundError:
                    st.session_state.outputs[
                        "c4_model"
                    ] = identify_c4_components_and_containers()
                    state.write_output(
                        {
                            "content": st.session_state.outputs["c4_model"].response[
                                "content"
                            ],
                            "cost": st.session_state.outputs["c4_model"].cost,
                            "tokens": st.session_state.outputs["c4_model"].tokens,
                            "messages": st.session_state.outputs["c4_model"].messages,
                        },
                        "c4_model.json",
                    )
            else:
                st.session_state.outputs[
                    "c4_model"
                ] = identify_c4_components_and_containers()
                state.write_output(
                    {
                        "content": st.session_state.outputs["c4_model"].response[
                            "content"
                        ],
                        "cost": st.session_state.outputs["c4_model"].cost,
                        "tokens": st.session_state.outputs["c4_model"].tokens,
                        "messages": st.session_state.outputs["c4_model"].messages,
                    },
                    "c4_model.json",
                )

    if st.button("Preview"):
        with st.spinner("Previewing generation..."):
            preview_output = identify_c4_components_and_containers(preview=True)
        with st.expander("C4 Model [Preview]", expanded=True):
            st.info(
                f"Input cost: ${preview_output.cost['input_cost']:.4f} ({preview_output.tokens['input_tokens']:,} input tokens)"
            )
            with st.expander("Messages", expanded=False):
                st.json(preview_output.messages)

    if "c4_model" in st.session_state.outputs:
        if st.button("Generate C4 Diagrams"):
            with st.spinner("Generating C4 Diagrams..."):
                c4_model_content = st.session_state.outputs["c4_model"].response[
                    "content"
                ]
                diagrams_output = generate_c4_diagrams(c4_model_content)

                st.session_state.outputs["c4_diagrams"] = diagrams_output
                state.write_output(
                    {
                        "content": diagrams_output.response["content"],
                        "cost": diagrams_output.cost,
                        "tokens": diagrams_output.tokens,
                        "messages": diagrams_output.messages,
                    },
                    "c4_diagrams.json",
                )
        if st.button("Preview C4 Diagrams"):
            with st.spinner("Previewing C4 Diagrams generation..."):
                c4_model_content = st.session_state.outputs["c4_model"].response[
                    "content"
                ]
                preview_output = generate_c4_diagrams(c4_model_content, preview=True)
            with st.expander("C4 Diagrams [Preview]", expanded=True):
                st.info(
                    f"Input cost: ${preview_output.cost['input_cost']:.4f} ({preview_output.tokens['input_tokens']:,} input tokens)"
                )
                with st.expander("Messages", expanded=False):
                    st.json(preview_output.messages)

    if "c4_diagrams" in st.session_state.outputs:
        with st.expander("C4 Diagrams", expanded=True):
            st.markdown(st.session_state.outputs["c4_diagrams"].response["content"])
            st.info(
                f"Total cost: ${st.session_state.outputs['c4_diagrams'].cost['total_cost']:.4f} "
                f"({st.session_state.outputs['c4_diagrams'].tokens['total_tokens']:,} tokens)"
            )
