from PySide6.QtWidgets import QApplication
from eidolist.main_window import MainWindow


app = QApplication()
window = MainWindow()
window.show()
app.exec()
