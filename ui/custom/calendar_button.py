from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from ui.custom.date_range_calendar import DateRangeCalendar


class DropDownCalendarWidget(QWidget):
    date_range_changed = pyqtSignal(tuple)
    date_range_toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setLayout(QVBoxLayout())

        self.use_date_range = QCheckBox("Enable Date Range", self)
        self.use_date_range.toggled.connect(self.use_date_range_changed)

        self.date_range_calendar = DateRangeCalendar(self)
        self.date_changed((QDate.currentDate(), None))
        self.date_range_calendar.date_range_changed.connect(self.date_changed)

        self.use_date_range.setChecked(False)

        self.dates: tuple[QDate, QDate] = (QDate.currentDate(), None)

        self.layout().addWidget(self.use_date_range)
        self.layout().addWidget(self.date_range_calendar)

        self.init_buttons()

    def init_buttons(self):
        button_layout = QHBoxLayout()

        this_week_button = QPushButton("This Week", self)
        this_week_button.clicked.connect(self.set_this_week)
        button_layout.addWidget(this_week_button)

        next_two_weeks_button = QPushButton("Next 2 Weeks", self)
        next_two_weeks_button.clicked.connect(self.set_next_two_weeks)
        button_layout.addWidget(next_two_weeks_button)

        this_month_button = QPushButton("This Month", self)
        this_month_button.clicked.connect(self.set_this_month)
        button_layout.addWidget(this_month_button)

        self.layout().addLayout(button_layout)

    def set_this_week(self):
        today = QDate.currentDate()
        start_of_week = today.addDays(-(today.dayOfWeek() - 1))
        end_of_week = start_of_week.addDays(4)
        self.date_range_calendar.clear_highlight()
        self.date_range_calendar.from_date = start_of_week
        self.date_range_calendar.set_range(end_of_week)
        self.date_range_calendar.date_range_changed.emit((start_of_week, end_of_week))

    def set_next_two_weeks(self):
        today = QDate.currentDate()
        start_of_week = today.addDays(-(today.dayOfWeek() - 1))
        end_of_next_week = start_of_week.addDays(11)
        self.date_range_calendar.clear_highlight()
        self.date_range_calendar.from_date = start_of_week
        self.date_range_calendar.set_range(end_of_next_week)
        self.date_range_calendar.date_range_changed.emit(
            (start_of_week, end_of_next_week)
        )

    def set_this_month(self):
        today = QDate.currentDate()
        start_of_month = QDate(today.year(), today.month(), 1)
        end_of_month = start_of_month.addMonths(1).addDays(-1)
        self.date_range_calendar.clear_highlight()
        self.date_range_calendar.from_date = start_of_month
        self.date_range_calendar.set_range(end_of_month)
        self.date_range_calendar.date_range_changed.emit((start_of_month, end_of_month))

    def date_changed(self, dates: tuple[QDate, QDate]):
        self.dates = dates
        if dates[0] and not self.use_date_range.isChecked():
            self.use_date_range.setChecked(True)
        self.date_range_changed.emit(dates)

    def use_date_range_changed(self):
        self.date_range_toggled.emit(self.use_date_range.isChecked())


class CalendarButton(QPushButton):
    date_range_changed = pyqtSignal(tuple)
    date_range_toggled = pyqtSignal(bool)

    def __init__(self, title: str):
        super().__init__(title)
        self.base_title = title
        self.dropdown_calendar = DropDownCalendarWidget()
        self.dropdown_calendar.date_range_changed.connect(self.on_dates_changed)
        self.dropdown_calendar.date_range_toggled.connect(self.on_date_range_toggled)
        self.date_range: tuple[QDate, QDate] = (QDate.currentDate(), None)
        self.date_range_checked: bool = False

        self.clicked.connect(self.toggle_dropdown)
        self.update_title((QDate.currentDate(), None))

        icon = QIcon("ui/svg/date_range.svg")
        self.setIcon(icon)

    def show_dropdown(self):
        button_rect = self.rect()
        global_pos = self.mapToGlobal(button_rect.bottomLeft())
        self.dropdown_calendar.move(global_pos)
        self.dropdown_calendar.show()

    def hide_dropdown(self):
        self.dropdown_calendar.hide()

    def toggle_dropdown(self):
        if self.dropdown_calendar.isVisible():
            self.hide_dropdown()
        else:
            self.show_dropdown()

    def on_dates_changed(self, dates: tuple[QDate, QDate]):
        self.date_range = dates
        self.date_range_changed.emit(dates)
        self.update_title(dates)

    def on_date_range_toggled(self, checked: bool):
        self.date_range_checked = checked
        self.date_range_toggled.emit(checked)
        self.update_title(self.date_range)

    def update_title(self, dates: tuple[QDate, QDate]):
        if self.dropdown_calendar.use_date_range.isChecked() and dates:
            try:
                self.setText(
                    f"  {self.base_title} ({dates[0].toString()} - {dates[1].toString()})"
                )
            except (KeyError, AttributeError):
                self.setText(f"  {self.base_title} ({dates[0].toString()})")
        else:
            self.setText(f"  {self.base_title} (Disabled)")
