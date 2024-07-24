from os.path import exists
import random

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QFileDialog, QCheckBox, QPushButton
from PySide6.QtUiTools import QUiLoader
from eidolist import workdir
from eidolist.message_box import MessageBox
from eidolist.patch_merging import PatchMergingWindow

loader = QUiLoader()


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        # check the working directory
        if not workdir.check_workdir():
            self.change_workdir()
        if not workdir.check_workdir():
            exit(1)

        # load the ui file
        self.ui = loader.load("ui/main_window.ui", None)
        self.ui_initialized = True

        # connect the buttons
        self.ui.workdirButton.clicked.connect(self.change_workdir)
        self.ui.patchButton.clicked.connect(self.start_patch_merging)

        # final touches
        self.ui.setWindowIcon(QIcon("icon.ico"))
        self.ui.workdirLabel.setText(f"The current working directory is **{workdir.get_workdir()}**.")

        splashes = [
            "Removed Baldtsuki",
            "Hamsterhype!",
            "PROFITS!",
            "Back up your files!",
            "1GB of uncompressed music files, guaranteed!",
            "Big Minna Hell's Patches!",
            "Remember to playtest!",
            "Also try Yume 2kki!",
            "Collective Unconscious... 2!",
            ":3",
            "Gotta merge 'em all!"
        ]
        self.ui.splashLabel.setText(splashes[random.randint(0, len(splashes) - 1)])

    def start_patch_merging(self):
        self.patch_merging = PatchMergingWindow()

    def show(self):
        self.ui.show()

    def change_workdir(self):
        MessageBox(
            "Before proceeding, make sure that you have placed the changelog in the main copy as **changelog.txt**. "
            "If the file isn't found, an empty changelog will be made."
        ).exec()

        new_workdir = QFileDialog.getExistingDirectory(self, "Select the working directory (main copy):", "/")
        if exists(new_workdir):
            if not exists(new_workdir + "/changelog.txt"):
                with open(new_workdir + "/changelog.txt", 'w') as file:
                    file.write("|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|=|")
            workdir.set_workdir(new_workdir)
            if self.ui_initialized:
                self.ui.workdirLabel.setText(f"The current working directory is **{new_workdir}**.")
        elif new_workdir != "":
            MessageBox("Failed to find the project folder.").exec()
        else:
            MessageBox("Not a directory!").exec()
