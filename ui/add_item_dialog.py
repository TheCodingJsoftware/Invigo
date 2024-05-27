from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from utils.components_inventory.component import Component
from utils.components_inventory.components_inventory import ComponentsInventory


class AddItemDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        components_inventory: ComponentsInventory,
        parent=None,
    ) -> None:
        super(AddItemDialog, self).__init__(parent)
        uic.loadUi("ui/add_item_dialog.ui", self)

        self.components_inventory = components_inventory

        self.setWindowIcon(QIcon("icons/icon.png"))

        self.setWindowTitle(title)
        self.lblMessage.setText(message)

        self.lineEdit_name.addItems(self.components_inventory.get_all_part_names())
        self.lineEdit_part_number.addItems(self.components_inventory.get_all_part_numbers())

        self.lineEdit_name.setCurrentText("")
        self.lineEdit_part_number.setCurrentText("")

        self.lineEdit_name.lineEdit().textChanged.connect(self.name_changed)
        # self.lineEdit_part_number.lineEdit().editingFinished.connect(
        #     self.part_number_changed
        # )
        self.pushButton_autofill.clicked.connect(self.autofill)

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def autofill(self) -> None:
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.lineEdit_part_number.setCurrentText(component.part_number)
                self._extracted_from_part_number_changed_10(component)

    def name_changed(self) -> None:
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.pushButton_autofill.setEnabled(True)
                return
            else:
                self.pushButton_autofill.setEnabled(False)

    def part_number_changed(self) -> None:
        for component in self.components_inventory.components:
            if component.part_number == self.lineEdit_part_number.currentText():
                self.lineEdit_name.setCurrentText(component.part_name)
                self._extracted_from_part_number_changed_10(component)

    # TODO Rename this here and in `name_changed` and `part_number_changed`
    def _extracted_from_part_number_changed_10(self, component: Component) -> None:
        self.comboBox_priority.setCurrentIndex(component.priority)
        self.spinBox_current_quantity.setValue(int(component.quantity))

        self.doubleSpinBox_unit_quantity.setValue(component.unit_quantity)
        self.doubleSpinBox_price.setValue(component.price)
        self.comboBox_exchange_price.setCurrentText("USD" if component.use_exchange_rate else "CAD")

        self.plainTextEdit_notes.setPlainText(component.notes)

    def get_part_number(self) -> str:
        return self.lineEdit_part_number.currentText().encode("ascii", "ignore").decode()

    def get_name(self) -> str:
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def get_priority(self) -> int:
        return self.comboBox_priority.currentIndex()

    def get_unit_quantity(self) -> float:
        return self.doubleSpinBox_unit_quantity.value()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_item_price(self) -> float:
        return self.doubleSpinBox_price.value()

    def get_exchange_rate(self) -> bool:
        return self.comboBox_exchange_price.currentText() == "USD"

    def get_notes(self) -> str:
        return self.plainTextEdit_notes.toPlainText().encode("ascii", "ignore").decode()
