import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class SetCustomLimitDialog(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.set_cancel,
        title: str = __name__,
        message: str = "",
        red_limit: int = 10,
        yellow_limit: int = 20,
    ) -> None:
        super(SetCustomLimitDialog, self).__init__(parent)
        uic.loadUi("ui/set_custom_limit_dialog.ui", self)

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.theme: str = "dark" if settings_file.get_value(item_name="dark_mode") else "light"

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        if red_limit is not None or yellow_limit is not None:
            self.doubleSpinBox_red_limit.setValue(red_limit)
            self.doubleSpinBox_yellow_limit.setValue(yellow_limit)

        self.doubleSpinBox_red_limit.valueChanged.connect(self.check_quantity_values)
        self.doubleSpinBox_yellow_limit.valueChanged.connect(self.check_quantity_values)

        self.load_dialog_buttons()

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        # self.resize(300, 150)
        self.load_theme()

    def load_theme(self) -> None:
        set_theme(self, theme="dark")

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
                button.setIcon(QIcon(f"icons/dialog_ok.svg"))
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

    def check_quantity_values(self) -> None:
        if self.get_red_limit() > self.get_yellow_limit():
            self.doubleSpinBox_red_limit.setValue(self.doubleSpinBox_yellow_limit.value())

    def get_response(self) -> str:
        return self.response.replace(" ", "")

    def get_red_limit(self) -> float:
        return self.doubleSpinBox_red_limit.value()

    def get_yellow_limit(self) -> float:
        return self.doubleSpinBox_yellow_limit.value()
