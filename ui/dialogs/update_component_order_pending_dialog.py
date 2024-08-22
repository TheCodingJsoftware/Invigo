from functools import partial

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.update_component_order_pending_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.inventory.order import Order


class UpdateComponentOrderPendingDialog(QDialog, Ui_Form):
    def __init__(
        self,
        order: Order,
        message: str,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Update Order")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.action: str = ""

        self.lblMessage.setText(message)
        self.doubleSpinBox_quantity.setValue(order.quantity)
        self.textEdit_notes.setPlainText(order.notes)

        self.pushButton_add_incoming_quantity.clicked.connect(partial(self.button_accept, "ADD_INCOMING_QUANTITY"))
        self.pushButton_update_order.clicked.connect(partial(self.button_accept, "UPDATE_ORDER"))
        self.pushButton_cancel_order.clicked.connect(partial(self.button_accept, "CANCEL_ORDER"))
        self.pushButton_cancel.clicked.connect(self.reject)

    def button_accept(self, action: str):
        self.action = action
        self.accept()

    def get_order_quantity(self) -> float:
        return self.doubleSpinBox_quantity.value()

    def get_notes(self) -> str:
        return self.textEdit_notes.toPlainText()
