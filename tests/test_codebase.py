from codeas.codebase import Codebase

from .utils import (
    C_FUNC,
    CSHARP_FUNC,
    GO_FUNC,
    JAVA_FUNC,
    JS_FUNC,
    PHP_FUNC,
    PY_FUNC,
    RUBY_FUNC,
    RUST_FUNC,
    TS_FUNC,
    create_dummy_repo,
    remove_dummy_repo,
)


def test_parse_modules():
    create_dummy_repo()
    codebase = Codebase()
    codebase.parse_modules()

    assert codebase.get_module("src.module1.py").content == PY_FUNC
    assert codebase.get_module("src.module2.java").content == JAVA_FUNC
    assert codebase.get_module("src.module3.js").content == JS_FUNC
    assert codebase.get_module("src.module4.ts").content == TS_FUNC
    assert codebase.get_module("src.module5.cs").content == CSHARP_FUNC
    assert codebase.get_module("src.module6.rs").content == RUST_FUNC
    assert codebase.get_module("src.module7.rb").content == RUBY_FUNC
    assert codebase.get_module("src.module8.c").content == C_FUNC
    assert codebase.get_module("src.module9.go").content == GO_FUNC
    assert codebase.get_module("src.module10.php").content == PHP_FUNC
    remove_dummy_repo()
