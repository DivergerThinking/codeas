import os

from dotenv import load_dotenv
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import AIMessage

from codeas.codebase import Codebase
from codeas.request import Request

from .utils import create_dummy_repo, remove_dummy_repo

load_dotenv()

remove_dummy_repo()
create_dummy_repo()
os.chdir("./dummy_repo")

dummy_func1 = """def dummy_func_rewritten1():\n    print('it worked')"""
dummy_func2 = """def dummy_func_rewritten12():\n    print('it worked')"""
msg = AIMessage(
    content=f"<module1>\n{dummy_func1}\n</module1>\n\n<module2>\n{dummy_func2}\n</module2>\n\n"
)
model = FakeMessagesListChatModel(responses=[msg])
# model = ChatOpenAI(
#     callbacks=[StreamingStdOutCallbackHandler()],
#     streaming=True,
# )

codebase = Codebase(language="python")
codebase.parse_modules()


def test_execute_globally():
    request = Request(
        instructions="instructions",
        model=model,
        context="code",
        target="code",
        guideline_prompt="",
    )
    request.execute_globally(codebase)
    assert codebase.get_module("module1").code == dummy_func1


def test_cleanup():
    os.chdir("..")
    remove_dummy_repo()
