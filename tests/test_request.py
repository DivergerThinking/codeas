from dotenv import load_dotenv
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import AIMessage

from codeas.codebase import Codebase
from codeas.request import Request

from .utils import create_dummy_repo, remove_dummy_repo

load_dotenv()

dummy_func1 = "def dummy_func_rewritten1():\n    print('it worked')"
dummy_func2 = "public String dummyFunctionRewritten2() {\n    return 'it worked';\n}\n"
msg = AIMessage(
    content=f"<module1.py>\n{dummy_func1}\n</module1.py>\n\n<module2.java>\n{dummy_func2}\n</module2.java>\n\n"
)
model_global = FakeMessagesListChatModel(responses=[msg])
msg = AIMessage(content="module1.py,module2.java")
model_instructions = FakeMessagesListChatModel(responses=[msg])


def test_execute_globally():
    create_dummy_repo()
    codebase = Codebase()
    codebase.parse_modules()
    request = Request(
        instructions="instructions",
        model=model_global,
        context="code",
        target="code",
        guideline_prompt="",
    )
    request.execute_globally(codebase)
    assert codebase.get_module("module1.py").code == dummy_func1
    assert codebase.get_module("module2.java").code == dummy_func2
    remove_dummy_repo()


def test_get_modules_from_instructions():
    create_dummy_repo()
    codebase = Codebase()
    codebase.parse_modules()
    request = Request(
        instructions="instructions",
        model=model_instructions,
        context="code",
        target="code",
        guideline_prompt="",
    )
    modules = request.get_modules_from_instructions(codebase)
    assert modules == ["module1.py", "module2.java"]
    remove_dummy_repo()
