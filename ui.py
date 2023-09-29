import os

import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, PrivateAttr

load_dotenv("./.env")

from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI

from divergen.codebase_assistant import CodebaseAssistant


class UI(BaseModel):
    _source_dir: str = PrivateAttr(None)
    _entities: list = PrivateAttr(None)
    _action: str = PrivateAttr(None)
    _template: str = PrivateAttr(None)
    _prompt: str = PrivateAttr(None)
    _user_input: dict = PrivateAttr(default_factory=dict)

    def add_title(self):
        st.title("Divergen")

    def show_context_banner(self):
        st.subheader("CONTEXT")
        col1, col2, col3 = st.columns(3)
        with col1:
            self.select_source_dir()

        with col2:
            self.select_action()

        with col3:
            self.select_entities()

    def show_prompt_banner(self):
        st.subheader("PROMPT")
        if self._action == "Ask LLM":
            self.write_prompt()
        else:
            col1, col2, col3 = st.columns([0.45, 0.1, 0.45])
            with col1:
                self.select_template()

            with col2:
                st.markdown(
                    "<h3 style='text-align: center'>OR</h3>", unsafe_allow_html=True
                )

            with col3:
                self.write_prompt()

    def select_source_dir(self):
        self._source_dir = st.text_input("Source directory", "demo")
        if self._source_dir:
            st.text(f"{os.path.abspath(self._source_dir)}")

    def select_action(self):
        if self._source_dir:
            self._action = st.selectbox(
                "Choose an action to perform",
                ["Modify codebase", "Generate markdown", "Generate tests","Ask LLM"],
                index=None,
            )

    def select_entities(self):
        if st.session_state["assistant"]:
            if self._action == "Modify codebase":
                _entities_list = st.session_state["assistant"].codebase.list_entities()
                _entities_list = self._list_modules_only(_entities_list)
            
            self._entities = st.multiselect(
                "Select entities to use as context",
                _entities_list
            )
    
    def _list_modules_only(self, entities_list):
        return [entity for entity in entities_list if entity.endswith(".py")]

    def select_template(self):
        self._template = st.selectbox(
            "Select a template",
            st.session_state["assistant"].prompt_manager.list_templates(self._action),
            index=None,
        )
        if self._template:
            st.session_state["has_template"] = True

    def write_prompt(self):
        self._prompt = st.text_input("Enter prompt")
        if self._prompt:
            st.session_state["has_prompt"] = True
            self._user_input["prompt"] = self._prompt
            if self._action == "Modify codebase":
                self._template = "generics/generic_modifier.yaml"
            else:
                self._template = "generics/generic.yaml"

    def print_prompts(self):
        for entity_name in self._entities:
            st.text(
                st.session_state["assistant"].prompt_manager.build(
                    template=self._template,
                    code=st.session_state["assistant"]
                    .codebase.get_entity(entity_name)
                    .get_code(),
                    **self._user_input,
                )
            )

    def run_llm(self):
        st.session_state["assistant"].run_action(
            action=self._action,
            template=self._template,
            entity_names=self._entities,
            model=ChatOpenAI(
                streaming=True, callbacks=[StreamlitCallbackHandler(st.container())]
            ),
            **self._user_input,
        )

    def show_code_comparison(self):
        col1, col2 = st.columns(2)
        for module in st.session_state["assistant"].codebase.get_modified_modules():
            with col1:
                original_path = os.path.join(
                    st.session_state["assistant"].codebase.source_dir, module.path
                )
                original_code = self._read_file(original_path)
                st.text(original_path)
                st.code(original_code)

            with col2:
                preview_path = original_path.replace(".py", "_preview.py")
                preview_code = self._read_file(preview_path)
                st.text(preview_path)
                st.code(preview_code)

    def show_original_code(self):
        _, col1, _ = st.columns([2, 4, 2])
        with col1:
            for module in st.session_state["assistant"].codebase.get_modified_modules():
                original_path = os.path.join(
                    st.session_state["assistant"].codebase.source_dir, module.path
                )
                original_code = self._read_file(original_path)
                st.text(original_path)
                st.code(original_code)

    def _read_file(self, path):
        with open(path, "r") as file_:
            return file_.read()

    def show_apply_reject(self):
        apply = st.selectbox(
            "Select change to apply",
            ["Apply changes", "Reject changes"],
            index=None,
        )
        if apply == "Apply changes":
            st.session_state["assistant"].apply_changes()
            st.text("Changes applied")
            self.show_original_code()
        elif apply == "Reject changes":
            st.session_state["assistant"].reject_changes()
            st.text("Changes rejected")
            self.show_original_code()


def configure_app():
    st.set_page_config(layout="wide")

    if "has_run" not in st.session_state:
        st.session_state["has_run"] = False
    if "template" not in st.session_state:
        st.session_state["has_template"] = False
    if "prompt" not in st.session_state:
        st.session_state["has_prompt"] = False
    if "show_code" not in st.session_state:
        st.session_state["show_code"] = False
    if "assistant" not in st.session_state:
        st.session_state["assistant"] = None


def instantiate_assistant(ui):
    if st.session_state["assistant"] is None and ui._source_dir is not None:
        st.session_state["assistant"] = CodebaseAssistant(
            codebase={"source_dir": ui._source_dir},
            prompt_manager={"prompt_library": "./assets/prompt-library", "add_titles": False},
        )
    elif (
        st.session_state["assistant"] is not None
        and ui._source_dir is not None
        and ui._source_dir != st.session_state["assistant"].codebase.source_dir
    ):
        st.session_state["assistant"] = CodebaseAssistant(
            codebase={"source_dir": ui._source_dir},
            prompt_manager={"prompt_library": "./assets/prompt-library", "add_titles": False},
        )
        st.rerun()


def main():
    configure_app()
    ui = UI()
    ui.add_title()
    ui.show_context_banner()
    instantiate_assistant(ui)

    if ui._source_dir and ui._entities and ui._action:
        ui.show_prompt_banner()
        if (
            st.session_state["has_template"] or st.session_state["has_prompt"]
        ) and st.session_state["has_run"] is False:
            # ui.print_prompts()
            ui.run_llm()
            st.session_state["has_run"] = True
            if ui._action == "Modify codebase":
                st.session_state["show_code"] = True
            else:
                st.session_state["show_code"] = False
        if st.session_state["show_code"]:
            ui.show_code_comparison()
            ui.show_apply_reject()


if __name__ == "__main__":
    main()
