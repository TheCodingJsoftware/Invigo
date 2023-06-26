import contextlib
import os
import sys
import typing
from datetime import datetime, timedelta
from functools import partial

from natsort import natsorted
from PyQt6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    QDateTime,
    QEvent,
    QMargins,
    QMimeData,
    QModelIndex,
    QPoint,
    QRegularExpression,
    QSettings,
    QSortFilterProxyModel,
    Qt,
    QTime,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDrag,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDropEvent,
    QFileSystemModel,
    QIcon,
    QPainter,
    QPalette,
    QPixmap,
    QRegularExpressionValidator,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
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
    QFormLayout,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utils.workspace.assembly import Assembly
from utils.workspace.item import Item


class FilterTabWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.tab_widget = QTabWidget()
        self.show_all_tab = QWidget()
        layout = QFormLayout(self.show_all_tab)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)  # Set alignment to top-left
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)  # Allow fields to grow
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # Set label alignment to left

        self.tab_widget.addTab(self.show_all_tab, "Show All")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        self.buttons: list[QPushButton] = []

        self.tabs = {"Show All": []}  # Dictionary to store tabs and their buttons
        self.tab_widget.currentChanged.connect(self.update_tab_button_visibility)

    def add_tab(self, name):
        tab_container = QWidget()
        tab_widget = QWidget()
        layout = QFormLayout(tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)  # Set alignment to top-left
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)  # Allow fields to grow
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # Set label alignment to left
        tab_widget.setLayout(layout)
        tab_container_layout = QVBoxLayout(tab_container)
        tab_container_layout.addWidget(tab_widget)
        self.tab_widget.addTab(tab_container, name)

        self.tabs[name] = []  # Add tab with an empty list for buttons

        return layout

    def add_button_to_tab(self, tab_name, button_name):
        buttons = self.tabs.get(tab_name)
        if buttons is not None:
            button = QPushButton(button_name, checkable=True)
            buttons.append(button)  # Add button to the list
            self.buttons.append(button)

    def get_buttons(self, tab_name):
        buttons = self.tabs.get(tab_name)
        if buttons is not None:
            return buttons
        return []

    def update_tab_button_visibility(self, tab_index: int):
        tab_name = self.tab_widget.tabText(tab_index)
        buttons = self.tabs.get(tab_name)
        if tab_name == "Show All":
            layout = self.tab_widget.widget(tab_index).layout()
            for button in self.buttons:
                layout.addWidget(button)
                button.setVisible(True)
        else:
            if buttons is not None:
                layout = self.tab_widget.widget(tab_index).layout()
                for button in self.buttons:
                    if button in buttons:
                        layout.addWidget(button)
                        button.setVisible(True)
                    else:
                        button.setVisible(False)


class ScrollPositionManager:
    def __init__(self):
        self.scroll_positions: dict[str, QPoint] = {}

    def save_scroll_position(self, tab_name: str, scroll: QTableWidget | QScrollArea):
        scroll_position = QPoint(scroll.horizontalScrollBar().value(), scroll.verticalScrollBar().value())
        if not scroll_position.y():
            return
        self.scroll_positions[tab_name] = scroll_position

    def restore_scroll_position(self, tab_name: str, scroll: QTableWidget | QScrollArea):
        try:
            scroll_position = self.scroll_positions[tab_name]
        except KeyError:
            return
        if scroll_position is not None:
            scroll.horizontalScrollBar().setValue(scroll_position.x())
            scroll.verticalScrollBar().setValue(scroll_position.y())


class RecordingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.recording = True
        self.recording_color = QColor("red")
        self.nonrecording_color = QColor("gray")
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
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(TimeSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(TimeSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        If the spinbox has focus, then it will behave as normal. If it doesn't have focus, then the
        wheel event will be ignored

        Args:
          event: The event object

        Returns:
          The super class of the HumbleSpinBox class.
        """
        if self.hasFocus():
            return super(TimeSpinBox, self).wheelEvent(event)
        else:
            event.ignore()

    def eventFilter(self, obj, event):
        """
        This function filters events and changes the value based on the wheel event.

        Args:
          obj: The object that is being filtered for events.
          event: The event parameter is an instance of the QEvent class, which represents an event that
        occurred in the application. It contains information about the type of event, its source, and
        any additional data associated with it. In this case, the code is checking if the event type is
        a wheel event, which

        Returns:
          a boolean value indicating whether the event has been handled or not. If the event type is a
        wheel event, the function returns True after calling the `changeValue()` method. If the event
        type is not a wheel event, the function calls the `eventFilter()` method of the parent class and
        returns the value returned by that method.
        """
        if event.type() == QEvent.Type.Wheel and self.hasFocus():
            delta = event.angleDelta().y() / 120
            self.changeValue(delta)
            return True

        return super().eventFilter(obj, event)

    def changeValue(self, delta):
        """
        This function changes the value of a variable based on a given delta, with different increments
        depending on the current value.

        Args:
          delta: The amount by which the value of the object should be changed. It can be a positive or
        negative number.
        """
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
        """
        This function converts a decimal value representing days, hours, and minutes into a formatted
        string.

        Args:
          value: A float value representing a duration in hours.

        Returns:
          a formatted string that represents the input value as a number of days, hours, and minutes.
        The input value is first converted to an integer number of days, and then the remaining hours
        and minutes are calculated and added to the string. The string includes pluralization of the
        units based on whether the value is singular or plural.
        """
        days = int(value)
        hours = int((value - days) * 24)
        minutes = int(((value - days) * 24 - hours) * 60)
        return f"{days} day{'s' if days != 1 else ''} {hours:02d} hour{'s' if hours != 1 else ''} {minutes:02d} minute{'s' if minutes != 1 else ''}"

    def valueFromText(self, text):
        """
        The function takes a string of time in days, hours, and minutes and returns the total value in
        days.

        Args:
          text: a string containing a time value in the format "X days Y hours Z minutes", where X, Y,
        and Z are integers.

        Returns:
          a float value that represents the total number of days, including fractions of a day,
        represented by the input text. The input text is expected to be in the format "X days Y hours Z
        minutes", where X, Y, and Z are integers. The function calculates the total number of days by
        adding the number of days, the fraction of a day represented by the number of
        """
        time_parts = text.split(" ")
        days = int(time_parts[0])
        hours = int(time_parts[2])
        minutes = int(time_parts[4])
        return days + hours / 24 + minutes / (24 * 60)

    def fixup(self, text):
        """
        The function takes in a string of time in days, hours, and minutes format and adds a leading
        zero to the days, hours, or minutes if they are equal to 1.

        Args:
          text: The input text that needs to be fixed up. It is expected to be a string containing time
        information in the format "X days Y hours Z minutes". The function will check if the number of
        parts in the string is 6, and if so, it will extract the number of days, hours

        Returns:
          a string that is either the original input `text` or a modified version of it with leading
        zeros added to the days, hours, or minutes if they are equal to 1.
        """
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
        """
        This function calculates the time difference between the current date and time and a future date
        and time based on a given value in days, hours, and minutes.

        Returns:
          A datetime.timedelta object is being returned.
        """
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
        if not self.dragging:
            self.buttonClicked.emit()
        self.dragging = False
        super().mouseReleaseEvent(event)


class DropWidget(QWidget):
    def __init__(self, parent, assembly: Assembly, item: Item, files_layout: QHBoxLayout, file_category: str):
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
            allowed_extensions = [".pdf", ".dxf", ".jpeg", ".geo", ".png", ".jpg", "sldprt"]  # Allowed file extensions
            valid_files = all(file_path.lower().endswith(tuple(allowed_extensions)) for file_path in file_paths)
            if valid_files:
                self.label.setText("Processing")
                self.label.setStyleSheet("background-color: rgba(70,210,110, 100);")
                self.parent.handle_dropped_file(self.label, file_paths, self.assembly, self.item, self.files_layout, self.file_category)
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
        """
        This function returns the number of keys in a dictionary.

        Args:
          parent: The parent parameter is an optional argument that specifies the parent item of the
        current item. In this case, it is set to None, which means that the current item has no parent.

        Returns:
          The function `rowCount` is returning the length of the `keys` attribute of the object.
        """
        return len(self.keys)

    def columnCount(self, parent=None):
        """
        This function returns the value 2 as the number of columns in a table or grid.

        Args:
          parent: The parent widget of the current widget. It is an optional parameter and if not
        specified, the current widget will be a top-level widget.

        Returns:
          the integer value 2.
        """
        return 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        This function returns the data for a given index and role in a dictionary model.

        Args:
          index: The index of the item in the model that the view is requesting data for.
          role: The role parameter is used to specify the type of data that is being requested. In this
        case, it is set to Qt.DisplayRole, which means that the data is being requested for display
        purposes. Other possible roles include Qt.EditRole (for editing data) and Qt.ToolTipRole (for
        providing tooltip

        Returns:
          The method `data()` returns the data to be displayed in a specific cell of a table view. If
        the `role` parameter is `Qt.DisplayRole`, it returns the data to be displayed as a string. If
        the `index` parameter refers to the first column, it returns the key of the dictionary at the
        corresponding row. If the `index` parameter refers to the second column, it
        """
        if role == Qt.ItemDataRole.DisplayRole:
            key = self.keys[index.row()]
            value = self.dictionary[key]

            if index.column() == 0:
                return key
            elif index.column() == 1:
                return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        This function returns the header data for a table view in a specific format based on the section,
        orientation, and role.

        Args:
          section: The index of the section for which header data is being requested. For example, if the
        header is for the first column, section would be 0.
          orientation: The orientation parameter specifies whether the header is for the horizontal axis
        (columns) or the vertical axis (rows) of a table or other data structure. It can have two possible
        values: Qt.Horizontal or Qt.Vertical.
          role: The role parameter is used to specify the type of data that is being requested. In this
        case, the function is checking if the role is equal to Qt.DisplayRole, which means that the data is
        being requested for display purposes.

        Returns:
          If the role is `Qt.DisplayRole`, the method returns the header data for the specified section and
        orientation. If the orientation is horizontal, it returns "Key" for section 0 and "Value" for
        section 1. If the orientation is vertical, it returns the section number as a string. If the role is
        not `Qt.DisplayRole`, it returns `None`.
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return ["Key", "Value"][section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)

        return None


class PartInformationViewer(QDialog):
    def __init__(self, title: str, dictionary: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)

        layout = QVBoxLayout(self)
        self.table_view = QTableView(self)
        layout.addWidget(self.table_view)

        model = DictionaryTableModel(dictionary, self)
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()
        self.setMinimumSize(450, 700)


class AssemblyMultiToolBox(QWidget):
    """The class MultiToolBox is a QWidget."""

    def __init__(self, parent=None):
        super(AssemblyMultiToolBox, self).__init__(parent)
        self.widgets: list[QWidget] = []
        self.buttons: list[QPushButton] = []
        self.input_box: list[QLineEdit] = []
        self.delete_buttons: list[DeletePushButton] = []
        self.duplicate_buttons: list[QPushButton] = []
        self.check_boxes: list[QCheckBox] = []
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet("QWidget#assembly_widget{border: 1px solid gray;}")
        self.setLayout(main_layout)

    def addItem(self, widget: QWidget, title: str):
        """
        This function adds a widget with a title and a toggle button to a layout.

        Args:
          widget (QWidget): QWidget - This is the widget that will be added to the sheet. It can be any
        type of QWidget, such as a QLabel, QComboBox, or even another layout.
          title (str): A string representing the title of the widget that will be added to the layout.
        """

        # Apply the drop shadow effect to the widget
        # checkbox = QCheckBox(widget)
        # checkbox.setStyleSheet("QCheckBox:indicator{width: 20px; height: 20px;}")
        # checkbox.setFixedWidth(22)
        _widget = QWidget(self)
        _widget.setContentsMargins(0, 0, 0, 0)
        widget.setParent(_widget)
        button = QPushButton(_widget)
        button.setObjectName("edit_sheet_nest_button")
        button.setFixedWidth(24)
        button.setFixedHeight(24)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setText(" 🡇")
        button.setChecked(True)
        button.setCheckable(True)

        input_box = QLineEdit(widget)
        button.clicked.connect(
            lambda checked, w=widget: (
                self.toggle_widget_visibility(w),
                button.setText(" 🡇" if w.isVisible() else " 🡆"),
                input_box.setStyleSheet(
                    "background-color: #3daee9; border-color: #3daee9; border-bottom-right-radius: 0.01em;"
                    if w.isVisible()
                    else "background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 8px;"
                ),
            )
        )
        input_box.setObjectName("input_box_multitoolbox")
        input_box.setText(title)
        input_box.setFixedHeight(24)
        input_box.setStyleSheet("background-color: #3daee9; border-color: #3daee9; border-bottom-right-radius: 0.01em;")

        delete_button = DeletePushButton(
            parent=widget, tool_tip=f"Delete {title} forever", icon=QIcon("ui/BreezeStyleSheets/dist/pyqt6/dark/trash.png")
        )
        delete_button.setFixedWidth(23)
        duplicate_button = QPushButton()
        duplicate_button.setIcon(QIcon(r"F:\Code\Python-Projects\Inventory Manager\ui\BreezeStyleSheets\dist\pyqt6\dark\duplicate.png"))
        duplicate_button.setFixedWidth(23)
        duplicate_button.setToolTip(f"Duplicate {title}")

        # widget.setMinimumHeight(100)

        hlaout = QHBoxLayout(widget)
        hlaout.setSpacing(0)
        hlaout.setContentsMargins(0, 0, 0, 0)
        # hlaout.addWidget(checkbox)
        hlaout.addWidget(button)
        hlaout.addWidget(input_box)
        hlaout.addWidget(duplicate_button)
        hlaout.addWidget(delete_button)
        layout = QVBoxLayout(_widget)
        layout.setSpacing(0)
        layout.addLayout(hlaout)
        layout.addWidget(widget)
        _widget.setLayout(layout)
        widget.setObjectName("edit_multi_tool_box_widget")

        self.buttons.append(button)
        self.delete_buttons.append(delete_button)
        self.input_box.append(input_box)
        self.widgets.append(widget)
        self.duplicate_buttons.append(duplicate_button)
        # self.check_boxes.append(checkbox)

        self.layout().addWidget(_widget)

    def removeItem(self, widget_to_delete: QWidget) -> None:
        main_layout = self.layout()  # Get the reference to the main layout
        for i in reversed(range(main_layout.count())):
            layout_item = main_layout.itemAt(i)
            if layout_item.itemAt(1).widget() == widget_to_delete:  # Check if the layout's widget matches the given widget
                self.delete_buttons[i].disconnect()
                self.buttons[i].disconnect()
                self.buttons.pop(i)
                self.delete_buttons.pop(i)
                self.duplicate_buttons.pop(i)
                self.check_boxes.pop(i)
                self.input_box.pop(i)
                self.widgets.pop(i)
                layout = layout_item.layout()
                self.clear_layout(layout)
                while layout.count():
                    item = layout.takeAt(0)
                    if item_widget := item.widget():
                        item_widget.deleteLater()
                main_layout.removeItem(layout_item)
                del layout
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

    def setItemText(self, index: int, new_name: str):
        """
        This function sets the text of a button at a given index to a new name.

        Args:
          index (int): an integer representing the index of the button whose text needs to be changed.
          new_name (str): A string representing the new text that will be set for the button at the
        specified index.
        """
        if 0 <= index < len(self.input_box):
            self.input_box[index].setText(new_name)

    def setItemIcon(self, index: int, icon_path: str):
        """
        This function sets the icon of a button at a given index with the icon located at a specified
        file path.

        Args:
          index (int): An integer representing the index of the button in the list of buttons.
          icon_path (str): The path to the icon file that will be used as the button's icon.
        """
        if 0 <= index < len(self.buttons):
            button = self.buttons[index]
            icon = QIcon(icon_path)
            button.setIcon(icon)

    def getWidget(self, index):
        """
        This function returns the widget at the specified index if it exists, otherwise it returns None.

        Args:
          index: The index parameter is an integer value that represents the position of the widget in
        the list of widgets. It is used to retrieve a specific widget from the list of widgets.

        Returns:
          The method `getWidget` returns either the widget at the specified index in the `self.widgets`
        list, or `None` if the index is out of range.
        """
        return self.widgets[index] if 0 <= index < len(self.widgets) else None

    def count(self) -> int:
        """
        The function returns the number of widgets in a class.

        Returns:
          The function `count()` is returning an integer value which represents the length of the
        `widgets` list.
        """
        return len(self.widgets)

    def toggle_widget_visibility(self, widget):
        """
        This function toggles the visibility of a widget in a Python GUI.

        Args:
          widget: The widget parameter is a reference to a graphical user interface (GUI) widget object.
        The function toggles the visibility of this widget, i.e., if the widget is currently visible, it
        will be hidden, and if it is currently hidden, it will be made visible. The widget object could
        be
        """
        widget.setVisible(not widget.isVisible())
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        if widget.isVisible():
            shadow.setColor(QColor(61, 174, 233, 255))
        else:
            shadow.setColor(QColor(0, 0, 0, 255))
        shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        widget.parentWidget().setGraphicsEffect(shadow)

    def close_all(self) -> None:
        for button, widget, input_box in zip(self.buttons, self.widgets, self.input_box):
            button.click()
            # button.setChecked(False)
            widget.setVisible(False)
            button.setText(" 🡇" if widget.isVisible() else " 🡆")
            input_box.setStyleSheet(
                "background-color: #3daee9; border-color: #3daee9; border-bottom-right-radius: 0.01em;"
                if widget.isVisible()
                else "background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 8px;"
            )

    def clear_layout(self, layout) -> None:
        """
        If the layout is not None, while the layout has items, take the first item, get the widget, if
        the widget is not None, delete it, otherwise clear the layout

        Args:
          layout: The layout to be cleared
        """
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
        """
        This function returns a dictionary containing the visibility status of each widget in a list of
        widgets.

        Returns:
          A dictionary where the keys are integers representing the index of each widget in a list of
        widgets, and the values are boolean values indicating whether each widget is currently visible
        or not.
        """
        return {i: widget.isVisible() for i, widget in enumerate(self.widgets)}

    def set_widgets_visibility(self, widgets_visibility: dict[int, bool]) -> None:
        """
        This function sets the visibility of widgets based on a dictionary of widget IDs and boolean
        values, and closes any widgets that are not visible.

        Args:
          widgets_visibility (dict[int, bool]): A dictionary where the keys are integers representing
        widget IDs and the values are boolean values indicating whether the widget should be visible or
        not.
        """
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
            self.buttons[index].setText(" 🡇")
            self.widgets[index].setVisible(True)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(61, 174, 233, 255))
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            self.widgets[index].parentWidget().setGraphicsEffect(shadow)
            self.input_box[index].setStyleSheet("background-color: #3daee9; border-color: #3daee9; border-bottom-right-radius: 0.01em;")

    def close(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setText(" 🡆")
            self.buttons[index].setChecked(True)
            self.widgets[index].setVisible(False)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(0, 0, 0, 255))  # Set the shadow color and opacity
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            self.widgets[index].parentWidget().setGraphicsEffect(shadow)
            self.input_box[index].setStyleSheet(
                "background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 8px;"
            )

    def close_all(self) -> None:
        for button, widget, input_box in zip(self.buttons, self.widgets, self.input_box):
            button.click()
            button.click()
            button.setChecked(True)
            button.setText(" 🡆")
            widget.setVisible(False)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(0, 0, 0, 255))  # Set the shadow color and opacity
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            widget.parentWidget().setGraphicsEffect(shadow)
            input_box.setStyleSheet("background-color: rgba(71, 71, 71, 110); border-color: rgba(76, 76, 76, 110); border-bottom-right-radius: 8px;")


class MultiToolBox(QWidget):
    """The class MultiToolBox is a QWidget."""

    def __init__(self, parent=None):
        super(MultiToolBox, self).__init__(parent)
        self.widgets: list[QWidget] = []
        self.widget_visibility: dict[int, bool] = {}
        self.buttons: list[QPushButton] = []
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(main_layout)

    def addItem(self, widget: QWidget, title: str):
        """
        This function adds a widget with a title and a toggle button to a layout.

        Args:
          widget (QWidget): QWidget - This is the widget that will be added to the sheet. It can be any
        type of QWidget, such as a QLabel, QComboBox, or even another layout.
          title (str): A string representing the title of the widget that will be added to the layout.
        """

        _widget = QWidget(self)
        _widget.setContentsMargins(0, 3, 0, 3)
        widget.setParent(_widget)
        button = QPushButton(_widget)
        button.setObjectName("sheet_nest_button")
        button.setText(title)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setChecked(False)
        button.setCheckable(True)
        button.clicked.connect(partial(self.toggle_widget_visibility, widget, button))

        widget.setVisible(False)

        layout = QVBoxLayout(_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button)
        layout.addWidget(widget)
        _widget.setLayout(layout)
        widget.setObjectName("nest_widget")
        widget.setAutoFillBackground(True)
        widget.setStyleSheet("QWidget#nest_widget{border: 1px solid #3daee9; background-color: rgb(33, 33, 33);}")

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        if widget.isVisible():
            shadow.setColor(QColor(0, 0, 0, 255))
        else:
            shadow.setColor(QColor(61, 174, 233, 255))
        shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        widget.parentWidget().setGraphicsEffect(shadow)

        self.buttons.append(button)
        self.widgets.append(widget)

        self.layout().addWidget(_widget)

    def setItemText(self, index: int, new_name: str):
        """
        This function sets the text of a button at a given index to a new name.

        Args:
          index (int): an integer representing the index of the button whose text needs to be changed.
          new_name (str): A string representing the new text that will be set for the button at the
        specified index.
        """
        if 0 <= index < len(self.buttons):
            self.buttons[index].setText(new_name)

    def setItemIcon(self, index: int, icon_path: str):
        """
        This function sets the icon of a button at a given index with the icon located at a specified
        file path.

        Args:
          index (int): An integer representing the index of the button in the list of buttons.
          icon_path (str): The path to the icon file that will be used as the button's icon.
        """
        if 0 <= index < len(self.buttons):
            button = self.buttons[index]
            icon = QIcon(icon_path)
            button.setIcon(icon)

    def getWidget(self, index):
        """
        This function returns the widget at the specified index if it exists, otherwise it returns None.

        Args:
          index: The index parameter is an integer value that represents the position of the widget in
        the list of widgets. It is used to retrieve a specific widget from the list of widgets.

        Returns:
          The method `getWidget` returns either the widget at the specified index in the `self.widgets`
        list, or `None` if the index is out of range.
        """
        return self.widgets[index] if 0 <= index < len(self.widgets) else None

    def count(self) -> int:
        """
        The function returns the number of widgets in a class.

        Returns:
          The function `count()` is returning an integer value which represents the length of the
        `widgets` list.
        """
        return len(self.widgets)

    def get_widget_visibility(self) -> dict[int, bool]:
        """
        This function returns a dictionary containing the visibility status of each widget in a list of
        widgets.

        Returns:
          A dictionary where the keys are integers representing the index of each widget in a list of
        widgets, and the values are boolean values indicating whether each widget is currently visible
        or not.
        """
        return {i: widget.isVisible() for i, widget in enumerate(self.widgets)}

    def set_widgets_visibility(self, widgets_visibility: dict[int, bool]) -> None:
        """
        This function sets the visibility of widgets based on a dictionary of widget IDs and boolean
        values, and closes any widgets that are not visible.

        Args:
          widgets_visibility (dict[int, bool]): A dictionary where the keys are integers representing
        widget IDs and the values are boolean values indicating whether the widget should be visible or
        not.
        """
        if len(widgets_visibility.items()) > 0:
            for i, is_visible in widgets_visibility.items():
                if is_visible:
                    self.open(i)
                else:
                    self.close(i)
        else:
            self.close_all()

    def toggle_widget_visibility(self, widget: QWidget, button: QPushButton):
        """
        This function toggles the visibility of a widget in a Python GUI.

        Args:
          widget: The widget parameter is a reference to a graphical user interface (GUI) widget object.
        The function toggles the visibility of this widget, i.e., if the widget is currently visible, it
        will be hidden, and if it is currently hidden, it will be made visible. The widget object could
        be
        """
        widget.setVisible(not widget.isVisible())
        # button.setChecked(not button.isChecked())
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        if widget.isVisible():
            shadow.setColor(QColor(61, 174, 233, 255))
        else:
            shadow.setColor(QColor(0, 0, 0, 255))
        widget.parentWidget().setGraphicsEffect(shadow)
        if button.isChecked():
            shadow.setColor(QColor(0, 0, 0, 255))
            button.setGraphicsEffect(shadow)
        else:
            shadow.setColor(QColor(61, 174, 233, 255))
            button.setGraphicsEffect(shadow)

    def open(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setChecked(False)
            self.widgets[index].setVisible(True)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(61, 174, 233, 255))
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            self.widgets[index].parentWidget().setGraphicsEffect(shadow)
            self.buttons[index].setGraphicsEffect(shadow)

    def close(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setChecked(True)
            self.widgets[index].setVisible(False)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setColor(QColor(0, 0, 0, 255))  # Set the shadow color and opacity
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            self.widgets[index].parentWidget().setGraphicsEffect(shadow)
            self.buttons[index].setGraphicsEffect(shadow)

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
            widget.parentWidget().setGraphicsEffect(shadow)
            button.setGraphicsEffect(shadow)


class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(CustomTabWidget, self).__init__(parent)
        self.tab_order = []  # Stores the current order of tabs as strings
        self.tabBar().installEventFilter(self)
        self.wheelEvent = lambda event: None

    def dragMoveEvent(self, event):
        # Check if it's a tab being dragged
        if event.source() == self.tabBar():
            event.ignore()  # Ignore the drag move event
        else:
            super().dragMoveEvent(event)

    def wheelEvent(self, event):
        """
        This function ignores the wheel event.

        Args:
          event: The event parameter in this code refers to a QWheelEvent object, which is an event that
        occurs when the user rotates the mouse wheel. This function is a method of a class that inherits
        from QWidget, and it is used to handle the wheel event when it occurs on the widget.
        """
        event.ignore()

    def update_tab_order(self):
        """
        This function updates the tab order of a widget by creating a list of tab texts in the order
        they appear.
        """
        self.tab_order = [self.tabText(i) for i in range(self.count())]

    def get_tab_order(self) -> list[str]:
        """
        This function returns a list of strings representing the tab order of a QTabWidget.

        Returns:
          A list of strings representing the tab order.
        """
        self.update_tab_order()
        return self.tab_order

    def set_tab_order(self, order):
        """
        This function sets the tab order of a tab bar based on a given list of tab names.

        Args:
          order: A list of tab names in the desired order. The function will reorder the tabs in the tab
        bar based on this order.
        """
        for tab_name in order:
            index = self.find_tab_by_name(tab_name)
            if index != -1:
                self.tabBar().moveTab(index, order.index(tab_name))

    def find_tab_by_name(self, name: str) -> int:
        """
        This function finds the index of a tab in a tab widget by its name.

        Args:
          name (str): A string representing the name of the tab that needs to be found.

        Returns:
          an integer value which represents the index of the tab with the given name in the tab widget.
        If the tab is not found, it returns -1.
        """
        for i in range(self.count()):
            if self.tabText(i) == name:
                return i
        return -1


class PdfFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def filterAcceptsRow(self, row, parent):
        """
        This function filters rows based on whether they contain a file with a .pdf extension.

        Args:
          row: The row number of the item being filtered in the view.
          parent: The parent index of the current index being filtered. It represents the parent item in
        the model hierarchy.

        Returns:
          a boolean value indicating whether the row should be included in the filtered view or not.
        """
        index = self.sourceModel().index(row, 0, parent)
        if not index.isValid():
            return False
        if self.sourceModel().isDir(index):
            return any(file.lower().endswith(".pdf") for file in os.listdir(self.sourceModel().filePath(index)))
        filename = self.sourceModel().fileName(index)
        return filename.lower().endswith(".pdf")


class PdfTreeView(QTreeView):
    def __init__(self, path: str):
        super().__init__()
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.setModel(self.model)
        self.filterModel = PdfFilterProxyModel()
        self.filterModel.setSourceModel(self.model)
        self.setModel(self.filterModel)
        self.filterModel.setFilterKeyColumn(0)
        self.setRootIndex(self.filterModel.mapFromSource(self.model.index(path)))
        self.header().resizeSection(0, 170)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.header().hideSection(1)  # Size
        self.header().hideSection(2)  # File type
        self.selected_indexes = []
        self.selected_items = []
        self.full_paths = []
        self.setSortingEnabled(True)
        # Connect the header's sectionClicked signal to handle sorting

        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        """
        This function updates a list of selected items and their full file paths when the selection in a
        model/view is changed.

        Args:
          selected: A list of QModelIndex objects representing the newly selected items in the view.
          deselected: The deselected parameter is a list of QModelIndex objects that represent the
        indexes that were previously selected but are no longer selected after the selection has
        changed.
        """
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
        """
        This function initializes a checkable and clickable button with the text "No Recut" and a fixed
        width of 100.

        Args:
          parent: The parent parameter is used to specify the parent widget of the current widget. If a
        parent widget is specified, the current widget becomes a child of the parent widget and is
        displayed within it. If no parent widget is specified, the current widget becomes a top-level
        widget and is displayed independently. In this
        """
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setObjectName("recut_button")
        self.setFixedWidth(100)
        self.setFlat(True)
        self.setText("No Recut")
        self.clicked.connect(self.toggle_state)

    def toggle_state(self):
        """
        This function toggles the text of a button between "Recut" and "No Recut" based on its current
        state.
        """
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
        if (
            cursorAction == self.CursorAction.MoveLeft
            and self.current.column() > 0
            and self.visualRect(current).topLeft().x() < self.frozenTableView.columnWidth(0)
        ):
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
            item = self.model().item(index.row(), index.column())
            if item:
                self.itemClicked.emit(item)
        return super().mousePressEvent(event)


class CustomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super(CustomTableWidget, self).__init__()
        self.editable_column_indexes = []

    def edit(self, index, trigger, event):
        """
        This function checks if a column is editable and allows editing if it is, otherwise it returns
        False.

        Args:
          index: The index of the item in the model that is being edited.
          trigger: The trigger parameter is an event that causes the editor to be opened for editing the
        cell. It can be one of the following values:
          event: The event parameter in the edit() method is an instance of QEvent class. It represents
        an event that occurred on the widget. The event parameter is used to determine the type of event
        that occurred, such as a mouse click or a key press, and to handle the event accordingly.

        Returns:
          If the column index of the given index is in the list of editable_column_indexes, then the
        super().edit() method is called and its return value is returned. Otherwise, False is returned.
        """
        if index.column() in self.editable_column_indexes:
            return super(CustomTableWidget, self).edit(index, trigger, event)
        else:
            return False

    def set_editable_column_index(self, columns: list[int]):
        """
        This function sets the indexes of columns that are editable in a table.

        Args:
          columns (list[int]): A list of integers representing the indexes of the columns that should be
        editable in a table or spreadsheet.
        """
        self.editable_column_indexes = columns


# class _CustomTableWidget(QTableView):
#     itemClicked = pyqtSignal(QStandardItem)

#     def __init__(self, parent=None, model: QStandardItemModel = None):
#         super(CustomTableWidget, self).__init__()
#         self.editable_column_indexes = []
#         self.frozenTableView = FrozenTableView(self)
#         self.frozenTableView.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
#         self.frozenTableView.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
#         self.frozenTableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
#         self.frozenTableView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

#         self.setModel(model)
#         self.init()
#         self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
#         self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
#         self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
#         self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)
#         self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
#         self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
#         self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
#         self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

#     def init(self):
#         self.frozenTableView.setModel(self.model())
#         self.frozenTableView.setFocusPolicy(Qt.FocusPolicy.NoFocus)
#         self.frozenTableView.verticalHeader().hide()
#         self.frozenTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
#         self.viewport().stackUnder(self.frozenTableView)

#         for col in range(1, self.model().columnCount()):
#             self.frozenTableView.setColumnHidden(col, True)
#         # self.frozenTableView.setStyleSheet(
#         #     """
#         #     QTableView { border: none;
#         #                  background-color: #8EDE21;
#         #                  selection-background-color: #999;
#         #     }"""
#         # )  # for demo purposes

#         self.frozenTableView.setSelectionModel(self.selectionModel())
#         self.frozenTableView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
#         self.frozenTableView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
#         self.frozenTableView.show()
#         self.updateFrozenTableGeometry()
#         self.setHorizontalScrollMode(self.ScrollMode.ScrollPerPixel)
#         self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
#         self.frozenTableView.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)

#     def edit(self, index, trigger, event):
#         """
#         This function checks if a column is editable and allows editing if it is, otherwise it returns
#         False.

#         Args:
#           index: The index of the item in the model that is being edited.
#           trigger: The trigger parameter is an event that causes the editor to be opened for editing the
#         cell. It can be one of the following values:
#           event: The event parameter in the edit() method is an instance of QEvent class. It represents
#         an event that occurred on the widget. The event parameter is used to determine the type of event
#         that occurred, such as a mouse click or a key press, and to handle the event accordingly.

#         Returns:
#           If the column index of the given index is in the list of editable_column_indexes, then the
#         super().edit() method is called and its return value is returned. Otherwise, False is returned.
#         """
#         if index.column() in self.editable_column_indexes:
#             return super(CustomTableWidget, self).edit(index, trigger, event)
#         else:
#             return False

#     def set_editable_column_index(self, columns: list[int]):
#         """
#         This function sets the indexes of columns that are editable in a table.

#         Args:
#           columns (list[int]): A list of integers representing the indexes of the columns that should be
#         editable in a table or spreadsheet.
#         """
#         self.editable_column_indexes = columns

#     def updateSectionWidth(self, logicalIndex, oldSize, newSize):
#         self.frozenTableView.setColumnWidth(0, newSize)
#         self.updateFrozenTableGeometry()

#     def updateSectionHeight(self, logicalIndex, oldSize, newSize):
#         self.frozenTableView.setRowHeight(logicalIndex, newSize)

#     def resizeEvent(self, event):
#         super(CustomTableWidget, self).resizeEvent(event)
#         self.updateFrozenTableGeometry()

#     def moveCursor(self, cursorAction, modifiers):
#         current = super(CustomTableWidget, self).moveCursor(cursorAction, modifiers)
#         if (
#             cursorAction == self.CursorAction.MoveLeft
#             and self.current.column() > 0
#             and self.visualRect(current).topLeft().x() < self.frozenTableView.columnWidth(0)
#         ):
#             newValue = self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() - self.frozenTableView.columnWidth(0)
#             self.horizontalScrollBar().setValue(newValue)
#         return current

#     def scrollTo(self, index, hint):
#         if index.column() > 0:
#             super(CustomTableWidget, self).scrollTo(index, hint)

#     def updateFrozenTableGeometry(self):
#         self.frozenTableView.setGeometry(
#             self.verticalHeader().width() + self.frameWidth(),
#             self.frameWidth(),
#             self.columnWidth(0),
#             self.viewport().height() + self.horizontalHeader().height(),
#         )

#     def removeCellWidget(self, row, column):
#         item = self.item(row, column)
#         if item and isinstance(item, QWidget):
#             widget = item.widget()
#             self.takeItem(row, column)
#             del widget

#     def setCellWidget(self, row, column, widget):
#         index = self.model().index(row, column)
#         self.setIndexWidget(index, widget)

#     def cellWidget(self, row, column):
#         index = self.model().index(row, column)
#         return self.indexWidget(index)

#     def setItem(self, row, column, item):
#         model = self.model()
#         model.setItem(row, column, item)

#     def item(self, row, column):
#         model = self.model()
#         return model.item(row, column) if model else None

#     def rowCount(self):
#         return self.model().rowCount()

#     def insertRow(self, row, items=None):
#         self.model().insertRow(row, items)

#     def removeRow(self, row):
#         self.model().removeRow(row - 1)

#     def eventFilter(self, obj, event):
#         if obj is self.viewport() and event.type() == QEvent.MouseButtonPress:
#             index = self.indexAt(event.pos())
#             if index.isValid():
#                 item = self.model().item(index.row(), index.column())
#                 if item:
#                     self.itemClicked.emit(item)
#         return super().eventFilter(obj, event)

#     def mousePressEvent(self, event):
#         index = self.indexAt(event.pos())
#         if index.isValid():
#             item = self.frozenTableView.model().item(index.row(), 0)
#             if item:
#                 self.itemClicked.emit(item)
#         return super().mousePressEvent(event)


class OrderStatusButton(QPushButton):
    def __init__(self, parent=None):
        """
        This function initializes a QPushButton with specific properties and sets its object name to
        "order_status".

        Args:
          parent: The parent widget of the QPushButton. If no parent is specified, the button will be a
        top-level window.
        """
        super(QPushButton, self).__init__(parent)
        self.setCheckable(True)
        self.setText("Order Pending")
        self.setFixedWidth(100)
        self.setObjectName("order_status")


class ItemCheckBox(QCheckBox):
    """This is a custom class that inherits from the QCheckBox class in PyQt and adds additional functionality for handling items."""

    def mousePressEvent(self, event):
        """
        This function checks if the pressed key is the Shift key and if so, calls the parent class's
        keyPressEvent method, otherwise it does nothing.

        :param event: The event parameter in this code refers to a key press event that is triggered
        when a key on the keyboard is pressed. It contains information about the key that was pressed,
        such as the key code and whether any modifier keys (such as Shift or Ctrl) were also pressed.
        The code checks if the
        """
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)


class ItemNameComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of items in the database"""

    def __init__(self, parent, selected_item: str, items: list[str], tool_tip: str):
        """
        It's a function that creates a dropdown menu with a list of items, and the selected item is the
        one that is displayed when the dropdown menu is first created

        Args:
          parent: The parent widget
          selected_item (str): The item that is selected by default
          items (list[str]): list[str] = ['item1', 'item2', 'item3']
          tool_tip (str): str = "This is the tool tip"
        """
        QComboBox.__init__(self, parent)
        self.addItems(items)
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.setEditable(True)
        self.wheelEvent = lambda event: None
        # self.setMinimumWidth(170)
        self.setMaximumWidth(350)


class PartNumberComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of part numbers in the database"""

    def __init__(self, parent, selected_item: str, items: list[str], tool_tip: str):
        """
        It's a function that creates a dropdown menu with a list of items, and the selected item is the
        one that is displayed when the dropdown menu is first created

        Args:
          parent: The parent widget
          selected_item (str): The item that is selected by default
          items (list[str]): list[str] = ['item1', 'item2', 'item3']
          tool_tip (str): str = "This is the tool tip"
        """
        QComboBox.__init__(self, parent)
        self.addItems(items)
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.setEditable(True)
        self.wheelEvent = lambda event: None
        self.setFixedWidth(120)


class PriorityComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of items in the database"""

    def __init__(self, parent, selected_item: int):
        """
        It's a function that creates a dropdown menu with a list of items, and the selected item is the
        one that is displayed when the dropdown menu is first created

        Args:
          parent: The parent widget
          selected_item (str): The item that is selected by default
          tool_tip (str): str = "This is the tool tip"
        """
        QComboBox.__init__(self, parent)
        self.addItems(["Default", "Low", "Medium", "High"])
        self.setCurrentIndex(selected_item)
        self.wheelEvent = lambda event: None
        # #self.setFixedWidth(60)


class ExchangeRateComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of items in the database"""

    def __init__(self, parent, selected_item: int):
        """
        The function takes in a parent, a selected item, and a tool tip. It then creates a QComboBox
        object, adds items to the combo box, sets the current text to the selected item, sets the tool
        tip to the tool tip, sets the wheel event to a lambda function that does nothing, and sets the
        fixed width to 40.

        Args:
          parent: The parent widget
          selected_item (int): The item that is selected when the combobox is created.
          tool_tip (str): The text that will be displayed when the user hovers over the combobox.
        """
        QComboBox.__init__(self, parent)
        self.addItems(["CAD", "USD"])
        self.setCurrentText(selected_item)
        self.wheelEvent = lambda event: None
        # #self.setFixedWidth(40)


class NotesPlainTextEdit(QPlainTextEdit):
    """It's a QPlainTextEdit that has a context menu with a "Copy" and "Paste" option"""

    def __init__(self, parent, text: str, tool_tip: str):
        """
        This function creates a QPlainTextEdit object with a minimum width of 100, a maximum width of
        200, a fixed height of 60, a plain text of text, and a tool tip of tool_tip

        Args:
          parent: The parent widget.
          text (str): The text that will be displayed in the text box.
          tool_tip (str): The text that will be displayed when the mouse hovers over the widget.
        """
        QPlainTextEdit.__init__(self, parent)
        self.setMinimumWidth(100)
        self.setObjectName("notes")
        self.setStyleSheet(
            "QPlainTextEdit:!focus#notes{background-color: rgba(32,32,32,130); border: none; border-radius: 0.001em; color: white;} QPlainTextEdit:focus#notes{background-color: rgba(32,32,32,130); border: none; border-radius: 0.001em; color: white;}"
        )
        self.setMaximumWidth(200)
        self.setFixedHeight(60)
        self.setPlainText(text)
        self.setToolTip(tool_tip)


class POPushButton(QPushButton):
    """This class is a subclass of QPushButton that has a signal that emits the button's text when
    the button is clicked"""

    def __init__(self, parent):
        """
        The function is called when the button is clicked

        Args:
          parent: The parent widget.
        """
        QPushButton.__init__(self, parent)
        # self.setFixedSize(36, 26)
        self.setText("PO")
        self.setToolTip("Open a new purchase order")


class DeletePushButton(QPushButton):
    """It creates a class called DeletePushButton that inherits from QPushButton."""

    def __init__(self, parent, tool_tip: str, icon: QIcon):
        """
        It creates a button with a trash icon

        Args:
          parent: The parent widget.
        """
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
    """It's a QPushButton that can display rich text"""

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
        """
        > Sets the text of the widget to the given text

        Args:
          text: The text to be displayed in the label.
        """
        set_status_button_stylesheet(button=self, color=color)
        if color == "lime":
            color = "#cef4d9"
        elif color == "yellow":
            color = "#ffffe0"
        elif color == "red":
            color = "lightpink"
        text = f'<p style="color:{color};">{text}</p>'
        self.__lbl.setText(text)
        self.updateGeometry()
        return

    def sizeHint(self) -> QSizePolicy:
        """
        The function returns a QSizePolicy object that is the size of the QLabel object

        Returns:
          The size of the button.
        """
        button_size = QPushButton.sizeHint(self)
        label_size = self.__lbl.sizeHint()
        button_size.setWidth(label_size.width())
        button_size.setHeight(label_size.height())
        return button_size


class HumbleDoubleSpinBox(QDoubleSpinBox):
    """It's a spin box that doesn't let you enter a value that's too close to zero."""

    def __init__(self, *args):
        """
        The function sets the focus policy of the spinbox to strong focus
        """
        super(HumbleDoubleSpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

    def focusInEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(HumbleDoubleSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(HumbleDoubleSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        If the spinbox has focus, then it will behave as normal. If it doesn't have focus, then the
        wheel event will be ignored

        Args:
          event: The event object

        Returns:
          The super class of the HumbleSpinBox class.
        """
        if self.hasFocus():
            return super(HumbleDoubleSpinBox, self).wheelEvent(event)
        else:
            event.ignore()


class HumbleSpinBox(QSpinBox):
    """It's a spin box that doesn't let you enter a value that's too close to zero."""

    def __init__(self, *args):
        """
        The function sets the focus policy of the spinbox to strong focus
        """
        super(HumbleSpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(60)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

    def focusInEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(HumbleSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(HumbleSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        If the spinbox has focus, then it will behave as normal. If it doesn't have focus, then the
        wheel event will be ignored

        Args:
          event: The event object

        Returns:
          The super class of the HumbleSpinBox class.
        """
        if self.hasFocus():
            return super(HumbleSpinBox, self).wheelEvent(event)
        else:
            event.ignore()


class CurrentQuantitySpinBox(QSpinBox):
    """It's a spin box that doesn't let you enter a value that's too close to zero."""

    def __init__(self, *args):
        """
        The function sets the focus policy of the spinbox to strong focus
        """
        super(CurrentQuantitySpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)
        self.lineEdit().setReadOnly(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def focusInEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        super(CurrentQuantitySpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        super(CurrentQuantitySpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        ignore all wheel events
        """
        event.ignore()


class HumbleComboBox(QComboBox):
    """> A QComboBox that can be set to a default value"""

    def __init__(self, scrollWidget=None, *args, **kwargs):
        """
        It sets the focus policy to strong focus.

        Args:
          scrollWidget: The widget that will be scrolled when the combobox is opened.
        """
        super(HumbleComboBox, self).__init__(*args, **kwargs)
        self.scrollWidget = scrollWidget
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        """
        If the combobox has focus, then the wheel event is handled by the combobox, otherwise the wheel
        event is handled by the scroll widget

        Returns:
          The return value is the return value of the last statement in the function.
        """
        if self.hasFocus():
            return QComboBox.wheelEvent(self, *args, **kwargs)
        else:
            return self.scrollWidget.wheelEvent(*args, **kwargs)


class PlaceholderTextComboBox(QComboBox):
    """This class is a subclass of QComboBox that allows the user to enter text into the combo box that is
    not in the list of items"""

    def paintEvent(self, event):
        """
        It draws the combobox frame, focusrect and selected etc

        Args:
          event: The event that triggered the paintEvent.
        """

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
    """It's a QTreeWidget that displays a list of files and folders"""

    def __init__(self, data):
        """
        It takes a value and creates a tree widget item for it.

        If the value is a dictionary, it creates a child item for each key and value pair.

        If the value is a list or tuple, it creates a child item for each value.

        If the value is anything else, it creates a child item with the value as its text.

        The function is recursive, so if the value is a dictionary or list, it calls itself to create
        the child items.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        Args:
          value: The value to be displayed in the tree.
        """
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
    """This class is a QScrollArea that has a header widget that is always visible"""

    def __init__(self, headers: dict[str:int], parent=None):
        """
        A QScrollArea with a QGridLayout inside of it. I'm then creating a QWidget with a
        QGridLayout inside of it and adding it to the QScrollArea. I'm then creating a QWidget with a
        QGridLayout inside of it and adding it to the QScrollArea.

        Args:
          headers (dict({str: int})): dict({str: int})
          parent: The parent widget.
        """
        QScrollArea.__init__(self, parent)
        self.headers: dict({str: int}) = headers

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
        """
        The function is called when the scroll area is resized. It resizes the headings widget to match
        the width of the scroll area and positions it at the top of the scroll area

        Args:
          event: QResizeEvent
        """
        rect = self.viewport().geometry()
        self.headings_widget.setGeometry(rect.x(), rect.y() - self.margins.top(), rect.width(), self.margins.top())
        QScrollArea.resizeEvent(self, event)


class DragableLayout(QWidget):
    """
    Generic list sorting handler.
    """

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
    """It's a delegate that can be used to display and edit data items from a model"""

    def sizeHint(self, option, index):
        """
        If the index is not a child of a parent, then set the height to 60

        Args:
          option: QStyleOptionViewItem
          index: The index of the item to be drawn.

        Returns:
          The size of the item.
        """
        item = super(StyledItemDelegate, self).sizeHint(option, index)
        if not index.parent().isValid():
            item.setHeight(60)
        return item


def set_default_dialog_button_stylesheet(button: QPushButton) -> None:
    """
    It sets the style sheet of the button

    Args:
        button (QPushButton): QPushButton
    """
    button.setStyleSheet(
        """
        QPushButton#default_dialog_button{
            background-color: #3daee9;
            border: 0.04em solid  #3daee9;
            border-radius: 8px;
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
            color: gray;
            border: 0.04em solid  gray;
            border-radius: 4px;
        }
        """
    )


def set_status_button_stylesheet(button: QPushButton, color: str) -> None:
    """
    It sets the style sheet of the button

    Args:
        button (QPushButton): QPushButton
    """
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
            border-radius: 5px;
            color: %(color)s;
        }
        QPushButton#status_button:hover{
            border: 0.04em solid  %(border_color)s;
            border-radius: 5px;
        }
        QPushButton#status_button:pressed{
            border: 0.15em solid  %(border_color)s;
            border-radius: 5px;
        }
        """
        % {"color": color, "border_color": border_color, "background_color": background_color}
    )
