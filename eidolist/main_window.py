from os.path import exists
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QFileDialog
from PySide6.QtUiTools import QUiLoader
from eidolist import workdir

loader = QUiLoader()


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        # check the working directory
        if not workdir.check_workdir():
            workdir.set_workdir(
                QFileDialog.getExistingDirectory(self, "Select the working directory (main copy):", "/"))
        if not workdir.check_workdir():
            exit(1)

        # load the ui file
        self.ui = loader.load("ui/main_window.ui", None)

        # connect the buttons
        self.ui.workdirButton.clicked.connect(self.change_workdir)

        # final touches
        self.ui.setWindowIcon(QIcon("icon.ico"))
        self.ui.workdirLabel.setText(f"The current working directory is **{workdir.get_workdir()}**.")

    def show(self):
        self.ui.show()

    def change_workdir(self):
        new_workdir = QFileDialog.getExistingDirectory(self, "Select the working directory (main copy):", "/")
        if exists(new_workdir):
            workdir.set_workdir(new_workdir)
            self.ui.workdirLabel.setText(f"The current working directory is **{new_workdir}**.")

    def
