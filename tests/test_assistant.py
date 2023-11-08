import os

import pytest
from dotenv import load_dotenv

from codeas.assistant import Assistant

from .utils import create_dummy_repo, remove_dummy_repo

load_dotenv()


def test_init_configs():
    create_dummy_repo()
    assistant = Assistant(model="fake")
    assistant.init_configs()
    assert os.path.exists(".codeas/assistant.yaml")
    assert os.path.exists(".codeas/prompts.yaml")
    remove_dummy_repo()


def test_execute_preprompt():
    create_dummy_repo()
    assistant = Assistant(model="fake")
    assistant._prompts = {
        "modify_code": {
            "instructions": "modify some code",
            "target": "code",
            "context": "code",
            "scope": "module",
        }
    }
    assistant.execute_preprompt("modify_code")
    assert os.path.exists("./src/module1_preview.py")
    remove_dummy_repo()


@pytest.mark.parametrize(
    "target, context",
    [
        ("code", "code"),
        ("tests", "code"),
        ("docs", "code"),
    ],
)
def test_execute_prompt(target, context):
    create_dummy_repo()
    assistant = Assistant(model="fake")
    assistant.execute_prompt(
        instructions="instructions", target=target, context=context, scope="module"
    )
    if target == "code":
        assert os.path.exists("./src/module1_preview.py")
    elif target == "tests":
        assert os.path.exists("./tests/test_module1_preview.py")
    elif target == "docs":
        assert os.path.exists("./docs/module1_preview.md")
    remove_dummy_repo()


def test_apply_changes():
    create_dummy_repo()
    assistant = Assistant(model="fake")
    assistant.execute_prompt("instructions", scope="module")
    assistant.apply_changes()
    assert not os.path.exists("./src/module1_preview.py")
    assert os.path.exists("./.codeas/backup/module1.py")
    remove_dummy_repo()


def test_reject_changes():
    create_dummy_repo()
    assistant = Assistant(model="fake")
    assistant.execute_prompt("instructions", scope="module")
    assistant.reject_changes()
    assert not os.path.exists("./src/module1_preview.py")
    assert not os.path.exists("./.codeas/backup/module1.py")
    remove_dummy_repo()
