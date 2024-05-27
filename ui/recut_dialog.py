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


class RecutDialog(QDialog):
    def __init__(
        self,
        message,
        max_value,
        parent,
    ) -> None:
        super(RecutDialog, self).__init__(parent)
        uic.loadUi("ui/recut_dialog.ui", self)

        self.setWindowTitle("Recut Count")
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.input_text: float = 0.0
        self.max_value = max_value

        self.lblMessage.setText(message)
        self.doubleSpinBox_input.setMaximum(max_value)

        self.pushButton_1.clicked.connect(partial(self.quick_input_button_press, "1"))
        self.pushButton_2.clicked.connect(partial(self.quick_input_button_press, "2"))
        self.pushButton_3.clicked.connect(partial(self.quick_input_button_press, "3"))
        self.pushButton_all.clicked.connect(partial(self.quick_input_button_press, "All"))

        self.doubleSpinBox_input.selectAll()
        self.pushButton_ok.clicked.connect(self.button_press)
        self.pushButton_cancel.clicked.connect(self.reject)

    def quick_input_button_press(self, input_text) -> None:
        if input_text == "All":
            self.input_text = self.max_value
        self.accept()

    def button_press(self) -> None:
        self.input_text = self.doubleSpinBox_input.value()
        self.accept()
