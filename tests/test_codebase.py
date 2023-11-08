from codeas.codebase import Codebase

from .utils import JAVA_FUNC, JS_FUNC, PY_FUNC, create_dummy_repo, remove_dummy_repo


def test_parse_modules():
    create_dummy_repo()
    codebase = Codebase()
    codebase.parse_modules()
    assert codebase.get_module("module1.py").code == PY_FUNC
    assert codebase.get_module("module2.java").code == JAVA_FUNC
    assert codebase.get_module("module3.js").code == JS_FUNC
    remove_dummy_repo()
