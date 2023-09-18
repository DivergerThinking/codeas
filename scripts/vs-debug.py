from divergen import CodebaseAssistant, PromptManager

prompt_manager = PromptManager(prompt_library="./assets/prompt-library")
print(
    prompt_manager.build_template(
        template_name="explain-codebase.yaml", 
        template_inputs={"code":"def function: ..."}
    )
)

codebase_assistant = CodebaseAssistant(
    source_dir="./src/",
    prompt_manager={"prompt_library":"./assets/prompt-library"}
)
# codebase_assistant.explain_codebase(module_name="codebase_assistant.py")
codebase_assistant.explain_codebase(entity_name="CodebaseAssistant")

# codebase_assistant.generate_docstrings(entity_name="CodebaseManager")
codebase_assistant.generate_docstrings(module_name="codebase_manager.py")
codebase_assistant.apply_changes()
codebase_assistant.revert_changes()
codebase_assistant.reject_changes()
print("ok")