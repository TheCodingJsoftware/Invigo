from datetime import datetime, timedelta

from PyQt6.QtCore import QDateTime, QEvent, QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QDoubleSpinBox


class MachineCutTimeDoubleSpinBox(QDoubleSpinBox):
    # ! IF VALUE IS SET TO 1, THAT IS 1 SECOND
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 99999999)
        self.setSingleStep(0.001)
        self.setDecimals(9)
        self.setWrapping(True)
        self.setAccelerated(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        regex = QRegularExpression(r"\d+.\d{2}")
        validator = QRegularExpressionValidator(regex, self)
        self.lineEdit().setValidator(validator)

        self.installEventFilter(self)

    def focusInEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super().focusOutEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            return super().wheelEvent(event)
        else:
            event.ignore()

    def eventFilter(self, obj, event: QEvent):
        if event.type() == QEvent.Type.Wheel and self.hasFocus():
            delta = event.angleDelta().y() / 120
            self.changeValue(delta)
            return True

        return super().eventFilter(obj, event)

    def changeValue(self, delta):
        current_value = self.value()

        if delta > 0:
            # Increase the value
            if current_value >= 5 * 3600:  # 5 hours
                self.setValue(current_value + 3600)  # Increase by 1 hour
            elif current_value >= 3600:  # 1 hour
                self.setValue(current_value + 60)  # Increase by 1 minute
            else:
                self.setValue(current_value + 1)  # Increase by 1 second
        elif delta < 0:
            # Decrease the value
            if current_value >= 5 * 3600:  # 5 hours
                self.setValue(current_value - 3600)  # Decrease by 1 hour
            elif current_value >= 3600:  # 1 hour
                self.setValue(current_value - 60)  # Decrease by 1 minute
            else:
                self.setValue(current_value - 1)  # Decrease by 1 second

    def textFromValue(self, value):
        hours = int(value // 3600)
        minutes = int((value % 3600) // 60)
        seconds = int(value % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def valueFromText(self, text):
        parts = text.split()
        hours = int(parts[0][:2])
        minutes = int(parts[1][:2])
        seconds = int(parts[2][:2])
        return hours * 3600 + minutes * 60 + seconds

    def fixup(self, text):
        time_parts = text.split(" ")
        if len(time_parts) == 6:
            days = int(time_parts[0])
            hours = int(time_parts[2])
            minutes = int(time_parts[4])
            if days == 1:
                time_parts[0] = f"0{time_parts[0]}"
            if hours == 1:
                time_parts[2] = f"0{time_parts[2]}"
            if minutes == 1:
                time_parts[4] = f"0{time_parts[4]}"
            return " ".join(time_parts)

        return text

    def get_time_delta(self) -> datetime:
        value = self.value()

        days = int(value)
        hours = int((value - days) * 24)
        minutes = int(((value - days) * 24 - hours) * 60)

        current_date_time = QDateTime.currentDateTime()
        end_date_time = current_date_time.addDays(days).addSecs(
            hours * 3600 + minutes * 60
        )

        time_delta = (
            end_date_time.toSecsSinceEpoch() - current_date_time.toSecsSinceEpoch()
        )
        return timedelta(seconds=time_delta)
