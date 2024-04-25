import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile
from utils.settings import Settings

settings_file = Settings()


class AddItemDialogPriceOfSteel(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.add_cancel,
        title: str = __name__,
        message: str = "",
    ) -> None:
        super(AddItemDialogPriceOfSteel, self).__init__(parent)
        uic.loadUi("ui/add_item_dialog_price_of_steel.ui", self)

        self.inventory = JsonFile(file_name=f"data/{settings_file.get_value('inventory_file_name')} - Price of Steel.json")
        self.price_of_steel_information = JsonFile(file_name="price_of_steel_information.json")

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)
        self.lineEdit_material.addItems(self.get_all_materials())
        self.comboBox_thickness.addItems(self.get_all_thicknesses())
        self.comboBox_group.addItem("None")
        self.comboBox_group.addItems(self.get_all_groups())

        self.lineEdit_material.setCurrentText("")
        self.comboBox_thickness.setCurrentText("")

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
        return f"{self.comboBox_thickness.currentText()} {self.lineEdit_material.currentText()} {self.get_sheet_dimension()}"

    def get_sheet_dimension(self) -> str:
        return "{:.3f}x{:.3f}".format(self.doubleSpinBox_length.value(), self.doubleSpinBox_width.value())

    def get_material(self) -> str:
        return self.lineEdit_material.currentText()

    def get_thickness(self) -> str:
        return self.comboBox_thickness.currentText()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_group(self) -> str:
        return self.comboBox_group.currentText()

    def get_all_groups(self) -> list[str]:
        groups = self.get_items_from_inventory("group")
        groups = set(groups)
        return groups

    def get_all_materials(self) -> list[str]:
        return self.price_of_steel_information.get_value("materials")

    def get_all_thicknesses(self) -> list[str]:
        return self.price_of_steel_information.get_value("thicknesses")

    def get_items_from_inventory(self, value_name: str) -> list[str]:
        data = self.inventory.get_data()
        result = []
        for category in list(data.keys()):
            try:
                result.extend(data[category][item][value_name] for item in list(data[category].keys()) if data[category][item][value_name] != None)

            except KeyError:
                continue
        return result
