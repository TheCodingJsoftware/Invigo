from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.generate_workorder_dialog_UI import Ui_Form
from ui.icons import Icons


class GenerateWorkorderDialog(QDialog, Ui_Form):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Generate Workorder")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.pushButton_generate_printout.clicked.connect(
            self.generate_printout_pressed
        )

        self.pushButton_generate.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def generate_printout_pressed(self):
        self.pushButton_show_qr_code.setChecked(
            self.pushButton_generate_printout.isChecked()
        )
        self.checkBox_open_workorder_when_generated.setChecked(
            self.pushButton_generate_printout.isChecked()
        )

    def should_update_inventory(self) -> bool:
        return self.pushButton_update_inventory.isChecked()

    def should_remove_sheet_quantity(self) -> bool:
        return self.pushButton_remove_sheet_quantity.isChecked()

    def should_open_printout(self) -> bool:
        return self.checkBox_open_workorder_when_generated.isChecked()

    def should_add_remaining_parts(self) -> bool:
        return self.pushButton_add_remaning_parts.isChecked()

    def should_add_overflow_parts(self) -> bool:
        return self.pushButton_add_overflow_parts.isChecked()

    def should_show_qr_code(self) -> bool:
        return self.pushButton_show_qr_code.isChecked()

    def should_generate_printout(self) -> bool:
        return self.pushButton_generate_printout.isChecked()
