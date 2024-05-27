from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from utils.components_inventory.components_inventory import ComponentsInventory
from utils.settings import Settings

settings_file = Settings()


class AddComponentDialog(QDialog):
    def __init__(self, components_inventory: ComponentsInventory, parent) -> None:
        super(AddComponentDialog, self).__init__(parent)
        uic.loadUi("ui/add_component_dialog.ui", self)

        self.components_inventory = components_inventory

        self.setWindowTitle("Add new component to Quote")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lineEdit_name.addItems(self.components_inventory.get_all_part_names())
        self.comboBox_part_number.addItems(self.components_inventory.get_all_part_numbers())
        self.lineEdit_name.setCurrentText("")
        self.lineEdit_name.lineEdit().textChanged.connect(self.name_changed)
        self.shelf_number = ""
        # self.lineEdit_part_number.lineEdit().editingFinished.connect(
        #     self.part_number_changed
        # )
        self.pushButton_autofill.clicked.connect(self.autofill)
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def autofill(self) -> None:
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.comboBox_part_number.setCurrentText(component.name)
                self.spinBox_current_quantity.setValue(component.quantity)
                self.doubleSpinBox_price.setValue(component.price)
                self.comboBox_exchange_price.setCurrentText("USD" if component.use_exchange_rate else "CAD")
                self.shelf_number = component.shelf_number

    def name_changed(self) -> None:
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.pushButton_autofill.setEnabled(True)
                return
            else:
                self.pushButton_autofill.setEnabled(False)

    def get_name(self) -> str:
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_item_price(self) -> float:
        return self.doubleSpinBox_price.value()

    def get_exchange_rate(self) -> bool:
        return self.comboBox_exchange_price.currentText() == "USD"

    def get_part_number(self) -> str:
        return self.comboBox_part_number.currentText()

    def get_shelf_number(self) -> str:
        return self.shelf_number
