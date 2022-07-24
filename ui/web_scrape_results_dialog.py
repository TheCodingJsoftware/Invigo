import os.path
import webbrowser
from functools import partial

from PyQt5 import QtSvg, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ui.custom_widgets import set_default_dialog_button_stylesheet
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class WebScrapeResultsDialog(QDialog):
    """
    Input dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.information,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        data: dict = {},
    ) -> None:
        super(WebScrapeResultsDialog, self).__init__(parent)
        uic.loadUi("ui/web_scrape_results_dialog.ui", self)

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = f"{title} (Alpha)"
        self.message = message
        self.inputText: str = ""
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        self.load_dialog_buttons()

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.resize(800, 650)

        self.load_theme()
        self.load_data(data)

    def load_data(self, data) -> None:
        """
        It takes a dictionary of dictionaries and creates a QGroupBox for each item in the dictionary,
        then adds a QLabel for each key in the inner dictionary, and finally adds a QPushButton that
        opens a URL when clicked.

        Args:
          data: a dictionary of dictionaries
        """
        for item in data:
            group_box = QGroupBox(self, title=item)
            layout_groupbox = QVBoxLayout(group_box)
            group_box.setLayout(layout_groupbox)
            price_label = QLabel(group_box, text=f'Price {data[item]["price"]}')
            shipping_label = QLabel(group_box, text=f'Shipping {data[item]["shipping"]}')
            link_button = QPushButton(group_box, text="Link")
            link_button.clicked.connect(partial(self.open_url, data[item]["url"]))
            layout_groupbox.addWidget(price_label)
            layout_groupbox.addWidget(shipping_label)
            layout_groupbox.addWidget(link_button)
            self.layout_results.addWidget(group_box)

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

    def open_url(self, url: str) -> None:
        """
        It opens a new tab in the default browser and navigates to the url passed as an argument

        Args:
          url (str): The URL to open.
        """
        webbrowser.open(url)

    def button_press(self, button) -> None:
        """
        The function is called when a button is pressed. It sets the response to the text of the button
        that was pressed, and the inputText to the text in the lineEditInput. Then it accepts the dialog

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
            if os.path.isfile(
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
