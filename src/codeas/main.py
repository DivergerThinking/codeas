import os
import subprocess


def start_ui():
    # get the directory of the current script file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # construct the relative path to Home.py
    home_path = os.path.join(dir_path, "ui", "🏠_Home.py")
    # run shell command "streamlit run Home.py"
    subprocess.run(["streamlit", "run", home_path])


if __name__ == "__main__":
    start_ui()
