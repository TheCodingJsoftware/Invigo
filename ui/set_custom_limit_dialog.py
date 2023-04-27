import os.path
from functools import partial

from PyQt5 import QtSvg, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class SetCustomLimitDialog(QDialog):
    """
    Message dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.set_cancel,
        title: str = __name__,
        message: str = "",
        red_limit: int=10,
        yellow_limit: int=20,
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
        super(SetCustomLimitDialog, self).__init__(parent)
        uic.loadUi("ui/set_custom_limit_dialog.ui", self)

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

        if red_limit is not None or yellow_limit is not None:
            self.doubleSpinBox_red_limit.setValue(red_limit)
            self.doubleSpinBox_yellow_limit.setValue(yellow_limit)

        self.doubleSpinBox_red_limit.valueChanged.connect(self.check_quantity_values)
        self.doubleSpinBox_yellow_limit.valueChanged.connect(self.check_quantity_values)

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
        set_theme(self, theme="dark")

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
        This function loads dialog buttons with icons and tooltips based on their names and sets the
        default button style.
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

    def check_quantity_values(self) -> None:
        """
        This function checks if the red limit value is greater than the yellow limit value and sets the
        red limit value to the yellow limit value if it is.
        """
        if self.get_red_limit() > self.get_yellow_limit():
            self.doubleSpinBox_red_limit.setValue(self.doubleSpinBox_yellow_limit.value())

    def get_response(self) -> str:
        """
        This function returns a string with all spaces removed from the input string.

        Returns:
          A string is being returned, which is the value of the instance variable `response` with all
        spaces removed.
        """
        return self.response.replace(" ", "")

    def get_red_limit(self) -> float:
        """
        This function returns the value of the red limit from a double spin box.

        Returns:
          The method `get_red_limit` is returning a float value which is obtained from the `value()`
        method of a `doubleSpinBox` object named `doubleSpinBox_red_limit`.
        """
        return self.doubleSpinBox_red_limit.value()

    def get_yellow_limit(self) -> float:
        """
        This function returns the value of the yellow limit from a double spin box.

        Returns:
          The method `get_yellow_limit` is returning a float value which is obtained from the `value()`
        method of a `doubleSpinBox` object named `doubleSpinBox_yellow_limit`.
        """
        return self.doubleSpinBox_yellow_limit.value()
