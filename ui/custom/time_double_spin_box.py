from datetime import datetime, timedelta

from PyQt6.QtCore import QDateTime, QEvent, QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QDoubleSpinBox


class TimeSpinBox(QDoubleSpinBox):
    # ! IF VALUE IS SET TO 1, THAT IS 1 DAY
    def __init__(self, parent=None):
        super(TimeSpinBox, self).__init__(parent)
        self.setRange(0, 99999999)
        self.setSingleStep(0.001)
        self.setDecimals(9)
        self.setFixedWidth(200)
        self.setWrapping(True)
        self.setAccelerated(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        regex = QRegularExpression(r"\d+.\d{2}")
        validator = QRegularExpressionValidator(regex, self)
        self.lineEdit().setValidator(validator)

        self.installEventFilter(self)

    def focusInEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(TimeSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(TimeSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            return super(TimeSpinBox, self).wheelEvent(event)
        else:
            event.ignore()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and self.hasFocus():
            delta = event.angleDelta().y() / 120
            self.changeValue(delta)
            return True

        return super().eventFilter(obj, event)

    def changeValue(self, delta):
        current_value = self.value()

        if delta > 0:
            # Increase the value
            if current_value >= 1:  # day
                self.setValue(current_value + 1)
            elif current_value >= 0.5:
                self.setValue(current_value + 0.0416666666666667)
            else:
                self.setValue(current_value + 0.000694444444444444)
        elif delta < 0:
            # Decrease the value
            if current_value >= 1:
                self.setValue(current_value - 1)
            elif current_value >= 0.5:
                self.setValue(current_value - 0.0416666666666667)
            else:
                self.setValue(current_value - 0.000694444444444444)

    def textFromValue(self, value):
        days = int(value)
        hours = int((value - days) * 24)
        minutes = int(((value - days) * 24 - hours) * 60)
        return f"{days} day{'s' if days != 1 else ''} {hours:02d} hour{'s' if hours != 1 else ''} {minutes:02d} minute{'s' if minutes != 1 else ''}"

    def valueFromText(self, text):
        time_parts = text.split(" ")
        days = int(time_parts[0])
        hours = int(time_parts[2])
        minutes = int(time_parts[4])
        return days + hours / 24 + minutes / (24 * 60)

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
        end_date_time = current_date_time.addDays(days).addSecs(hours * 3600 + minutes * 60)

        time_delta = end_date_time.toSecsSinceEpoch() - current_date_time.toSecsSinceEpoch()
        return timedelta(seconds=time_delta)
