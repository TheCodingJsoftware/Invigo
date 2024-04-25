import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QDialog, QPushButton, QRadioButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class GenerateQuoteDialog(QDialog):

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        options: list = None,
    ) -> None:
        if options is None:
            options = []
        super(GenerateQuoteDialog, self).__init__(parent)
        uic.loadUi("ui/generate_quote_dialog.ui", self)

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.inputText: str = ""
        settings_file.load_data()
        self.theme: str = "dark" if settings_file.get_value(item_name="dark_mode") else "light"

        self.should_open_quote_when_generated: bool = settings_file.get_value(item_name='open_quote_when_generated')
        self.should_open_workorder_when_generated: bool = settings_file.get_value(item_name='open_workorder_when_generated')
        self.should_open_packing_slip_when_generated: bool = settings_file.get_value(item_name='open_packing_slip_when_generated')

        self.checkBox_quote.setChecked(self.should_open_quote_when_generated)
        self.checkBox_quote.toggled.connect(lambda:(settings_file.add_item('open_quote_when_generated', self.checkBox_quote.isChecked())))
        self.checkBox_workorder.setChecked(self.should_open_workorder_when_generated)
        self.checkBox_workorder.toggled.connect(lambda:(settings_file.add_item('open_workorder_when_generated', self.checkBox_workorder.isChecked())))
        self.checkBox_packing_slip.setChecked(self.should_open_packing_slip_when_generated)
        self.checkBox_packing_slip.toggled.connect(lambda:(settings_file.add_item('open_packing_slip_when_generated', self.checkBox_packing_slip.isChecked())))

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        self.load_dialog_buttons()
        self.pushButton_quote.clicked.connect(
            lambda: (self.pushButton_packingslip.setChecked(False),) if self.pushButton_quote.isChecked() else self.pushButton_quote.isChecked()
        )
        self.pushButton_workorder.clicked.connect(
            lambda: (
                self.pushButton_update_inventory.setChecked(True),
                self.pushButton_packingslip.setChecked(False),
                self.pushButton_quote.setChecked(False),
            )
            if self.pushButton_workorder.isChecked()
            else self.pushButton_workorder.isChecked()
        )
        self.pushButton_packingslip.clicked.connect(
            lambda: (self.pushButton_quote.setChecked(False),) if self.pushButton_packingslip.isChecked() else self.pushButton_packingslip.isChecked()
        )
        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.resize(320, 250)

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
            if name == DialogButtons.generate:
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

    def get_selected_item(self) -> tuple[bool, bool, bool, bool, bool]:
        return (
            self.pushButton_quote.isChecked(),
            self.pushButton_workorder.isChecked(),
            self.pushButton_update_inventory.isChecked(),
            self.pushButton_packingslip.isChecked(),
            self.pushButton_group.isChecked(),
        )

    def should_remove_sheet_quantities(self) -> bool:
        return self.checkBox_remove_sheet_quantities.isChecked()
