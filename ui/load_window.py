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
        painter.fillRect(event.rect(), QBrush(QColor(49, 54, 59, 180)))

        amount_of_circles = 12

        for i in range(amount_of_circles):
            painter.setPen(QPen(Qt.NoPen))
            if (self.counter) % amount_of_circles == i:
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i + 4:
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i + 8:
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i - 4:
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            elif (self.counter) % amount_of_circles == i - 8:
                painter.setBrush(QBrush(QColor(61, 174, 233)))
            else:
                painter.setBrush(QBrush(QColor(40, 40, 40)))
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

    def showEvent(self, event):
        self.timer = self.startTimer(100)
        self.counter = 0

    def timerEvent(self, event):
        self.counter += 1
        self.update()
