import sys

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPolygon
from PyQt6.QtWidgets import QApplication, QWidget


class DraggableRotatableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(1080 * 3)
        self.setFixedWidth(1920 * 3)
        self.ruler_length = 500
        self.ruler_width = 40
        self.dragging = False
        self.rotation = 0
        self.offset = QPoint()

    def mousePressEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal(event.pos()) - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = int(event.angleDelta().y() / 30)  # Get the scroll wheel delta value
            self.ruler_length += delta  # Adjust the ruler length based on the scroll wheel movement
        else:
            delta = event.angleDelta().y() / 500
            self.rotation += delta
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        offset = self.ruler_width // 2

        # Translate the painter to the center of the widget
        painter.translate(self.width() // 3, self.height() // 3)

        # Rotate the painter by the specified angle
        painter.rotate(self.rotation)
        rect = QRect(int(-self.ruler_width / 2), (-self.ruler_length + (self.ruler_width // 2)), self.ruler_width, self.ruler_length)

        # Create a QPolygon based on the rotated rectangle coordinates
        polygon = QPolygon([rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()])

        # Set the pen and brush for drawing the polygon
        pen = painter.pen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 255, 255, 140))
        painter.setPen(pen)

        brush = painter.brush()
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        brush.setColor(QColor(255, 255, 255, 1))
        painter.setBrush(brush)

        # Draw the rotated polygon
        painter.drawPolygon(polygon)
        pen = painter.pen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 255, 255, 255))
        painter.setPen(pen)
        lineStart = QPoint(0, (-self.ruler_length + (self.ruler_width // 2)))
        lineEnd = QPoint(0, -self.ruler_width // 2)
        painter.drawLine(lineStart, lineEnd)

        pen = painter.pen()
        pen.setWidth(1)
        pen.setColor(QColor(0, 0, 0, 255))
        painter.setPen(pen)

        lineStart = QPoint((self.ruler_width // 2), 0)
        lineEnd = QPoint(-(self.ruler_width // 2), 0)
        painter.drawLine(lineStart, lineEnd)

        lineStart = QPoint(0, (self.ruler_width // 2))
        lineEnd = QPoint(0, -(self.ruler_width // 2))
        painter.drawLine(lineStart, lineEnd)

        # Calculate the radius of the circle based on the ruler width
        circleRadius = self.ruler_width // 2

        brush = painter.brush()
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        brush.setColor(QColor(255, 255, 255, 25))
        painter.setBrush(brush)
        pen = painter.pen()
        pen.setWidth(0)
        painter.setPen(pen)

        # Set the circle thickness
        # Draw the circle at the rotation point
        painter.drawEllipse(QPoint(0, 0), circleRadius, circleRadius)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DraggableRotatableWidget()
    widget.show()
    sys.exit(app.exec())
