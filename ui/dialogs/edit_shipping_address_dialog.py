from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.edit_shipping_address_UI import Ui_Form
from ui.icons import Icons
from utils.purchase_order.shipping_address import ShippingAddress, ShippingAddressDict


class EditShippingAddressDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent=None,
        shipping_address: ShippingAddress | None = None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Shipping Address")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.pushButton_save.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.id = -1

        if shipping_address:
            self.id = shipping_address.id
            self.lineEdit_name.setText(shipping_address.name)
            self.lineEdit_email.setText(shipping_address.email)
            self.lineEdit_phone.setText(shipping_address.phone)
            self.lineEdit_website.setText(shipping_address.website)
            self.plainTextEdit_address.setPlainText(shipping_address.address)
            self.plainTextEdit_notes.setPlainText(shipping_address.notes)

    def get_shipping_address(self) -> ShippingAddress:
        business_info_data: ShippingAddressDict = {
            "id": self.id,
            "name": self.lineEdit_name.text(),
            "email": self.lineEdit_email.text(),
            "phone": self.lineEdit_phone.text(),
            "address": self.plainTextEdit_address.toPlainText(),
            "website": self.lineEdit_website.text(),
            "notes": self.plainTextEdit_notes.toPlainText(),
        }
        return ShippingAddress(business_info_data)
