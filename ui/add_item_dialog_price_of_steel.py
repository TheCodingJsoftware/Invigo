import os.path
from functools import partial

from PyQt5 import QtSvg, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class AddItemDialogPriceOfSteel(QDialog):
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
        super(AddItemDialogPriceOfSteel, self).__init__(parent)
        uic.loadUi("ui/add_item_dialog_price_of_steel.ui", self)

        self.inventory = JsonFile(
            file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')} - Price of Steel.json"
        )
        self.price_of_steel_information = JsonFile(
            file_name="price_of_steel_information.json"
        )

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
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
        """
        It loads the stylesheet.qss file from the theme folder
        """
        set_theme(self, theme='dark')

    def get_icon(self, path_to_icon: str) -> QtSvg.QSvgWidget:
        """
        It returns a QSvgWidget object that is initialized with a path to an SVG icon

        Args:
          path_to_icon (str): The path to the icon you want to use.

        Returns:
          A QSvgWidget object.
        """
        return QtSvg.QSvgWidget(
            f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/{path_to_icon}"
        )

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
                button.setIcon(
                    QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/dialog_ok.svg")
                )
            elif os.path.isfile(
                f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/dialog_{name.lower()}.svg"
            ):
                button = QPushButton(f"  {name}")
                button.setIcon(
                    QIcon(
                        f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/dialog_{name.lower()}.svg"
                    )
                )
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
        """
        This function returns the response of the class

        Returns:
          The response
        """
        return self.response.replace(" ", "")

    def get_name(self) -> str:
        """
        It returns a string that is the concatenation of the current text of a QComboBox, a QLineEdit,
        and a function that returns a string

        Returns:
          The name of the sheet.
        """
        return f"{self.comboBox_thickness.currentText()} {self.lineEdit_material.currentText()} {self.get_sheet_dimension()}"

    def get_sheet_dimension(self) -> str:
        """
        It returns the text in the lineEdit_part_number widget

        Returns:
          The text in the lineEdit_part_number widget.
        """
        return "{:.3f}x{:.3f}".format(
            self.doubleSpinBox_length.value(), self.doubleSpinBox_width.value()
        )

    def get_material(self) -> str:
        """
        It returns the text in the lineEdit_name widget

        Returns:
          The text in the lineEdit_name widget.
        """
        return self.lineEdit_material.currentText()

    def get_thickness(self) -> str:
        """
        It returns the text in the lineEdit_name widget

        Returns:
          The text in the lineEdit_name widget.
        """
        return self.comboBox_thickness.currentText()

    def get_current_quantity(self) -> int:
        """
        It returns the value of the spinBox_current_quantity widget

        Returns:
          The value of the spinBox_current_quantity.
        """
        return self.spinBox_current_quantity.value()

    def get_group(self) -> str:
        """
        It returns the current text of the lineEdit_group widget, encoded as ASCII, ignoring any errors

        Returns:
          The current text in the lineEdit_group widget.
        """
        return self.comboBox_group.currentText()

    def get_all_groups(self) -> list[str]:
        """
        This function returns a list of all the groups in the inventory

        Returns:
          A list of strings
        """
        groups = self.get_items_from_inventory("group")
        groups = set(groups)
        return groups

    def get_all_materials(self) -> list[str]:
        """
        This function returns a list of all the materials that are available in the price of steel
        information

        Returns:
          A list of strings.
        """
        return self.price_of_steel_information.get_value("materials")

    def get_all_thicknesses(self) -> list[str]:
        """
        This function returns a list of all the thicknesses of steel that are available

        Returns:
          A list of strings.
        """
        return self.price_of_steel_information.get_value("thicknesses")

    def get_items_from_inventory(self, value_name: str) -> list[str]:
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
                result.extend(
                    data[category][item][value_name]
                    for item in list(data[category].keys())
                    if data[category][item][value_name] != None
                )

            except KeyError:
                continue
        return result
