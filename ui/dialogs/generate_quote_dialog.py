from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.generate_quote_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.settings import Settings


class GenerateQuoteDialog(QDialog, Ui_Form):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.settings_file = Settings()

        self.should_open_quote_when_generated: bool = self.settings_file.get_value(
            "open_quote_when_generated"
        )
        self.should_open_workorder_when_generated: bool = self.settings_file.get_value(
            "open_workorder_when_generated"
        )
        self.should_open_packing_slip_when_generated: bool = (
            self.settings_file.get_value("open_packing_slip_when_generated")
        )
        self.pushButton_group.setHidden(True)

        self.checkBox_quote.setChecked(self.should_open_quote_when_generated)
        self.checkBox_quote.toggled.connect(
            lambda: (
                self.settings_file.set_value(
                    "open_quote_when_generated", self.checkBox_quote.isChecked()
                )
            )
        )
        self.checkBox_workorder.setChecked(self.should_open_workorder_when_generated)
        self.checkBox_workorder.toggled.connect(
            lambda: (
                self.settings_file.set_value(
                    "open_workorder_when_generated", self.checkBox_workorder.isChecked()
                )
            )
        )
        self.checkBox_packing_slip.setChecked(
            self.should_open_packing_slip_when_generated
        )
        self.checkBox_packing_slip.toggled.connect(
            lambda: (
                self.settings_file.set_value(
                    "open_packing_slip_when_generated",
                    self.checkBox_packing_slip.isChecked(),
                )
            )
        )

        self.setWindowTitle("Generate Printout")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.pushButton_quote.clicked.connect(
            lambda: (
                (self.pushButton_packingslip.setChecked(False),)
                if self.pushButton_quote.isChecked()
                else self.pushButton_quote.isChecked()
            )
        )
        self.pushButton_workorder.clicked.connect(
            lambda: (
                (
                    self.pushButton_update_inventory.setChecked(True),
                    self.pushButton_remove_sheet_quantity.setChecked(True),
                    self.pushButton_packingslip.setChecked(False),
                    self.pushButton_quote.setChecked(False),
                )
                if self.pushButton_workorder.isChecked()
                else self.pushButton_workorder.isChecked()
            )
        )
        self.pushButton_packingslip.clicked.connect(
            lambda: (
                (self.pushButton_quote.setChecked(False),)
                if self.pushButton_packingslip.isChecked()
                else self.pushButton_packingslip.isChecked()
            )
        )

        self.pushButton_generate.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def get_selected_item(self) -> tuple[bool, bool, bool, bool, bool, bool]:
        return (
            self.pushButton_quote.isChecked(),
            self.pushButton_workorder.isChecked(),
            self.pushButton_update_inventory.isChecked(),
            self.pushButton_packingslip.isChecked(),
            self.pushButton_group.isChecked(),
            self.pushButton_remove_sheet_quantity.isChecked(),
        )
