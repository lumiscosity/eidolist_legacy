from os.path import exists

from PySide6 import QtCore
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QFileDialog
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

        # connect the buttons
        self.ui.workdirButton.clicked.connect(self.change_workdir)
        self.ui.patchButton.clicked.connect(self.start_patch_merging)

        # final touches
        self.ui.setWindowIcon(QIcon("icon.ico"))
        self.ui.workdirLabel.setText(f"The current working directory is **{workdir.get_workdir()}**.")

    def start_patch_merging(self):
        self.patch_merging = PatchMergingWindow()

    def show(self):
        self.ui.show()

    def change_workdir(self):
        MessageBox("Before proceeding, make sure that you have placed the changelog in the main copy as **changelog.txt**.").exec()

        new_workdir = QFileDialog.getExistingDirectory(self, "Select the working directory (main copy):", "/")
        if exists(new_workdir):
            if exists(new_workdir + "/changelog.txt"):
                workdir.set_workdir(new_workdir)
                self.ui.workdirLabel.setText(f"The current working directory is **{new_workdir}**.")
            else:
                MessageBox("Failed to find **changelog.txt**.").exec()
        elif new_workdir != "":
            MessageBox("Failed to find the project folder.").exec()

