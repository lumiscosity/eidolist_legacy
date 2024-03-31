from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPixmap, QPainter, QMouseEvent, QPaintEvent, QPen, QColor, QImage
from PySide6.QtWidgets import QLabel, QWidget


# Convenience code for the images in the map tile picker.
class SelectorImage(QLabel):
    def __init__(self, path):
        super().__init__()
        self.setPixmap(QPixmap().load(path))

    def set_transparent(self, transparency: bool):
        pass


# The selector grid is an object that captures mouse events to let you select tiles.
# It itself is a widget with a pixmap; this pixmap is used to display the highlights.
class SelectorGrid(QWidget):
    # map_x and map_y are the map size in tiles
    def __init__(self, map_x, map_y):
        super().__init__()

        self.layer = "lower"
        self.draw_mode = True  # True for draw, False for erase
        self.lower_sel = set()
        self.upper_sel = set()
        self.event_sel = set()
        self.map_x = map_x
        self.map_y = map_y

        self.setFixedSize(map_x * 16, map_y * 16)
        self.image = QPixmap(map_x * 16, map_y * 16)
        self.image.fill(QColor(0, 0, 0, 0))

        self.previous_pos = None
        self.painter = QPainter()
        self.painter.setBackgroundMode(Qt.BGMode.TransparentMode)
        self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.image)

    def mousePressEvent(self, event: QMouseEvent):
        self.previous_pos = event.position().toPoint()
        current_pos = event.position().toPoint()
        pos1 = current_pos.x() // 16
        pos2 = current_pos.y() // 16
        pos = (pos1, pos2)
        if 0 < pos1 < self.map_x and 0 < pos2 < self.map_y:
            if self.layer == "lower":
                self.draw_mode = not bool(self.lower_sel & {pos})
            elif self.layer == "upper":
                self.draw_mode = not bool(self.upper_sel & {pos})
            elif self.layer == "event":
                self.draw_mode = not bool(self.event_sel & {pos})
        self.mouseMoveEvent(event)
        QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        current_pos = event.position().toPoint()
        pen = QPen()
        # mark the tile as selected/deselected
        pos1 = current_pos.x() // 16
        pos2 = current_pos.y() // 16
        pos = (pos1, pos2)
        if 0 < pos1 < self.map_x and 0 < pos2 < self.map_y:
            if self.layer == "lower":
                if self.draw_mode:
                    self.lower_sel.add((pos1, pos2))
                else:
                    try:
                        self.lower_sel.remove((pos1, pos2))
                    except KeyError:
                        pass
            elif self.layer == "upper":
                if self.draw_mode:
                    self.upper_sel.add((pos1, pos2))
                else:
                    try:
                        self.upper_sel.remove((pos1, pos2))
                    except KeyError:
                        pass
            elif self.layer == "event":
                if self.draw_mode:
                    self.event_sel.add((pos1, pos2))
                else:
                    try:
                        self.event_sel.remove((pos1, pos2))
                    except KeyError:
                        pass
            # calculate the new colour for the tile and draw it
            self.painter.begin(self.image)
            self.painter.setRenderHints(QPainter.Antialiasing, False)
            self.painter.setPen(pen)
            pos1 = current_pos.x() - (current_pos.x() % 16)
            pos2 = current_pos.y() - (current_pos.y() % 16)
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            self.painter.eraseRect(QRect(pos1, pos2, 16, 16))
            self.painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            self.painter.setOpacity(50)
            col_base = [0, 0, 0]
            if self.lower_sel & {pos}:
                col_base[0] = 200
            if self.upper_sel & {pos}:
                col_base[1] = 200
            if self.event_sel & {pos}:
                col_base[2] = 200
            if col_base != [0, 0, 0]:
                pen.setColor(QColor(col_base[0], col_base[1], col_base[2]))
                self.painter.setOpacity(0.6)
                self.painter.fillRect(QRect(pos1, pos2, 16, 16), pen.color())
            self.painter.end()
        self.previous_pos = current_pos
        self.update()

        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.previous_pos = None
        QWidget.mouseReleaseEvent(self, event)

    def setDrawMode(self, checked):
        self.draw_mode = checked

    def changeLayer(self, layer):
        if layer == 0:
            self.layer = "lower"
        elif layer == 1:
            self.layer = "upper"
        elif layer == 2:
            self.layer = "event"
