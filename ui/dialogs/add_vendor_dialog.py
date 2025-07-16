from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.add_vendor_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.purchase_order.vendor import Vendor, VendorDict


class AddVendorDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent=None,
        vendor: Vendor | None = None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Vendor")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.pushButton_save.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.id = -1

        if vendor:
            self.id = vendor.id
            self.lineEdit_name.setText(vendor.name)
            self.plainTextEdit_address.setPlainText(vendor.address)
            self.lineEdit_phone.setText(vendor.phone)
            self.lineEdit_email.setText(vendor.email)
            self.lineEdit_website.setText(vendor.website)
            self.plainTextEdit_notes.setPlainText(vendor.notes)

    def get_vendor(self) -> Vendor:
        vendor_data: VendorDict = {
            "id": self.id,
            "name": self.lineEdit_name.text(),
            "address": self.plainTextEdit_address.toPlainText(),
            "phone": self.lineEdit_phone.text(),
            "email": self.lineEdit_email.text(),
            "website": self.lineEdit_website.text(),
            "notes": self.plainTextEdit_notes.toPlainText(),
        }
        return Vendor(vendor_data)
