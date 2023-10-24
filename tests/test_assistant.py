import os
import shutil

import pytest
from dotenv import load_dotenv

from divergen.assistant import Assistant

load_dotenv()


@pytest.fixture
def assistant():
    _clean_dummy_files()
    _create_dummy_files()
    return Assistant()


def _clean_dummy_files():
    if os.path.exists("./src"):
        shutil.rmtree("./src")
    if os.path.exists("./tests"):
        shutil.rmtree("./tests")
    if os.path.exists("./docs"):
        shutil.rmtree("./docs")


def _create_dummy_files():
    os.mkdir("./src")
    with open("./src/dummy_module.py", "w") as f:
        f.write("def dummy_function():\n    pass\n")


def test_init_configs(assistant):
    if os.path.exists(".divergen"):
        shutil.rmtree("./.divergen")
    assistant.init_configs()
    assert os.path.exists(".divergen")
    assert os.path.exists(".divergen/assistant.yaml")
    assert os.path.exists(".divergen/prompts.yaml")


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
    assert os.path.exists("./.divergen/backup/dummy_module.py")


def test_reject_changes(assistant):
    if os.path.exists("./.divergen/backup/"):
        shutil.rmtree("./.divergen/backup/")
    _monkeypatch_model(assistant)
    assistant.execute_prompt("instructions")
    assistant.reject_changes()
    assert not os.path.exists("./src/dummy_module_preview.py")
    assert not os.path.exists("./.divergen/backup/dummy_module.py")


def test_cleanup():
    _clean_dummy_files()
    if os.path.exists(".divergen"):
        shutil.rmtree("./.divergen")
