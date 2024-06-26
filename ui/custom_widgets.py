import contextlib
import copy
import itertools
import os
import sys
import typing
from datetime import datetime, timedelta
from functools import partial

from natsort import natsorted
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QAbstractItemModel, QAbstractTableModel, QDate, QDateTime, QEvent, QMargins, QMimeData, QModelIndex, QPoint, QRegularExpression, QSettings, QSize, QSortFilterProxyModel, Qt, QTime, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QClipboard, QColor, QCursor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QFileSystemModel, QIcon, QKeySequence, QMouseEvent, QPainter, QPalette, QPixmap, QRegularExpressionValidator, QStandardItem, QStandardItemModel, QTextCharFormat
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplashScreen,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStylePainter,
    QTabBar,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBox,
    QToolButton,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utils.colors import darken_color, lighten_color
from utils.inventory.category import Category
from utils.workspace.assembly import Assembly
from utils.workspace.workspace_item import WorkspaceItem


class PreviousQuoteItem(QGroupBox):
    load_quote = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_quote = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget) -> None:
        super().__init__(parent)
        quote_name = file_info.get("name")
        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime("%A, %B %d, %Y, %I:%M:%S %p")

        self.setTitle(quote_name)

        modified = QLabel(f"Saved: {modified_date}")
        load_quote_button = QPushButton("Load Quote", self)
        load_quote_button.clicked.connect(self.load_quote.emit)
        load_quote_button.setToolTip("Loads the selected quote into a new tab for detailed viewing and editing.")

        open_external = ClickableLabel(self)
        open_external.setTextFormat(Qt.TextFormat.RichText)
        open_external.setText('<a href="open-in-browser">Open in Browser</a>')
        open_external.clicked.connect(self.open_webpage.emit)
        open_external.setToolTip("Will open up the printout in your default web browser.")

        delete_button = DeletePushButton(self, f"Permanently delete {quote_name}.\nThis action is irreversible.\nPlease exercise caution.", QIcon("icons/trash.png"))
        delete_button.setFixedWidth(25)
        delete_button.clicked.connect(self.delete_quote.emit)

        layout = QVBoxLayout(self)

        h_layout_1 = QHBoxLayout()
        h_layout_1.addWidget(load_quote_button)
        h_layout_1.addWidget(open_external)

        h_layout_2 = QHBoxLayout()
        h_layout_2.addWidget(modified)
        h_layout_2.addWidget(delete_button)

        layout.addLayout(h_layout_1)
        layout.addLayout(h_layout_2)

        self.setLayout(layout)
        self.setStyleSheet("QGroupBox{border: 1px solid #8C8C8C;}")


class SavedQuoteItem(QGroupBox):
    load_quote = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_quote = pyqtSignal()
    status_changed = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget) -> None:
        super().__init__(parent)
        quote_name = file_info.get("name")
        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime("%A, %B %d, %Y, %I:%M:%S %p")
        order_number = file_info.get("order_number")
        status = file_info.get("status")

        self.setTitle(quote_name)

        order_number = QLabel(f"Order #: {int(order_number)}", self)
        quote_status = QLabel("Status:", self)
        quote_status.setFixedWidth(50)

        self.status_combobox = QComboBox(self)
        self.status_combobox.addItems(["In progress", "Need more info", "Quoted", "Confirmed"])
        self.status_combobox.wheelEvent = lambda event: None
        self.status_combobox.setCurrentText(status)
        self.status_combobox.currentTextChanged.connect(self.status_changed.emit)

        modified = QLabel(f"Modified: {modified_date}")

        load_quote_button = QPushButton("Load Quote", self)
        load_quote_button.clicked.connect(self.load_quote.emit)
        load_quote_button.setToolTip("Loads the selected quote into a new tab for detailed viewing and editing.")

        open_external = ClickableLabel(self)
        open_external.setTextFormat(Qt.TextFormat.RichText)
        open_external.setText('<a href="open-in-browser">Open in Browser</a>')
        open_external.clicked.connect(self.open_webpage.emit)
        open_external.setToolTip("Will open up the printout in your default web browser.")

        delete_button = DeletePushButton(self, f"Permanently delete {quote_name}.\nThis action is irreversible.\nPlease exercise caution.", QIcon("icons/trash.png"))
        delete_button.setFixedWidth(25)
        delete_button.clicked.connect(self.delete_quote.emit)

        layout = QVBoxLayout(self)

        h_layout_1 = QHBoxLayout()
        h_layout_1.addWidget(order_number)
        h_layout_1.addWidget(quote_status)
        h_layout_1.addWidget(self.status_combobox)

        h_layout_2 = QHBoxLayout()
        h_layout_2.addWidget(load_quote_button)
        h_layout_2.addWidget(open_external)

        h_layout_3 = QHBoxLayout()
        h_layout_3.addWidget(modified)
        h_layout_3.addWidget(delete_button)

        layout.addLayout(h_layout_1)
        layout.addLayout(h_layout_2)
        layout.addLayout(h_layout_3)

        self.setLayout(layout)
        self.setStyleSheet("QGroupBox{border: 1px solid #8C8C8C;}")


class FilterButton(QPushButton):
    def __init__(self, name: str, parent=None):
        super(FilterButton, self).__init__(parent)
        self.setText(name)
        # self.setFixedSize(QSize(100, self.sizeHint().height()))
        self.setCheckable(True)
        self.setStyleSheet(
            """QPushButton{
	color: #ffffff;
    background-color: #3daee9;
    border: 1px solid #3daee9;
    border-radius: 5px;
}
QPushButton:checked{
    background-color: #3daee9;
    color: #171717;
}
QPushButton:hover{
    background-color: #48b6ed;
    border-color: #3daee9;
}
QPushButton:pressed{
    background-color: #2b92c5;
    color: #171717;
}

QPushButton:!checked {
    background-color: rgba(71, 71, 71, 130);
    border-color: rgba(71, 71, 71, 130);
    color: #8C8C8C;
}

QPushButton:hover:!checked {
    background-color: rgba(76, 76, 76, 130);
    border-color: #3daee9;
}

QPushButton:pressed:!checked {
    background-color: #3daee9;
    color: #171717;
}"""
        )


class AssemblyImage(QLabel):
    clicked = pyqtSignal()
    imagePathDropped = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = ...) -> None:
        super(AssemblyImage, self).__init__(parent)
        self.setMinimumSize(120, 120)
        self.setFixedHeight(120)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Press to enlarge")
        self.setText("Drop an Image.\nRight click to Paste\nfrom clipboard.\n(PNG, JPG, JPEG)")
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self.setStyleSheet("background-color: rgba(30,30,30,100);")
        self.image_dropped: bool = False
        self.path_to_image: str = ""

    def set_new_image(self, path_to_image):
        pixmap = QPixmap(path_to_image)
        pixmap = pixmap.scaledToHeight(100, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setStyleSheet("background-color: rgba(30,30,30,100);")
        self.path_to_image = path_to_image
        self.image_dropped = True

    def clear_image(self):
        self.setPixmap(QPixmap())
        self.setText("Drop an Image.\nRight click to Paste\nfrom clipboard.\n(PNG, JPG, JPEG)")
        self.setStyleSheet("background-color: rgba(30,30,30,100);")
        self.path_to_image = ""
        self.image_dropped = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()  # Emit the clicked signal

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasImage():
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            self.setText("Drop Me")
            self.setStyleSheet("background-color: rgba(70,210,110, 100);")
            event.acceptProposedAction()
            event.accept()

    def dropEvent(self, event: QDropEvent):
        if urls := event.mimeData().urls():
            image_path = urls[0].toLocalFile()
            if image_path.lower().endswith((".png", ".jpg", ".jpeg")):
                self.setPixmap(QPixmap(image_path).scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio))
                self.imagePathDropped.emit(image_path)
                event.accept()
            else:
                self.setText("Not allowed")
                self.setStyleSheet("background-color: rgba(210,70,60, 100);")
                event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setText("Drop an Image.\nRight click to Paste\nfrom clipboard.\n(PNG, JPG, JPEG)")
        self.setStyleSheet("background-color: rgba(30,30,30,100);")
        event.accept()
        if self.image_dropped:
            self.set_new_image(self.path_to_image)


class LoadingScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setPixmap(QPixmap("icons/loading.png"))  # Load an image for the loading screen
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)


class SelectRangeCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super(SelectRangeCalendar, self).__init__(parent)
        self.setObjectName("select_range_calendar")
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.from_date: QDate = None
        self.to_date: QDate = None

        self.highlighter_format = QTextCharFormat()
        # get the calendar default highlight setting
        self.highlighter_format.setBackground(QColor("#3daee9"))
        self.highlighter_format.setForeground(QColor("white"))
        self.highlighter_format.setFontWeight(400)

        # this will pass selected date value as a QDate object
        self.clicked.connect(self.select_range)

        self.load_theme()
        super().dateTextFormat()

    def get_timeline(self) -> tuple[QDate, QDate]:
        return (self.from_date, self.to_date)

    def load_theme(self):
        weekend_format = QTextCharFormat()
        weekend_format.setForeground(QColor("black"))  # Set the desired color
        weekend_format.setBackground(QColor(44, 44, 44, 130))
        weekday_format = QTextCharFormat()
        weekday_format.setForeground(QColor("white"))  # Set the desired color
        weekday_format.setBackground(QColor(65, 65, 65, 150))

        self.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Monday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Tuesday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Wednesday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Thursday, weekday_format)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Friday, weekday_format)

    def highlight_range(self, format):
        if self.from_date and self.to_date:
            d1: QDate = min(self.from_date, self.to_date)
            d2: QDate = max(self.from_date, self.to_date)
            while d1 <= d2:
                self.setDateTextFormat(d1, format)
                d1 = d1.addDays(1)

    def select_range(self, date_value: QDate):
        self.highlight_range(QTextCharFormat())

        # check if a keyboard modifer is pressed
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier and self.from_date:
            self.to_date = date_value
            if self.to_date < self.from_date:
                self.to_date, self.from_date = self.from_date, self.to_date
            self.highlight_range(self.highlighter_format)
        else:
            # required
            self.from_date = date_value
            self.to_date = None

    def set_range(self, date_value: QDate):
        self.highlight_range(QTextCharFormat())
        self.to_date = date_value
        if self.to_date < self.from_date:
            self.to_date, self.from_date = self.from_date, self.to_date
        self.highlight_range(self.highlighter_format)


class ItemsGroupBox(QGroupBox):
    filesDropped = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = ...) -> None:
        super(ItemsGroupBox, self).__init__(parent)
        self.setTitle("Items")
        self.setObjectName("items_group_box")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx"):
                    self.setStyleSheet("QGroupBox#items_group_box {background-color: rgba(29, 185, 84, 100);}")
                else:
                    self.setStyleSheet("QGroupBox#items_group_box {background-color: rgba(229, 9, 20, 100);}")
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx"):
                    event.setDropAction(Qt.DropAction.CopyAction)
                    event.accept()
                else:
                    event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.setStyleSheet("QGroupBox#items_group_box {}")
        return super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.setStyleSheet("QGroupBox#items_group_box {}")
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx"):
                    files = [str(url.toLocalFile()) for url in event.mimeData().urls()]
                    self.filesDropped.emit(files)
            event.ignore()


class FilterTabWidget(QWidget):
    filterButtonPressed = pyqtSignal()

    def __init__(self, columns: int, parent: QWidget | None = ...) -> None:
        super(FilterTabWidget, self).__init__(parent)
        self.tab_widget = QTabWidget()
        self.show_all_tab = QWidget(self)
        self.num_columns = columns
        layout = QGridLayout(self.show_all_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # Set horizontal alignment to center
        self.show_all_tab.setLayout(layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.show_all_tab)

        # self.tab_widget.addTab(scroll_area, "Show All")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        self.buttons: list[QPushButton] = []

        self.tabs = {"Show All": []}  # Dictionary to store tabs and their buttons
        self.tab_widget.currentChanged.connect(self.update_tab_button_visibility)

    def add_tab(self, name):
        tab_widget = QWidget(self)
        tab_widget.setObjectName("filter_tab_widget")
        tab_widget.setStyleSheet("QWidget#filter_tab_widget{background-color: rgba(25, 25, 25, 100); border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;}")
        layout = QGridLayout(tab_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # Set horizontal alignment to center

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(tab_widget)

        tab_widget.setLayout(layout)
        self.tab_widget.addTab(scroll_area, name)

        self.tabs[name] = []  # Add tab with an empty list for buttons

        return layout

    def clear_selections(self, tab_name: str) -> None:
        buttons = self.tabs.get(tab_name)
        if buttons is not None:
            for button in buttons:
                button.setChecked(False)

    def clear_all_selections(self) -> None:
        for button in self.buttons:
            button.setChecked(False)

    def enable_button(self, button_name: str) -> None:
        for button in self.buttons:
            if button.text() == button_name:
                button.setChecked(True)

    def add_button_to_tab(self, tab_name, button_name):
        buttons = self.tabs.get(tab_name)
        if buttons is not None:
            button = QPushButton(button_name, checkable=True)
            button.clicked.connect(self.filterButtonPressed.emit)
            button.setStyleSheet(
                """QPushButton{
	color: #ffffff;
    background-color: #3daee9;
    border: 1px solid #3daee9;
    border-radius: 5px;
}
QPushButton:checked{
    background-color: #3daee9;
}
QPushButton:hover{
    background-color: #48b6ed;
    border-color: #3daee9;
}
QPushButton:pressed{
    background-color: #2b92c5;
}

QPushButton:!checked {
    background-color: rgba(71, 71, 71, 130);
    border-color: rgba(71, 71, 71, 130);
    color: #8C8C8C;
}

QPushButton:hover:!checked {
    background-color: rgba(76, 76, 76, 130);
    border-color: #3daee9;
}

QPushButton:pressed:!checked {
    background-color: #3daee9;
    color: #EAE9FC;
}"""
            )
            button.setFixedSize(QSize(100, button.sizeHint().height()))
            buttons.append(button)  # Add button to the list
            self.buttons.append(button)

    def add_buttons_to_tab(self, tab_name, button_names):
        for button in button_names:
            self.add_button_to_tab(tab_name, button)

    def get_buttons(self, tab_name):
        buttons = self.tabs.get(tab_name)
        return buttons if buttons is not None else []

    def update_tab_button_visibility(self, tab_index: int):
        tab_name = self.tab_widget.tabText(tab_index)
        buttons = self.tabs.get(tab_name)
        num_columns = self.num_columns
        if tab_name == "Show All":
            layout: QGridLayout = self.tab_widget.widget(tab_index).widget().layout()
            row = 0
            col = 0
            for button in self.buttons:
                layout.addWidget(button, row, col)
                button.setVisible(True)
                col += 1
                if col == num_columns:
                    col = 0
                    row += 1
        elif buttons is not None:
            layout: QGridLayout = self.tab_widget.widget(tab_index).widget().layout()
            row = 0
            col = 0
            for button in buttons:
                layout.addWidget(button, row, col)
                button.setVisible(True)
                col += 1
                if col == num_columns:
                    col = 0
                    row += 1


class ScrollPositionManager:
    def __init__(self):
        self.scroll_positions: dict[str, int] = {}

    def save_scroll_position(self, category: str, scroll: QTableWidget | QScrollArea):
        scroll_position = QPoint(scroll.horizontalScrollBar().value(), scroll.verticalScrollBar().value())
        if not scroll_position.y():
            return
        self.scroll_positions[category] = scroll_position.y()

    def get_scroll_position(self, category: str) -> int:
        try:
            return self.scroll_positions[category]
        except KeyError:
            return


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


class MachineCutTimeSpinBox(QDoubleSpinBox):
    # ! IF VALUE IS SET TO 1, THAT IS 1 SECOND
    def __init__(self, parent=None):
        super(MachineCutTimeSpinBox, self).__init__(parent)
        self.setRange(0, 99999999)
        self.setSingleStep(0.001)
        self.setDecimals(9)
        self.setFixedWidth(200)
        self.setWrapping(True)
        self.setAccelerated(True)
        self.wheelEvent = lambda event: None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        regex = QRegularExpression(r"\d+.\d{2}")
        validator = QRegularExpressionValidator(regex, self)
        self.lineEdit().setValidator(validator)

        self.installEventFilter(self)

    def focusInEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(MachineCutTimeSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(MachineCutTimeSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            return super(MachineCutTimeSpinBox, self).wheelEvent(event)
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
        end_date_time = current_date_time.addDays(days).addSecs(hours * 3600 + minutes * 60)

        time_delta = end_date_time.toSecsSinceEpoch() - current_date_time.toSecsSinceEpoch()
        return timedelta(seconds=time_delta)


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


class DraggableButton(QPushButton):
    buttonClicked = pyqtSignal()
    longDragThreshold = 30

    def __init__(self, parent=None):
        super(QPushButton, self).__init__(parent)
        self.setAcceptDrops(True)
        self.dragging = False
        self.file = None
        self.drag_start_position = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def setFile(self, file: str) -> None:
        self.file = file

    def mouseMoveEvent(self, event):
        if self.dragging:
            return
        try:
            distance = (event.pos() - self.drag_start_position).manhattanLength()
        except TypeError:
            return
        if distance >= self.longDragThreshold:
            self.dragging = True
            mime_data = QMimeData()
            url = QUrl.fromLocalFile(self.file)  # Replace with the actual file path
            mime_data.setUrls([url])

            drag = QDrag(self)
            drag.setMimeData(mime_data)

            # Start the drag operation
            drag.exec(Qt.DropAction.CopyAction)
            super().mousePressEvent(event)

    def mousePressEvent(self, event):
        self.dragging = False
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.dragging and event.button() == Qt.MouseButton.LeftButton:
            self.buttonClicked.emit()
        self.dragging = False
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)


class DropWidget(QWidget):
    def __init__(
        self,
        parent,
        assembly: Assembly,
        item: WorkspaceItem,
        files_layout: QHBoxLayout,
        file_category: str,
    ):
        super().__init__()
        self.parent = parent
        self.setAcceptDrops(True)
        self.assembly = assembly
        self.item = item
        self.files_layout = files_layout
        self.file_category = file_category
        self.setMaximumWidth(1000)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.label = QLabel("Drag Here", self)
        self.label.setMaximumWidth(1000)
        self.label.setMinimumHeight(40)
        self.label.setStyleSheet("background-color: rgba(30,30,30,100);")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.label.setText("Drop Me")
            self.label.setStyleSheet("background-color: rgba(70,210,110, 100);")
            event.accept()
        else:
            self.label.setText("Drag Here")
            self.label.setStyleSheet("background-color: rgba(30,30,30,100);")
            event.ignore()

    def dragLeaveEvent(self, event: QDragEnterEvent):
        self.label.setText("Drag Here")
        self.label.setStyleSheet("background-color: rgba(30,30,30,100);")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            allowed_extensions = [
                ".pdf",
                ".dxf",
                ".jpeg",
                ".geo",
                ".png",
                ".jpg",
                "sldprt",
            ]  # Allowed file extensions
            valid_files = all(file_path.lower().endswith(tuple(allowed_extensions)) for file_path in file_paths)
            if valid_files:
                self.label.setText("Processing")
                self.label.setStyleSheet("background-color: rgba(70,210,110, 100);")
                self.parent.handle_dropped_file(
                    self.label,
                    file_paths,
                    self.assembly,
                    self.item,
                    self.files_layout,
                    self.file_category,
                )
                event.accept()
            else:
                self.label.setText("Not allowed")
                self.label.setStyleSheet("background-color: rgba(210,70,60, 100);")
                event.ignore()
        else:
            event.ignore()


class DictionaryTableModel(QAbstractTableModel):
    def __init__(self, dictionary, parent=None):
        super().__init__(parent)
        self.keys = list(dictionary.keys())
        self.dictionary = dictionary

    def rowCount(self, parent=None):
        return len(self.keys)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            key = self.keys[index.row()]
            value = self.dictionary[key]

            if index.column() == 0:
                return key
            elif index.column() == 1:
                return str(value)

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole and index.isValid() and index.column() == 1:
            key = self.keys[index.row()]
            self.dictionary[key] = value
            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        if index.column() == 1:
            return super().flags(index) | Qt.ItemFlag.ItemIsEditable
        return super().flags(index)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return ["Key", "Value"][section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)

        return None

    def getUpdatedDictionary(self):
        return self.dictionary


class AssemblyMultiToolBox(QWidget):
    def __init__(self, parent=None):
        super(AssemblyMultiToolBox, self).__init__(parent)
        self.widgets: list[QWidget] = []
        self.buttons: list[QPushButton] = []
        self.input_box: list[QLineEdit] = []
        self.colors: list[str] = []
        self.delete_buttons: list[DeletePushButton] = []
        self.duplicate_buttons: list[QPushButton] = []
        self.check_boxes: list[QCheckBox] = []
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(1)
        main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(main_layout)

    def addItem(self, widget: QWidget, title: str, base_color: str = "#3daee9"):
        # Apply the drop shadow effect to the widget
        # checkbox = QCheckBox(widget)
        # checkbox.setStyleSheet("QCheckBox:indicator{width: 20px; height: 20px;}")
        # checkbox.setFixedWidth(22)
        hover_color: str = lighten_color(base_color)
        pressed_color: str = darken_color(base_color)
        _widget = QWidget()
        _widget.setContentsMargins(0, 3, 0, 3)
        widget.setParent(_widget)
        button = QPushButton()
        button.setObjectName("edit_sheet_nest_button")
        button.setStyleSheet(
            """
QPushButton#edit_sheet_nest_button {
    border: none;
    background-color: rgba(71, 71, 71, 110);
    border-top-left-radius: 5px;
    border-top-right-radius: 0px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 0px;
    color: rgb(210, 210, 210);
    text-align: left;
}

QPushButton:hover#edit_sheet_nest_button {
    background-color: rgba(76, 76, 76, 110);
}

QPushButton:pressed#edit_sheet_nest_button {
    background-color: rgba(39, 39, 39, 110);
    color: rgb(132, 132, 132);
}

QPushButton:checked#edit_sheet_nest_button {
    color: #8C8C8C;
}

QPushButton:!checked#edit_sheet_nest_button {
    color: #EAE9FC;
    background-color: %(base_color)s;
    border-top-left-radius: 5px;
    border-top-right-radius: 0px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}

QPushButton:!checked:hover#edit_sheet_nest_button {
    background-color: %(hover_color)s;
}

QPushButton:!checked:pressed#edit_sheet_nest_button {
    background-color: %(pressed_color)s;
}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": pressed_color,
            }
        )
        button.setFixedWidth(34)
        button.setFixedHeight(34)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setText("🡇")
        button.setChecked(True)
        button.setCheckable(True)

        input_box = QLineEdit(widget)
        button.clicked.connect(
            lambda checked, w=widget: (
                self.toggle_widget_visibility(w),
                button.setText("🡇" if w.isVisible() else "🡆"),
                input_box.setStyleSheet(
                    "QLineEdit{background-color: %(base_color)s; border-color: %(base_color)s; border-bottom-right-radius: 0px;} QMenu { background-color: rgb(22,22,22);}" % {"base_color": base_color}
                    if w.isVisible()
                    else "QLineEdit{background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 5px;} QMenu { background-color: rgb(22,22,22);}"
                ),
            )
        )
        input_box.setObjectName("input_box_multitoolbox")
        input_box.setText(title)
        input_box.setFixedHeight(34)
        input_box.setStyleSheet("QLineEdit{background-color: %(base_color)s; border-color: %(base_color)s; border-bottom-right-radius: 0px;} QMenu { background-color: rgb(22,22,22);}" % {"base_color": base_color})

        delete_button = DeletePushButton(
            parent=widget,
            tool_tip=f"Delete {title} forever",
            icon=QIcon("icons/trash.png"),
        )
        delete_button.setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")
        delete_button.setFixedWidth(33)
        delete_button.setFixedHeight(34)
        duplicate_button = QPushButton()
        duplicate_button.setFixedHeight(34)
        duplicate_button.setStyleSheet("border-radius: none; border: none;")
        duplicate_button.setIcon(QIcon("icons/duplicate.png"))
        duplicate_button.setFixedWidth(35)
        duplicate_button.setToolTip(f"Duplicate {title}")

        # widget.setMinimumHeight(100)

        hlaout = QHBoxLayout()
        hlaout.setSpacing(0)
        hlaout.setContentsMargins(0, 0, 0, 0)
        # hlaout.addWidget(checkbox)
        hlaout.addWidget(button)
        hlaout.addWidget(input_box)
        hlaout.addWidget(duplicate_button)
        hlaout.addWidget(delete_button)
        layout = QVBoxLayout(_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(hlaout)
        layout.addWidget(widget)
        # # The above code is creating a widget in Python.
        _widget.setLayout(layout)
        widget.setObjectName("edit_multi_tool_box_widget")
        widget.setStyleSheet(
            """
QWidget#edit_multi_tool_box_widget {
border: 1px solid %(base_color)s;
border-bottom-left-radius: 5px;
border-bottom-right-radius: 5px;
border-top-right-radius: 0px;
border-top-left-radius: 0px;
background-color: rgba(25, 25, 25, 0.6);
}
"""
            % {"base_color": base_color}
        )

        self.buttons.append(button)
        self.delete_buttons.append(delete_button)
        self.input_box.append(input_box)
        self.widgets.append(widget)
        self.colors.append(base_color)
        self.duplicate_buttons.append(duplicate_button)
        # self.check_boxes.append(checkbox)

        self.layout().addWidget(_widget)

    def removeItem(self, widget_to_delete: QWidget) -> None:
        main_layout = self.layout()  # Get the reference to the main layout
        for i in range(main_layout.count()):
            layout_item = main_layout.itemAt(i)
            widget = layout_item.widget().layout().itemAt(1).widget()  # This is what were trying to find
            # layout = widget.layout()
            if widget == widget_to_delete:  # Check if the layout's widget matches the given widget
                self.delete_buttons[i].disconnect()
                self.buttons[i].disconnect()
                self.buttons.pop(i)
                self.delete_buttons.pop(i)
                self.duplicate_buttons.pop(i)
                self.input_box.pop(i)
                self.widgets.pop(i)
                self.colors.pop(i)
                self.clear_widget(layout_item.widget())
                break

    def getDeleteButton(self, index: int) -> "DeletePushButton":
        return self.delete_buttons[index]

    def getLastDeleteButton(self) -> "DeletePushButton":
        return self.delete_buttons[-1]

    def getDuplicateButton(self, index: int) -> QPushButton:
        return self.duplicate_buttons[index]

    def getLastDuplicateButton(self) -> QPushButton:
        return self.duplicate_buttons[-1]

    def getInputBox(self, index: int) -> QLineEdit:
        return self.input_box[index]

    def getLastInputBox(self) -> QLineEdit:
        return self.input_box[-1]

    def getLastToggleButton(self) -> QPushButton:
        return self.buttons[-1]

    def closeLastToolBox(self):
        self.buttons[-1].setText("🡆")
        self.buttons[-1].setChecked(True)
        self.widgets[-1].setVisible(False)
        self.delete_buttons[-1].setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")
        self.input_box[-1].setStyleSheet("QLineEdit{background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 5px;} QMenu { background-color: rgb(22,22,22);}")

    def openLastToolBox(self):
        self.buttons[-1].setText("🡇")
        self.buttons[-1].setChecked(False)
        self.widgets[-1].setVisible(True)
        self.delete_buttons[-1].setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 0px;")
        self.input_box[-1].setStyleSheet("QLineEdit{background-color: %(base_color)s; border-color: %(base_color)s; border-bottom-right-radius: 0px;} QMenu { background-color: rgb(22,22,22);}" % {"base_color": self.colors[-1]})

    def setItemText(self, index: int, new_name: str):
        if 0 <= index < len(self.input_box):
            self.input_box[index].setText(new_name)

    def setItemIcon(self, index: int, icon_path: str):
        if 0 <= index < len(self.buttons):
            button = self.buttons[index]
            icon = QIcon(icon_path)
            button.setIcon(icon)

    def getWidget(self, index):
        return self.widgets[index] if 0 <= index < len(self.widgets) else None

    def count(self) -> int:
        return len(self.widgets)

    def toggle_widget_visibility(self, widget: QWidget):
        widget.setVisible(not widget.isVisible())
        for _widget, button, delete_button in zip(self.widgets, self.buttons, self.delete_buttons):
            if widget == _widget:
                if button.isChecked():
                    delete_button.setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")
                else:
                    delete_button.setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 0px;")

    def clear_widget(self, widget: QWidget):
        with contextlib.suppress(TypeError):  # Dont care, it works.
            if widget is None:
                return

            layout = widget.layout()
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        self.clear_widget(item.widget())
                        item.widget().deleteLater()

            parent_widget = widget.parent()
            if parent_widget is not None:
                parent_layout = parent_widget.layout()
                if parent_layout is not None:
                    parent_layout.removeWidget(widget)

            widget.setParent(None)
            widget.deleteLater()

    def clear_layout(self, layout) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())

    def get_widget_visibility(self) -> dict[int, bool]:
        return {i: widget.isVisible() for i, widget in enumerate(self.widgets)}

    def set_widgets_visibility(self, widgets_visibility: dict[int, bool]) -> None:
        if len(widgets_visibility.items()) > 0:
            for i, is_visible in widgets_visibility.items():
                if is_visible:
                    self.open(i)
                else:
                    self.close(i)
        else:
            self.close_all()

    def open(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setChecked(False)
            self.buttons[index].setText("🡇")
            self.widgets[index].setVisible(True)
            self.delete_buttons[index].setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 0px;")
            self.input_box[index].setStyleSheet("QLineEdit{background-color: %(base_color)s; border-color: %(base_color)s; border-bottom-right-radius: 0px;} QMenu { background-color: rgb(22,22,22);}" % {"base_color": self.colors[index]})

    def close(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setText("🡆")
            self.buttons[index].setChecked(True)
            self.widgets[index].setVisible(False)
            self.delete_buttons[index].setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")
            self.input_box[index].setStyleSheet("QLineEdit{background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 5px;} QMenu { background-color: rgb(22,22,22);}")

    def close_all(self) -> None:
        for button, widget, input_box, delete_button in zip(self.buttons, self.widgets, self.input_box, self.delete_buttons):
            button.setChecked(True)
            button.setText("🡆")
            widget.setVisible(False)
            input_box.setStyleSheet("background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 5px;")
            delete_button.setStyleSheet("border-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;")


class MultiToolBox(QWidget):
    def __init__(self, parent=None):
        super(MultiToolBox, self).__init__(parent)
        self.widgets: list[QWidget] = []
        self.widget_visibility: dict[int, bool] = {}
        self.buttons: list[QPushButton] = []
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(1)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.main_layout)

    def clear(self):
        self.widgets.clear()
        self.buttons.clear()
        self.widget_visibility.clear()
        self.clear_layout(self.main_layout)

    def addItem(self, widget: QWidget, title: str, base_color: str = "#3daee9"):
        hover_color: str = lighten_color(base_color)
        pressed_color: str = darken_color(base_color)

        _widget = QWidget(self)
        _widget.setContentsMargins(0, 3, 0, 3)
        # _widget.setParent(widget)
        button = QPushButton(_widget)
        button.setFixedHeight(30)
        button.setObjectName("sheet_nest_button")
        button.setStyleSheet(
            """
QPushButton#sheet_nest_button {
    border: 1px solid rgba(71, 71, 71, 110);
    background-color: rgba(71, 71, 71, 110);
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
    color: #EAE9FC;
    text-align: left;
}

QPushButton:hover#sheet_nest_button {
    background-color: rgba(76, 76, 76, 110);
    border: 1px solid %(base_color)s;
}

QPushButton:pressed#sheet_nest_button {
    background-color: %(base_color)s;
    color: #171717;
}

QPushButton:checked#sheet_nest_button {
    color: #8C8C8C;
}

QPushButton:checked:pressed#sheet_nest_button {
    color: #171717;
}

QPushButton:!checked#sheet_nest_button {
    color: #171717;
    border-color: %(base_color)s;
    background-color: %(base_color)s;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}

QPushButton:!checked:hover#sheet_nest_button {
    background-color: %(hover_color)s;
}

QPushButton:!checked:pressed#sheet_nest_button {
    color: #171717;
    background-color: %(pressed_color)s;
}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": pressed_color,
            }
        )
        button.setText(title)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setChecked(True)
        button.setCheckable(True)
        button.clicked.connect(partial(self.toggle_widget_visibility, widget))

        widget.setVisible(False)

        layout = QVBoxLayout(_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button)
        layout.addWidget(widget)
        _widget.setLayout(layout)
        widget.setObjectName("nest_widget")
        # widget.setAutoFillBackground(True)
        widget.setStyleSheet("QWidget#nest_widget{border: 1px solid %(base_color)s; background-color: rgba(25,25,25, 0.7); }" % {"base_color": base_color})

        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        # if widget.isVisible():
        #     shadow.setColor(QColor(0, 0, 0, 255))
        # else:
        #     shadow.setColor(QColor(61, 174, 233, 255))
        # shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        # widget.parentWidget().setGraphicsEffect(shadow)

        self.buttons.append(button)
        self.widgets.append(widget)

        self.layout().addWidget(_widget)

    def setItemText(self, index: int, new_name: str):
        if 0 <= index < len(self.buttons):
            self.buttons[index].setText(new_name)

    def setItemIcon(self, index: int, icon_path: str):
        if 0 <= index < len(self.buttons):
            button = self.buttons[index]
            icon = QIcon(icon_path)
            button.setIcon(icon)

    def getWidget(self, index) -> QWidget:
        return self.widgets[index] if 0 <= index < len(self.widgets) else None

    def getButton(self, index) -> QPushButton:
        return self.buttons[index] if 0 <= index < len(self.buttons) else None

    def count(self) -> int:
        return len(self.widgets)

    def get_widget_visibility(self) -> dict[int, bool]:
        return {i: widget.isVisible() for i, widget in enumerate(self.widgets)}

    def set_widgets_visibility(self, widgets_visibility: dict[int, bool]) -> None:
        try:
            if len(widgets_visibility.items()) > 0:
                for i, is_visible in widgets_visibility.items():
                    if is_visible:
                        self.open(i)
                    else:
                        self.close(i)
            else:
                self.close_all()
        except AttributeError:
            self.close_all()

    def toggle_widget_visibility(self, widget):
        widget.setVisible(not widget.isVisible())
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        # if widget.isVisible():
        #     shadow.setColor(QColor(61, 174, 233, 255))
        # else:
        #     shadow.setColor(QColor(0, 0, 0, 255))
        # shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        # widget.parentWidget().setGraphicsEffect(shadow)

    def closeLastToolBox(self):
        self.buttons[-1].setChecked(True)
        self.widgets[-1].setVisible(False)

    def openLastToolBox(self):
        self.buttons[-1].setChecked(False)
        self.widgets[-1].setVisible(True)

    def open(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setChecked(False)
            self.widgets[index].setVisible(True)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(61, 174, 233, 255))
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            # self.widgets[index].parentWidget().setGraphicsEffect(shadow)

    def close(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setChecked(True)
            self.widgets[index].setVisible(False)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(0, 0, 0, 255))  # Set the shadow color and opacity
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            # self.widgets[index].parentWidget().setGraphicsEffect(shadow)

    def close_all(self) -> None:
        for button, widget in zip(self.buttons, self.widgets):
            button.click()
            button.click()
            button.setChecked(True)
            widget.setVisible(False)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(0, 0, 0, 255))  # Set the shadow color and opacity
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            # widget.parentWidget().setGraphicsEffect(shadow)

    def open_all(self) -> None:
        for button, widget in zip(self.buttons, self.widgets):
            button.click()
            button.click()
            button.setChecked(False)
            widget.setVisible(True)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(61, 174, 233, 255))
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            # widget.parentWidget().setGraphicsEffect(shadow)

    def clear_layout(self, layout: QVBoxLayout | QWidget) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())


class TabButton(QPushButton):
    doubleClicked = pyqtSignal()

    def __init__(self, text: str, parent: QWidget = None):
        super(TabButton, self).__init__(text, parent)
        self.setCheckable(True)
        self.setObjectName("custom_tab_button")
        self.drag_start_pos = None
        self.drag_timer = QTimer(self)
        self.drag_timer.setSingleShot(True)
        self.drag_timer.timeout.connect(self.initiateDrag)
        self.drag_threshold = 350  # milliseconds
        self.move_threshold = 20  # pixels

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = e.position().toPoint()
            self.drag_timer.start(self.drag_threshold)

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)
        if e.buttons() == Qt.MouseButton.LeftButton and self.drag_start_pos is not None and (e.position().toPoint() - self.drag_start_pos).manhattanLength() > self.move_threshold:
            if not self.drag_timer.isActive():
                self.initiateDrag()

    def mouseReleaseEvent(self, e: QMouseEvent):
        super().mouseReleaseEvent(e)
        self.drag_timer.stop()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        super().mouseDoubleClickEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()
            self.drag_timer.stop()

    def initiateDrag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.text())
        drag.setMimeData(mime)
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_pos - QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.exec(Qt.DropAction.MoveAction)


class CustomTabWidget(QWidget):
    currentChanged = pyqtSignal()
    tabBarDoubleClicked = pyqtSignal()
    addCategory = pyqtSignal()
    removeCategory = pyqtSignal()
    tabOrderChanged = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setAcceptDrops(True)

        self.rows: list[QHBoxLayout] = []
        self.tabs_per_row = 10
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)

        self.corner_layout = QHBoxLayout()
        self.corner_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.main_layout.addLayout(self.corner_layout)
        self.main_layout.addWidget(self.stacked_widget)

        self.buttons: list[TabButton] = []

        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 6)
        add_category = QPushButton(self)
        add_category.setObjectName("add_category")
        add_category.setIcon(QIcon("icons/list_add.png"))
        add_category.setStyleSheet("QPushButton#add_category{border-top-left-radius: 12px; border-bottom-left-radius: 12px; border-bottom-right-radius: 0px; border-top-right-radius: 0px;}")
        add_category.clicked.connect(self.addCategory.emit)
        remove_category = QPushButton(self)
        remove_category.setObjectName("remove_category")
        remove_category.setIcon(QIcon("icons/list_remove.png"))
        remove_category.setStyleSheet("QPushButton#remove_category{border-top-right-radius: 12px; border-bottom-right-radius: 12px; border-bottom-left-radius: 0px; border-top-left-radius: 0px;}")
        remove_category.clicked.connect(self.removeCategory.emit)
        layout.addWidget(add_category)
        layout.addWidget(remove_category)

        self.setCornerWidget(widget)

    def setCornerWidget(self, widget: QWidget):
        self.corner_layout.addWidget(widget)

    def addTab(self, widget: QWidget, text: str):
        button = self.create_button(text)
        self.buttons.append(button)
        self.stacked_widget.addWidget(widget)

        if len(self.buttons) == 1:
            button.setChecked(True)
            self.stacked_widget.setCurrentWidget(widget)

    def insertTab(self, index: int, widget: QWidget, text: str):
        button = self.create_button(text)
        self.buttons.insert(index, button)
        self.stacked_widget.addWidget(widget)

        if len(self.buttons) == 1:
            button.setChecked(True)
            self.stacked_widget.setCurrentWidget(widget)

    def removeTab(self, index: int):
        widget = self.stacked_widget.widget(index)
        self.stacked_widget.removeWidget(widget)
        self.buttons[index].deleteLater()
        self.buttons.pop(index)

    def setTabText(self, index: int, text: str):
        self.buttons[index].setText(text)

    def currentIndex(self) -> int:
        return next((i for i, button in enumerate(self.buttons) if button.isChecked()), 0)

    def setCurrentIndex(self, index: int):
        self.buttons[index].click()

    def currentTabText(self) -> str:
        return next((button.text() for button in self.buttons if button.isChecked()), None)

    def currentTab(self) -> TabButton:
        return next((button for button in self.buttons if button.isChecked()), None)

    def clear(self):
        while self.stacked_widget.count():
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
            self.buttons.pop()
        for layout in self.rows:
            self.clear_layout(layout)
        self.rows.clear()

    def create_button(self, text) -> TabButton:
        if not self.rows or len(self.buttons) % self.tabs_per_row == 0:
            self.add_new_tab_row()
        result = TabButton(text, self)
        result.doubleClicked.connect(self.tabBarDoubleClicked.emit)
        result.clicked.connect(partial(self.tab_selected, result))
        self.rows[-1].addWidget(result, alignment=Qt.AlignmentFlag.AlignBottom)
        return result

    def add_new_tab_row(self):
        row_layout = QHBoxLayout()
        row_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        # row_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        row_layout.setContentsMargins(0, 0, 0, 1)
        row_layout.setSpacing(1)
        self.main_layout.insertLayout(self.main_layout.count() - 1, row_layout)
        self.rows.append(row_layout)

    def tab_selected(self, selected_button: TabButton):
        for button in self.buttons:
            button.setChecked(button is selected_button)
        index = self.buttons.index(selected_button)
        self.stacked_widget.setCurrentIndex(index)
        self.currentChanged.emit()

    def get_tab_order(self) -> list[str]:
        order = []
        for layout in self.rows:
            for i in range(layout.count()):
                if widget := layout.itemAt(i).widget():
                    if isinstance(widget, TabButton):
                        order.append(widget.text())
        return order

    def find_tab_by_name(self, name: str) -> int:
        return next((i for i in range(self.count()) if self.tabText(i) == name), -1)

    def tabText(self, index: int) -> str:
        return self.buttons[index].text()

    def count(self) -> int:
        return len(self.buttons)

    def dropEvent(self, event: QDropEvent):
        position: QPoint = event.position().toPoint()
        button: DraggableButton = event.source()
        if button in self.buttons:
            original_index = self.buttons.index(button)
            for i, btn in enumerate(self.buttons):
                if btn != button and btn.geometry().contains(position):
                    self.buttons.insert(i, self.buttons.pop(original_index))
                    self.stacked_widget.insertWidget(i, self.stacked_widget.widget(original_index))
                    break
            self.rearrange_buttons()
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.accept()

    def rearrange_buttons(self):
        for row in self.rows:
            while row.count():
                row.itemAt(0).widget().setParent(None)
        for i, button in enumerate(self.buttons):
            self.rows[i // self.tabs_per_row].addWidget(button, alignment=Qt.AlignmentFlag.AlignBottom)
        self.stacked_widget.setCurrentIndex(self.currentIndex())
        self.tabOrderChanged.emit()

    def clear_layout(self, layout: QVBoxLayout | QWidget) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())


class PdfFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, model, parent=None, path=""):
        super().__init__(parent)
        self.path = path
        self.setSourceModel(model)

    def filterAcceptsRow(self, row, parent):
        index = self.sourceModel().index(row, 0, parent)
        if not index.isValid():
            return False
        if self.sourceModel().isDir(index):
            return self.directoryContainsPdf(self.sourceModel().filePath(index))
        filename = self.sourceModel().fileName(index)
        return filename.lower().endswith(".pdf")

    def directoryContainsPdf(self, directory):
        if self.path not in directory:
            return False
        return any(any(file.lower().endswith(".pdf") for file in files) for root, dirs, files in os.walk(directory))

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        left_index = left.sibling(left.row(), 0)
        right_index = right.sibling(right.row(), 0)
        left_is_folder = self.sourceModel().isDir(left_index)
        right_is_folder = self.sourceModel().isDir(right_index)

        if left_is_folder and not right_is_folder or not left_is_folder and right_is_folder:
            return False  # Folders come first
        left_modified = self.sourceModel().fileInfo(left_index).lastModified()
        right_modified = self.sourceModel().fileInfo(right_index).lastModified()

        return left_modified < right_modified


class PdfTreeView(QTreeView):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        print(path)
        self.parent = parent
        self.model = QFileSystemModel(self.parent)
        self.model.setRootPath(path)
        self.setModel(self.model)
        self.filterModel = PdfFilterProxyModel(self.model, self.parent, path)
        self.filterModel.setSourceModel(self.model)
        self.filterModel.setFilterKeyColumn(0)
        self.setModel(self.filterModel)
        self.setRootIndex(self.filterModel.mapFromSource(self.model.index(path)))
        self.header().resizeSection(0, 170)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.header().hideSection(1)  # Size
        self.header().hideSection(2)  # File type
        self.setAnimated(True)
        self.selected_indexes = []
        self.selected_items = []
        self.full_paths = []
        self.setSortingEnabled(True)
        # Connect the header's sectionClicked signal to handle sorting

        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        self.selected_indexes = self.selectionModel().selectedIndexes()
        self.selected_items = [index.data() for index in self.selected_indexes if ".pdf" in index.data()]
        self.full_paths.clear()
        for index in self.selected_indexes:
            source_index = self.filterModel.mapToSource(index)
            self.full_paths.append(self.model.filePath(source_index))
        self.full_paths = natsorted(self.full_paths)
        self.selected_items = natsorted(self.selected_items)


class RecutButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setObjectName("recut_button")
        self.setFixedWidth(100)
        self.setFlat(True)
        self.setText("No Recut")
        self.clicked.connect(self.toggle_state)

    def toggle_state(self):
        if self.isChecked():
            self.setText("Recut")
        else:
            self.setText("No Recut")


class FreezeTableWidget(QTableView):
    def __init__(self, model):
        super(FreezeTableWidget, self).__init__()
        self.setModel(model)
        self.frozenTableView = QTableView(self)
        self.init()
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def init(self):
        self.frozenTableView.setModel(self.model())
        self.frozenTableView.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.frozenTableView.verticalHeader().hide()
        self.frozenTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.viewport().stackUnder(self.frozenTableView)

        self.frozenTableView.setStyleSheet(
            """
            QTableView { border: none;
                         background-color: #8EDE21;
                         selection-background-color: #999;
            }"""
        )  # for demo purposes

        self.frozenTableView.setSelectionModel(self.selectionModel())
        for col in range(1, self.model().columnCount()):
            self.frozenTableView.setColumnHidden(col, True)
        self.frozenTableView.setColumnWidth(0, self.columnWidth(0))
        self.frozenTableView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozenTableView.show()
        self.updateFrozenTableGeometry()
        self.setHorizontalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)

    def updateSectionWidth(self, logicalIndex, oldSize, newSize):
        self.frozenTableView.setColumnWidth(0, newSize)
        self.updateFrozenTableGeometry()

    def updateSectionHeight(self, logicalIndex, oldSize, newSize):
        self.frozenTableView.setRowHeight(logicalIndex, newSize)

    def resizeEvent(self, event):
        super(FreezeTableWidget, self).resizeEvent(event)
        self.updateFrozenTableGeometry()

    def moveCursor(self, cursorAction, modifiers):
        current = super(FreezeTableWidget, self).moveCursor(cursorAction, modifiers)
        if cursorAction == self.CursorAction.MoveLeft and self.current.column() > 0 and self.visualRect(current).topLeft().x() < self.frozenTableView.columnWidth(0):
            newValue = self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() - self.frozenTableView.columnWidth(0)
            self.horizontalScrollBar().setValue(newValue)
        return current

    def scrollTo(self, index, hint):
        if index.column() > 0:
            super(FreezeTableWidget, self).scrollTo(index, hint)

    def updateFrozenTableGeometry(self):
        self.frozenTableView.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(),
            self.columnWidth(0),
            self.viewport().height() + self.horizontalHeader().height(),
        )


class CustomStandardItemModel(QStandardItemModel):
    itemChanged = pyqtSignal(QStandardItem)
    itemClicked = pyqtSignal(QStandardItem)

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole):
        if item := self.itemFromIndex(index):
            item.setData(value, role)
            self.itemChanged.emit(item)
            return True
        return super(CustomStandardItemModel, self).setData(index, value, role)

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        index = super(CustomStandardItemModel, self).index(row, column, parent)
        if item := self.itemFromIndex(index):
            self.itemClicked.emit(item)
        return index


class FrozenTableView(QTableView):
    itemClicked = pyqtSignal(QStandardItem)

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            if item := self.model().item(index.row(), index.column()):
                self.itemClicked.emit(item)
        return super().mousePressEvent(event)


class CustomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super(CustomTableWidget, self).__init__()
        self.editable_column_indexes = []
        self.setStyleSheet("QScrollBar:horizontal {height: 20px;}")

    def edit(self, index, trigger, event):
        if index.column() in self.editable_column_indexes:
            return super(CustomTableWidget, self).edit(index, trigger, event)
        else:
            return False

    def set_editable_column_index(self, columns: list[int]):
        self.editable_column_indexes = columns


class ComponentsCustomTableWidget(CustomTableWidget):
    imagePasted = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super(ComponentsCustomTableWidget, self).__init__(parent)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            # Handle Ctrl+V
            self.pasteImageFromClipboard()
        else:
            # Pass other key events to the base class
            super().keyPressEvent(event)

    def copySelectedCells(self):
        # Implement this function to copy selected cells to the clipboard if needed
        pass

    def pasteImageFromClipboard(self):
        app = QApplication.instance()
        clipboard = app.clipboard()
        image = clipboard.image()
        if not image.isNull():
            selected_items = self.selectedItems()
            for selected_item in selected_items:
                if selected_item.column() == 0:
                    item = selected_item
                    break

            original_width = image.width()
            original_height = image.height()

            new_height = 60
            new_width = int(original_width * (new_height / original_height))

            if not os.path.exists("images/items"):
                os.makedirs("images/items")
            # Resize the image to fit the specified height while maintaining aspect ratio
            pixmap = QPixmap.fromImage(image).scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_path = f'images/items/{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png'
            pixmap.save(image_path)

            item.setData(Qt.ItemDataRole.DecorationRole, pixmap)

            # Optionally, resize the cell to fit the image
            self.resizeColumnToContents(item.column())
            self.resizeRowToContents(item.row())
            self.imagePasted.emit(image_path, item.row())


class OrderStatusButton(QPushButton):
    def __init__(self, parent=None):
        super(OrderStatusButton, self).__init__(parent)
        self.setCheckable(True)
        self.setText("Order Pending")
        self.setFixedWidth(150)
        self.setObjectName("order_status")


class ItemCheckBox(QCheckBox):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)


class ItemNameComboBox(QComboBox):
    def __init__(self, parent, selected_item: str, items: list[str], tool_tip: str):
        QComboBox.__init__(self, parent)
        self.addItems(items)
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.setEditable(True)
        self.wheelEvent = lambda event: None
        # self.setMinimumWidth(170)
        self.setMaximumWidth(350)


class PartNumberComboBox(QComboBox):
    def __init__(self, parent, selected_item: str, items: list[str], tool_tip: str):
        QComboBox.__init__(self, parent)
        self.addItems(items)
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.setEditable(True)
        self.wheelEvent = lambda event: None
        self.setFixedWidth(120)


class PriorityComboBox(QComboBox):
    def __init__(self, parent, selected_item: int):
        QComboBox.__init__(self, parent)
        self.addItems(["Default", "Low", "Medium", "High"])
        self.setCurrentIndex(selected_item)
        self.wheelEvent = lambda event: None
        self.setFixedWidth(120)


class ExchangeRateComboBox(QComboBox):
    def __init__(self, parent, selected_item: int):
        QComboBox.__init__(self, parent)
        self.addItems(["CAD", "USD"])
        self.setCurrentText(selected_item)
        self.wheelEvent = lambda event: None
        # #self.setFixedWidth(40)


class NotesPlainTextEdit(QPlainTextEdit):
    def __init__(self, parent, text: str, tool_tip: str):
        QPlainTextEdit.__init__(self, parent)
        self.setMinimumWidth(100)
        self.setObjectName("notes")
        self.setStyleSheet("QPlainTextEdit#notes{border-radius: 0px;}QPlainTextEdit:focus#notes{background-color: rgba(32,32,32,130); border: 1px solid #3daee9; border-radius: 0px; color: #EAE9FC;}QPlainTextEdit:hover#notes{border-color: #3daee9;border-radius: 0px; }")
        self.setMaximumWidth(200)
        self.setFixedHeight(60)
        self.setPlainText(text)
        self.setToolTip(tool_tip)


class POPushButton(QPushButton):
    def __init__(self, parent):
        QPushButton.__init__(self, parent)
        # self.setFixedSize(36, 26)
        self.setText("PO")
        self.setToolTip("Open a new purchase order")


class DeletePushButton(QPushButton):
    def __init__(self, parent, tool_tip: str, icon: QIcon):
        QPushButton.__init__(self, parent)
        # self.setFixedSize(26, 26)
        self.setObjectName("delete_button")
        self.setIcon(icon)
        self.setToolTip(tool_tip)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # Signal emitted when the label is clicked

    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the clicked signal


class RichTextPushButton(QPushButton):
    def __init__(self, parent=None, text=None):
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()
        self.__lbl = QLabel(self)
        if text is not None:
            self.__lbl.setText(text)
        self.__layout = QHBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(0)
        self.setLayout(self.__layout)
        self.__lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # type: ignore
        self.__lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)  # type: ignore
        self.__lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # type: ignore
        self.__lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.__lbl.setTextFormat(Qt.TextFormat.RichText)  # type: ignore
        self.__layout.addWidget(self.__lbl)
        return

    def setText(self, text: str, color: str) -> None:
        set_status_button_stylesheet(button=self, color=color)
        if color == "lime":
            color = "#cef4d9"
        elif color == "yellow":
            color = "#ffffe0"
        elif color == "red":
            color = "lightpink"
        text = f'<p style="color:{color};">{text} - {datetime.now().strftime("%r")}</p>'
        self.__lbl.setText(text)
        self.updateGeometry()
        return

    def sizeHint(self) -> QSizePolicy:
        button_size = QPushButton.sizeHint(self)
        label_size = self.__lbl.sizeHint()
        button_size.setWidth(label_size.width())
        button_size.setHeight(label_size.height())
        return button_size


class HumbleDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args):
        super(HumbleDoubleSpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

    def focusInEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(HumbleDoubleSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(HumbleDoubleSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            return super(HumbleDoubleSpinBox, self).wheelEvent(event)
        else:
            event.ignore()


class HumbleSpinBox(QSpinBox):
    def __init__(self, *args):
        super(HumbleSpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(60)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

    def focusInEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(HumbleSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(HumbleSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        if self.hasFocus():
            return super(HumbleSpinBox, self).wheelEvent(event)
        else:
            event.ignore()


class CurrentQuantitySpinBox(QSpinBox):
    def __init__(self, *args):
        super(CurrentQuantitySpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)
        self.lineEdit().setReadOnly(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def focusInEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(CurrentQuantitySpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(CurrentQuantitySpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        event.ignore()


class HumbleComboBox(QComboBox):
    def __init__(self, scrollWidget=None, *args, **kwargs):
        super(HumbleComboBox, self).__init__(*args, **kwargs)
        self.scrollWidget = scrollWidget
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QComboBox.wheelEvent(self, *args, **kwargs)
        else:
            return self.scrollWidget.wheelEvent(*args, **kwargs)


class PlaceholderTextComboBox(QComboBox):
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.Text))

        # draw the combobox frame, focusrect and selected etc.
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)

        if self.currentIndex() < 0:
            opt.palette.setBrush(
                QPalette.ButtonText,
                opt.palette.brush(QPalette.ButtonText).color().lighter(),
            )
            if self.placeholderText():
                opt.currentText = self.placeholderText()

        # draw the icon and text
        painter.drawControl(QStyle.CE_ComboBoxLabel, opt)


class ViewTree(QTreeWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setHeaderLabels(
            [
                "Name",
                "Part Number",
                "Unit Quantity",
                "Current Quantity",
                "Price",
                "Priority",
                "Notes",
            ]
        )
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 70)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 90)
        self.setColumnWidth(4, 50)
        self.setColumnWidth(5, 40)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.setAlternatingRowColors(True)
        delegate = StyledItemDelegate(self)
        self.setItemDelegate(delegate)
        self.load_ui()

    def load_ui(self) -> None:
        def fill_item(item, value):
            """
            It takes a QTreeWidgetItem and a value, and if the value is a dict, list, or tuple, it
            creates a new QTreeWidgetItem for each key/value pair or list item, and recursively calls
            itself on each of those new QTreeWidgetItems

            Args:
              item: The item to fill
              value: The value to be displayed in the tree.

            Returns:
              A dictionary with a list of dictionaries.
            """

            def new_item(parent, text, val=None):
                if type(val) != dict:
                    child = QTreeWidgetItem([text, str(val)])
                else:
                    try:
                        child = QTreeWidgetItem(
                            [
                                text,
                                str(val["part_number"]),
                                str(val["unit_quantity"]),
                                str(val["current_quantity"]),
                                str(val["price"]),
                                str(val["priority"]),
                                str(val["notes"]),
                            ]
                        )
                    except KeyError:
                        child = QTreeWidgetItem([text])
                        fill_item(child, val)
                parent.addChild(child)

            if value is None:
                return
            elif isinstance(value, dict):
                for key, val in sorted(value.items()):
                    new_item(item, str(key), val)
            elif isinstance(value, (list, tuple)):
                for val in value:
                    text = f"[{type(val).__name__}]" if isinstance(val, (dict, list, tuple)) else str(val)
                    new_item(item, text, val)

        fill_item(self.invisibleRootItem(), self.data)


class HeaderScrollArea(QScrollArea):
    def __init__(self, headers: dict[str:int], parent=None):
        QScrollArea.__init__(self, parent)
        self.headers: dict[str, int] = headers

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setVerticalSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_widget.setLayout(self.grid_layout)
        self.setWidgetResizable(True)
        self.setWidget(self.grid_widget)

        self.margins = QMargins(0, 30, 0, 0)
        self.setViewportMargins(self.margins)
        self.headings_widget = QWidget(self)
        self.headings_widget.setStyleSheet("border-bottom: 1px solid #3daee9;")
        self.headings_layout = QGridLayout()
        self.headings_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headings_widget.setLayout(self.headings_layout)
        self.headings_layout.setContentsMargins(0, 0, 0, 0)
        self.headings_layout.columnStretch(0)
        for col_index, header in enumerate(list(self.headers.keys())):
            heading = QLabel(header)
            heading.setFixedWidth(self.headers[header])
            heading.setContentsMargins(0, 0, 0, 0)
            self.headings_layout.addWidget(heading, 0, col_index)
            self.headings_layout.setColumnStretch(col_index, 0)

    def resizeEvent(self, event) -> None:
        rect = self.viewport().geometry()
        self.headings_widget.setGeometry(rect.x(), rect.y() - self.margins.top(), rect.width(), self.margins.top())
        QScrollArea.resizeEvent(self, event)


class DragableLayout(QWidget):
    orderChanged = pyqtSignal(list)

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                # Drag drop horizontally.
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                # We didn't drag past this widget.
                # insert to the left of it.
                self.blayout.insertWidget(n - 1, widget)
                self.orderChanged.emit(self.get_item_data())
                break

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data


class StyledItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        item = super(StyledItemDelegate, self).sizeHint(option, index)
        if not index.parent().isValid():
            item.setHeight(60)
        return item


def set_default_dialog_button_stylesheet(button: QPushButton) -> None:
    button.setStyleSheet(
        """
        QPushButton#default_dialog_button{
            background-color: #3daee9;
            border: 0.04em solid  #3daee9;
            border-radius: 5px;
        }
        QPushButton#default_dialog_button:hover{
            background-color: #49b3eb;
            border: 0.04em solid  #49b3eb;
        }
        QPushButton#default_dialog_button:pressed{
            background-color: #5cbaed;
            color: #bae2f8;
            border: 0.04em solid  #5cbaed;
        }
        QPushButton#default_dialog_button:disabled{
            background-color: rgba(32,32,32,130);
            color: #8C8C8C;
            border: 0.04em solid  #8C8C8C;
            border-radius: 4px;
        }
        """
    )


def set_status_button_stylesheet(button: QPushButton, color: str) -> None:
    background_color = "rgb(71, 71, 71)"
    border_color = "rgb(71, 71, 71)"
    if color == "lime":
        background_color = "#315432"
        border_color = "darkgreen"
    elif color == "yellow":
        background_color = "#413C28"
        border_color = "gold"
    elif color == "red":
        background_color = "#3F1E25"
        border_color = "darkred"
    elif color == "#3daee9":
        background_color = "#1E363F"
        border_color = "#3E8C99"
    button.setStyleSheet(
        """
        QPushButton#status_button:flat {
            border: none;
        }
        QPushButton#status_button{
            border: 0.04em solid  %(background_color)s;
            background-color: %(background_color)s;
            border-radius: 0px;
            color: %(color)s;
        }
        QPushButton#status_button:hover{
            border: 0.04em solid  %(border_color)s;
        }
        QPushButton#status_button:pressed{
            border: 0.15em solid  %(border_color)s;
        }
        """
        % {
            "color": color,
            "border_color": border_color,
            "background_color": background_color,
        }
    )
