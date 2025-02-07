from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QWidget


class SpinBox(QDoubleSpinBox):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)
        self.setDecimals(0)
        self.setFixedWidth(45)
        self.setRange(0, 999999999)
        self.setDecimals(0)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.wheelEvent = lambda event: self.parent().wheelEvent(event)
        self.setFixedHeight(30)


class TimeSpinBox(QWidget):
    dateTimeChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)

        # Create QDoubleSpinBoxes for days, hours, minutes, and seconds
        self.days_spinbox = SpinBox(self)
        self.days_spinbox.setSuffix("d")
        self.days_spinbox.setStyleSheet(
            "border-top-right-radius: 0; border-bottom-right-radius: 0;"
        )

        self.hours_spinbox = SpinBox(self)
        self.hours_spinbox.setSuffix("h")
        self.hours_spinbox.setStyleSheet("border-radius: 0;")

        self.minutes_spinbox = SpinBox(self)
        self.minutes_spinbox.setSuffix("m")
        self.minutes_spinbox.setStyleSheet("border-radius: 0;")

        self.seconds_spinbox = SpinBox(self)
        self.seconds_spinbox.setSuffix("s")
        self.seconds_spinbox.setStyleSheet(
            "border-top-left-radius: 0; border-bottom-left-radius: 0;"
        )

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.days_spinbox)
        layout.addWidget(self.hours_spinbox)
        layout.addWidget(self.minutes_spinbox)
        layout.addWidget(self.seconds_spinbox)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

        self.days_spinbox.valueChanged.connect(self.emit_dateTimeChanged)
        self.hours_spinbox.valueChanged.connect(self.emit_dateTimeChanged)
        self.minutes_spinbox.valueChanged.connect(self.emit_dateTimeChanged)
        self.seconds_spinbox.valueChanged.connect(self.emit_dateTimeChanged)

        self.setFixedWidth(180)

    def emit_dateTimeChanged(self):
        self.dateTimeChanged.emit(self.value())

    def setValue(self, total_seconds):
        days = total_seconds // 86400
        remaining_seconds = total_seconds % 86400
        hours = remaining_seconds // 3600
        remaining_seconds %= 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        self.days_spinbox.setValue(days)
        self.hours_spinbox.setValue(hours)
        self.minutes_spinbox.setValue(minutes)
        self.seconds_spinbox.setValue(seconds)

    def value(self):
        days = int(self.days_spinbox.value())
        hours = int(self.hours_spinbox.value())
        minutes = int(self.minutes_spinbox.value())
        seconds = int(self.seconds_spinbox.value())

        total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
        return total_seconds
