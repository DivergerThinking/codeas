from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import AIMessage

from codeas.codebase import Codebase
from codeas.request import Request

from .utils import create_dummy_repo, remove_dummy_repo


def test_add_relevant_guidelines():
    create_dummy_repo()

    codebase = Codebase()
    codebase.parse_modules()

    msg = AIMessage(content="docs,clean_code")
    model = FakeMessagesListChatModel(responses=[msg])

    request = Request(
        instructions="instructions",
        guidelines={"docs": "documentation", "clean_code": "code is clean"},
        model=model,
    )
    request.add_relevant_guidelines()

    assert request.instructions == "instructions\ndocumentation\ncode is clean"

    remove_dummy_repo()


def test_identify_relevant_files():
    create_dummy_repo()

    codebase = Codebase()
    codebase.parse_modules()

    msg = AIMessage(content="<read>\n'src.module1.py,src.module2.java'\n</read>\n\n")
    model = FakeMessagesListChatModel(responses=[msg])

    request = Request(
        instructions="instructions",
        model=model,
    )
    relevant_files = request.identify_relevant_files(codebase)

    assert relevant_files["read"] == "'src.module1.py,src.module2.java'"

    remove_dummy_repo()


def test_execute_request():
    create_dummy_repo()

    codebase = Codebase()
    codebase.parse_modules()

    dummy_func1 = "def dummy_func_rewritten1():\n    print('it worked')"
    dummy_func2 = (
        "public String dummyFunctionRewritten2() {\n    return 'it worked';\n}\n"
    )
    msg = AIMessage(
        content=f"<src.module1.py>\n{dummy_func1}\n</src.module1.py>\n\n<src.module2.java>\n{dummy_func2}\n</src.module2.java>\n\n"
    )
    model = FakeMessagesListChatModel(responses=[msg])

    relevant_files = {
        "read": "src.module1.py,src.module2.java",
        "modify": "src.module1.py,src.module2.java",
    }

    request = Request(
        instructions="instructions",
        model=model,
    )
    request.execute_request(codebase, relevant_files)

    assert codebase.get_module("src.module1.py").content == dummy_func1
    assert codebase.get_module("src.module2.java").content == dummy_func2

    remove_dummy_repo()
