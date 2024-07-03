
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog


class SetOrderPendingDialog(QDialog):
    def __init__(
        self,
        message: str,
        label_text: str,
        parent,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/set_order_pending_dialog.ui", self)

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
