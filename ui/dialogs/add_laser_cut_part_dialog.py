from natsort import natsorted
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QCompleter, QDialog

from ui.dialogs.add_laser_cut_part_dialog_UI import Ui_Form
from ui.icons import Icons
from ui.theme import theme_var
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart


class AddLaserCutPartDialog(QDialog, Ui_Form):
    def __init__(self, laser_cut_inventory: LaserCutInventory, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent

        self.laser_cut_inventory = laser_cut_inventory

        self.setWindowTitle("Add New Laser Cut Part")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.completer = QCompleter(
            natsorted(self.laser_cut_inventory.get_all_part_names())
        )
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setWidget(self.lineEdit_name)
        self.completer.activated.connect(self.handleCompletion)
        self.lineEdit_name.textChanged.connect(self.name_changed)
        self._completing = False

        self.listWidget_laser_cut_parts.addItems(
            natsorted(self.laser_cut_inventory.get_all_part_names())
        )
        self.listWidget_laser_cut_parts.currentTextChanged.connect(
            self.selection_changed
        )
        self.label_laser_cut_part_status.setStyleSheet(f"color: {theme_var('error')};")
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def handleCompletion(self, text):
        if not self._completing:
            self._completing = True
            prefix = self.completer.completionPrefix()
            self.lineEdit_name.setText(self.lineEdit_name.text()[: -len(prefix)] + text)
            self._completing = False

    def selection_changed(self):
        if len(self.listWidget_laser_cut_parts.selectedItems()) > 1:
            return
        for laser_cut_part in self.laser_cut_inventory.laser_cut_parts:
            if (
                laser_cut_part.name
                == self.listWidget_laser_cut_parts.currentItem().text()
            ):
                self.lineEdit_name.blockSignals(True)
                self.lineEdit_name.setText(laser_cut_part.name)
                self.lineEdit_name.blockSignals(False)
                self.label_laser_cut_part_status.setStyleSheet(
                    f"color: {theme_var('primary-green')};"
                )
                self.label_laser_cut_part_status.setText(
                    " * Laser Cut Part exists in inventory."
                )
                return
            else:
                self.label_laser_cut_part_status.setStyleSheet(
                    f"color: {theme_var('error')};"
                )
                self.label_laser_cut_part_status.setText(
                    " * Laser Cut Part does NOT exists in inventory."
                )

    def get_laser_cut_part_row(self, laser_cut_part_name: str) -> int:
        return next(
            (
                row
                for row in range(self.listWidget_laser_cut_parts.count())
                if self.listWidget_laser_cut_parts.item(row).text()
                == laser_cut_part_name
            ),
            0,
        )

    def name_changed(self, text: str):
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
        self.label_laser_cut_part_status.setStyleSheet(f"color: {theme_var('error')};")
        self.listWidget_laser_cut_parts.blockSignals(True)
        self.listWidget_laser_cut_parts.clear()
        for name in self.laser_cut_inventory.get_all_part_names():
            if text.lower() in name.lower():
                new_parts_last.append(name)
        self.listWidget_laser_cut_parts.addItems(new_parts_last)
        self.listWidget_laser_cut_parts.blockSignals(False)

    def get_name(self) -> str:
        return self.lineEdit_name.text().encode("ascii", "ignore").decode()

    def get_current_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_selected_laser_cut_parts(self) -> list[LaserCutPart]:
        if len(self.listWidget_laser_cut_parts.selectedItems()) == 0:
            return []
        selected_laser_cut_parts: list[LaserCutPart] = []
        for list_item in self.listWidget_laser_cut_parts.selectedItems():
            selected_laser_cut_parts.append(
                self.laser_cut_inventory.get_laser_cut_part_by_name(list_item.text())
            )
        return selected_laser_cut_parts
