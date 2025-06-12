from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat
from PyQt6.QtWidgets import QApplication, QCalendarWidget

from ui.theme import theme_var


class DateRangeCalendar(QCalendarWidget):
    date_range_changed = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("select_range_calendar")
        self.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.from_date: QDate = QDate.currentDate()
        self.to_date: QDate = None

        self.highlighter_format = QTextCharFormat()
        # get the calendar default highlight setting
        self.highlighter_format.setBackground(QColor(theme_var("primary")))
        self.highlighter_format.setForeground(QColor("white"))
        self.highlighter_format.setFontWeight(400)

        # this will pass selected date value as a QDate object
        self.clicked.connect(self.select_range)

        self.load_theme()
        super().dateTextFormat()

    def get_timeline(self) -> tuple[QDate, QDate]:
        return self.from_date, self.to_date

    def load_theme(self):
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor("red"))  # Set the desired color
        weekend_format.setBackground(QColor(44, 44, 44, 130))

        weekday_format = QTextCharFormat()
        weekday_format.setForeground(QColor("white"))  # Set the desired color
        weekday_format.setBackground(QColor(65, 65, 65, 150))

        self.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Monday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Tuesday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Wednesday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Thursday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Friday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)

    def highlight_range(self, format):
        if self.from_date and self.to_date:
            d1: QDate = min(self.from_date, self.to_date)
            d2: QDate = max(self.from_date, self.to_date)
            while d1 <= d2:
                self.setDateTextFormat(d1, format)
                d1 = d1.addDays(1)

    def clear_highlight(self):
        today = QDate.currentDate()
        start_date = QDate(today.year(), 1, 1)
        end_date = QDate(today.year(), 12, 31)
        while start_date <= end_date:
            self.setDateTextFormat(start_date, QTextCharFormat())
            start_date = start_date.addDays(1)

    def select_range(self, date_value: QDate):
        self.clear_highlight()

        # check if a keyboard modifer is pressed
        if (
            QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier
            and self.from_date
        ):
            self.to_date = date_value
            if self.to_date < self.from_date:
                self.to_date, self.from_date = self.from_date, self.to_date
            self.highlight_range(self.highlighter_format)
        else:
            # required
            self.from_date = date_value
            self.to_date = None

        self.date_range_changed.emit((self.from_date, self.to_date))

    def set_range(self, date_value: QDate):
        self.highlight_range(QTextCharFormat())
        self.to_date = date_value
        if self.to_date < self.from_date:
            self.to_date, self.from_date = self.from_date, self.to_date
        self.highlight_range(self.highlighter_format)
