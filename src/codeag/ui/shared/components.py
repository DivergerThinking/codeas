import streamlit as st

from codeag.ui.shared.state import get_state


def clicked(key):
    get_state("clicked")[key] = True


def display_steps(steps):
    with st.expander("Steps"):
        for step in steps:
            display_command(step)


def display_button(label, key):
    st.button(
        label,
        type="primary",
        key=key,
        on_click=lambda: clicked(key),
    )


def run_section(command_name, spinner_text):
    with st.spinner(spinner_text):
        if get_state("commands").exists_output(command_name):
            outputs = get_state("commands").read(command_name)
            st.info("Using stored outputs.")
        else:
            outputs = get_state("commands").run(command_name)
            get_state("commands").write(command_name, outputs)
        return outputs


def display_command(command_name: str):
    label = command_name.replace("_", " ").title()

    with st.expander(label):
        display_command_configs(command_name)
        display_run_button(command_name)
        display_estimate_button(command_name)

        if get_state("clicked").get(f"estimate_{command_name}"):
            st.divider()
            display_estimates(command_name)

        if get_state("clicked").get(f"run_{command_name}"):
            st.divider()

            if get_state("clicked").get(f"rerun_{command_name}"):
                outputs = run_command(command_name)
                display_outputs(command_name, outputs)
                get_state("clicked")[f"rerun_{command_name}"] = False

            elif get_state("commands").exists_output(command_name):
                outputs = get_state("commands").read(command_name)
                display_outputs(command_name, outputs)
                st.info("Using stored outputs.")
                display_rerun_button(command_name)

            else:
                outputs = run_command(command_name)
                display_outputs(command_name, outputs)


def run_command(command_name: str):
    with st.spinner(f"Running '{command_name}'..."):
        outputs = get_state("commands").run(command_name)
        get_state("commands").write(command_name, outputs)
    return outputs


def display_command_configs(command_name: str):
    with st.expander("Configs", expanded=False):
        st.json(get_state("commands").COMMAND_ARGS[command_name].dict())


def display_run_button(command_name):
    st.button(
        "Run",
        type="primary",
        key=f"run_{command_name}",
        on_click=lambda: clicked(f"run_{command_name}"),
    )


def display_rerun_button(command_name):
    st.button(
        "Rerun",
        type="primary",
        key=f"rerun_{command_name}",
        on_click=lambda: clicked(f"rerun_{command_name}"),
    )


def display_estimate_button(command_name):
    st.button(
        "Estimate",
        type="secondary",
        key=f"estimate_{command_name}",
        on_click=lambda: clicked(f"estimate_{command_name}"),
    )


def display_estimates(command_name: str):
    st.write("**Estimates**:")
    estimates = get_state("commands").estimate(command_name)
    st.write(
        f"tokens: {estimates['tokens']:,} (in: {estimates['in_tokens']:,} | out: {estimates['out_tokens']:,})"
    )
    st.write(f"cost: ${estimates['cost']}")

    if get_state("commands").COMMAND_ARGS[command_name].multiple_requests:
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

    if get_state("commands").COMMAND_ARGS[command_name].multiple_requests:
        st.write(f"messages [n = {len(outputs['messages'])}]:")
    else:
        st.write("messages:")
    st.json(outputs["messages"], expanded=False)

    if get_state("commands").COMMAND_ARGS[command_name].multiple_requests:
        st.write(f"responses [n = {len(outputs['contents'])}]:")
    else:
        st.write("response:")

    if isinstance(outputs["contents"], str):
        st.write(outputs["contents"])
    else:
        st.json(outputs["contents"], expanded=False)
