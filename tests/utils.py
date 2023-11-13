import os
import shutil

PY_FUNC = "def dummy_function():\n    pass\n"
JAVA_FUNC = "public String dummyFunction() {\n    return 'dummy';\n}\n"
JS_FUNC = "function dummyFunction() {\n    return 'dummy';\n}\n"
TS_FUNC = "function dummyFunction(): string {\n    return 'dummy';\n}\n"
CSHARP_FUNC = "public string DummyFunction()\n{\n    return 'dummy';\n}\n"
RUST_FUNC = "fn dummy_function() {\n    // do something dummy\n}\n"
RUBY_FUNC = "def dummy_function\n  # do something dummy\nend\n"
C_FUNC = "#include <stdio.h>\n\nvoid dummyFunction() {\n    // do something dummy\n}\n"
GO_FUNC = 'package main\n\nimport "fmt"\n\nfunc dummyFunction() {\n    fmt.Println("dummy")\n}\n'
PHP_FUNC = "<?php\n\nfunction dummyFunction() {\n    return 'dummy';\n}\n"


def create_dummy_repo():
    if os.path.exists("./dummy_repo"):
        shutil.rmtree("./dummy_repo")
    os.makedirs("./dummy_repo/src")
    with open("./dummy_repo/src/module1.py", "w") as f:
        f.write(PY_FUNC)
    with open("./dummy_repo/src/module2.java", "w") as f:
        f.write(JAVA_FUNC)
    with open("./dummy_repo/src/module3.js", "w") as f:
        f.write(JS_FUNC)
    with open("./dummy_repo/src/module4.ts", "w") as f:
        f.write(TS_FUNC)
    with open("./dummy_repo/src/module5.cs", "w") as f:
        f.write(CSHARP_FUNC)
    with open("./dummy_repo/src/module6.rs", "w") as f:
        f.write(RUST_FUNC)
    with open("./dummy_repo/src/module7.rb", "w") as f:
        f.write(RUBY_FUNC)
    with open("./dummy_repo/src/module8.c", "w") as f:
        f.write(C_FUNC)
    with open("./dummy_repo/src/module9.go", "w") as f:
        f.write(GO_FUNC)
    with open("./dummy_repo/src/module10.php", "w") as f:
        f.write(PHP_FUNC)
    os.chdir("./dummy_repo")


def remove_dummy_repo():
    os.chdir("..")
    if os.path.exists("./dummy_repo"):
        shutil.rmtree("./dummy_repo")
