from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.edit_contact_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.purchase_order.contact_info import ContactInfo, ContactInfoDict


class EditContactInfoDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Contact Info")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.contact_info = ContactInfo()

        self.pushButton_save.clicked.connect(self.save)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.lineEdit_name.setText(self.contact_info.name)
        self.lineEdit_phone.setText(self.contact_info.phone)
        self.lineEdit_email.setText(self.contact_info.email)

    def save(self):
        contact_info_data: ContactInfoDict = {
            "name": self.lineEdit_name.text(),
            "phone": self.lineEdit_phone.text(),
            "email": self.lineEdit_email.text(),
        }
        self.contact_info.load_data(contact_info_data)
        self.contact_info.save_data()
        self.accept()
