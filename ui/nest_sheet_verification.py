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
from utils.json_file import JsonFile


class NestSheetVerification(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        thickness: str = "",
        material: str = "",
    ) -> None:
        super(NestSheetVerification, self).__init__(parent)
        uic.loadUi("ui/nest_sheet_verification.ui", self)

        price_of_steel_information = JsonFile(file_name="price_of_steel_information.json")

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.inputText: str = ""

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.load_dialog_buttons()

        self.listWidget_thicknesses.addItems(price_of_steel_information.get_value("thicknesses"))
        self.listWidget_thicknesses.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        try:
            self.listWidget_thicknesses.setCurrentRow(price_of_steel_information.get_value("thicknesses").index(thickness))
        except ValueError:
            self.message += f'\n\nNOTICE: "{thickness}" is not in the global thickness list in "price_of_steel_information.json"; to add it got to Settings > Edit Sheets > Add Thickness'

        self.listWidget_materials.addItems(price_of_steel_information.get_value("materials"))
        self.listWidget_materials.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        try:
            self.listWidget_materials.setCurrentRow(price_of_steel_information.get_value("materials").index(material))
        except ValueError:
            self.message += f'\n\nNOTICE: "{material}" is not in the global material list in "price_of_steel_information.json"; to add it got to Settings > Edit Sheets > Add Material'

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        # self.resize(320, 250)

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

    def get_selected_material(self) -> str:
        try:
            return self.listWidget_materials.currentItem().text()
        except AttributeError:
            return None

    def get_selected_thickness(self) -> str:
        try:
            return self.listWidget_thicknesses.currentItem().text()
        except AttributeError:
            return None
