from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QListWidget

from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory


class AddComponentDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/add_component_dialog.ui", self)
        self.parent = parent

        self.components_inventory: ComponentsInventory = (
            self.parent.components_inventory
        )
        self.selected_component: Component = None

        self.setWindowTitle("Add New Component")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.comboBox_component_name: QComboBox
        self.comboBox_part_number: QComboBox
        self.listWidget_components: QListWidget

        self.comboBox_part_number.addItems(
            natsorted(self.components_inventory.get_all_part_numbers())
        )
        self.comboBox_part_number.setCurrentText("")
        self.comboBox_part_number.lineEdit().textChanged.connect(
            self.part_number_changed
        )

        self.comboBox_component_name.addItems(
            natsorted(self.components_inventory.get_all_part_names())
        )
        self.comboBox_component_name.setCurrentText("")
        self.comboBox_component_name.lineEdit().textChanged.connect(
            self.component_name_changed
        )

        self.listWidget_components.addItems(
            natsorted(
                self.components_inventory.get_all_part_names()
                + self.components_inventory.get_all_part_numbers()
            )
        )
        self.listWidget_components.currentTextChanged.connect(self.selection_changed)
        self.label_component_status.setStyleSheet("color: #E74E4E;")
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def selection_changed(self):
        for component in self.components_inventory.components:
            if (
                component.part_name == self.listWidget_components.currentItem().text()
                or component.part_number
                == self.listWidget_components.currentItem().text()
            ):
                self.comboBox_component_name.lineEdit().blockSignals(True)
                self.comboBox_component_name.setCurrentText(component.part_name)
                self.comboBox_component_name.lineEdit().blockSignals(False)
                self.comboBox_part_number.lineEdit().blockSignals(True)
                self.comboBox_part_number.setCurrentText(component.part_number)
                self.comboBox_part_number.lineEdit().blockSignals(False)
                self.label_component_status.setStyleSheet("color: #4EE753;")
                self.label_component_status.setText(" * Component exists in inventory.")
                self.selected_component = component
                return
            else:
                self.label_component_status.setStyleSheet("color: #E74E4E;")
                self.label_component_status.setText(
                    " * Component does NOT exists in inventory."
                )
                self.selected_component = None

    def get_component_row(self, component_name: str) -> int:
        return next(
            (
                row
                for row in range(self.listWidget_components.count())
                if self.listWidget_components.item(row).text() == component_name
            ),
            0,
        )

    def component_name_changed(self) -> None:
        for component in self.components_inventory.components:
            if component.part_name == self.comboBox_component_name.currentText():
                self.listWidget_components.blockSignals(True)
                self.listWidget_components.setCurrentRow(
                    self.get_component_row(component.part_name)
                )
                self.listWidget_components.blockSignals(False)
                self.comboBox_part_number.lineEdit().blockSignals(True)
                self.comboBox_part_number.setCurrentText(component.part_number)
                self.comboBox_part_number.lineEdit().blockSignals(False)
                self.label_component_status.setStyleSheet("color: #4EE753;")
                self.label_component_status.setText(" * Component exists in inventory.")
                self.selected_component = component
                return
            else:
                self.label_component_status.setStyleSheet("color: #E74E4E;")
                self.label_component_status.setText(
                    " * Component does NOT exists in inventory."
                )
                self.selected_component = None

    def part_number_changed(self) -> None:
        for component in self.components_inventory.components:
            if component.part_number == self.comboBox_part_number.currentText():
                self.listWidget_components.blockSignals(True)
                self.listWidget_components.setCurrentRow(
                    self.get_component_row(component.part_number)
                )
                self.listWidget_components.blockSignals(False)
                self.comboBox_component_name.lineEdit().blockSignals(True)
                self.comboBox_component_name.setCurrentText(component.part_name)
                self.comboBox_component_name.lineEdit().blockSignals(False)
                self.label_component_status.setStyleSheet("color: #4EE753;")
                self.label_component_status.setText(" * Component exists in inventory.")
                self.selected_component = component
                return
            else:
                self.label_component_status.setStyleSheet("color: #E74E4E;")
                self.label_component_status.setText(
                    " * Component does NOT exists in inventory."
                )
                self.selected_component = None

    def get_name(self) -> str:
        return (
            self.comboBox_component_name.currentText()
            .encode("ascii", "ignore")
            .decode()
        )

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_part_number(self) -> str:
        return self.comboBox_part_number.currentText()

    def get_selected_component(self) -> Component:
        return self.selected_component
