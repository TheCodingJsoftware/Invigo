import contextlib
import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QEvent, QFile, QObject, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QRadioButton, QVBoxLayout,
                             QWidget)

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

workspace_tags = JsonFile(file_name="data/workspace_settings")


class ButtonFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            event.ignore()
            return True

        return super().eventFilter(obj, event)


class EditStatusesDialog(QDialog):
    def __init__(
        self,
        parent=None,
    ) -> None:
        super(EditStatusesDialog, self).__init__(parent)
        uic.loadUi("ui/edit_statuses_dialog.ui", self)
        self.parent = parent

        self.icon_name = Icons.information
        self.title = "Edit Statuses"
        self.message = "Add/Remove statuses for each flow tag as well as determining when the item moves forward in its flow stage"
        self.inputText: str = ""
        self.theme: str = "dark"
        self.tag_boxes: list[QComboBox] = []

        self.setWindowIcon(QIcon("icons/icon.png"))

        self.setWindowTitle(self.title)
        self.lblMessage.setText(self.message)

        svg_icon = self.get_icon(self.icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.load_theme()

        self.load_done: bool = False
        workspace_tags.load_data()
        if not workspace_tags.get_data()["flow_tag_statuses"]:
            workspace_tags.add_item("flow_tag_statuses", {})
            for tag in workspace_tags.get_value("all_tags"):
                workspace_tags.add_item_in_object("flow_tag_statuses", tag)
        self.comboBox_current_status.addItems(workspace_tags.get_value("all_tags"))
        self.comboBox_current_status.currentTextChanged.connect(self.load_statuses)
        button_filter = ButtonFilter()
        self.pushButton_add_status.clicked.connect(self.add_new_status)
        self.pushButton_add_status.installEventFilter(button_filter)
        self.load_statuses()

    def add_new_status(self) -> None:
        workspace_tags.load_data()
        data = workspace_tags.get_data()
        data["flow_tag_statuses"][self.comboBox_current_status.currentText()]["enter status name"] = {"completed": False}
        workspace_tags.save_data(data)
        self.load_statuses()

    def delete_status(self, status_line_edit: QLineEdit) -> None:
        workspace_tags.load_data()
        data = workspace_tags.get_data()
        del data["flow_tag_statuses"][self.comboBox_current_status.currentText()][status_line_edit.text()]
        workspace_tags.save_data(data)
        self.load_statuses()

    def status_name_change(self, old_name: str, status_line_edit: QLineEdit) -> None:
        workspace_tags.load_data()
        status_line_edit.disconnect()
        data = workspace_tags.get_data()
        data["flow_tag_statuses"][self.comboBox_current_status.currentText()][status_line_edit.text()] = data["flow_tag_statuses"][self.comboBox_current_status.currentText()][old_name]
        del data["flow_tag_statuses"][self.comboBox_current_status.currentText()][old_name]
        workspace_tags.save_data(data)
        status_line_edit.textChanged.connect(partial(self.status_name_change, status_line_edit.text(), status_line_edit))

    def status_is_complete_change(self, status_line_edit: QLineEdit, rad: QRadioButton) -> None:
        workspace_tags.load_data()
        data = workspace_tags.get_data()
        data["flow_tag_statuses"][self.comboBox_current_status.currentText()][status_line_edit.text()]["completed"] = rad.isChecked()
        workspace_tags.save_data(data)

    def load_statuses(self) -> None:
        workspace_tags.load_data()
        # tag_layout
        self.clear_layout(self.tag_layout)
        status_layout = QVBoxLayout()
        rad_layout = QVBoxLayout()
        delete_layout = QVBoxLayout()
        for status_name in workspace_tags.get_data()["flow_tag_statuses"][self.comboBox_current_status.currentText()]:
            button_filter = ButtonFilter()
            status_line_edit = QLineEdit(self)
            status_line_edit.setText(status_name)
            status_line_edit.textChanged.connect(partial(self.status_name_change, status_name, status_line_edit))
            status_layout.addWidget(status_line_edit)
            rad = QRadioButton(self)
            rad.setText("Moves Tag Forward")
            rad.setChecked(workspace_tags.get_data()["flow_tag_statuses"][self.comboBox_current_status.currentText()][status_name]["completed"])
            rad.toggled.connect(partial(self.status_is_complete_change, status_line_edit, rad))
            rad_layout.addWidget(rad)
            delete_button = QPushButton("DEL", self)
            delete_button.clicked.connect(partial(self.delete_status, status_line_edit))
            delete_button.installEventFilter(button_filter)
            delete_layout.addWidget(delete_button)
        self.tag_layout.addLayout(status_layout)
        self.tag_layout.addLayout(rad_layout)
        self.tag_layout.addLayout(delete_layout)

    def load_theme(self) -> None:
        set_theme(self, theme="dark")

    def get_icon(self, path_to_icon: str) -> QSvgWidget:
        return QSvgWidget(f"icons/{path_to_icon}")

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

    def keyPressEvent(self, event):
        event.ignore()
