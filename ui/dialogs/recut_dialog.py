from functools import partial

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.recut_dialog_UI import Ui_Form
from ui.icons import Icons


class RecutDialog(QDialog, Ui_Form):
    def __init__(
        self,
        message: str,
        max_value: float,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Recut Count")
        self.setWindowIcon(QIcon(Icons.invigo_icon))
        self.input_text: float = 0.0
        self.max_value = max_value

        self.lblMessage.setText(message)
        self.doubleSpinBox_input.setMaximum(float(max_value))

        self.pushButton_1.clicked.connect(partial(self.quick_input_button_press, "1"))
        self.pushButton_2.clicked.connect(partial(self.quick_input_button_press, "2"))
        self.pushButton_3.clicked.connect(partial(self.quick_input_button_press, "3"))
        self.pushButton_all.clicked.connect(
            partial(self.quick_input_button_press, "All")
        )

        self.doubleSpinBox_input.selectAll()
        self.pushButton_ok.clicked.connect(self.button_press)
        self.pushButton_cancel.clicked.connect(self.reject)

    def quick_input_button_press(self, input_text: str):
        if input_text == "All":
            self.input_text = float(self.max_value)
        else:
            self.input_text = float(input_text)
        self.doubleSpinBox_input.setValue(self.input_text)
        self.accept()

    def button_press(self):
        self.input_text = self.doubleSpinBox_input.value()
        self.accept()

    def get_quantity(self) -> int:
        return int(self.input_text)
