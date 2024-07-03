from PyQt6 import uic
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QLineEdit,
    QTextEdit,
)

from utils.quote.quote import Quote


class SaveQuoteDialog(QDialog):
    def __init__(
        self,
        quote: Quote,
        parent=None,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/save_quote_dialog.ui", self)

        self.quote = quote

        self.setWindowTitle("Save Quote")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.pushButton_save.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.comboBox_type = self.findChild(QComboBox, "comboBox_type")
        self.comboBox_type.setCurrentText("Quote")
        self.lineEdit_name = self.findChild(QLineEdit, "lineEdit_name")
        self.lineEdit_name.setText(self.quote.name)
        self.doubleSpinBox_order_number = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_order_number"
        )
        self.doubleSpinBox_order_number.setValue(self.quote.order_number)
        self.comboBox_status = self.findChild(QComboBox, "comboBox_status")
        self.comboBox_status.setCurrentText(self.quote.status)
        self.dateEdit_shipped = self.findChild(QDateEdit, "dateEdit_shipped")
        try:
            year, month, day = map(int, self.quote.date_shipped.split("-"))
            self.dateEdit_shipped.setDate(QDate(year, month, day))
        except ValueError:
            self.dateEdit_shipped.setDate(QDate.currentDate())
        self.dateEdit_expected = self.findChild(QDateEdit, "dateEdit_expected")
        try:
            year, month, day = map(int, self.quote.date_expected.split("-"))
            self.dateEdit_expected.setDate(QDate(year, month, day))
        except ValueError:
            self.dateEdit_expected.setDate(QDate.currentDate())
        self.textEdit_ship_to = self.findChild(QTextEdit, "textEdit_ship_to")
        self.textEdit_ship_to.setText(self.quote.ship_to)

    def get_type(self) -> str:
        return self.comboBox_type.currentText()

    def get_name(self) -> str:
        return self.lineEdit_name.text()

    def get_order_number(self) -> float:
        return self.doubleSpinBox_order_number.value()

    def get_status(self) -> str:
        return self.comboBox_status.currentText()

    def get_date_shipped(self) -> str:
        return self.dateEdit_shipped.date().toString("yyyy-MM-dd")

    def get_date_expected(self) -> str:
        return self.dateEdit_expected.date().toString("yyyy-MM-dd")

    def get_ship_to(self) -> str:
        return self.textEdit_ship_to.toPlainText()
