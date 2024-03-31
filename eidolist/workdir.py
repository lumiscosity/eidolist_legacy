from os.path import exists

from PySide6.QtWidgets import QFileDialog


def set_workdir(directory: str):
    with open("workdir.txt", 'w') as file:
        file.write(directory)


def get_workdir() -> str:
    with open("workdir.txt") as file:
        return file.read()


# Returns True is the workdir file and the directory it points to exist.
# Returns False otherwise.
def check_workdir() -> bool:
    if exists("workdir.txt"):
        with open("workdir.txt") as file:
            return exists(file.read())
    else:
        return False


