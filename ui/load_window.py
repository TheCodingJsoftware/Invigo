import math
from functools import partial

from PyQt6 import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)


class LoadWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.WIDTH, self.HEIGHT = 1000, 400
        self.ANIMATION_DURATION: int = 7000

        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet("background-color: transparent;")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setStyleSheet("QWidget{border-radius: 25px; background-color: rgba:(0,0,0,0);}")
        widget = QWidget(self)
        widget.resize(300, 150)
        widget.setObjectName("widget")
        widget.setStyleSheet(
            "QWidget#widget{ border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:10px; border-bottom-right-radius:10px; border: 1px solid #3daee9; background-color: #292929;}"
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        shadow.setColor(QColor(61, 174, 233, 255))
        shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        widget.setGraphicsEffect(shadow)
        widget.move(QPoint(400, 120))
        self.progress_text = QLabel(widget)
        self.progress_text.setStyleSheet("color: white; font-size: 100px; font-family: Vivaldi;")
        self.progress_text.setText("Invigo")
        self.progress_text.setFixedSize(self.WIDTH - 20, 120)
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.progress_text.move(QPoint(-350, 10))
        # Set the window flags to achieve a translucent background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowTransparentForInput | Qt.WindowType.WindowStaysOnTopHint)

        # Set a background color with transparency

        widget = QWidget(self)
        widget.resize(self.WIDTH, self.HEIGHT)
        self.anim_group = QParallelAnimationGroup(widget)
        DEGREE: int = 360
        CIRCLE_RADIUS: int = 30
        starting_value: int = 0
        for _ in range(10):
            progress_bar = QWidget(widget)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(0, 0, 0, 255))
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            progress_bar.setGraphicsEffect(shadow)
            progress_bar.setStyleSheet("background-color: #3daee9; border-radius: 15px; border: 3px solid #101010;")
            progress_bar.resize(CIRCLE_RADIUS, CIRCLE_RADIUS)
            self.anim = QPropertyAnimation(progress_bar, b"pos")
            self.anim.setDuration(self.ANIMATION_DURATION)
            self.anim.setEasingCurve(QEasingCurve.Type.OutInElastic)
            self.anim_2 = QPropertyAnimation(progress_bar, b"size")
            self.anim_2.setStartValue(QSize(CIRCLE_RADIUS, CIRCLE_RADIUS))
            self.anim_2.setEndValue(QSize(CIRCLE_RADIUS, CIRCLE_RADIUS))
            self.anim_group.addAnimation(self.anim_2)
            for i in range(DEGREE):
                angle_radians = math.radians(i) + starting_value
                x: int = int(math.cos(angle_radians) * 80) + 200
                y: int = int(math.sin(angle_radians) * 80) + 180
                if i == 0:
                    self.anim.setStartValue(QPoint(x, y))
                if i % 90 == 0:
                    self.anim.setKeyValueAt(i / DEGREE, QPoint(x, y))
                # if i%180 == 0:
                #     self.anim.setKeyValueAt(i/DEGREE, QPoint(int(math.cos(angle_radians)*100)+200, int(math.sin(angle_radians)*100)+200))
                if i == DEGREE - 1:
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


if __name__ == "__main__":
    app = QApplication([])
    load_window = LoadWindow()
    load_window.show()
    app.exec()
