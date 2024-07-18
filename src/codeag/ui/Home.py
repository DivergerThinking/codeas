import streamlit as st

from codeag.core.agent import Agent
from codeag.core.commands import Commands

if "commands" not in st.session_state:
    st.session_state.commands = Commands(agent=Agent(repo_path="."))
if "estimates" not in st.session_state:
    st.session_state.estimates = {}
if "outputs" not in st.session_state:
    st.session_state.outputs = {}


def display_command(command_name: str):
    label = command_name.replace("_", " ").title()
    with st.expander(label):
        st.write("**Estimates**:")

        if command_name not in st.session_state.estimates:
            estimates = st.session_state.commands.estimate(command_name)
            st.session_state.estimates[command_name] = estimates

        tokens, in_tokens, out_tokens, cost, messages = (
            st.session_state.estimates[command_name]["tokens"],
            st.session_state.estimates[command_name]["in_tokens"],
            st.session_state.estimates[command_name]["out_tokens"],
            st.session_state.estimates[command_name]["cost"],
            st.session_state.estimates[command_name]["messages"],
        )
        st.write(f"tokens: {tokens:,} (in: {in_tokens:,} | out: {out_tokens:,})")
        st.write(f"cost: ${cost}")
        if st.session_state.commands.COMMAND_ARGS[command_name].multiple_requests:
            st.write(f"messages [n = {len(messages)}]:")
        else:
            st.write("messages:")
        st.json(messages, expanded=False)

        run_func = st.button(label, type="primary")

        if run_func:
            with st.spinner(f"Running '{command_name}'..."):
                outputs = st.session_state.commands.run(command_name)
                st.session_state.commands.write(command_name, outputs)

        if command_name not in st.session_state.outputs:
            outputs = st.session_state.commands.read(command_name)
            if outputs:
                st.session_state.outputs[command_name] = outputs

        if command_name in st.session_state.outputs:
            st.write("**Output**:")
            cost, tokens, in_tokens, out_tokens, contents = (
                st.session_state.outputs[command_name]["cost"],
                st.session_state.outputs[command_name]["tokens"],
                st.session_state.outputs[command_name]["in_tokens"],
                st.session_state.outputs[command_name]["out_tokens"],
                st.session_state.outputs[command_name]["contents"],
            )
            st.write(f"tokens: {tokens:,} (in: {in_tokens:,} | out: {out_tokens:,})")
            st.write(f"cost: {cost}")
            if st.session_state.commands.COMMAND_ARGS[command_name].multiple_requests:
                st.write(f"responses [n = {len(contents)}]:")
            else:
                st.write("response:")
            if isinstance(contents, str):
                st.write(contents)
            else:
                st.json(contents, expanded=False)


st.markdown("### Extract codebase information")
display_command("extract_file_descriptions")
display_command("extract_directory_descriptions")

st.markdown("### Generate documentation")
display_command("define_documentation_sections")
display_command("identify_sections_context")
display_command("generate_documentation_sections")
display_command("generate_introduction")
