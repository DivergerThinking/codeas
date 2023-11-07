import os
import shutil

PY_FUNC = "def dummy_function1():\n    pass\n"
JAVA_FUNC = "public String dummyFunction2() {\n    return 'dummy';\n}\n"
JS_FUNC = "function dummyFunction3() {\n    return 'dummy';\n}\n"


def create_dummy_repo():
    os.makedirs("./dummy_repo/src")
    with open("./dummy_repo/src/module1.py", "w") as f:
        f.write(PY_FUNC)
    with open("./dummy_repo/src/module2.java", "w") as f:
        f.write(JAVA_FUNC)
    with open("./dummy_repo/src/module3.js", "w") as f:
        f.write(JS_FUNC)


def remove_dummy_repo():
    if os.path.exists("./dummy_repo"):
        shutil.rmtree("./dummy_repo")


def reset_dummy_repo():
    os.chdir("..")
    remove_dummy_repo()
    create_dummy_repo()
    os.chdir("./dummy_repo")
