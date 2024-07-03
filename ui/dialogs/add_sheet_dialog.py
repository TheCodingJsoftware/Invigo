from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from utils.inventory.category import Category
from utils.inventory.sheet import Sheet
from utils.inventory.sheets_inventory import SheetsInventory
from utils.sheet_settings.sheet_settings import SheetSettings


class AddSheetDialog(QDialog):
    def __init__(
        self,
        sheet: Sheet,
        category: Category,
        sheets_inventory: SheetsInventory,
        sheet_settings: SheetSettings,
        parent=None,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/add_sheet_dialog.ui", self)

        self.sheet_settings = sheet_settings
        self.category = category
        self.sheet = sheet
        self.sheets_inventory = sheets_inventory

        self.setWindowTitle("Add sheet")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)
        self.comboBox_categories.addItems(
            [category.name for category in self.sheets_inventory.get_categories()]
        )
        if category:
            self.comboBox_categories.setCurrentText(category.name)
        self.lineEdit_material.addItems(self.sheet_settings.get_materials())
        self.comboBox_thickness.addItems(self.sheet_settings.get_thicknesses())

        if self.sheet:
            self.lineEdit_material.setCurrentText(sheet.material)
            self.comboBox_thickness.setCurrentText(sheet.thickness)
            self.doubleSpinBox_length.setValue(sheet.length)
            self.doubleSpinBox_width.setValue(sheet.width)

    def get_length(self) -> float:
        return self.doubleSpinBox_length.value()

    def get_width(self) -> float:
        return self.doubleSpinBox_width.value()

    def get_material(self) -> str:
        return self.lineEdit_material.currentText()

    def get_thickness(self) -> str:
        return self.comboBox_thickness.currentText()

    def get_quantity(self) -> int:
        return self.spinBox_current_quantity.value()

    def get_category(self) -> str:
        return self.comboBox_categories.currentText()
