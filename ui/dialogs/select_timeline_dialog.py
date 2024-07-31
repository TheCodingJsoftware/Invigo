from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QIcon, QTextCharFormat
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QCalendarWidget, QDialog


class SelectTimeLineDialog(QDialog):
    def __init__(
        self,
        message: str,
        starting_date: str,
        ending_date: str,
        parent,
    ):
        super().__init__(parent)
        uic.loadUi("ui/dialogs/select_timeline_dialog.ui", self)

        self.setWindowTitle("Set Timeline")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblMessage.setText(message)

        self.left_calendar.clicked.connect(self.update_selection)
        self.left_calendar.clicked.connect(self.use_set_days)
        self.left_calendar.currentPageChanged.connect(self.update_right_calendar_month)
        self.right_calendar.clicked.connect(self.update_selection)
        self.right_calendar.clicked.connect(self.set_new_days)
        self.days.valueChanged.connect(self.set_days)
        self.pushButton_set.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        if starting_date is not None:
            self.left_calendar.setSelectedDate(QDate.fromString(starting_date, "yyyy-MM-dd"))
        if ending_date is not None:
            self.right_calendar.setSelectedDate(QDate.fromString(ending_date, "yyyy-MM-dd"))

        self.from_date: QDate = None
        self.to_date: QDate = None

        self.update_selection()
        self.load_theme()

    def clearSelection(self):
        self.left_calendar.setSelectedDate(QDate.currentDate())
        self.right_calendar.setSelectedDate(QDate.currentDate())

    def update_right_calendar_month(self):
        left_page_year = self.left_calendar.yearShown()
        left_page_month = self.left_calendar.monthShown()
        next_month = QDate(left_page_year, left_page_month, 1).addMonths(1)
        self.right_calendar.setCurrentPage(next_month.year(), next_month.month())

    def set_new_days(self):
        if self.checkBox.isChecked():
            self.from_date = self.left_calendar.selectedDate()
            self.to_date = self.right_calendar.selectedDate()
            days = self.from_date.daysTo(self.to_date)
            self.days.setValue(days)
            self.right_calendar.setSelectedDate(self.left_calendar.selectedDate().addDays(self.days.value()))
            self.update_selection()

    def set_days(self):
        self.right_calendar.setSelectedDate(self.left_calendar.selectedDate().addDays(self.days.value()))
        self.update_selection()

    def use_set_days(self):
        if self.checkBox.isChecked():
            self.right_calendar.setSelectedDate(self.left_calendar.selectedDate().addDays(self.days.value()))
            self.update_selection()

    def update_selection(self):
        self.right_calendar.setMinimumDate(self.left_calendar.selectedDate())

        # self.right_calendar.highlight_range(QTextCharFormat())
        # self.left_calendar.highlight_range(QTextCharFormat())

        self.right_calendar.from_date = self.right_calendar.minimumDate()
        self.right_calendar.to_date = self.right_calendar.selectedDate()

        self.left_calendar.from_date = self.left_calendar.selectedDate()
        self.left_calendar.to_date = self.right_calendar.selectedDate()

        # The above code is highlighting a range of dates in a calendar.
        # self.right_calendar.highlight_range(self.right_calendar.highlighter_format)
        # self.left_calendar.highlight_range(self.left_calendar.highlighter_format)
        self.highlight_selection(self.left_calendar)
        self.highlight_selection(self.right_calendar)

        self.from_date = self.left_calendar.selectedDate()
        self.to_date = self.right_calendar.selectedDate()

        days = self.from_date.daysTo(self.to_date)
        weeks = days / 7

        if not self.checkBox.isChecked():
            self.days.setValue(days)

        self.selection_label.setText(f'Selection is from {self.from_date.toString("MMMM d")} to {self.to_date.toString("MMMM d")}, which is {days} days or {weeks:.1f} weeks.')
        self.label.setText(f'days from {self.from_date.toString("MMMM d")}')

    def highlight_selection(self, calendar: QCalendarWidget):
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#3daee9"))
        highlight_format.setForeground(QColor("white"))

        calendar.setDateTextFormat(QDate(), QTextCharFormat())
        if calendar == self.right_calendar:
            from_date: QDate = self.right_calendar.minimumDate()
            to_date: QDate = self.right_calendar.selectedDate()
        elif calendar == self.left_calendar:
            from_date: QDate = self.left_calendar.selectedDate()
            to_date: QDate = self.right_calendar.selectedDate()

        if from_date and to_date:
            d1 = min(from_date, to_date)
            d2 = max(from_date, to_date)
            while d1 <= d2:
                calendar.setDateTextFormat(d1, highlight_format)
                d1 = d1.addDays(1)

    def load_theme(self):
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor("black"))  # Set the desired color
        weekend_format.setBackground(QColor(44, 44, 44, 130))
        weekday_format = QTextCharFormat()
        weekday_format.setForeground(QColor("white"))  # Set the desired color
        weekday_format.setBackground(QColor(65, 65, 65, 150))

        # Set the weekend format as the calendar's weekendTextFormat

        # Create the left calendar (current month)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Monday, weekday_format)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Tuesday, weekday_format)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Wednesday, weekday_format)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Thursday, weekday_format)
        self.left_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Friday, weekday_format)

        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Monday, weekday_format)
        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Tuesday, weekday_format)
        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Wednesday, weekday_format)
        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Thursday, weekday_format)
        self.right_calendar.setWeekdayTextFormat(Qt.DayOfWeek.Friday, weekday_format)

    def get_icon(self, path_to_icon: str) -> QSvgWidget:
        return QSvgWidget(f"icons/{path_to_icon}")

    def get_timeline(self) -> tuple[QDate, QDate]:
        return (self.left_calendar.selectedDate(), self.right_calendar.selectedDate())
