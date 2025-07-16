from natsort import natsorted
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QCompleter, QDialog

from ui.dialogs.add_component_dialog_UI import Ui_Form
from ui.icons import Icons
from ui.theme import theme_var
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory


class AddComponentDialog(QDialog, Ui_Form):
    def __init__(self, components_inventory: ComponentsInventory, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent

        self.components_inventory = components_inventory
        self.selected_component: Component = None

        self.setWindowTitle("Add New Component")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.completer = QCompleter(natsorted(self.components_inventory.get_all_part_names()))
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setWidget(self.lineEdit_component_name)
        self.completer.activated.connect(self.handleCompletion)
        self.lineEdit_component_name.textChanged.connect(self.component_name_changed)
        self._completing = False

        self.listWidget_components.addItems(natsorted(self.components_inventory.get_all_part_names()))
        self.listWidget_components.currentTextChanged.connect(self.selection_changed)
        self.label_component_status.setStyleSheet(f"color: {theme_var('error')};")
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def handleCompletion(self, text):
        if not self._completing:
            self._completing = True
            prefix = self.completer.completionPrefix()
            self.lineEdit_component_name.setText(self.lineEdit_component_name.text()[: -len(prefix)] + text)
            self._completing = False

    def selection_changed(self):
        if len(self.listWidget_components.selectedItems()) > 1:
            return
        for component in self.components_inventory.components:
            if component.part_name == self.listWidget_components.currentItem().text():
                self.lineEdit_component_name.blockSignals(True)
                self.lineEdit_component_name.setText(component.part_name)
                self.lineEdit_component_name.blockSignals(False)
                self.label_component_status.setStyleSheet(f"color: {theme_var('primary-green')};")
                self.label_component_status.setText(" * Component exists in inventory.")
                self.selected_component = component
                return
            else:
                self.label_component_status.setStyleSheet(f"color: {theme_var('error')};")
                self.label_component_status.setText(" * Component does NOT exists in inventory.")
                self.selected_component = None

    def get_component_row(self, component_name: str) -> int:
        return next(
            (row for row in range(self.listWidget_components.count()) if self.listWidget_components.item(row).text() == component_name),
            0,
        )

    def component_name_changed(self, text: str):
        if not self._completing:
            found = False
            prefix = text.rpartition(",")[-1]
            if len(prefix) > 1:
                self.completer.setCompletionPrefix(prefix)
                if self.completer.currentRow() >= 0:
                    found = True
            if found:
                self.completer.complete()
            else:
                self.completer.popup().hide()

        new_parts_last = []
        self.label_component_status.setStyleSheet(f"color: {theme_var('error')};")
        self.listWidget_components.blockSignals(True)
        self.listWidget_components.clear()
        for name in self.components_inventory.get_all_part_names():
            if text.lower() in name.lower():
                new_parts_last.append(name)
        self.listWidget_components.addItems(natsorted(new_parts_last))
        self.listWidget_components.blockSignals(False)

    def get_name(self) -> str:
        return self.lineEdit_component_name.text().encode("ascii", "ignore").decode()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_selected_components(self) -> list[Component]:
        if len(self.listWidget_components.selectedItems()) == 0 or not self.selected_component:
            return []
        selected_components: list[Component] = []
        for list_item in self.listWidget_components.selectedItems():
            selected_components.append(self.components_inventory.get_component_by_part_name(list_item.text()))
        return selected_components
