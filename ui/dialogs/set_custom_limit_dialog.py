from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog


class SetCustomLimitDialog(QDialog):
    def __init__(
        self,
        parent=None,
        message: str = "",
        red_limit: int = 10,
        yellow_limit: int = 20,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/set_custom_limit_dialog.ui", self)

        self.message = message

        self.setWindowIcon(QIcon("icons/icon.png"))

        self.setWindowTitle("Set Custom Quantity Limit")
        self.lblMessage.setText(self.message)

        if red_limit is not None or yellow_limit is not None:
            self.doubleSpinBox_red_limit.setValue(red_limit)
            self.doubleSpinBox_yellow_limit.setValue(yellow_limit)

        self.doubleSpinBox_red_limit.valueChanged.connect(self.check_quantity_values)
        self.doubleSpinBox_yellow_limit.valueChanged.connect(self.check_quantity_values)

        self.pushButton_set.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def check_quantity_values(self) -> None:
        if self.get_red_limit() > self.get_yellow_limit():
            self.doubleSpinBox_red_limit.setValue(
                self.doubleSpinBox_yellow_limit.value()
            )

    def get_red_limit(self) -> float:
        return self.doubleSpinBox_red_limit.value()

    def get_yellow_limit(self) -> float:
        return self.doubleSpinBox_yellow_limit.value()
