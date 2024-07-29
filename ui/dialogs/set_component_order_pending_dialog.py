from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog


class SetComponentOrderPendingDialog(QDialog):
    def __init__(
        self,
        message: str,
        parent,
    ):
        super().__init__(parent)
        uic.loadUi("ui/dialogs/set_component_order_pending_dialog.ui", self)

        self.setWindowTitle("Create Order")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblMessage.setText(message)

        self.pushButton_set.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def get_selected_date(self) -> str:
        try:
            return self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        except AttributeError:
            return None

    def get_order_quantity(self) -> float:
        return self.doubleSpinBox_sheets_ordered.value()

    def get_notes(self) -> str:
        return self.textEdit_notes.toPlainText()
