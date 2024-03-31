# Convenience class for message boxes.
from PySide6 import QtCore
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox


class MessageBox(QMessageBox):
    def __init__(self, text):
        super().__init__()
        self.setWindowTitle("Eidolist")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setText(text)
        self.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)

