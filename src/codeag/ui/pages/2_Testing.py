import json

import streamlit as st

from codeag.configs.storage_configs import SETTINGS_PATH
from codeag.ui.shared.components import display_button, display_steps, run_section
from codeag.ui.shared.state import get_state, init_state

init_state()


def display_testing():
    st.write("## Testing")
    with st.expander("Define test cases"):
        display_define_test_cases()
    display_selected_test_cases()
    with st.expander("Define testing guidelines"):
        display_define_testing_guidelines()
    with st.expander("Generate tests"):
        display_generate_tests()
    display_export_test_files_button()


def display_define_test_cases():
    display_steps(
        [
            # "categorize_test_files",
            "define_test_cases",
        ]
    )
    display_button("Define test cases", "define_test_cases")

    if get_state("clicked").get("define_test_cases"):
        outputs = run_section("define_test_cases", "Defining test cases...")
        display_test_cases_in_editor(outputs)


def display_define_testing_guidelines():
    display_steps(
        [
            "define_testing_guidelines",
        ]
    )
    display_button("Define testing guidelines", "define_testing_guidelines")

    if get_state("clicked").get("define_testing_guidelines"):
        outputs = run_section(
            "define_testing_guidelines", "Defining testing guidelines..."
        )
        display_testing_guidelines(outputs)


def display_generate_tests():
    display_steps(
        [
            "generate_tests",
        ]
    )
    display_button("Generate tests", "generate_tests")

    if get_state("clicked").get("generate_tests"):
        outputs = run_section("generate_tests", "Generating tests...")
        display_generated_tests(outputs)


def display_test_cases_in_editor(outputs):
    with st.expander("Test cases", expanded=True):
        for path, cases in outputs["contents"].items():
            data = {
                "incl.": [False] * len(cases),
                "test": [],
                "description": [],
                "asserts": [],
                "parent": [],
            }
            for name, case in cases.items():
                data["test"].append(name)
                data["description"].append(case["description"])
                data["asserts"].append(case["asserts"])
                data["parent"].append(case["parent_name"])

            with st.expander(path):
                display_data_editor(data, key=path)


def display_data_editor(data, key):
    st.data_editor(
        data, key=key, on_change=lambda: update_selected_test_cases(key, data)
    )


def update_selected_test_cases(path, data):
    updated_data = st.session_state[path]
    for row_nr, edited_values in updated_data["edited_rows"].items():
        if edited_values.get("incl.", False) is True:
            if path not in get_state("selected_test_cases"):
                get_state("selected_test_cases")[path] = []
            if data["test"][row_nr] not in get_state("selected_test_cases")[path]:
                get_state("selected_test_cases")[path].append(data["test"][row_nr])
        elif edited_values.get("incl.", True) is False:
            if path in get_state("selected_test_cases"):
                get_state("selected_test_cases")[path].remove(data["test"][row_nr])


def display_selected_test_cases():
    nr_test_cases = 0
    for _, cases in get_state("selected_test_cases").items():
        nr_test_cases += len(cases)
    if nr_test_cases > 0:
        st.write(f"{nr_test_cases} cases selected.")
        with open(
            f"{get_state('repo_path')}/{SETTINGS_PATH}/selected_test_cases.json", "w"
        ) as f:
            f.write(json.dumps(get_state("selected_test_cases")))


def display_testing_guidelines(outputs):
    with st.expander("Testing guidelines", expanded=True):
        st.write(outputs["contents"])


def display_generated_tests(outputs):
    with st.expander("Generated test cases", expanded=True):
        for contents in outputs["contents"].values():
            for test_file, tests in contents.items():
                with st.expander(test_file):
                    st.code(tests)


def display_export_test_files_button():
    display_button("Export test files", "export_test_files")

    if get_state("clicked").get("export_test_files"):
        outputs = get_state("commands").read("generate_tests")
        for contents in outputs["contents"].values():
            for test_file_path, tests in contents.items():
                with open(test_file_path, "w") as f:
                    f.write(tests)


display_testing()
