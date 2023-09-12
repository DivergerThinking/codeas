from divergen.codebase_assistant import CodebaseAssistant

code_assist = CodebaseAssistant(
    code_manager={"source_dir":"./src/"}
)
code_assist.generate_docstrings()