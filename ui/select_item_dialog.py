import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QAbstractItemView, QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons


class SelectItemDialog(QDialog):
    def __init__(
        self,
        button_names: str,
        title: str,
        message: str,
        items: list[str],
        parent,
    ) -> None:
        super(SelectItemDialog, self).__init__(parent)
        uic.loadUi("ui/select_item_dialog.ui", self)

        self.button_names = button_names
        self.items = items

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblMessage.setText(message)

        self.load_dialog_buttons()

        self.listWidget.addItems(self.items)
        self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def button_press(self, button) -> None:
        self.response = button.text()
        self.accept()

    def load_dialog_buttons(self) -> None:
        button_names = self.button_names.split(", ")
        for index, name in enumerate(button_names):
            if name in [DialogButtons.clone, DialogButtons.set]:
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

    def get_selected_item(self) -> str:
        try:
            return self.listWidget.currentItem().text()
        except AttributeError:
            return None

    def get_selected_items(self) -> list[str]:
        try:
            return [item.text() for item in self.listWidget.selectedItems()]
        except AttributeError:
            return None
