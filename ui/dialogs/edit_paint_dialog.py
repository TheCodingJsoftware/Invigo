from PyQt6.QtWidgets import QDialog

from ui.dialogs.edit_paint_dialog_UI import Ui_Dialog
from utils.inventory.laser_cut_inventory import LaserCutInventory


class EditPaintDialog(QDialog, Ui_Dialog):
    def __init__(self, laser_cut_inventory: LaserCutInventory, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.laser_cut_inventory = laser_cut_inventory
        self.paint_inventory = self.laser_cut_inventory.paint_inventory

        self.pushButton_apply.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.comboBox_paint.addItems(["None"] + [paint.name for paint in self.paint_inventory.paints])
        self.comboBox_primer.addItems(["None"] + [primer.name for primer in self.paint_inventory.primers])
        self.comboBox_powder.addItems(["None"] + [powder.name for powder in self.paint_inventory.powders])

    def uses_paint(self) -> bool:
        return self.checkBox_paint.isChecked()

    def get_paint(self) -> dict:
        paint_name = self.comboBox_paint.currentText()
        return {
            "paint_name": "" if paint_name == "None" else paint_name,
            "uses_paint": self.checkBox_paint.isChecked(),
            "paint_overspray": self.doubleSpinBox_paint_overspray.value(),
            "paint_item": None if paint_name == "None" else self.paint_inventory.get_paint(paint_name),
        }

    def uses_primer(self) -> bool:
        return self.checkBox_primer.isChecked()

    def get_primer(self) -> dict:
        primer_name = self.comboBox_primer.currentText()
        return {
            "primer_name": "" if primer_name == "None" else primer_name,
            "uses_primer": self.checkBox_primer.isChecked(),
            "primer_overspray": self.doubleSpinBox_primer_overspray.value(),
            "primer_item": None if primer_name == "None" else self.paint_inventory.get_primer(primer_name),
        }

    def uses_powder(self) -> bool:
        return self.checkBox_powder.isChecked()

    def get_powder(self) -> dict:
        powder_name = self.comboBox_powder.currentText()
        return {
            "powder_name": "" if powder_name == "None" else powder_name,
            "uses_powder": self.checkBox_powder.isChecked(),
            "powder_transfer_efficiency": self.doubleSpinBox_powder_transfer_efficiency.value(),
            "powder_item": None if powder_name == "None" else self.paint_inventory.get_powder(powder_name),
        }
