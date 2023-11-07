import os
import shutil


def create_dummy_repo():
    os.makedirs("./dummy_repo/src")
    with open("./dummy_repo/src/module1.py", "w") as f:
        f.write("def dummy_function1():\n    pass\n")
    with open("./dummy_repo/src/module2.py", "w") as f:
        f.write("def dummy_function2():\n    pass\n")


def remove_dummy_repo():
    if os.path.exists("./dummy_repo"):
        shutil.rmtree("./dummy_repo")


def reset_dummy_repo():
    os.chdir("..")
    remove_dummy_repo()
    create_dummy_repo()
    os.chdir("./dummy_repo")
