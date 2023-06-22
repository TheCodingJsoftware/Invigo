import contextlib
import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QEvent, QFile, QObject, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme import set_theme
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

workspace_tags = JsonFile(file_name="data/workspace_settings")


class ButtonFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
            return True

        return super().eventFilter(obj, event)


class EditTagsDialog(QDialog):
    """
    Select dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.information,
        title: str = __name__,
        message: str = "",
        options: list = None,
    ) -> None:
        """
        It's a function that takes in a list of options and displays them in a list widget

        Args:
          parent: The parent widget of the dialog.
          icon_name (str): str = Icons.question,
          button_names (str): str = DialogButtons.ok_cancel,
          title (str): str = __name__,
          message (str): str = "",
          options (list): list = None,
        """
        super(EditTagsDialog, self).__init__(parent)
        uic.loadUi("ui/edit_tags_dialog.ui", self)
        self.parent = parent
        self.showMaximized()

        self.icon_name = icon_name
        self.title = title
        self.message = message
        self.inputText: str = ""
        self.theme: str = "dark"
        self.tag_boxes: dict[QWidget, QComboBox] = {}
        self.check_boxes: dict[QCheckBox, QComboBox] = {}

        self.setWindowIcon(QIcon("icons/icon.png"))

        self.setWindowTitle(self.title)
        self.lblMessage.setText(self.message)

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.load_theme()

        self.pushButton_create_flow_tag.clicked.connect(self.create_flow_tag)

        self.load_done: bool = False

        if len(workspace_tags.get_value("flow_tags")) != 0:
            self.load_flow_tags()
        else:
            self.load_done = True
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

    def load_flow_tags(self) -> None:
        for flow_tag in workspace_tags.get_value("flow_tags"):
            widget, layout, button = self.create_flow_tag_layout(flow_tag[0])
            self.flow_tag_layout.addWidget(widget)
            for tag in flow_tag[1:]:
                button.setHidden(True)
                tagbox = self.get_tag_box(tag)
                try:
                    timer_check_box = self.get_timer_check_box(tagbox, workspace_tags.get_value("is_timer_enabled")[tag])
                except (KeyError, TypeError, AttributeError):
                    timer_check_box = self.get_timer_check_box(tagbox, False)
                lbl = QLabel("➜", self)
                lbl.setFixedWidth(20)
                v_widget = QWidget()
                v_layout = QVBoxLayout(v_widget)
                v_layout.addWidget(tagbox)
                v_layout.addWidget(timer_check_box)
                v_widget.setLayout(v_layout)
                layout.addWidget(lbl)
                layout.addWidget(v_widget)
            add = QPushButton("Add", self)
            add.setFixedWidth(30)
            add.clicked.connect(partial(self.add_flow_tag, layout, add))
            add.clicked.connect(self.save_flow_tags)
            layout.addWidget(add)
        self.load_done = True

    def get_all_flow_tags(self) -> list[str]:
        """
        This function returns a list of all flow tags in the workspace.

        Returns:
          A list of strings containing all flow tags.
        """
        return workspace_tags.get_value("all_tags")

    def save_flow_tags(self) -> None:
        """
        This function saves flow tags and all tags in a workspace.

        Returns:
          None is being returned.
        """
        if not self.load_done:
            return
        workspace_tags.load_data()
        all_flow_tags = set()
        flow_tags = []
        self.tag_boxes.clear()
        self.check_boxes.clear()
        last_tag_box = None
        for i in range(self.flow_tag_layout.count()):
            item = self.flow_tag_layout.itemAt(i)
            if item.widget() is not None:
                widget = item.widget()
                if isinstance(widget, QWidget):
                    tags = []
                    self.tag_boxes[widget] = []
                    for j in range(widget.layout().count()):
                        _widget = widget.layout().itemAt(j).widget()
                        if isinstance(_widget.layout(), QVBoxLayout):
                            for k in range(_widget.layout().count()):
                                child_widget = _widget.layout().itemAt(k).widget()
                                if isinstance(child_widget, QComboBox):
                                    tag_name = child_widget.currentText()
                                    self.tag_boxes[widget].append(child_widget)
                                if isinstance(child_widget, QComboBox) and tag_name != "None":
                                    tags.append(tag_name)
                                    all_flow_tags.add(tag_name)
                                    last_tag_box = child_widget
                                if isinstance(child_widget, QCheckBox):
                                    self.check_boxes[child_widget] = last_tag_box
                    if len(tags) > 1:
                        flow_tags.append(tags)
        for flow_tag_widget in self.tag_boxes:
            used_tags = []
            for tag_box in self.tag_boxes[flow_tag_widget]:
                current_text = tag_box.currentText()
                tag_box.disconnect()
                tag_box.clear()
                _list = list(all_flow_tags)
                for tag_to_remove in used_tags:
                    with contextlib.suppress(ValueError):
                        _list.remove(tag_to_remove)
                tag_box.addItems(_list)
                tag_box.setCurrentText(current_text)
                tag_box.editTextChanged.connect(self.save_flow_tags)
                used_tags.append(current_text)
        workspace_tags.add_item("flow_tags", flow_tags)
        for check_box, tag_box in self.check_boxes.items():
            check_box.disconnect()
            with contextlib.suppress(KeyError, TypeError, AttributeError):
                check_box.setChecked(workspace_tags.get_value("is_timer_enabled")[tag_box.currentText()])
            check_box.toggled.connect(partial(self.update_timer_enabled, tag_box, check_box))
        workspace_tags.add_item("all_tags", list(all_flow_tags))
        data = workspace_tags.get_data()

        # Initialize flow_tag_statuses and is_timer_enabled for new tags
        for tag in all_flow_tags:
            data.setdefault("flow_tag_statuses", {}).setdefault(tag, {})
            data.setdefault("is_timer_enabled", {}).setdefault(tag, False)

        # Remove flow_tag_statuses and is_timer_enabled for tags not in all_flow_tags
        data["flow_tag_statuses"] = {tag: data["flow_tag_statuses"][tag] for tag in all_flow_tags if tag in data["flow_tag_statuses"]}
        data["is_timer_enabled"] = {tag: data["is_timer_enabled"][tag] for tag in all_flow_tags if tag in data["is_timer_enabled"]}

        workspace_tags.save_data(data)
        self.comboBox_current_status.disconnect()
        self.comboBox_current_status.clear()
        self.comboBox_current_status.addItems(workspace_tags.get_value("all_tags"))
        self.comboBox_current_status.currentTextChanged.connect(self.load_statuses)
        self.clear_layout(self.tag_layout)

    def add_flow_tag(self, layout: QHBoxLayout, button: QPushButton, tag_name: str = "None") -> None:
        """
        This function adds a flow tag to a QHBoxLayout with a tag name and an "Add" button.

        Args:
          layout (QHBoxLayout): QHBoxLayout object representing the layout where the widgets will be
        added
          button (QPushButton): The button parameter is a QPushButton object that will be hidden in this
        function.
          tag_name (str): The name of the tag to be added to the tagbox. If no name is provided, the
        default value is "None". Defaults to None
        """
        button.setHidden(True)
        tagbox = self.get_tag_box(tag_name)
        try:
            timer_check_box = self.get_timer_check_box(tagbox, workspace_tags.get_value("is_timer_enabled")[tag_name])
        except KeyError:
            timer_check_box = self.get_timer_check_box(tagbox, False)
        lbl = QLabel("➜", self)
        lbl.setFixedWidth(20)
        add = QPushButton("Add", self)
        add.setFixedWidth(30)
        add.clicked.connect(partial(self.add_flow_tag, layout, add))
        add.clicked.connect(self.save_flow_tags)
        v_widget = QWidget()
        v_layout = QVBoxLayout(v_widget)
        v_layout.addWidget(tagbox)
        v_layout.addWidget(timer_check_box)
        v_widget.setLayout(v_layout)
        layout.addWidget(lbl)
        layout.addWidget(v_widget)
        layout.addWidget(add)

    def create_flow_tag_layout(self, tag_name: str = "None") -> QWidget:
        """
        This function creates a layout for a flow tag with a tag box and an "Add" button.

        Args:
          tag_name (str): A string representing the name of the tag to be displayed in the tag box. If
        no tag name is provided, the default value is "None". Defaults to None

        Returns:
          a tuple containing a QWidget object, a QHBoxLayout object, and a QPushButton object.
        """
        widget = QWidget(self)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Set the alignment to left
        widget.setLayout(layout)
        tagbox = self.get_tag_box(tag_name)
        try:
            timer_check_box = self.get_timer_check_box(tagbox, workspace_tags.get_value("is_timer_enabled")[tag_name])
        except (KeyError, TypeError, AttributeError):
            timer_check_box = self.get_timer_check_box(tagbox, False)
        add = QPushButton("Add", self)
        add.setFixedWidth(30)
        add.clicked.connect(partial(self.add_flow_tag, layout, add))
        add.clicked.connect(self.save_flow_tags)
        v_widget = QWidget()
        v_layout = QVBoxLayout(v_widget)
        v_layout.addWidget(tagbox)
        v_layout.addWidget(timer_check_box)
        v_widget.setLayout(v_layout)
        layout.addWidget(v_widget)
        layout.addWidget(add)

        return widget, layout, add

    def get_tag_box(self, tag_name: str) -> QComboBox:
        """
        This function returns a QComboBox object with a specified tag name and editable text field.

        Args:
          tag_name (str): A string representing the name of a tag. If it is False, it will be replaced
        with the string "None".

        Returns:
          A QComboBox object is being returned.
        """
        if not tag_name:
            tag_name = "None"
        result = QComboBox(self)
        result.editTextChanged.connect(self.save_flow_tags)
        result.setFixedWidth(100)
        _list = list(self.get_all_flow_tags())
        with contextlib.suppress(ValueError):
            _list.remove(tag_name)
        result.addItems(_list)
        result.setEditable(True)
        result.setItemText(0, tag_name)
        return result

    def update_timer_enabled(self, tag_box: QComboBox, check: QCheckBox):
        data = workspace_tags.get_data()
        try:
            data["is_timer_enabled"][tag_box.currentText()] = check.isChecked()
        except (KeyError, TypeError, AttributeError):
            data["is_timer_enabled"] = {}
            data["is_timer_enabled"][tag_box.currentText()] = check.isChecked()
        workspace_tags.save_data(data)
        self.save_flow_tags()

    def get_timer_check_box(self, tag_box: QComboBox, is_checked: bool = False) -> QCheckBox:
        result = QCheckBox(self)
        result.setText("Recording")
        result.setChecked(is_checked)
        result.toggled.connect(partial(self.update_timer_enabled, tag_box, result))
        return result

    def create_flow_tag(self) -> None:
        """
        This function adds a widget to a flow tag layout.
        """
        widget, _, _ = self.create_flow_tag_layout()
        self.flow_tag_layout.addWidget(widget)

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
        data["flow_tag_statuses"][self.comboBox_current_status.currentText()][status_line_edit.text()] = data["flow_tag_statuses"][
            self.comboBox_current_status.currentText()
        ][old_name]
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
        """
        It loads the stylesheet.qss file from the theme folder
        """
        set_theme(self, theme="dark")

    def get_icon(self, path_to_icon: str) -> QSvgWidget:
        """
        It returns a QSvgWidget object that is initialized with a path to an SVG icon

        Args:
          path_to_icon (str): The path to the icon you want to use.

        Returns:
          A QSvgWidget object.
        """
        return QSvgWidget(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/{path_to_icon}")

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
