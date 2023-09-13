from divergen import CodebaseAssistant, CodebaseManager

codebase_assistant = CodebaseAssistant(source_dir="./src/")
codebase_assistant.generate_docstrings()
codebase_assistant.apply_changes()
codebase_assistant.revert_changes()
codebase_assistant.reject_changes()
print("ok")