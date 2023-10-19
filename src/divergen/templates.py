TEMPLATE = """
You are a senior software developer.
You will be given some {context} and instructions to perform on that {context}. 

{CONTEXT}:
{entity_context}

INSTRUCTIONS:
{user_prompt}
{guideline_prompt}

IMPORTANT: only return the {target}. Do not include explanations outside of the {target}.
"""
