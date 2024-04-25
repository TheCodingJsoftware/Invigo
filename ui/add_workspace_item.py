import contextlib
import os.path
from functools import partial

from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QCompleter, QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile
from utils.settings import Settings

settings_file = Settings()


class AddWorkspaceItem(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.add_cancel,
        title: str = __name__,
        message: str = "",
    ) -> None:
        super(AddWorkspaceItem, self).__init__(parent)
        uic.loadUi("ui/add_workspace_item.ui", self)

        self.inventory = JsonFile(file_name=f"data/{settings_file.get_value('inventory_file_name')}.json")
        self.parts_in_inventory = JsonFile(file_name=f"data/{settings_file.get_value('inventory_file_name')} - Parts in Inventory.json")

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.thickness = ""
        self.material = ""

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        all_part_names = natsorted(self.get_all_part_names())

        completer = QCompleter(all_part_names, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.lineEdit_name.setCompleter(completer)
        self.lineEdit_name.textChanged.connect(self.name_changed)

        self.listWidget_all_items.itemSelectionChanged.connect(self.listWidget_item_changed)
        self.listWidget_all_items.addItems(all_part_names)

        self.load_dialog_buttons()

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        # self.resize(300, 150)
        self.load_theme()

    def listWidget_item_changed(self) -> None:
        self.lineEdit_name.setText(self.listWidget_all_items.currentItem().text())
        self.thickness = ""
        self.material = ""
        with contextlib.suppress(KeyError):
            for category, category_data in self.parts_in_inventory.get_data().items():
                for name, part_data in category_data.items():
                    if name == self.lineEdit_name.text():
                        self.thickness = part_data['gauge']
                        self.material = part_data['material']
                        break

    def name_changed(self) -> None:
        all_part_names = natsorted(self.get_all_part_names())
        for part_name in all_part_names:
            if part_name == self.lineEdit_name.text():
                index = all_part_names.index(part_name)
                self.listWidget_all_items.setCurrentRow(index)
                break

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
            if name == DialogButtons.add:
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

    def get_name(self) -> str:
        return self.lineEdit_name.text().encode("ascii", "ignore").decode()

    def get_all_part_names(self) -> list[str]:
        part_names = []
        for category in list(self.inventory.data.keys()):
            part_names.extend(iter(list(self.inventory.data[category].keys())))
        for category in list(self.parts_in_inventory.data.keys()):
            part_names.extend(iter(list(self.parts_in_inventory.data[category].keys())))
        return list(set(part_names))

