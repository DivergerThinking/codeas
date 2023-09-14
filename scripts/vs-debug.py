from divergen import CodebaseAssistant, CodebaseManager

# cbm = CodebaseManager(source_dir="./src")
# cbm.get_codebase_source_code()
# cbm.get_module_source_code("codebase_assistant.py")
# cbm.get_entity_source_code("CodebaseAssistant._move_preview_files_to_target")

codebase_assistant = CodebaseAssistant(
    source_dir="./src/",
    prompt_manager={"prompt_library":"./assets/prompt-library"}
)
# codebase_assistant.generate_docstrings(entity_name="CodebaseManager")
codebase_assistant.generate_docstrings(module_name="codebase_manager.py")
codebase_assistant.reject_changes()
# codebase_assistant.apply_changes()
# codebase_assistant.revert_changes()
print("ok")