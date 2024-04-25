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

settings_file = JsonFile(file_name="settings")


class AddItemDialog(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.add_cancel,
        title: str = __name__,
        message: str = "",
    ) -> None:
        super(AddItemDialog, self).__init__(parent)
        uic.loadUi("ui/add_item_dialog.ui", self)

        self.inventory = JsonFile(file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')}.json")

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

        self.lineEdit_name.addItems(self.get_all_part_names())
        self.lineEdit_part_number.addItems(self.get_all_part_numbers())
        self.comboBox_group.addItem("None")
        self.comboBox_group.addItems(self.get_all_groups())

        self.lineEdit_name.setCurrentText("")
        self.lineEdit_part_number.setCurrentText("")

        self.lineEdit_name.lineEdit().textChanged.connect(self.name_changed)
        # self.lineEdit_part_number.lineEdit().editingFinished.connect(
        #     self.part_number_changed
        # )
        self.pushButton_autofill.clicked.connect(self.autofill)

        self.setTabOrder(self.lineEdit_name, self.lineEdit_part_number)
        self.setTabOrder(self.lineEdit_part_number, self.spinBox_current_quantity)
        self.setTabOrder(self.spinBox_current_quantity, self.doubleSpinBox_unit_quantity)
        self.setTabOrder(self.doubleSpinBox_unit_quantity, self.doubleSpinBox_price)
        self.setTabOrder(self.doubleSpinBox_price, self.plainTextEdit_notes)
        self.setTabOrder(self.plainTextEdit_notes, self.comboBox_group)

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

    def autofill(self) -> None:
        data = self.inventory.get_data()
        for category in list(data.keys()):
            for item in list(data[category].keys()):
                if item == self.lineEdit_name.currentText():
                    self.lineEdit_part_number.setCurrentText(data[category][item]["part_number"])
                    self._extracted_from_part_number_changed_10(data, category, item)

    def name_changed(self) -> None:
        data = self.inventory.get_data()
        for category in list(data.keys()):
            for item in list(data[category].keys()):
                if item == self.lineEdit_name.currentText():
                    self.pushButton_autofill.setEnabled(True)
                    return
                else:
                    self.pushButton_autofill.setEnabled(False)
                    # self.lineEdit_part_number.setCurrentText(
                    #     data[category][item]["part_number"]
                    # )
                    # self._extracted_from_part_number_changed_10(data, category, item)

    def part_number_changed(self) -> None:
        data = self.inventory.get_data()
        for category in list(data.keys()):
            for item in list(data[category].keys()):
                if data[category][item]["part_number"] == self.lineEdit_part_number.currentText():
                    self.lineEdit_name.setCurrentText(item)
                    self._extracted_from_part_number_changed_10(data, category, item)

    # TODO Rename this here and in `name_changed` and `part_number_changed`
    def _extracted_from_part_number_changed_10(self, data, category, item) -> None:
        self.comboBox_priority.setCurrentIndex(data[category][item]["priority"])
        self.spinBox_current_quantity.setValue(int(data[category][item]["current_quantity"]))

        self.doubleSpinBox_unit_quantity.setValue(float(data[category][item]["unit_quantity"]))
        self.doubleSpinBox_price.setValue(data[category][item]["price"])
        self.comboBox_exchange_price.setCurrentText("USD" if data[category][item]["use_exchange_rate"] else "CAD")

        self.plainTextEdit_notes.setPlainText(data[category][item]["notes"])

    def get_response(self) -> str:
        return self.response.replace(" ", "")

    def get_part_number(self) -> str:
        return self.lineEdit_part_number.currentText().encode("ascii", "ignore").decode()

    def get_name(self) -> str:
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def get_priority(self) -> int:
        return self.comboBox_priority.currentIndex()

    def get_unit_quantity(self) -> float:
        return self.doubleSpinBox_unit_quantity.value()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_item_price(self) -> float:
        return self.doubleSpinBox_price.value()

    def get_exchange_rate(self) -> bool:

        return self.comboBox_exchange_price.currentText() == "USD"

    def get_notes(self) -> str:
        return self.plainTextEdit_notes.toPlainText().encode("ascii", "ignore").decode()

    def get_group(self) -> str:
        return self.comboBox_group.currentText().encode("ascii", "ignore").decode()

    def get_all_part_numbers(self) -> list[str]:
        part_numbers = self.get_items_from_inventory("part_number")
        part_numbers = list(set(part_numbers))
        return part_numbers

    def get_all_part_names(self) -> list[str]:
        data = self.inventory.get_data()
        part_names = []
        for category in list(data.keys()):
            part_names.extend(iter(list(data[category].keys())))
        return list(set(part_names))

    def get_all_groups(self) -> list[str]:
        groups = self.get_items_from_inventory("group")
        groups = set(groups)
        return groups

    def get_items_from_inventory(self, value_name: str):
        data = self.inventory.get_data()
        result = []
        for category in list(data.keys()):
            try:
                result.extend(data[category][item][value_name] for item in list(data[category].keys()) if data[category][item][value_name] != None)

            except KeyError:
                continue
        return result
