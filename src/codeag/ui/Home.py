import streamlit as st

from codeag.core.agent import Agent
from codeag.core.commands import Commands

if "commands" not in st.session_state:
    st.session_state.commands = Commands(agent=Agent(repo_path="."), write_output=True)
if "estimates" not in st.session_state:
    st.session_state.estimates = {}
if "outputs" not in st.session_state:
    st.session_state.outputs = {}


def display_step(label: str, command_name: str, has_multiple_requests: bool):
    with st.expander(label, expanded=True):
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
        if has_multiple_requests:
            st.write(f"messages [n = {len(messages)}]:")
        else:
            st.write("messages:")
        st.json(messages, expanded=False)

        run_func = st.button(label, type="primary")

        if run_func:
            with st.spinner(f"Running '{command_name}'..."):
                st.session_state.commands.run(command_name)

        if command_name not in st.session_state.outputs:
            outputs = st.session_state.commands.read_output(command_name)
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
            if has_multiple_requests:
                st.write(f"responses [n = {len(contents)}]:")
            else:
                st.write("response:")
            st.json(contents, expanded=False)


st.markdown("### Extract codebase information")
display_step(
    "Extract file descriptions", "extract_file_descriptions", has_multiple_requests=True
)
display_step(
    "Extract directory descriptions",
    "extract_directory_descriptions",
    has_multiple_requests=False,
)

st.markdown("### Generate documentation")
# display_step("Extract documentation labels", "extract_documentation_labels", has_multiple_requests=True)
# display_step("Document directories", "document_directories", has_multiple_requests=False)
display_step(
    "Define documentation sections",
    "define_documentation_sections",
    has_multiple_requests=False,
)
