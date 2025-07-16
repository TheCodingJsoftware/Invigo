from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.edit_business_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.purchase_order.business_info import BusinessInfo, BusinessInfoDict


class EditBusinessInfoDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Business Info")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.business_info = BusinessInfo()

        self.pushButton_save.clicked.connect(self.save)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.lineEdit_name.setText(self.business_info.name)
        self.lineEdit_email.setText(self.business_info.email)
        self.lineEdit_phone.setText(self.business_info.phone)
        self.plainTextEdit_address.setPlainText(self.business_info.address)
        self.lineEdit_gst_number.setText(self.business_info.gst_number)
        self.lineEdit_pst_number.setText(self.business_info.pst_number)
        self.doubleSpinBox_pst_rate.setValue(self.business_info.pst_rate * 100)
        self.doubleSpinBox_gst_rate.setValue(self.business_info.gst_rate * 100)
        self.lineEdit_business_number.setText(self.business_info.business_number)

    def save(self):
        business_info_data: BusinessInfoDict = {
            "name": self.lineEdit_name.text(),
            "email": self.lineEdit_email.text(),
            "phone": self.lineEdit_phone.text(),
            "address": self.plainTextEdit_address.toPlainText(),
            "gst_number": self.lineEdit_gst_number.text(),
            "pst_number": self.lineEdit_pst_number.text(),
            "gst_rate": self.doubleSpinBox_gst_rate.value() / 100,
            "pst_rate": self.doubleSpinBox_pst_rate.value() / 100,
            "business_number": self.lineEdit_business_number.text(),
        }
        self.business_info.load_data(business_info_data)
        self.business_info.save_data()
        self.accept()
