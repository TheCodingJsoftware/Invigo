import math
from functools import partial

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QDialog


class LoadWindow(QDialog):
    """Loading animation window"""

    def __init__(self):
        QDialog.__init__(self)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.setFixedSize(1024, 600)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.show()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(39, 44, 49, 180)))

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
                painter.setBrush(QBrush(QColor(30, 30, 30)))
            # else: painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                int(
                    self.width() / 2
                    + 50 * math.cos(2 * math.pi * i / amount_of_circles)
                    - 20
                ),
                int(
                    self.height() / 2.2
                    + 50 * math.sin(2 * math.pi * i / amount_of_circles)
                    - 20
                ),
                20,
                20,
            )
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.setFont(QFont("Arial", 20, 0))
            painter.drawText(
                int(self.width() / 2 - 80),
                int(self.height() / 1.5),
                200,
                50,
                Qt.AlignLeft | Qt.AlignLeft,
                "I am loading",
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
            int(self.width() / 2 + 50 * math.cos(2 * math.pi * i / amount_of_circles) - 21), 
            int(self.height() / 2.2 + 50 * math.sin(2 * math.pi * i / amount_of_circles) - 21),
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
    LoadWindow()