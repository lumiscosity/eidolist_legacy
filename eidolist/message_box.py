# Convenience classes for message boxes.
import shutil

from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QPushButton, QDialog, QVBoxLayout, QLabel, QPlainTextEdit, \
    QDialogButtonBox, QWidget, QGridLayout, QFrame

loader = QUiLoader()


class MessageBox(QMessageBox):
    def __init__(self, text):
        super().__init__()
        self.setWindowTitle("Eidolist")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setText(text)
        self.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)


class WarningBox(QDialog):
    def __init__(self, text, field_text):
        super().__init__()
        self.setWindowTitle("Eidolist")
        self.setWindowIcon(QIcon("icon.ico"))

        self.setLayout(QVBoxLayout())

        self.dialogText = QLabel(text)
        self.dialogWarnings = QPlainTextEdit(field_text)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)

        self.layout().addWidget(self.dialogText)
        self.layout().addWidget(self.dialogWarnings)
        self.layout().addWidget(self.buttonBox)


class ProgressBox(QProgressDialog):
    def __init__(self, text, item_count, parent):
        super().__init__(labelText=text, parent=parent)
        bogus = QPushButton()
        self.setWindowTitle("Eidolist")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setCancelButton(bogus)
        bogus.hide()
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setMaximum(item_count)