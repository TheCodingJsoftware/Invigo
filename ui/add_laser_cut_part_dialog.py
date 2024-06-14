from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QListWidget

from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings


class AddLaserCutPartDialog(QDialog):
    def __init__(self, parent) -> None:
        super(AddLaserCutPartDialog, self).__init__(parent)
        uic.loadUi("ui/add_laser_cut_part_dialog.ui", self)
        self.parent = parent

        self.laser_cut_inventory: LaserCutInventory = self.parent.laser_cut_inventory
        self.selected_laser_cut_part: LaserCutPart = None

        self.setWindowTitle("Add New Laser Cut Part")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.comboBox_name: QComboBox
        self.listWidget_laser_cut_parts: QListWidget

        self.comboBox_name.addItems(natsorted(self.laser_cut_inventory.get_all_part_names()))
        self.comboBox_name.setCurrentText("")
        self.comboBox_name.lineEdit().textChanged.connect(self.name_changed)

        self.listWidget_laser_cut_parts.addItems(natsorted(self.laser_cut_inventory.get_all_part_names()))
        self.listWidget_laser_cut_parts.currentTextChanged.connect(self.selection_changed)
        self.label_laser_cut_part_status.setStyleSheet("color: #E74E4E;")
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def selection_changed(self):
        for laser_cut_part in self.laser_cut_inventory.laser_cut_parts:
            if laser_cut_part.name == self.listWidget_laser_cut_parts.currentItem().text():
                self.comboBox_name.lineEdit().blockSignals(True)
                self.comboBox_name.setCurrentText(laser_cut_part.name)
                self.comboBox_name.lineEdit().blockSignals(False)
                self.label_laser_cut_part_status.setStyleSheet("color: #4EE753;")
                self.label_laser_cut_part_status.setText(" * Laser Cut Part exists in inventory.")
                self.selected_laser_cut_part = laser_cut_part
                return
            else:
                self.label_laser_cut_part_status.setStyleSheet("color: #E74E4E;")
                self.label_laser_cut_part_status.setText(" * Laser Cut Part does NOT exists in inventory.")
                self.selected_laser_cut_part = None

    def get_laser_cut_part_row(self, laser_cut_part_name: str) -> int:
        return next(
            (row for row in range(self.listWidget_laser_cut_parts.count()) if self.listWidget_laser_cut_parts.item(row).text() == laser_cut_part_name),
            0,
        )

    def name_changed(self) -> None:
        for laser_cut_part in self.laser_cut_inventory.laser_cut_parts:
            if laser_cut_part.name == self.comboBox_name.currentText():
                self.listWidget_laser_cut_parts.blockSignals(True)
                self.listWidget_laser_cut_parts.setCurrentRow(self.get_laser_cut_part_row(laser_cut_part.name))
                self.listWidget_laser_cut_parts.blockSignals(False)
                self.label_laser_cut_part_status.setStyleSheet("color: #4EE753;")
                self.label_laser_cut_part_status.setText(" * Laser Cut Part exists in inventory.")
                self.selected_laser_cut_part = laser_cut_part
                return
            else:
                self.label_laser_cut_part_status.setStyleSheet("color: #E74E4E;")
                self.label_laser_cut_part_status.setText(" * Laser Cut Part does NOT exists in inventory.")
                self.selected_laser_cut_part = None

    def get_name(self) -> str:
        return self.comboBox_name.currentText().encode("ascii", "ignore").decode()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_selected_laser_cut_part(self) -> LaserCutPart:
        return self.selected_laser_cut_part
