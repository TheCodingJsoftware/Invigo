import os.path
from functools import partial

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QAbstractItemView, QDialog, QPushButton

from ui.dialogs.select_item_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.dialog_buttons import DialogButtons


class SelectItemDialog(QDialog, Ui_Form):
    def __init__(
        self,
        button_names: str,
        title: str,
        message: str,
        items: list[str],
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.button_names = button_names
        self.items = items

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.lblMessage.setText(message)

        self.load_dialog_buttons()

        self.listWidget.addItems(self.items)
        self.listWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def button_press(self, button: QPushButton):
        self.response = button.text()
        self.accept()

    def load_dialog_buttons(self):  # Dont ask me what this is supposed to do
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
            button.setDefault(True)
            button.setFixedWidth(100)
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
