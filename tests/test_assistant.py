import os
import shutil

import pytest
from dotenv import load_dotenv

from codeas.assistant import Assistant

from .utils import create_dummy_repo, remove_dummy_repo, reset_dummy_repo

load_dotenv()

remove_dummy_repo()
create_dummy_repo()
os.chdir("./dummy_repo")


@pytest.fixture
def assistant():
    reset_dummy_repo()
    return Assistant()


def test_init_configs(assistant):
    if os.path.exists(".codeas"):
        shutil.rmtree("./.codeas")
    assistant.init_configs()
    assert os.path.exists(".codeas")
    assert os.path.exists(".codeas/assistant.yaml")
    assert os.path.exists(".codeas/prompts.yaml")


def test_execute_preprompt(assistant):
    _monkeypatch_prompts(assistant)
    _monkeypatch_model(assistant)
    assistant.execute_preprompt("modify_code")
    assert os.path.exists("./src/dummy_module_preview.py")


def _monkeypatch_prompts(assistant):
    assistant._prompts = {
        "modify_code": {
            "instructions": "modify some code",
            "target": "code",
            "context": "code",
        }
    }


def _monkeypatch_model(assistant):
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
def test_execute_prompt(target, context, assistant):
    _monkeypatch_model(assistant)
    assistant.execute_prompt(
        instructions="instructions",
        target=target,
        context=context,
    )
    if target == "code":
        assert os.path.exists("./src/dummy_module_preview.py")
    elif target == "tests":
        assert os.path.exists("./tests/test_dummy_module_preview.py")
    elif target == "docs":
        assert os.path.exists("./docs/dummy_module_preview.md")


def test_apply_changes(assistant):
    _monkeypatch_model(assistant)
    assistant.execute_prompt("instructions")
    assistant.apply_changes()
    assert not os.path.exists("./src/dummy_module_preview.py")
    assert os.path.exists("./.codeas/backup/dummy_module.py")


def test_reject_changes(assistant):
    if os.path.exists("./.codeas/backup/"):
        shutil.rmtree("./.codeas/backup/")
    _monkeypatch_model(assistant)
    assistant.execute_prompt("instructions")
    assistant.reject_changes()
    assert not os.path.exists("./src/dummy_module_preview.py")
    assert not os.path.exists("./.codeas/backup/dummy_module.py")


def test_cleanup():
    os.chdir("..")
    remove_dummy_repo()
