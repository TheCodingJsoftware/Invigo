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


class AddComponentDialog(QDialog):
    """
    Message dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.add_cancel,
        title: str = __name__,
        message: str = "",
    ) -> None:
        """
        It's a constructor for a class that inherits from QDialog. It takes in a bunch of arguments and
        sets some class variables

        Args:
          parent: The parent widget of the dialog.
          icon_name (str): str = Icons.question,
          button_names (str): str = DialogButtons.add_cancel,
          title (str): str = __name__,
          message (str): str = "",
        """
        super(AddComponentDialog, self).__init__(parent)
        uic.loadUi("ui/add_component_dialog.ui", self)

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
        self.comboBox_part_number.addItems(self.get_all_part_numbers())
        self.lineEdit_name.setCurrentText("")
        self.lineEdit_name.lineEdit().textChanged.connect(self.name_changed)
        self.shelf_number = ""
        # self.lineEdit_part_number.lineEdit().editingFinished.connect(
        #     self.part_number_changed
        # )
        self.pushButton_autofill.clicked.connect(self.autofill)

        self.load_dialog_buttons()

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.setFixedSize(400, 250)
        self.load_theme()

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
        return QSvgWidget(f"icons/{path_to_icon}")

    def button_press(self, button) -> None:
        """
        The function is called when a button is pressed. It sets the response to the text of the button
        and then closes the dialog

        Args:
          button: The button that was clicked.
        """
        self.response = button.text()
        self.accept()

    def load_dialog_buttons(self) -> None:
        """
        It takes a string of button names, splits them into a list, and then creates a button for each
        name in the list
        """
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
        """
        It takes the data from the inventory, and if the item name matches the item name in the
        inventory, it will fill in the part number and the rest of the data.
        """
        data = self.inventory.get_data()
        for category in list(data.keys()):
            for item in list(data[category].keys()):
                if item == self.lineEdit_name.currentText():
                    self.comboBox_part_number.setCurrentText(data[category][item]["part_number"])
                    self._extracted_from_part_number_changed_10(data, category, item)

    def name_changed(self) -> None:
        """
        It takes the name of an item from a combobox, and then fills in the rest of the fields with the
        data from the dictionary.
        """
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

    # TODO Rename this here and in `name_changed` and `part_number_changed`
    def _extracted_from_part_number_changed_10(self, data, category, item) -> None:
        self.spinBox_current_quantity.setValue(int(data[category][item]["current_quantity"]))
        self.doubleSpinBox_price.setValue(data[category][item]["price"])
        self.comboBox_exchange_price.setCurrentText("USD" if data[category][item]["use_exchange_rate"] else "CAD")
        try:
            self.shelf_number = data[category][item]["shelf_number"]
        except KeyError:
            self.shelf_number = ""

    def get_response(self) -> str:
        """
        This function returns the response of the class

        Returns:
          The response
        """
        return self.response.replace(" ", "")

    def get_name(self) -> str:
        """
        It returns the text in the lineEdit_name widget

        Returns:
          The text in the lineEdit_name widget.
        """
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def get_current_quantity(self) -> int:
        """
        It returns the value of the spinBox_current_quantity widget

        Returns:
          The value of the spinBox_current_quantity.
        """
        return self.spinBox_current_quantity.value()

    def get_item_price(self) -> float:
        """
        It returns the value of the doubleSpinBox_price widget

        Returns:
          The value of the doubleSpinBox_price.
        """
        return self.doubleSpinBox_price.value()

    def get_exchange_rate(self) -> bool:
        """
        It returns the value of the doubleSpinBox_price widget

        Returns:
          The value of the doubleSpinBox_price.
        """

        return self.comboBox_exchange_price.currentText() == "USD"

    def get_part_number(self) -> str:
        return self.comboBox_part_number.currentText()

    def get_shelf_number(self) -> str:
        return self.shelf_number

    def get_all_part_names(self) -> list[str]:
        """
        This function returns a list of all the part names in the inventory

        Returns:
          A list of all the part names in the inventory.
        """
        data = self.inventory.get_data()
        part_names = []
        for category in list(data.keys()):
            part_names.extend(iter(list(data[category].keys())))
        return list(set(part_names))

    def get_all_part_numbers(self) -> list[str]:
        """
        This function returns a list of all the unique part numbers in the inventory

        Returns:
          A list of unique part numbers.
        """
        part_numbers = self.get_items_from_inventory("part_number")
        part_numbers = list(set(part_numbers))
        return part_numbers

    def get_items_from_inventory(self, value_name: str):
        """
        It takes a string as an argument, and returns a list of all the values in the inventory that
        match that string

        Args:
          value_name (str): The name of the value you want to get from the inventory.

        Returns:
          A list of all the values of the key "value_name" in the inventory.
        """
        data = self.inventory.get_data()
        result = []
        for category in list(data.keys()):
            try:
                result.extend(data[category][item][value_name] for item in list(data[category].keys()) if data[category][item][value_name] != None)

            except KeyError:
                continue
        return result
