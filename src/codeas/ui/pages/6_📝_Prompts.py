import streamlit as st
import streamlit_nested_layout  # noqa

from codeas.configs import prompts
from codeas.core.clients import MODELS, LLMClients
from codeas.core.usage_tracker import usage_tracker
from codeas.ui.utils import (
    delete_saved_prompt,
    read_prompts,
    save_existing_prompt,
    save_prompt,
)

PROMPT_TYPES = [
    "📚 DOCUMENTATION",
    "🧪 TESTING",
    "🔄 REFACTORING",
    "🚀 DEPLOYMENT",
    "❔ OTHER",
]
ICONS = {
    "📚 DOCUMENTATION": "📚",
    "🧪 TESTING": "🧪",
    "🔄 REFACTORING": "🔄",
    "🚀 DEPLOYMENT": "🚀",
    "❔ OTHER": "❔",
}


def page():
    display_prompt_generator()
    display_add_manually()
    display_saved_prompts()


def display_saved_prompts():
    prompts = read_prompts()
    st.subheader("📝 Prompts")
    if prompts:
        for prompt_name, prompt in prompts.items():
            display_saved_prompt(prompt_name, prompt)
    else:
        st.info("No prompts saved yet")


def display_add_manually():
    with st.expander("ADD MANUALLY", icon="✏️", expanded=False):
        col1, col2 = st.columns(2)
        with col2:
            st.text_input("Prompt Name", key="manual_prompt_name")
        with col1:
            st.selectbox("Prompt Type", [""] + PROMPT_TYPES, key="manual_prompt_type")

        st.text_area(
            "Prompt", placeholder="Add prompt here", height=150, key="manual_prompt"
        )
        if st.button("Save", icon="💾", key="manual_save"):
            if (
                st.session_state.get("manual_prompt_name")
                and st.session_state.get("manual_prompt_type")
                and st.session_state.get("manual_prompt")
            ):
                prompt_name = f"[{st.session_state.get('manual_prompt_type')}] {st.session_state.get('manual_prompt_name')}"
                save_prompt(prompt_name, st.session_state.manual_prompt)
                st.success("Prompt Saved")

            else:
                st.warning("Please fill in all fields before saving.")


def display_saved_prompt(prompt_name, prompt):
    with st.expander(prompt_name, expanded=False):
        input_name = st.text_input("Name", value=prompt_name)
        input_prompt = st.text_area("Prompt", value=prompt, height=200)
        display_modify_prompt(prompt_name, input_prompt)
        input_prompt = (
            st.session_state.get("modified_prompt")
            if st.session_state.get("modified_prompt")
            else input_prompt
        )
        if st.button("Save", icon="💾", key=f"save_{prompt_name}"):
            if st.session_state.get("modified_prompt"):
                del st.session_state["modified_prompt"]
            save_existing_prompt(prompt_name, input_name, input_prompt)
            st.info("Changes saved")
            if st.button("Reload"):
                st.rerun()
        if st.button("Delete", icon="🗑️", type="primary", key=f"delete_{prompt_name}"):
            delete_saved_prompt(prompt_name)
            st.rerun()


def display_modify_prompt(prompt_name, prompt_to_modify):
    with st.expander("Modify", icon="🤖", expanded=False):
        modify_instructions = st.text_area(
            "Modifications",
            height=50,
            placeholder="How would you like to modify the prompt?",
            key=f"modify_{prompt_name}",
        )
        st.selectbox(
            "Model",
            options=MODELS.keys(),
            index=4,
            key=f"modify_model_{prompt_name}",
            disabled=True,
        )
        if st.button(
            "Run", key=f"run_{prompt_name}", disabled=modify_instructions == ""
        ):
            with st.spinner("Modifying prompt..."):
                llm_client = LLMClients(
                    model=st.session_state.get(f"modify_model_{prompt_name}")
                )
                messages = [{"role": "user", "content": prompts.meta_prompt_modify}]
                messages.append({"role": "assistant", "content": prompt_to_modify})
                messages.append({"role": "user", "content": modify_instructions})
                response = llm_client.run(messages)
                cost = llm_client.calculate_cost(messages, response.content[0].text)
                usage_tracker.log_prompt_generator(
                    st.session_state.get(f"modify_model_{prompt_name}"),
                    prompt_to_modify,
                    cost,
                    "prompt_modifications",
                    "Modify",
                )
                st.text_area(
                    "Modified Prompt",
                    value=response.content[0].text,
                    height=200,
                    key="modified_prompt",
                )
                st.write(f"💰 ${cost['total_cost']:.4f}")


def display_prompt_generator():
    with st.expander("PROMPT GENERATOR", icon="🤖", expanded=True):
        display_prompt_name()
        st.text_area(
            "Instructions",
            placeholder="Describe the task you want to perform",
            height=150,
            key="instructions",
        )
        display_generators()

        # Add model selection
        col1, _ = st.columns([1, 2])
        with col1:
            st.selectbox(
                "Model",
                options=MODELS.keys(),
                index=4,
                key="prompt_generation_model",
                disabled=True,
            )

        # Check if all fields are filled and at least one generator is selected
        all_fields_filled = (
            st.session_state.prompt_name
            and st.session_state.prompt_type
            and st.session_state.instructions
            and st.session_state.prompt_generation_model
        )
        any_generator_selected = (
            st.session_state.standard_generator
            or st.session_state.advanced_generator
            or st.session_state.chain_of_thought_generator
        )

        if st.button("Generate Prompt"):
            if all_fields_filled and any_generator_selected:
                generate_prompts()
            else:
                st.warning(
                    "Please fill in all fields and select at least one generator before generating the prompt."
                )
        else:
            display_generated_prompts()


def display_prompt_name():
    col1, col2 = st.columns(2)
    with col2:
        st.text_input("Prompt Name", key="prompt_name")
    with col1:
        st.selectbox("Prompt Type", [""] + PROMPT_TYPES, key="prompt_type")


def display_generators():
    st.write("**Generators**:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.checkbox("Standard", key="standard_generator", value=True)

    with col2:
        st.checkbox("Advanced", key="advanced_generator", value=True)

    with col3:
        st.checkbox("Chain-of-Thought", key="chain_of_thought_generator", value=True)


def display_generated_prompts():
    if st.session_state.get("standard_prompt"):
        display_generated_prompt("standard", st.session_state.standard_prompt, True)
    if st.session_state.get("advanced_prompt"):
        display_generated_prompt("advanced", st.session_state.advanced_prompt, True)
    if st.session_state.get("chain_of_thought_prompt"):
        display_generated_prompt(
            "chain_of_thought", st.session_state.chain_of_thought_prompt, True
        )


def display_generated_prompt(generator, prompt, enable_actions):
    with st.expander(f"{generator}", icon="📝", expanded=True):
        st.text_area("Prompt", value=prompt, height=300)
        if st.button(
            "Save", icon="💾", key=f"save_{generator}", disabled=not enable_actions
        ):
            prompt_name = f"{ICONS[st.session_state.get('prompt_type')]} {st.session_state.get('prompt_name')}"
            save_prompt(prompt_name, prompt)
            delete_prompt(generator)
        if st.button(
            "Delete",
            icon="🗑️",
            type="primary",
            key=f"delete_{generator}",
            disabled=not enable_actions,
        ):
            delete_prompt(generator)


def delete_prompt(generator):
    del st.session_state[f"{generator}_prompt"]
    st.rerun()


def generate_prompts():
    if st.session_state.standard_generator:
        with st.spinner("Running Standard Generator..."):
            response = generate_prompt(prompts.meta_prompt_basic, "standard")
            st.session_state.standard_prompt = response.content[0].text
        display_generated_prompt("standard", st.session_state.standard_prompt, False)

    if st.session_state.advanced_generator:
        with st.spinner("Running Advanced Generator..."):
            response = generate_prompt(prompts.meta_prompt_advanced, "advanced")
            st.session_state.advanced_prompt = parse_markup(
                response.content[0].text, "prompt"
            )
        display_generated_prompt("advanced", st.session_state.advanced_prompt, False)

    if st.session_state.chain_of_thought_generator:
        with st.spinner("Running Chain-of-Thought..."):
            response = generate_prompt(
                prompts.meta_prompt_chain_of_thought, "chain_of_thought"
            )
            st.session_state.chain_of_thought_prompt = parse_markup(
                response.content[0].text, "Instructions"
            )
        display_generated_prompt(
            "chain_of_thought", st.session_state.chain_of_thought_prompt, False
        )
    st.rerun()


def parse_markup(completion: str, tag_name: str):
    return completion.split(f"<{tag_name}>")[1].split(f"</{tag_name}")[0].strip()


def generate_prompt(generator_prompt: str, generator: str):
    llm_client = LLMClients(model=st.session_state.prompt_generation_model)
    messages = [{"role": "user", "content": generator_prompt}]
    messages.append(
        {"role": "user", "content": f"<Task>{st.session_state.instructions}</Task>"}
    )
    response = llm_client.run(messages)
    cost = llm_client.calculate_cost(messages, response.content[0].text)
    usage_tracker.log_prompt_generator(
        st.session_state.prompt_generation_model,
        st.session_state.instructions,
        cost,
        generator,
        "Generate",
    )
    return response


page()
