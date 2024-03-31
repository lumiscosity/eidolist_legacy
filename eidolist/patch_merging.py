from os.path import exists

from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QFileDialog, QDialog, QWidget

from eidolist.message_box import MessageBox

loader = QUiLoader()


class PatchMergingWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.patchdir = None

        # get the patch
        self.change_patchdir()
        if not self.patchdir:
            self.close()
            return

        # load the ui file
        self.ui = loader.load("ui/patch_merging.ui", None)

        # final touches
        self.ui.setWindowIcon(QIcon("icon.ico"))
        self.ui.show()

    def change_patchdir(self):
        MessageBox(
            "Before proceeding, make sure that you have placed the changelog in the patch as **changelog.txt**.").exec()

        new_patchdir = QFileDialog.getExistingDirectory(self, "Select the working directory (main copy):", "/")
        if exists(new_patchdir):
            if exists(new_patchdir + "/changelog.txt"):
                self.patchdir = new_patchdir
            else:
                MessageBox("Failed to find **changelog.txt**.").exec()
        elif new_patchdir != "":
            MessageBox("Failed to find the project folder.").exec()
        else:
            self.close()
            return
