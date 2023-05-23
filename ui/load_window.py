import math
from functools import partial

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)


class LoadWindow(QWidget):
    """Loading animation window"""

    def __init__(self, parent=None):
        super().__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setPalette(palette)
        self.setFixedSize(300, 300)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.show()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # painter.fillRect(event.rect(), QBrush(QColor(44, 44, 44, 180)))

        amount_of_circles = 12

        for i in range(amount_of_circles):
            painter.setPen(QPen(Qt.NoPen))
            if (self.counter) % amount_of_circles == i:
                self.draw_outline(painter, i, amount_of_circles)
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i + 4:
                self.draw_outline(painter, i, amount_of_circles)
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i + 8:
                self.draw_outline(painter, i, amount_of_circles)
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i - 4:
                self.draw_outline(painter, i, amount_of_circles)
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i - 8:
                self.draw_outline(painter, i, amount_of_circles)
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            else:
                painter.setBrush(QBrush(QColor(39, 39, 39)))
            # else: painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                int(
                    self.width() / 2
                    + 50 * math.cos(2 * math.pi * i / amount_of_circles)
                    - 20 + 10
                ),
                int(
                    self.height() / 2.2
                    + 50 * math.sin(2 * math.pi * i / amount_of_circles)
                    - 20 + 10
                ),
                20,
                20,
            )
            painter.setPen(QPen(QColor(250, 250, 250), 0))
            painter.setFont(QFont("Calbri", 20, 0))
            painter.drawText(
                int(self.width() / 2 - 80),
                int(self.height() / 1.3),
                200,
                50,
                Qt.AlignLeft | Qt.AlignLeft,
                f"I am loading{'.'*(self.counter%4)}",
            )

        painter.end()

    def draw_outline(self, painter, i, amount_of_circles):
        """
        This function draws an ellipse with a specific position and size using the QPainter object in
        Python.
        
        Args:
          painter: The QPainter object used to draw the ellipse.
          i: The index of the circle being drawn in the loop.
          amount_of_circles: The total number of circles to be drawn in the outline.
        """
        painter.setBrush(QBrush(QColor(0, 251, 255)))
        painter.drawEllipse(
            int(self.width() / 2 + 50 * math.cos(2 * math.pi * i / amount_of_circles) - 21) + 10, 
            int(self.height() / 2.2 + 50 * math.sin(2 * math.pi * i / amount_of_circles) - 21) + 10,
            22,
            22,
        )

    def showEvent(self, event):
        self.timer = self.startTimer(100)
        self.counter = 0

    def timerEvent(self, event):
        self.counter += 1
        self.update()

if __name__ == '__main__':
    app = QApplication([])
    load_window = LoadWindow()
    app.exec_()