from divergen import CodebaseAssistant, CodebaseManager

codebase_assistant = CodebaseAssistant(
    source_dir="./src/",
    prompt_manager={"prompt_library":"./assets/prompt-library"}
)
codebase_assistant.generate_docstrings(model_name="fake")
codebase_assistant.reject_changes()
codebase_assistant.apply_changes()
codebase_assistant.revert_changes()
print("ok")