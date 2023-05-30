import os.path
from functools import partial

from PyQt5 import QtSvg, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton, QRadioButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class GenerateQuoteDialog(QDialog):
    """
    Select dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        options: list = None,
    ) -> None:
        """
        It's a function that takes in a list of options and displays them in a list widget

        Args:
          parent: The parent widget of the dialog.
          icon_name (str): str = Icons.question,
          button_names (str): str = DialogButtons.ok_cancel,
          title (str): str = __name__,
          message (str): str = "",
          options (list): list = None,
        """
        if options is None:
            options = []
        super(GenerateQuoteDialog, self).__init__(parent)
        uic.loadUi("ui/generate_quote_dialog.ui", self)

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.inputText: str = ""
        self.theme: str = "dark" if settings_file.get_value(item_name="dark_mode") else "light"

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        self.load_dialog_buttons()
        self.pushButton_update_inventory.clicked.connect(
            lambda: self.pushButton_update_inventory.setText("Add Parts to Inventory")
            if self.pushButton_update_inventory.isChecked()
            else self.pushButton_update_inventory.setText("Do NOT Add Parts to Inventory")
        )
        self.pushButton_quote.clicked.connect(
            lambda: self.pushButton_quote.setText("Generate Quote")
            if self.pushButton_quote.isChecked()
            else self.pushButton_quote.setText("Do NOT Generate Quote")
        )
        self.pushButton_workorder.clicked.connect(
            lambda: self.pushButton_workorder.setText("Generate Workorder")
            if self.pushButton_workorder.isChecked()
            else self.pushButton_workorder.setText("Do NOT Generate Workorder")
        )
        self.pushButton_packingslip.clicked.connect(
            lambda: self.pushButton_packingslip.setText("Generate Packing Slip")
            if self.pushButton_packingslip.isChecked()
            else self.pushButton_packingslip.setText("Do NOT Generate Packing Slip")
        )
        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.resize(320, 250)

        self.load_theme()

    def load_theme(self) -> None:
        """
        It loads the stylesheet.qss file from the theme folder
        """
        set_theme(self, theme="dark")

    def get_icon(self, path_to_icon: str) -> QtSvg.QSvgWidget:
        """
        It returns a QSvgWidget object that is initialized with a path to an SVG icon

        Args:
          path_to_icon (str): The path to the icon you want to use.

        Returns:
          A QSvgWidget object.
        """
        return QtSvg.QSvgWidget(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/{path_to_icon}")

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
            if name == DialogButtons.clone:
                button = QPushButton(f"  {name}")
                button.setIcon(QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/dialog_ok.svg"))
            elif os.path.isfile(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/dialog_{name.lower()}.svg"):
                button = QPushButton(f"  {name}")
                button.setIcon(QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/dialog_{name.lower()}.svg"))
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

    def get_selected_item(self) -> tuple[bool, bool, bool, bool]:
        """
        This function returns a tuple of boolean values indicating which push buttons are checked.

        Returns:
          A tuple containing three boolean values representing whether the corresponding push button
        (quote, work order, update inventory) is checked or not.
        """
        return (
            self.pushButton_quote.isChecked(),
            self.pushButton_workorder.isChecked(),
            self.pushButton_update_inventory.isChecked(),
            self.pushButton_packingslip.isChecked(),
        )
