from codeas.codebase import Codebase

from .utils import JAVA_FUNC, JS_FUNC, PY_FUNC, reset_dummy_repo


def test_parse_modules():
    reset_dummy_repo()
    codebase = Codebase()
    codebase.parse_modules()
    assert codebase.get_module("module1.py").code == PY_FUNC
    assert codebase.get_module("module2.py").code == JAVA_FUNC
    assert codebase.get_module("module3.py").code == JS_FUNC
