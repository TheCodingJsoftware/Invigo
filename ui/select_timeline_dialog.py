import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QDate, QDateTime, QFile, Qt, QTextStream
from PyQt6.QtGui import QColor, QIcon, QTextCharFormat
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QAbstractItemView, QCalendarWidget, QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons


class SelectTimeLineDialog(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        starting_date: str = None,
        ending_date: str = None
    ) -> None:
        super(SelectTimeLineDialog, self).__init__(parent)
        uic.loadUi("ui/select_timeline_dialog.ui", self)

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.inputText: str = ""

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        self.left_calendar.clicked.connect(self.update_selection)
        self.left_calendar.clicked.connect(self.use_set_days)
        self.left_calendar.currentPageChanged.connect(self.update_right_calendar_month)
        self.right_calendar.clicked.connect(self.update_selection)
        self.right_calendar.clicked.connect(self.set_new_days)
        self.days.valueChanged.connect(self.set_days)

        if starting_date is not None:
            self.left_calendar.setSelectedDate(QDate.fromString(starting_date, "yyyy-M-d"))
        if ending_date is not None:
            self.right_calendar.setSelectedDate(QDate.fromString(ending_date, "yyyy-M-d"))

        self.from_date: QDate = None
        self.to_date: QDate = None

        self.update_selection()

        self.load_dialog_buttons()

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        # self.resize(320, 250)

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

        self.selection_label.setText(
            f'Selection is from {self.from_date.toString("MMMM d")} to {self.to_date.toString("MMMM d")}, which is {days} days or {weeks:.1f} weeks.'
        )
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

    def load_theme(self) -> None:
        set_theme(self, theme="dark")
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

    def button_press(self, button) -> None:
        self.response = button.text()
        self.accept()

    def load_dialog_buttons(self) -> None:
        button_names = self.button_names.split(", ")
        for index, name in enumerate(button_names):
            if name == DialogButtons.set:
                button = QPushButton(f"  {name}")
                button.setIcon(QIcon("icons/dialog_ok.svg"))
            elif os.path.isfile(f"icons/dialog_{name.lower()}.svg"):
                button = QPushButton(f"  {name}")
                button.setIcon(QIcon(f"icons/dialog_{name.lower()}.svg"))
            else:
                button = QPushButton(name)
            if index == 0:
                button.setObjectName("default_dialog_button")
                set_default_dialog_button_stylesheet(button)
            button.setFixedWidth(100)
            if name == DialogButtons.copy:
                button.setToolTip("Will copy this window to your clipboard.")
            elif name == DialogButtons.save and self.icon_name == Icons.critical:
                button.setToolTip("Will save this error log to the logs directory.")
            button.clicked.connect(partial(self.button_press, button))
            self.buttonsLayout.addWidget(button)

    def get_response(self) -> str:
        return self.response.replace(" ", "")

    def get_timeline(self) -> tuple[QDate, QDate]:
        return (self.left_calendar.selectedDate(), self.right_calendar.selectedDate())
