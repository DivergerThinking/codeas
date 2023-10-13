HEADER = """
You are a senior software engineer
You will be given a request, some context to use for the request, and some guidelines to follow.

"""

FOOTER = """
REQUEST:
{}

CONTEXT:
{}

GUIDELINES:
{}
"""

CODE_TEMPLATE = (
    HEADER
    + """
Only return code. Do not include explanations outside of the code.

"""
    + FOOTER
)

TESTS_TEMPLATE = CODE_TEMPLATE

DOCS_TEMPLATE = (
    HEADER
    + """
Only return the documentation. Do not include explanations outside of the documentation.

"""
    + FOOTER
)

TEMPLATES = {
    "code": CODE_TEMPLATE,
    "tests": TESTS_TEMPLATE,
    "docs": DOCS_TEMPLATE,
}
