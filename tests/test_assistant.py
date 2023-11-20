import os

from dotenv import load_dotenv
from langchain.chat_models.fake import FakeMessagesListChatModel
from langchain.schema import AIMessage

from codeas.assistant import Assistant
from codeas.request import Request

from .utils import create_dummy_repo, remove_dummy_repo

load_dotenv()


def monkey_patch_relevant_files(self, codebase):
    return {"read": "src.module1.py", "modify": "src.module1.py"}


Request.identify_relevant_files = monkey_patch_relevant_files
dummy_func1 = "def dummy_func_rewritten1():\n    print('it worked')"
msg = AIMessage(content=f"<src.module1.py>\n{dummy_func1}\n</src.module1.py>\n\n")
dummy_model = FakeMessagesListChatModel(responses=[msg])


def test_init_configs():
    create_dummy_repo()
    assistant = Assistant()
    assistant.init_configs()
    assert os.path.exists(".codeas/assistant.yaml")
    assert os.path.exists(".codeas/prompts.yaml")
    remove_dummy_repo()


def test_execute_preprompt():
    create_dummy_repo()
    assistant = Assistant()
    assistant._openai_model = dummy_model
    assistant._prompts = {
        "modify_code": {
            "instructions": "modify some code",
        }
    }
    assistant.execute_preprompt("modify_code")
    assert os.path.exists("./src/module1_preview.py")
    remove_dummy_repo()


def test_apply_changes():
    create_dummy_repo()
    assistant = Assistant()
    assistant._openai_model = dummy_model
    assistant._prompts = {
        "modify_code": {
            "instructions": "modify some code",
        }
    }
    assistant.execute_preprompt("modify_code")
    assistant.apply_changes()
    assert not os.path.exists("./src/module1_preview.py")
    assert os.path.exists("./.codeas/backup/module1.py")
    remove_dummy_repo()


def test_reject_changes():
    create_dummy_repo()
    assistant = Assistant()
    assistant._openai_model = dummy_model
    assistant._prompts = {
        "modify_code": {
            "instructions": "modify some code",
        }
    }
    assistant.execute_preprompt("modify_code")
    assistant.reject_changes()
    assert not os.path.exists("./src/module1_preview.py")
    assert not os.path.exists("./.codeas/backup/module1.py")
    remove_dummy_repo()
