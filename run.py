from PySide6.QtWidgets import QApplication

from eidolist.main_window import MainWindow
from eidolist.map_merging import MapMergingWindow

app = QApplication()
window = MainWindow()
# window = MapMergingWindow("Map0121", "E:\games and tools\dev\cu_meta\CU_240316", "E:\games and tools\dev\cu_meta\som_submit")
window.ui.show()
app.exec()
