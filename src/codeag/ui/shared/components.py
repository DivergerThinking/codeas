import streamlit as st

from codeag.ui.shared.state import state


def display_button(label, key, type="primary"):
    st.button(
        label,
        type=type,
        key=key,
        on_click=lambda: state.clicked(key),
    )


def display_chain(chain_name, label, steps, output_func):
    display_button(label, chain_name)
    # display_input_cost("extract_files_info")
    if state.is_clicked(chain_name):
        for step in steps:
            with st.spinner(f"Running {step}..."):
                state.unclicked(step)
                state.orchestrator.run(step)

    display_button("Preview", f"preview_{chain_name}", "secondary")
    if state.is_clicked(f"preview_{chain_name}"):
        with st.expander("Preview", expanded=True):
            for i, step in enumerate(steps):
                st.markdown(f"**Step {i+1}:** {step}")
                # try:
                preview = state.orchestrator.preview(step)
                st.json(preview, expanded=False)
                # except Exception as e:
                #     st.warning(f"Can't preview '{step}' until previous steps are run.")
                #     logging.error(e)
    with st.expander("Output"):
        output_func()
        # display_output_cost("extract_files_info")


def display_agent(agent_name, label, output_func):
    display_button(label, agent_name)
    # display_input_cost("extract_files_info")
    if state.is_clicked(agent_name):
        with st.spinner(f"Running {agent_name}..."):
            state.unclicked(agent_name)
            state.orchestrator.run(agent_name)

    display_button("Preview", f"preview_{agent_name}", "secondary")
    if state.is_clicked(f"preview_{agent_name}"):
        preview = state.orchestrator.preview(agent_name)
        with st.expander("Preview", expanded=True):
            st.json(preview, expanded=False)

    with st.expander("Output"):
        if not state.orchestrator.exist_output(agent_name):
            st.error("No output found.")
        else:
            output = state.orchestrator.read_output(agent_name)
            output_func(output)
            # display_output_cost("extract_files_info")


# def display_extract_files_info():
#     display_info("Files", "extract_files_info", "preview_extract_files_info")

# def display_extract_folders_info():
#     display_info("Folders", "extract_folders_info", "preview_extract_folders_info")

# def display_agent(agent_name):
#     display_run_button(agent_name)
#     display_outputs(agent_name)

# def display_run_button(agent_name):
#     st.button(
#         "Run",
#         type="primary",
#         key=f"run_{agent_name}",
#         on_click=lambda: state.clicked(f"run_{agent_name}"),
#     )

# def display_outputs(agent_name):
#     with st.expander("Outputs"):
#         if not state.orchestrator.exist_output(agent_name):
#             st.error("No output found.")
#         else:
#             output = state.orchestrator.read_output(agent_name)
#             if isinstance


# def run_agent(agent_name, spinner_text):
#     with st.spinner(spinner_text):

#         else:
#             return state.orchestrator.run(agent_name, write_output=True)


# def display_command(command_name: str):
#     label = command_name.replace("_", " ").title()

#     with st.expander(label):
#         display_command_configs(command_name)
#         display_run_button(command_name)
#         display_estimate_button(command_name)

#         if state.clicked.get(f"estimate_{command_name}"):
#             st.divider()
#             display_estimates(command_name)

#         if state.clicked.get(f"run_{command_name}"):
#             st.divider()

#             if state.clicked.get(f"rerun_{command_name}"):
#                 outputs = run_command(command_name)
#                 display_outputs(command_name, outputs)
#                 state.clicked[f"rerun_{command_name}"] = False

#             elif state.orchestrator.exists_output(command_name):
#                 outputs = state.orchestrator.read(command_name)
#                 display_outputs(command_name, outputs)
#                 st.info("Using stored outputs.")
#                 display_rerun_button(command_name)

#             else:
#                 outputs = run_command(command_name)
#                 display_outputs(command_name, outputs)


def run_command(command_name: str):
    with st.spinner(f"Running '{command_name}'..."):
        outputs = state.orchestrator.run(command_name)
        state.orchestrator.write(command_name, outputs)
    return outputs


def display_command_configs(command_name: str):
    with st.expander("Configs", expanded=False):
        st.json(state.orchestrator.COMMAND_ARGS[command_name].dict())


# def display_rerun_button(command_name):
#     st.button(
#         "Rerun",
#         type="primary",
#         key=f"rerun_{command_name}",
#         on_click=lambda: clicked(f"rerun_{command_name}"),
#     )


# def display_estimate_button(command_name):
#     st.button(
#         "Estimate",
#         type="secondary",
#         key=f"estimate_{command_name}",
#         on_click=lambda: clicked(f"estimate_{command_name}"),
#     )


def display_estimates(command_name: str):
    st.write("**Estimates**:")
    estimates = state.orchestrator.estimate(command_name)
    st.write(
        f"tokens: {estimates['tokens']:,} (in: {estimates['in_tokens']:,} | out: {estimates['out_tokens']:,})"
    )
    st.write(f"cost: ${estimates['cost']}")

    if state.orchestrator.COMMAND_ARGS[command_name].multiple_requests:
        st.write(f"messages [n = {len(estimates['messages'])}]:")
    else:
        st.write("messages:")
    st.json(estimates["messages"], expanded=False)


def display_outputs(command_name: str, outputs: str):
    st.write("**Outputs**:")

    st.write(
        f"tokens: {outputs['tokens']:,} (in: {outputs['in_tokens']:,} | out: {outputs['out_tokens']:,})"
    )
    st.write(f"cost: {outputs['cost']}")

    if state.orchestrator.COMMAND_ARGS[command_name].multiple_requests:
        st.write(f"messages [n = {len(outputs['messages'])}]:")
    else:
        st.write("messages:")
    st.json(outputs["messages"], expanded=False)

    if state.orchestrator.COMMAND_ARGS[command_name].multiple_requests:
        st.write(f"responses [n = {len(outputs['contents'])}]:")
    else:
        st.write("response:")

    if isinstance(outputs["contents"], str):
        st.write(outputs["contents"])
    else:
        st.json(outputs["contents"], expanded=False)
