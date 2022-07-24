import os.path
from functools import partial

from PyQt5 import QtSvg, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class AddItemDialog(QDialog):
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
        super(AddItemDialog, self).__init__(parent)
        uic.loadUi("ui/add_item_dialog.ui", self)

        self.inventory = JsonFile(
            file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')}.json"
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

        self.lineEdit_name.addItems(self.get_all_part_names())
        self.lineEdit_part_number.addItems(self.get_all_part_numbers())
        self.comboBox_group.addItem("None")
        self.comboBox_group.addItems(self.get_all_groups())

        self.lineEdit_name.setCurrentText("")
        self.lineEdit_part_number.setCurrentText("")

        # self.lineEdit_name.lineEdit().editingFinished.connect(self.name_changed)
        # self.lineEdit_part_number.lineEdit().editingFinished.connect(
        #     self.part_number_changed
        # )

        self.setTabOrder(self.lineEdit_name, self.lineEdit_part_number)
        self.setTabOrder(self.lineEdit_part_number, self.spinBox_current_quantity)
        self.setTabOrder(self.spinBox_current_quantity, self.spinBox_unit_quantity)
        self.setTabOrder(self.spinBox_unit_quantity, self.doubleSpinBox_price)
        self.setTabOrder(self.doubleSpinBox_price, self.plainTextEdit_notes)
        self.setTabOrder(self.plainTextEdit_notes, self.comboBox_group)

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
        stylesheet_file = QFile(
            f"ui/BreezeStyleSheets/dist/qrc/{self.theme}/stylesheet.qss"
        )
        stylesheet_file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(stylesheet_file)
        self.setStyleSheet(stream.readAll())

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

    def name_changed(self) -> None:
        """
        It takes the name of an item from a combobox, and then fills in the rest of the fields with the
        data from the dictionary.
        """
        data = self.inventory.get_data()
        for category in list(data.keys()):
            for item in list(data[category].keys()):
                if item == self.lineEdit_name.currentText():
                    self.lineEdit_part_number.setCurrentText(
                        data[category][item]["part_number"]
                    )
                    self._extracted_from_part_number_changed_10(data, category, item)

    def part_number_changed(self) -> None:
        """
        It takes the part number from the lineEdit_part_number widget and searches the self.inventory data
        for a matching part number. If it finds a match, it sets the other widgets to the values of the
        matching part number.
        """
        data = self.inventory.get_data()
        for category in list(data.keys()):
            for item in list(data[category].keys()):
                if (
                    data[category][item]["part_number"]
                    == self.lineEdit_part_number.currentText()
                ):
                    self.lineEdit_name.setCurrentText(item)
                    self._extracted_from_part_number_changed_10(data, category, item)

    # TODO Rename this here and in `name_changed` and `part_number_changed`
    def _extracted_from_part_number_changed_10(self, data, category, item) -> None:
        self.comboBox_priority.setCurrentIndex(data[category][item]["priority"])
        self.spinBox_current_quantity.setValue(
            int(data[category][item]["current_quantity"])
        )

        self.spinBox_unit_quantity.setValue(int(data[category][item]["unit_quantity"]))
        self.doubleSpinBox_price.setValue(data[category][item]["price"])
        self.comboBox_exchange_price.setCurrentText(
            "USD" if data[category][item]["use_exchange_rate"] else "CAD"
        )

        self.plainTextEdit_notes.setPlainText(data[category][item]["notes"])

    def get_response(self) -> str:
        """
        This function returns the response of the class

        Returns:
          The response
        """
        return self.response.replace(" ", "")

    def get_part_number(self) -> str:
        """
        It returns the text in the lineEdit_part_number widget

        Returns:
          The text in the lineEdit_part_number widget.
        """
        return self.lineEdit_part_number.currentText().encode("ascii", "ignore").decode()

    def get_name(self) -> str:
        """
        It returns the text in the lineEdit_name widget

        Returns:
          The text in the lineEdit_name widget.
        """
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def get_priority(self) -> int:
        """
        It returns the current index of the comboBox_priority

        Returns:
          The current index of the comboBox_priority.
        """
        return self.comboBox_priority.currentIndex()

    def get_unit_quantity(self) -> int:
        """
        It returns the value of the spinBox_unit_quantity widget

        Returns:
          The value of the spinBox_unit_quantity.
        """
        return self.spinBox_unit_quantity.value()

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

    def get_notes(self) -> str:
        """
        It returns the text from a QPlainTextEdit widget

        Returns:
          The text in the text box.
        """
        return self.plainTextEdit_notes.toPlainText().encode("ascii", "ignore").decode()

    def get_group(self) -> str:
        """
        It returns the current text of the lineEdit_group widget, encoded as ASCII, ignoring any errors

        Returns:
          The current text in the lineEdit_group widget.
        """
        return self.comboBox_group.currentText().encode("ascii", "ignore").decode()

    def get_all_part_numbers(self) -> list[str]:
        """
        This function returns a list of all the unique part numbers in the inventory

        Returns:
          A list of unique part numbers.
        """
        part_numbers = self.get_items_from_inventory("part_number")
        part_numbers = list(set(part_numbers))
        return part_numbers

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
        part_names = list(set(part_names))
        return part_names

    def get_all_groups(self) -> list[str]:
        """
        This function returns a list of all the groups in the inventory

        Returns:
          A list of strings
        """
        groups = self.get_items_from_inventory("group")
        groups = set(groups)
        return groups

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
                result.extend(
                    data[category][item][value_name]
                    for item in list(data[category].keys())
                    if data[category][item][value_name] != None
                )

            except KeyError:
                continue
        return result
