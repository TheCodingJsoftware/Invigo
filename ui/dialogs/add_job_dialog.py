
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog


class AddJobDialog(QDialog):
    def __init__(
        self,
        group_names: list[str],
        parent,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/add_job_dialog.ui", self)

        self.inputText: str = ""

        self.setWindowTitle("Add job")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)
        self.comboBox_group_name.addItems(group_names)
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def get_selected_items(self) -> tuple[str, bool, bool]:
        return (
            self.lineEdit_job_name.text(),
            self.pushButton_has_items.isChecked(),
            self.pushButton_has_sub_assemblies.isChecked(),
        )

    def get_group_name(self) -> str:
        return self.comboBox_group_name.currentText()
