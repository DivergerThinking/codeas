import streamlit as st

from codeag.ui.shared.components import display_chain
from codeag.ui.shared.state import state


def display_testing():
    st.write("## Testing")
    display_identify_test_cases()


def display_identify_test_cases():
    with st.expander("Identify test cases", expanded=True):
        display_chain(
            "identify_test_cases",
            "Identify test cases",
            ["identify_test_cases", "prioritize_test_cases"],
            display_test_cases,
        )


def display_test_cases():
    identify_test_cases = state.storage.read("identify_test_cases")
    prioritize_test_cases = state.storage.read("prioritize_test_cases")

    if not identify_test_cases or not prioritize_test_cases:
        st.warning("Test cases have not been identified or prioritized yet.")
        return

    for priority in ["High", "Medium", "Low"]:
        with st.expander(
            f"{priority} Priority", expanded=True if priority == "High" else False
        ):
            for file_path in prioritize_test_cases["responses"]["content"].get(
                priority, []
            ):
                if file_path in identify_test_cases["responses"].keys():
                    data = {
                        "incl.": [],
                        "test": [],
                        "description": [],
                        "asserts": [],
                        "importance": [],
                    }
                    for test_name, test_info in identify_test_cases["responses"][
                        file_path
                    ]["content"].items():
                        data["incl."].append(False)
                        data["test"].append(test_name)
                        data["description"].append(test_info["description"])
                        data["asserts"].append(test_info["asserts"])
                        data["importance"].append(test_info["importance"])

                    with st.expander(file_path):
                        display_data_editor(data, key=f"{priority}_{file_path}")

    # Display selected test cases if any
    if any(state.selected_test_cases):
        # display number of selected test cases
        st.info(
            f"{sum(len(v) for v in state.selected_test_cases.values())} selected test cases"
        )


def display_data_editor(data, key):
    updated_data = st.data_editor(
        data, key=key, disabled=["test", "description", "asserts", "importance"]
    )
    if st.button("Add test cases", key=f"update_{key}", type="primary"):
        update_selected_test_cases(key, updated_data)


def update_selected_test_cases(key, data):
    selected_cases = {}
    priority, file_path = key.split("_", 1)

    for i, included in enumerate(data["incl."]):
        if included:
            if file_path not in selected_cases:
                selected_cases[file_path] = []

            selected_cases[file_path].append(
                {
                    "test": data["test"][i],
                    "description": data["description"][i],
                    "asserts": data["asserts"][i],
                    "importance": data["importance"][i],
                    "priority": priority,
                }
            )

    state.selected_test_cases.update(selected_cases)
    state.storage.write_json(
        "state/selected_test_cases.json", state.selected_test_cases
    )
    st.success("Test cases added")


def display_selected_test_cases():
    ...


def display_testing_guidelines(outputs):
    with st.expander("Testing guidelines", expanded=True):
        st.write(outputs["contents"])


def display_generated_tests(outputs):
    with st.expander("Generated test cases", expanded=True):
        for contents in outputs["contents"].values():
            for test_file, tests in contents.items():
                with st.expander(test_file):
                    st.code(tests)


# def display_export_test_files_button():
#     display_button("Export test files", "export_test_files")

#     if get_state("clicked").get("export_test_files"):
#         outputs = get_state("commands").read("generate_tests")
#         for contents in outputs["contents"].values():
#             for test_file_path, tests in contents.items():
#                 if not os.path.exists(os.path.dirname(test_file_path)):
#                     os.makedirs(os.path.dirname(test_file_path))
#                 with open(test_file_path, "w") as f:
#                     f.write(tests)


display_testing()
