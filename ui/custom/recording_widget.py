from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtWidgets import QWidget


class RecordingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.recording = True
        self.recording_color = QColor("red")
        self.nonrecording_color = QColor("#8C8C8C")
        self.current_color = self.nonrecording_color
        self.scale = 1.0
        self.scale_factor = 0.01
        self.scale_direction = 0.1
        self.animation_duration = 3000
        self.elapsed_time = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateAnimation)
        self.timer.start(1)  # Update every 20 milliseconds

    def set_recording(self, recording):
        self.recording = recording

    def updateAnimation(self):
        if self.recording:
            self.elapsed_time += self.timer.interval()
            if self.elapsed_time >= self.animation_duration:
                self.elapsed_time = 0

            progress = self.elapsed_time / self.animation_duration
            scale_progress = 1 - (2 * abs(progress - 0.5) * 0.3)
            self.scale = scale_progress

            self.current_color = self.interpolateColors(self.recording_color, QColor("darkred"), scale_progress)
        else:
            self.elapsed_time = 0
            self.scale = 1.0
            self.current_color = self.interpolateColors(self.nonrecording_color, self.recording_color, 1.0)

        self.update()

    def interpolateColors(self, start_color, end_color, progress):
        red = int(start_color.red() + progress * (end_color.red() - start_color.red()))
        green = int(start_color.green() + progress * (end_color.green() - start_color.green()))
        blue = int(start_color.blue() + progress * (end_color.blue() - start_color.blue()))

        return QColor(red, green, blue)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(self.current_color))

        # Calculate the center of the widget
        center = self.rect().center()

        # Calculate the radius of the circle based on the widget size
        radius = int(min(self.rect().width(), self.rect().height()) / 2)

        # Adjust the radius based on the scale
        radius = int(radius * self.scale)

        # Calculate the top-left corner of the circle bounding rectangle
        x = center.x() - radius
        y = center.y() - radius

        # Draw the circle
        painter.drawEllipse(x, y, 2 * radius, 2 * radius)
