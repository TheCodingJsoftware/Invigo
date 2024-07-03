from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QCompleter, QDialog

from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.settings import Settings

settings_file = Settings()


class AddWorkspaceItem(QDialog):
    def __init__(
        self,
        components_inventory: ComponentsInventory,
        laser_cut_inventory: LaserCutInventory,
        parent=None,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/add_workspace_item.ui", self)

        self.components_inventory = components_inventory
        self.laser_cut_inventory = laser_cut_inventory

        self.thickness = ""
        self.material = ""

        self.setWindowTitle("Add Workspace Item")
        self.setWindowIcon(QIcon("icons/icon.png"))

        all_part_names = natsorted(self.get_all_part_names())

        completer = QCompleter(all_part_names, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.lineEdit_name.setCompleter(completer)
        self.lineEdit_name.textChanged.connect(self.name_changed)

        self.listWidget_all_items.itemSelectionChanged.connect(
            self.listWidget_item_changed
        )
        self.listWidget_all_items.addItems(all_part_names)

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def listWidget_item_changed(self) -> None:
        self.lineEdit_name.setText(self.listWidget_all_items.currentItem().text())
        self.thickness = ""
        self.material = ""
        for laser_cut_part in self.laser_cut_inventory.laser_cut_parts:
            if laser_cut_part.name == self.lineEdit_name.text():
                self.thickness = laser_cut_part.gauge
                self.material = laser_cut_part.material
                break

    def name_changed(self) -> None:
        all_part_names = natsorted(self.get_all_part_names())
        for part_name in all_part_names:
            if part_name == self.lineEdit_name.text():
                index = all_part_names.index(part_name)
                self.listWidget_all_items.setCurrentRow(index)
                break

    def get_name(self) -> str:
        return self.lineEdit_name.text().encode("ascii", "ignore").decode()

    def get_all_part_names(self) -> list[str]:
        return (
            self.components_inventory.get_all_part_names()
            + self.laser_cut_inventory.get_all_part_names()
        )
