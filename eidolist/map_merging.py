import os
import shutil
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QStackedLayout, QLabel, QGraphicsOpacityEffect

from eidolist.selector_grid import SelectorGrid

loader = QUiLoader()


class MapMergingLayer(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.setPixmap(pixmap)
        self.op = QGraphicsOpacityEffect(self)
        self.op.setOpacity(1)
        self.setGraphicsEffect(self.op)
        self.setAutoFillBackground(True)

    def set_visibility(self, setting: Qt.CheckState):
        print(bool(setting))
        self.setVisible(bool(setting))

    def set_transparency(self, setting: Qt.CheckState):
        self.op.setOpacity(1 - (0.5 * setting))


class MapMergingWindow(QWidget):
    def __init__(self, map_id, workdir, patchdir):
        super().__init__()

        self.workdir = workdir
        self.patchdir = patchdir

        # TODO: Set up the UI

        self.ui = loader.load("ui/map_merging.ui", None)
        self.ui.setWindowIcon(QIcon("icon.ico"))

        self.ui.scrollAreaLayout = QStackedLayout()
        self.ui.scrollAreaLayout.setStackingMode(QStackedLayout.StackAll)
        self.ui.scrollAreaWidgetContents.setLayout(self.ui.scrollAreaLayout)

        # Generate the map pictures and pin them to the scrollview

        # lmu2png is awful, because we need lmu files in the main copy folder
        # unfortunately the main copy folder notably includes The Main Copy Of The Map Itself

        subprocess.run(f"{os.getcwd() + '/lmu2png.exe'} "
                       f'"{workdir}/{map_id}.lmu" '
                       f"-o {os.getcwd()}/temp_main/{map_id}l.png "
                       f"--no-background "
                       f"--no-uppertiles --no-events")
        subprocess.run(f"{os.getcwd() + '/lmu2png.exe'} "
                       f'"{workdir}/{map_id}.lmu" '
                       f"-o {os.getcwd()}/temp_main/{map_id}u.png "
                       f"--no-background "
                       f"--no-lowertiles --no-events")
        subprocess.run(f"{os.getcwd() + '/lmu2png.exe'} "
                       f'"{workdir}/{map_id}.lmu" '
                       f"-o {os.getcwd()}/temp_main/{map_id}e.png "
                       f"--no-background "
                       f"--no-lowertiles --no-uppertiles")

        shutil.move(f"{workdir}/{map_id}.lmu", f"{os.getcwd()}/temp_main/{map_id}.lmu")
        shutil.move(f"{patchdir}/{map_id}.lmu", f"{workdir}/{map_id}.lmu")
        subprocess.run(f"{os.getcwd() + '/lmu2png.exe'} "
                       f'"{workdir}/{map_id}.lmu" '
                       f"-o {os.getcwd()}/temp_patch/{map_id}l.png "
                       f"--no-background "
                       f"--no-uppertiles --no-events")
        subprocess.run(f"{os.getcwd() + '/lmu2png.exe'} "
                       f'"{workdir}/{map_id}.lmu" '
                       f"-o {os.getcwd()}/temp_patch/{map_id}u.png "
                       f"--no-background "
                       f"--no-lowertiles --no-events")
        subprocess.run(f"{os.getcwd() + '/lmu2png.exe'} "
                       f'"{workdir}/{map_id}.lmu" '
                       f"-o {os.getcwd()}/temp_patch/{map_id}e.png "
                       f"--no-background "
                       f"--no-lowertiles --no-uppertiles")
        shutil.move(f"{workdir}/{map_id}.lmu", f"{patchdir}/{map_id}.lmu")
        shutil.move(f"{os.getcwd()}/temp_main/{map_id}.lmu", f"{workdir}/{map_id}.lmu")

        self.pixmaps = [
            QPixmap(f"{os.getcwd()}/temp_main/{map_id}l.png"),
            QPixmap(f"{os.getcwd()}/temp_patch/{map_id}l.png"),
            QPixmap(f"{os.getcwd()}/temp_main/{map_id}u.png"),
            QPixmap(f"{os.getcwd()}/temp_patch/{map_id}u.png"),
            QPixmap(f"{os.getcwd()}/temp_main/{map_id}e.png"),
            QPixmap(f"{os.getcwd()}/temp_patch/{map_id}e.png"),
        ]

        if self.pixmaps[0].size() != self.pixmaps[1].size():
            print("Map sizes don't match, manual intervention is required")

        holders = []
        for i in self.pixmaps:
            holders.append(MapMergingLayer(i))

        self.ui.mainLowerCheckbox.clicked.connect(holders[0].set_visibility)
        self.ui.mainUpperCheckbox.clicked.connect(holders[2].set_visibility)
        self.ui.mainEventCheckbox.clicked.connect(holders[4].set_visibility)
        self.ui.patchLowerCheckbox.clicked.connect(holders[1].set_visibility)
        self.ui.patchUpperCheckbox.clicked.connect(holders[3].set_visibility)
        self.ui.patchEventCheckbox.clicked.connect(holders[5].set_visibility)

        self.ui.mainTransparentCheckbox.clicked.connect(holders[0].set_transparency)
        self.ui.mainTransparentCheckbox.clicked.connect(holders[2].set_transparency)
        self.ui.mainTransparentCheckbox.clicked.connect(holders[4].set_transparency)
        self.ui.patchTransparentCheckbox.clicked.connect(holders[1].set_transparency)
        self.ui.patchTransparentCheckbox.clicked.connect(holders[3].set_transparency)
        self.ui.patchTransparentCheckbox.clicked.connect(holders[5].set_transparency)

        for i in reversed(holders):
            self.ui.scrollAreaLayout.addWidget(i)

        self.map_x = self.pixmaps[0].size().width() // 16
        self.map_y = self.pixmaps[0].size().height() // 16

        # Add and connect the grid selection

        self.ui.selectorGrid = SelectorGrid(self.map_x, self.map_y)
        self.ui.scrollAreaLayout.addWidget(self.ui.selectorGrid)
        self.ui.comboBox.activated.connect(self.ui.selectorGrid.changeLayer)
