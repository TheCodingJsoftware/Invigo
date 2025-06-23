import contextlib
import os
from datetime import datetime, timedelta
from functools import partial
from typing import Literal

from natsort import natsorted
from PyQt6.QtCore import (
    QDateTime,
    QEasingCurve,
    QEvent,
    QMimeData,
    QModelIndex,
    QPoint,
    QPropertyAnimation,
    QRegularExpression,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QCursor,
    QDrag,
    QDragEnterEvent,
    QDropEvent,
    QFileSystemModel,
    QFont,
    QIcon,
    QMouseEvent,
    QRegularExpressionValidator,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ui.icons import Icons
from ui.theme import theme_var
from utils.colors import get_contrast_text_color, lighten_color


class PreviousQuoteItem(QGroupBox):
    load_quote = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_quote = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget):
        super().__init__(parent)
        quote_name = file_info.get("name")
        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime(
            "%A, %B %d, %Y, %I:%M:%S %p"
        )

        self.setTitle(quote_name)

        modified = QLabel(f"Saved: {modified_date}")
        modified.setWordWrap(True)
        load_quote_button = QPushButton("Load Quote", self)
        load_quote_button.clicked.connect(self.load_quote.emit)
        load_quote_button.setToolTip(
            "Loads the selected quote into a new tab for detailed viewing and editing."
        )

        open_external = QPushButton(self)
        open_external.setObjectName("pushButton_open_in_browser")
        open_external.setStyleSheet(
            """
QPushButton#pushButton_open_in_browser:flat {
    background-color: transparent;
	border-color: transparent;
}
"""
        )
        open_external.setFlat(True)
        open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        open_external.setFixedSize(25, 25)
        open_external.setIcon(QIcon("icons/website.png"))
        open_external.clicked.connect(self.open_webpage.emit)
        open_external.setToolTip(
            "Will open up the printout in your default web browser."
        )

        delete_button = DeletePushButton(
            self,
            f"Permanently delete {quote_name}.\nThis action is irreversible.\nPlease exercise caution.",
        )
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
        self.setStyleSheet(f"QGroupBox{{border: 1px solid {theme_var('outline')};}}")


class SavedQuoteItem(QGroupBox):
    load_quote = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_quote = pyqtSignal()
    status_changed = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget):
        super().__init__(parent)
        quote_name = file_info.get("name")
        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime(
            "%A, %B %d, %Y, %I:%M:%S %p"
        )
        order_number = file_info.get("order_number")
        status = file_info.get("status")

        self.setTitle(quote_name)

        order_number = QLabel(f"Order #: {int(order_number)}", self)
        quote_status = QLabel("Status:", self)
        quote_status.setFixedWidth(50)

        self.status_combobox = QComboBox(self)
        self.status_combobox.addItems(
            ["In progress", "Need more info", "Quoted", "Confirmed"]
        )
        self.status_combobox.setCurrentText(status)
        self.status_combobox.currentTextChanged.connect(self.status_changed.emit)

        modified = QLabel(f"Modified: {modified_date}")
        modified.setWordWrap(True)

        load_quote_button = QPushButton("Load Quote", self)
        load_quote_button.clicked.connect(self.load_quote.emit)
        load_quote_button.setToolTip(
            "Loads the selected quote into a new tab for detailed viewing and editing."
        )

        open_external = QPushButton(self)
        open_external.setCursor(Qt.CursorShape.PointingHandCursor)
        open_external.setObjectName("pushButton_open_in_browser")
        open_external.setStyleSheet(
            """
QPushButton#pushButton_open_in_browser:flat {
    background-color: transparent;
	border-color: transparent;
}
"""
        )
        open_external.setFlat(True)
        open_external.setFixedSize(25, 25)
        open_external.setIcon(QIcon("icons/website.png"))
        open_external.clicked.connect(self.open_webpage.emit)
        open_external.setToolTip(
            "Will open up the printout in your default web browser."
        )

        delete_button = DeletePushButton(
            self,
            f"Permanently delete {quote_name}.\nThis action is irreversible.\nPlease exercise caution.",
        )
        delete_button.setFixedSize(25, 25)
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
        self.setStyleSheet(f"QGroupBox{{border: 1px solid {theme_var('outline')};}}")


class FilterButton(QPushButton):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setText(name)
        self.setCheckable(True)
        self.setFlat(True)


class ScrollPositionManager:
    def __init__(self):
        self.scroll_positions: dict[str, int] = {}

    def save_scroll_position(self, category: str, scroll: QTableWidget | QScrollArea):
        scroll_position = QPoint(
            scroll.horizontalScrollBar().value(), scroll.verticalScrollBar().value()
        )
        if not scroll_position.y():
            return
        self.scroll_positions[category] = scroll_position.y()

    def get_scroll_position(self, category: str) -> int:
        try:
            return self.scroll_positions[category]
        except KeyError:
            return


class MachineCutTimeSpinBox(QDoubleSpinBox):
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
        end_date_time = current_date_time.addDays(days).addSecs(
            hours * 3600 + minutes * 60
        )

        time_delta = (
            end_date_time.toSecsSinceEpoch() - current_date_time.toSecsSinceEpoch()
        )
        return timedelta(seconds=time_delta)


class AssemblyMultiToolBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets: list[QWidget] = []
        self.buttons: list[QPushButton] = []
        self.input_boxes: list[QLineEdit] = []
        self.colors: list[str] = []
        self.delete_buttons: list[DeletePushButton] = []
        self.duplicate_buttons: list[QPushButton] = []
        self.check_boxes: list[QCheckBox] = []
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(main_layout)

    def addItem(self, widget: QWidget, title: str, base_color: str = None):
        if not base_color:
            base_color = theme_var("primary")
        # Apply the drop shadow effect to the widget
        # checkbox = QCheckBox(widget)
        # checkbox.setStyleSheet("QCheckBox:indicator{width: 20px; height: 20px;}")
        # checkbox.setFixedWidth(22)
        hover_color: str = lighten_color(base_color)
        font_color = get_contrast_text_color(base_color)
        _widget = QWidget()
        _widget.setContentsMargins(0, 3, 0, 3)
        widget.setParent(_widget)
        drop_down_toggle_button = QPushButton()
        drop_down_toggle_button.setObjectName("drop_down_button")
        drop_down_toggle_button.setFixedWidth(34)
        drop_down_toggle_button.setText("🡇")
        drop_down_toggle_button.setFixedHeight(34)
        drop_down_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        drop_down_toggle_button.setChecked(False)
        drop_down_toggle_button.setCheckable(True)
        drop_down_toggle_button.setStyleSheet(
            f"""QPushButton:checked#drop_down_button {{
                    color: {theme_var("on-surface")};
                    background-color: {theme_var("surface")};
                    border: 1px solid {theme_var("outline")};
                    border-radius: 0px;
                    border-top-left-radius: {theme_var("border-radius")};
                    border-bottom-left-radius: {theme_var("border-radius")};
                }}
                QPushButton:checked:hover#drop_down_button {{
                    background-color: {theme_var("outline-variant")};
                }}

                QPushButton:checked:pressed#drop_down_button {{
                    background-color: {theme_var("surface")};
                }}
                QPushButton:!checked#drop_down_button {{
                    color: {font_color};
                    background-color: {base_color};
                    border: 1px solid {base_color};
                    border-radius: 0px;
                    border-top-left-radius: {theme_var("border-radius")};
                }}

                QPushButton:!checked:hover#drop_down_button {{
                    background-color: {hover_color};
                }}

                QPushButton:!checked:pressed#drop_down_button {{
                    background-color: {base_color};
                }}"""
        )

        input_box = QLineEdit(widget)
        input_box.setObjectName("input_box_multitoolbox")
        input_box.setText(title)
        input_box.setFixedHeight(34)
        input_box.setStyleSheet(
            f"""QLineEdit#input_box_multitoolbox{{
                    border: 1px solid {base_color};
                    border-radius: 0px;
                    background-color: {base_color};
                    color: {font_color};
                }}
                QLineEdit:hover#input_box_multitoolbox{{
                    border-radius: 0px;
                    border: 1px solid {hover_color};
                    background-color: {hover_color};
                    color: {font_color};
                }}
                QLineEdit:focus#input_box_multitoolbox{{
                    border: 1px solid {hover_color};
                    background-color: {hover_color};
                }}"""
        )

        delete_button = DeletePushButton(
            parent=widget,
            tool_tip=f"Delete {title} forever",
        )
        delete_button.setStyleSheet(
            f"border-radius: 0px; border-top-right-radius: {theme_var('border-radius')};"
        )
        delete_button.setFixedWidth(33)
        delete_button.setFixedHeight(34)
        drop_down_toggle_button.clicked.connect(
            partial(
                self.toggle_style_sheet,
                drop_down_toggle_button,
                widget,
                input_box,
                delete_button,
                base_color,
                hover_color,
                font_color,
            )
        )

        duplicate_button = QPushButton()
        duplicate_button.setFlat(True)
        duplicate_button.setFixedHeight(34)
        duplicate_button.setStyleSheet("border-radius: 0px;")
        duplicate_button.setIcon(Icons.copy_icon)
        duplicate_button.setFixedWidth(35)
        duplicate_button.setToolTip(f"Duplicate {title}")

        # widget.setMinimumHeight(100)

        hlaout = QHBoxLayout()
        hlaout.setSpacing(0)
        hlaout.setContentsMargins(0, 0, 0, 0)
        # hlaout.addWidget(checkbox)
        hlaout.addWidget(drop_down_toggle_button)
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
            f"""
            QWidget#edit_multi_tool_box_widget {{
            border: 1px solid {base_color};
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            border-top-right-radius: 0px;
            border-top-left-radius: 0px;
            background-color: {theme_var("surface")};
        }}"""
        )
        self.buttons.append(drop_down_toggle_button)
        self.delete_buttons.append(delete_button)
        self.input_boxes.append(input_box)
        self.widgets.append(widget)
        self.colors.append(base_color)
        self.duplicate_buttons.append(duplicate_button)
        # self.check_boxes.append(checkbox)
        # drop_down_toggle_button.click()

        self.layout().addWidget(_widget)

    def toggle_style_sheet(
        self,
        button: QPushButton,
        widget: QWidget,
        input_box: QLineEdit,
        delete_button: QPushButton,
        base_color: str,
        hover_color: str,
        font_color: str,
    ):
        self.toggle_widget_visibility(widget)
        button.setText("🡇" if widget.isVisible() else "🡆")
        if widget.isVisible():
            input_box.setStyleSheet(
                f"""QLineEdit#input_box_multitoolbox{{
                        border: 1px solid {base_color};
                        border-radius: 0px;
                        background-color: {base_color};
                        color: {font_color};
                    }}
                    QLineEdit:hover#input_box_multitoolbox{{
                        border-radius: 0px;
                        border: 1px solid {hover_color};
                        background-color: {hover_color};
                        color: {font_color};
                    }}
                    QLineEdit:focus#input_box_multitoolbox{{
                        border: 1px solid {hover_color};
                        background-color: {hover_color};
                    }}"""
            )
            delete_button.setStyleSheet(
                f"border-radius: 0px; border-top-right-radius: {theme_var('border-radius')};"
            )
        else:
            input_box.setStyleSheet(
                f"""QLineEdit#input_box_multitoolbox{{
                        border-radius: 0px;
                        border: 1px solid {theme_var("outline")};
                        border-right-color: {theme_var("surface")};
                        border-left-color: {theme_var("surface")};
                        margin-left: -1px;
                        margin-right: -1px;
                        background-color: {theme_var("surface")};
                        color: {theme_var("on-surface")}
                    }}
                    QLineEdit:hover#input_box_multitoolbox{{
                        background-color: {theme_var("outline-variant")};
                        color: {theme_var("on-surface")}
                    }}
                    QLineEdit:focus#input_box_multitoolbox{{
                        background-color: {theme_var("outline-variant")};
                        color: {theme_var("on-surface")}
                    }}"""
            )
            delete_button.setStyleSheet(
                f"border-radius: 0px; border-top-right-radius: {theme_var('border-radius')}; border-bottom-right-radius: {theme_var('border-radius')};"
            )

    def removeItem(self, widget_to_delete: QWidget):
        main_layout = self.layout()  # Get the reference to the main layout
        for i in range(main_layout.count()):
            layout_item = main_layout.itemAt(i)
            widget = (
                layout_item.widget().layout().itemAt(1).widget()
            )  # This is what were trying to find
            # layout = widget.layout()
            if (
                widget == widget_to_delete
            ):  # Check if the layout's widget matches the given widget
                self.delete_buttons[i].disconnect()
                self.buttons[i].disconnect()
                self.buttons.pop(i)
                self.delete_buttons.pop(i)
                self.duplicate_buttons.pop(i)
                self.input_boxes.pop(i)
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
        return self.input_boxes[index]

    def getLastInputBox(self) -> QLineEdit:
        return self.input_boxes[-1]

    def getLastToggleButton(self) -> QPushButton:
        return self.buttons[-1]

    def openLastToolBox(self):
        self.buttons[-1].setText("🡇")
        self.buttons[-1].setChecked(False)
        self.widgets[-1].setVisible(True)

    def closeLastToolBox(self):
        self.buttons[-1].setText("🡆")
        self.buttons[-1].setChecked(True)
        self.widgets[-1].setHidden(True)
        self.input_boxes[-1].setStyleSheet(
            f"""QLineEdit#input_box_multitoolbox{{
                        border-radius: 0px;
                        border: 1px solid {theme_var("outline")};
                        border-right-color: {theme_var("surface")};
                        border-left-color: {theme_var("surface")};
                        margin-left: -1px;
                        margin-right: -1px;
                        background-color: {theme_var("surface")};
                        color: {theme_var("on-surface")}
                    }}
                    QLineEdit:hover#input_box_multitoolbox{{
                        background-color: {theme_var("outline-variant")};
                        color: {theme_var("on-surface")}
                    }}
                    QLineEdit:focus#input_box_multitoolbox{{
                        background-color: {theme_var("outline-variant")};
                        color: {theme_var("on-surface")}
                    }}"""
        )
        self.delete_buttons[-1].setStyleSheet(
            f"border-radius: 0px; border-top-right-radius: {theme_var('border-radius')}; border-bottom-right-radius: {theme_var('border-radius')};"
        )

    def setItemText(self, index: int, new_name: str):
        if 0 <= index < len(self.input_boxes):
            self.input_boxes[index].setText(new_name)

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

    def clear_layout(self, layout):
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


class MultiToolBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widgets: list[QWidget] = []
        self.widget_visibility: dict[int, bool] = {}
        self.buttons: list[QPushButton] = []
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.main_layout)

    def clear(self):
        self.widgets.clear()
        self.buttons.clear()
        self.widget_visibility.clear()
        self.clear_layout(self.main_layout)

    def addItem(self, widget: QWidget, title: str, base_color: str = None, icon=None):
        if not base_color:
            base_color = theme_var("primary")

        hover_color = lighten_color(base_color)
        font_color = get_contrast_text_color(base_color)

        _widget = QWidget(self)
        _widget.setContentsMargins(0, 3, 0, 3)
        # _widget.setParent(widget)
        button = QPushButton(_widget)
        button.setFixedHeight(30)
        button.setObjectName("multi_tool_box_button")
        button.setStyleSheet(
            f"""QPushButton#multi_tool_box_button {{
                    border: 1px solid {theme_var("surface")};
                    background-color: {theme_var("surface")};
                    border-radius: {theme_var("border-radius")};
                    text-align: left;
                }}
                /* CLOSED */
                QPushButton:checked#multi_tool_box_button {{
                    color: {base_color};
                    border: 1px solid {theme_var("outline")};
                }}

                QPushButton:checked:hover#multi_tool_box_button {{
                    background-color: {theme_var("outline-variant")};
                }}
                QPushButton:checked:pressed#multi_tool_box_button {{
                    background-color: {theme_var("surface")};
                }}
                /* OPENED */
                QPushButton:!checked#multi_tool_box_button {{
                    color: {font_color};
                    border-color: {base_color};
                    background-color: {base_color};
                    border-top-left-radius: {theme_var("border-radius")};
                    border-top-right-radius: {theme_var("border-radius")};
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}

                QPushButton:!checked:hover#multi_tool_box_button {{
                    background-color: {hover_color};
                }}

                QPushButton:!checked:pressed#multi_tool_box_button {{
                    background-color: {base_color};
                }}"""
        )
        button.setText(title)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setChecked(True)
        button.setCheckable(True)
        if icon:
            button.setIcon(icon)
        button.clicked.connect(partial(self.toggle_widget_visibility, widget))

        widget.setVisible(False)

        layout = QVBoxLayout(_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button)
        layout.addWidget(widget)
        _widget.setLayout(layout)
        widget.setObjectName("nest_widget")
        widget.setStyleSheet(
            f"""
            QWidget#nest_widget{{
                border: 1px solid {base_color};
                background-color: {theme_var("surface")};
            }}
            QPushButton#load_job{{
                color: {font_color};
                background-color: {base_color};
                border-color: {base_color};
            }}
            QPushButton#load_job:hover{{
                background-color: {hover_color};
                border-color: {hover_color};
            }}
            QPushButton#load_job:pressed{{
                background-color: {base_color};
                border-color: {base_color};
            }}
            QComboBox:hover{{
                border-color: {base_color};
            }}
            QComboBox:focus{{
                border-color: {base_color};
            }}"""
        )

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

    def getLastButton(self) -> QPushButton:
        return self.buttons[-1]

    def count(self) -> int:
        return len(self.widgets)

    def get_widget_visibility(self) -> dict[int, bool]:
        return {i: widget.isVisible() for i, widget in enumerate(self.widgets)}

    def set_widgets_visibility(self, widgets_visibility: dict[int, bool]):
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

    def close(self, index: int) -> QWidget:
        if 0 <= index < len(self.buttons):
            self.buttons[index].click()
            self.buttons[index].setChecked(True)
            self.widgets[index].setVisible(False)

    def close_all(self):
        for button, widget in zip(self.buttons, self.widgets):
            button.click()
            button.click()
            button.setChecked(True)
            widget.setVisible(False)

    def open_all(self):
        for button, widget in zip(self.buttons, self.widgets):
            button.click()
            button.click()
            button.setChecked(False)
            widget.setVisible(True)

    def clear_layout(self, layout: QVBoxLayout | QWidget):
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
    dropped = pyqtSignal(object, object)

    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setAcceptDrops(True)  # Add this line
        self.setObjectName("custom_tab_button")
        self.drag_start_pos = None
        self.drag_timer = QTimer(self)
        self.drag_timer.setSingleShot(True)
        self.drag_timer.timeout.connect(self.initiateDrag)
        self.drag_threshold = 350  # milliseconds
        self.move_threshold = 20  # pixels
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e: QMouseEvent):
        super().mousePressEvent(e)
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = e.position().toPoint()
            self.drag_timer.start(self.drag_threshold)

    def mouseMoveEvent(self, e: QMouseEvent):
        super().mouseMoveEvent(e)
        if e.buttons() == Qt.MouseButton.LeftButton and self.drag_start_pos is not None:
            if (
                e.position().toPoint() - self.drag_start_pos
            ).manhattanLength() > self.move_threshold:
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
        drag.setHotSpot(
            self.drag_start_pos - QPoint(pixmap.width() // 2, pixmap.height() // 2)
        )
        drag.exec(Qt.DropAction.MoveAction)
        self.dropped.emit(self, QCursor.pos())


class MainTabButton(TabButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = QFont("Segoe UI", 12, QFont.Weight.Bold, False)
        self.setFont(font)


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

        self.corner_widget = QWidget(self)
        layout = QHBoxLayout(self.corner_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 6)
        add_category = QPushButton(self)
        add_category.setFlat(True)
        add_category.setObjectName("add_category")
        add_category.setIcon(Icons.plus_icon)
        add_category.setStyleSheet(
            "QPushButton#add_category{border-top-left-radius: 12px; border-bottom-left-radius: 12px; border-bottom-right-radius: 0px; border-top-right-radius: 0px;}"
        )
        add_category.clicked.connect(self.addCategory.emit)
        remove_category = QPushButton(self)
        remove_category.setFlat(True)
        remove_category.setObjectName("remove_category")
        remove_category.setIcon(Icons.minus_icon)
        remove_category.setStyleSheet(
            "QPushButton#remove_category{border-top-right-radius: 12px; border-bottom-right-radius: 12px; border-bottom-left-radius: 0px; border-top-left-radius: 0px;}"
        )
        remove_category.clicked.connect(self.removeCategory.emit)
        layout.addWidget(add_category)
        layout.addWidget(remove_category)

        self.setCornerWidget(self.corner_widget)

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
        return next(
            (i for i, button in enumerate(self.buttons) if button.isChecked()), 0
        )

    def setCurrentIndex(self, index: int):
        try:
            self.buttons[index].click()
        except IndexError:
            self.setCurrentIndex(index - 1)

    def currentTabText(self) -> str:
        return next(
            (button.text() for button in self.buttons if button.isChecked()), None
        )

    def currentTab(self) -> TabButton:
        return next((button for button in self.buttons if button.isChecked()), None)

    def clear_signals(self):
        self.currentChanged.disconnect()
        self.tabBarDoubleClicked.disconnect()
        self.addCategory.disconnect()
        self.removeCategory.disconnect()
        self.tabOrderChanged.disconnect()

    def clear(self):
        with contextlib.suppress(TypeError):  # Because it just initialized
            self.clear_signals()
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
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
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
        try:
            return self.buttons[index].text()
        except IndexError:
            return None

    def count(self) -> int:
        return len(self.buttons)

    def dropEvent(self, event: QDropEvent):
        position: QPoint = event.position().toPoint()
        button = event.source()
        if button in self.buttons:
            original_index = self.buttons.index(button)
            for i, btn in enumerate(self.buttons):
                if btn != button and btn.geometry().contains(position):
                    self.buttons.insert(i, self.buttons.pop(original_index))
                    self.stacked_widget.insertWidget(
                        i, self.stacked_widget.widget(original_index)
                    )
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
            self.rows[i // self.tabs_per_row].addWidget(
                button, alignment=Qt.AlignmentFlag.AlignBottom
            )
        self.stacked_widget.setCurrentIndex(self.currentIndex())
        self.tabOrderChanged.emit()

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())


class ButtonManagerWidget(QWidget):
    """Use in main menu for main tabs"""

    tabOrderChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.layout: QHBoxLayout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setAcceptDrops(True)

    def addButton(self, button: MainTabButton):
        self.layout.addWidget(button)
        self.buttons.append(button)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.accept()

    def dropEvent(self, event: QDropEvent):
        position = event.position().toPoint()
        button = event.source()
        if button in self.buttons:
            original_index = self.buttons.index(button)
            for i, btn in enumerate(self.buttons):
                if btn != button and btn.geometry().contains(position):
                    self.buttons.insert(i, self.buttons.pop(original_index))
                    break
            self.rearrange_buttons()
        event.accept()

    def rearrange_buttons(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        for button in self.buttons:
            self.layout.addWidget(button)
        self.tabOrderChanged.emit()


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
        return any(
            any(file.lower().endswith(".pdf") for file in files)
            for root, dirs, files in os.walk(directory)
        )

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        left_index = left.sibling(left.row(), 0)
        right_index = right.sibling(right.row(), 0)
        left_is_folder = self.sourceModel().isDir(left_index)
        right_is_folder = self.sourceModel().isDir(right_index)

        if (
            left_is_folder
            and not right_is_folder
            or not left_is_folder
            and right_is_folder
        ):
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
        self.selected_items = [
            index.data() for index in self.selected_indexes if ".pdf" in index.data()
        ]
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
        self.setFixedWidth(100)
        self.setFlat(True)
        self.setText("No Recut")
        self.clicked.connect(self.toggle_state)

    def set_to_recut(self):
        self.setChecked(True)
        self.setText("Recut")

    def set_to_no_recut(self):
        self.setChecked(False)
        self.setText("No Recut")

    def toggle_state(self):
        if self.isChecked():
            self.setText("Recut")
        else:
            self.setText("No Recut")


class CustomTableWidget(QTableWidget):
    rowChanged = pyqtSignal(int)  # Custom signal that takes a row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editable_column_indexes = []
        self.setStyleSheet("QScrollBar:horizontal {height: 20px;}")

        self.changed_rows = set()
        self.row_change_timer = QTimer()
        self.row_change_timer.setSingleShot(True)
        self.row_change_timer.timeout.connect(self.handle_row_change)

        self.cellChanged.connect(self.table_changed)

    def table_changed(self, row, column):
        self.changed_rows.add(row)
        self.row_change_timer.start(100)  # Adjust the delay as needed

    def handle_row_change(self):
        changed_rows_copy = self.changed_rows.copy()  # Make a copy of the set
        for row in changed_rows_copy:
            if not self.signalsBlocked():
                self.rowChanged.emit(row)
        self.changed_rows.clear()

    def edit(self, index, trigger, event):
        if index.column() in self.editable_column_indexes:
            return super().edit(index, trigger, event)
        else:
            return False

    def set_editable_column_index(self, columns: list[int]):
        self.editable_column_indexes = columns


class OrderStatusButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setText("Order Pending")
        self.setFixedWidth(150)
        self.setObjectName("order_status")


class PriorityComboBox(QComboBox):
    def __init__(self, parent, selected_item: int):
        super().__init__(parent)
        self.addItems(["Default", "Low", "Medium", "High"])
        self.setCurrentIndex(selected_item)
        self.setFixedWidth(120)

    def wheelEvent(self, event):
        # Do nothing, or comment this out to disable wheel scrolling
        event.ignore()


class ExchangeRateComboBox(QComboBox):
    def __init__(self, parent, selected_item: int):
        super().__init__(parent)
        self.addItems(["CAD", "USD"])
        self.setCurrentText(selected_item)
        # #self.setFixedWidth(40)

    def wheelEvent(self, event):
        # Do nothing, or comment this out to disable wheel scrolling
        event.ignore()


class NotesPlainTextEdit(QPlainTextEdit):
    def __init__(self, parent, text: str, tool_tip: str):
        super().__init__(parent)
        self.setMinimumWidth(100)
        self.setObjectName("notes")
        self.setStyleSheet("QPlainTextEdit#notes{border-radius: 0px;}")
        self.setMaximumWidth(200)
        self.setFixedHeight(60)
        self.setPlainText(text)
        self.setToolTip(tool_tip)


class POPushButton(QPushButton):
    def __init__(self, parent):
        QPushButton.__init__(self, parent)
        self.setText("PO")
        self.setToolTip("Open a new purchase order")


class DeletePushButton(QPushButton):
    def __init__(self, parent, tool_tip: str):
        QPushButton.__init__(self, parent)
        self.setObjectName("delete_button")
        self.setIcon(Icons.delete_icon)
        self.setToolTip(tool_tip)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # Signal emitted when the label is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setWordWrap(True)

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the clicked signal


class ClickableRichTextLabel(QLabel):
    clicked = pyqtSignal()  # Signal emitted when the label is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the clicked signal


class RichTextPushButton(QPushButton):
    def __init__(self, parent=None, text=None):
        super().__init__(parent)
        self.__lbl = QLabel(self)
        if text is not None:
            self.__lbl.setText(text)
        self.__layout = QHBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(0)
        self.setLayout(self.__layout)
        self.__lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.__lbl.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.__lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.__lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.__lbl.setTextFormat(Qt.TextFormat.RichText)
        self.__layout.addWidget(self.__lbl)
        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(
            self.make_transparent
        )  # Make the button transparent when the timer times out

        # Initialize colors and animations
        self._bg_color = QColor(theme_var("surface"))
        self._text_color = QColor(theme_var("surface"))
        self._border_color = QColor(theme_var("surface"))
        self.bg_animation = QPropertyAnimation(self, b"bgColor")
        self.bg_animation.setDuration(300)
        self.bg_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.text_animation = QPropertyAnimation(self, b"textColor")
        self.text_animation.setDuration(300)
        self.text_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.border_animation = QPropertyAnimation(self, b"borderColor")
        self.border_animation.setDuration(300)
        self.border_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    @pyqtProperty(QColor)
    def bgColor(self):
        return self._bg_color

    @bgColor.setter
    def bgColor(self, color):
        self._bg_color = color
        self.update_stylesheet()

    @pyqtProperty(QColor)
    def textColor(self):
        return self._text_color

    @textColor.setter
    def textColor(self, color):
        self._text_color = color
        self.update_stylesheet()

    @pyqtProperty(QColor)
    def borderColor(self):
        return self._border_color

    @borderColor.setter
    def borderColor(self, color):
        self._border_color = color
        self.update_stylesheet()

    def setText(self, text: str, color: Literal["lime", "yellow", "red", "green"]):
        if color == "lime" or color == "green":
            text_color = QColor(theme_var("on-primary-green"))
            background_color = QColor(theme_var("primary-green"))
            border_color = QColor(theme_var("on-primary-green"))
        elif color == "yellow":
            text_color = QColor(theme_var("on-primary-yellow"))
            background_color = QColor(theme_var("primary-yellow"))
            border_color = QColor(theme_var("on-primary-yellow"))
        elif color == "red":
            text_color = QColor(theme_var("on-error"))
            background_color = QColor(theme_var("primary-red"))
            border_color = QColor(theme_var("on-primary-red"))
        else:
            text_color = QColor(theme_var("on-primary"))
            background_color = QColor(theme_var("primary"))
            border_color = QColor(theme_var("on-primary"))

        self.text_animation.setStartValue(self._text_color)
        self.text_animation.setEndValue(text_color)
        self.text_animation.start()

        self.bg_animation.setStartValue(self._bg_color)
        self.bg_animation.setEndValue(background_color)
        self.bg_animation.start()

        self.border_animation.setStartValue(self._border_color)
        self.border_animation.setEndValue(border_color)
        self.border_animation.start()

        self.__lbl.setText(f"{text} - {datetime.now().strftime('%r')}")
        self.__timer.start(3000)

    def make_transparent(self):
        transparent_color = QColor(theme_var("surface"))
        self.bg_animation.setStartValue(self._bg_color)
        self.bg_animation.setEndValue(transparent_color)
        self.bg_animation.start()

        self.text_animation.setStartValue(self._text_color)
        self.text_animation.setEndValue(transparent_color)
        self.text_animation.start()

        self.border_animation.setStartValue(self._border_color)
        self.border_animation.setEndValue(transparent_color)
        self.border_animation.start()

    def update_stylesheet(self):
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self._bg_color.name()};
                color: {self._text_color.name()};
                border: 0.04em solid {self._border_color.name()};
                border-radius: 0px;
            }}
            QLabel {{
                background-color: {self._bg_color.name()};
                color: {self._text_color.name()};
                border: 0.04em solid {self._border_color.name()};
                border-radius: 0px;
            }}
            QPushButton:flat {{
                border: none;
                border-radius: 0px;
            }}
            """
        )

    def sizeHint(self) -> QSizePolicy:
        button_size = QPushButton.sizeHint(self)
        label_size = self.__lbl.sizeHint()
        button_size.setWidth(label_size.width())
        button_size.setHeight(label_size.height())
        return button_size


class HumbleDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

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
