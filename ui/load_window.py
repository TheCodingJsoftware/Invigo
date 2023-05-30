import math
from functools import partial

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import math
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)


class LoadWindow(QWidget):
    """Loading animation window"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.WIDTH, self.HEIGHT = 1000, 400
        self.ANIMATION_DURATION: int = 7000

        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        widget = QWidget(self)
        widget.resize(300, 150)
        widget.setObjectName("widget")
        widget.setStyleSheet(
            "QWidget#widget{ border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:10px; border-bottom-right-radius:10px; border: 1px solid #3daee9; background-color: #292929;}"
        )
        widget.move(QPoint(400,120))
        self.progress_text = QLabel(widget)
        self.progress_text.setStyleSheet("color: white; font-size: 100px; font-family: Vivaldi;")
        self.progress_text.setText("Invigo")
        self.progress_text.setFixedSize(self.WIDTH - 20, 120)
        self.progress_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.progress_text.move(QPoint(-350,10))
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        widget = QWidget(self)
        widget.resize(self.WIDTH, self.HEIGHT)
        self.anim_group = QParallelAnimationGroup(widget)
        DEGREE: int = 360
        CIRCLE_RADIUS: int = 30
        starting_value: int = 0
        for _ in range(10):
            progress_bar = QWidget(widget)
            progress_bar.setStyleSheet(
                "background-color: #3daee9; border-radius: 15px; border: 3px solid #101010;"
            )
            progress_bar.resize(CIRCLE_RADIUS, CIRCLE_RADIUS)
            self.anim = QPropertyAnimation(progress_bar, b"pos")
            self.anim.setDuration(self.ANIMATION_DURATION)
            self.anim.setEasingCurve(QEasingCurve.OutInElastic)
            self.anim_2 = QPropertyAnimation(progress_bar, b"size")
            self.anim_2.setStartValue(QSize(CIRCLE_RADIUS, CIRCLE_RADIUS))
            self.anim_2.setEndValue(QSize(CIRCLE_RADIUS, CIRCLE_RADIUS))
            self.anim_group.addAnimation(self.anim_2)
            for i in range(DEGREE):
                angle_radians = math.radians(i) + starting_value
                x: int = int(math.cos(angle_radians)*80)+200
                y: int = int(math.sin(angle_radians)*80)+180
                if i == 0:
                    self.anim.setStartValue(QPoint(x, y))
                if i % 90 == 0:
                    self.anim.setKeyValueAt(i/DEGREE, QPoint(x, y))
                # if i%180 == 0:
                #     self.anim.setKeyValueAt(i/DEGREE, QPoint(int(math.cos(angle_radians)*100)+200, int(math.sin(angle_radians)*100)+200))
                if i == DEGREE-1:
                    self.anim.setEndValue(QPoint(x, y))
            starting_value += 120
            self.anim_group.addAnimation(self.anim)
            self.anim_group.addAnimation(self.anim_2)
        self.anim_group.setLoopCount(-1)
        self.show()
        self.start_animation()
        # timer = QTimer(self)
        # timer.setSingleShot(True)
        # timer.timeout.connect(self.start_animation)
        # timer.start(1000)  # 2000 milliseconds = 2 seconds

    def start_animation(self):
        self.anim_group.start()

if __name__ == '__main__':
    app = QApplication([])
    load_window = LoadWindow()
    app.exec_()