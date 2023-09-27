import os
import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, PrivateAttr

load_dotenv("./.env")

from divergen.codebase_assistant import CodebaseAssistant
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI


class UI(BaseModel):
    _source_dir: str = PrivateAttr(None)
    _entities: list = PrivateAttr(None)
    _action: str = PrivateAttr(None)
    _template: str = PrivateAttr(None)
    _prompt: str = PrivateAttr(None)

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
        self._source_dir = st.text_input("Source directory")
        if self._source_dir:
            st.text(f"{os.path.abspath(self._source_dir)}")

    def _set_assistant(self, source_dir):
        st.session_state["assistant"] = CodebaseAssistant(
            codebase={"source_dir": source_dir},
            prompt_manager={"prompt_library": "./assets/prompt-library"},
        )

    def select_action(self):
        self._action = st.selectbox(
            "Choose an action to perform",
            ["Modify codebase", "Generate markdown"],
            index=None,
        )

    def select_entities(self):
        if st.session_state["assistant"]:
            self._entities = st.multiselect(
                "Select entities to use as context",
                st.session_state["assistant"].codebase.list_entities(),
            )

    def select_template(self):
        self._template = st.selectbox(
            "Select a template",
            st.session_state["assistant"].prompt_manager.list_templates(),
            index=None,
        )
        if self._template:
            st.session_state["has_template"] = True

    def write_prompt(self):
        self._prompt = st.text_input("Enter prompt")
        if self._prompt:
            st.session_state["has_prompt"] = True

    def print_prompts(self):
        for entity_name in self._entities:
            st.text(
                st.session_state["assistant"].prompt_manager.build(
                    template=self._template,
                    code=st.session_state["assistant"]
                    .codebase.get_entity(entity_name)
                    .get_code(),
                )
            )

    def run_llm(self):
        if self._prompt:
            self._template = "templates/generic_modifier"
            user_input = {"prompt": self._prompt}
        else:
            user_input = {}

        st.session_state["assistant"].run_action(
            action=self._action,
            template=self._template,
            entity_names=self._entities,
            model=ChatOpenAI(
                streaming=True, callbacks=[StreamlitCallbackHandler(st.container())]
            ),
            **user_input,
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
            prompt_manager={"prompt_library": "./assets/prompt-library"},
        )
    elif (
        st.session_state["assistant"] is not None
        and ui._source_dir is not None
        and ui._source_dir != st.session_state["assistant"].codebase.source_dir
    ):
        st.session_state["assistant"] = CodebaseAssistant(
            codebase={"source_dir": ui._source_dir},
            prompt_manager={"prompt_library": "./assets/prompt-library"},
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
            ui.print_prompts()
            ui.run_llm()
            st.session_state["has_run"] = True
            st.session_state["show_code"] = True
        if st.session_state["show_code"]:
            ui.show_code_comparison()
            ui.show_apply_reject()


if __name__ == "__main__":
    main()
