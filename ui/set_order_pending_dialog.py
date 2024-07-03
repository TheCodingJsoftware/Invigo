import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QAbstractItemView, QDialog, QPushButton

from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons


class SetOrderPendingDialog(QDialog):
    def __init__(
        self,
        message: str,
        label_text: str,
        parent,
    ) -> None:
        super(SetOrderPendingDialog, self).__init__(parent)
        uic.loadUi("ui/set_order_pending_dialog.ui", self)

        self.setWindowTitle("Set Expected Arrival Time & Quantity")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblMessage.setText(message)
        self.label.setText(label_text)

        self.pushButton_set.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def get_selected_date(self) -> str:
        try:
            return self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        except AttributeError:
            return None

    def get_order_quantity(self) -> float:
        return self.doubleSpinBox_sheets_ordered.value()
