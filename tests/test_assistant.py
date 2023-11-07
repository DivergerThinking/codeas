import os
import shutil

import pytest
from dotenv import load_dotenv

from codeas.assistant import Assistant

from .utils import create_dummy_repo, remove_dummy_repo, reset_dummy_repo

load_dotenv()


@pytest.fixture
def assistant():
    reset_dummy_repo()
    return Assistant()


def test_init_configs(assistant: Assistant):
    remove_dummy_repo()
    create_dummy_repo()
    os.chdir("./dummy_repo")
    assistant.init_configs()
    assert os.path.exists(".codeas/assistant.yaml")
    assert os.path.exists(".codeas/prompts.yaml")


def test_execute_preprompt(assistant: Assistant):
    _monkeypatch_prompts(assistant)
    _monkeypatch_model(assistant)
    assistant.execute_preprompt("modify_code")
    assert os.path.exists("./src/module1_preview.py")


def _monkeypatch_prompts(assistant: Assistant):
    assistant._prompts = {
        "modify_code": {
            "instructions": "modify some code",
            "target": "code",
            "context": "code",
            "scope": "module",
        }
    }


def _monkeypatch_model(assistant: Assistant):
    assistant.model = "fake"
    assistant._set_openai_model()


@pytest.mark.parametrize(
    "target, context",
    [
        ("code", "code"),
        ("tests", "code"),
        ("docs", "code"),
    ],
)
def test_execute_prompt(target, context, assistant: Assistant):
    _monkeypatch_model(assistant)
    assistant.execute_prompt(
        instructions="instructions", target=target, context=context, scope="module"
    )
    if target == "code":
        assert os.path.exists("./src/module1_preview.py")
    elif target == "tests":
        assert os.path.exists("./tests/test_module1_preview.py")
    elif target == "docs":
        assert os.path.exists("./docs/module1_preview.md")


def test_apply_changes(assistant: Assistant):
    _monkeypatch_model(assistant)
    assistant.execute_prompt("instructions", scope="module")
    assistant.apply_changes()
    assert not os.path.exists("./src/module1_preview.py")
    assert os.path.exists("./.codeas/backup/module1.py")


def test_reject_changes(assistant: Assistant):
    if os.path.exists("./.codeas/backup/"):
        shutil.rmtree("./.codeas/backup/")
    _monkeypatch_model(assistant)
    assistant.execute_prompt("instructions", scope="module")
    assistant.reject_changes()
    assert not os.path.exists("./src/module1_preview.py")
    assert not os.path.exists("./.codeas/backup/module1.py")
