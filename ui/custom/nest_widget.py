import os
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from ui.add_sheet_dialog import AddSheetDialog
from ui.custom.machine_cut_time_double_spin_box import MachineCutTimeDoubleSpinBox
from utils.inventory.sheets_inventory import Sheet, SheetsInventory
from utils.quote.nest import Nest

if TYPE_CHECKING:
    from ui.custom.job_widget import JobWidget


class NestWidget(QWidget):
    updateNestSummary = pyqtSignal()
    updateLaserCutPartSettings = pyqtSignal(Nest)

    def __init__(self, nest: Nest, parent: QWidget) -> None:
        super(NestWidget, self).__init__(parent)
        uic.loadUi("ui/nest_widget.ui", self)

        self.parent: JobWidget = parent
        self.nest = nest
        self.sheets_inventory = self.parent.parent.job_manager.sheets_inventory
        self.sheet_settings = self.parent.parent.job_manager.sheet_settings

        self.load_ui()

    def load_ui(self):
        self.label_sheet_status = self.findChild(QLabel, "label_sheet_status")
        self.pushButton_add_sheet = self.findChild(QPushButton, "pushButton_add_sheet")
        self.pushButton_add_sheet.clicked.connect(self.add_new_sheet_to_inventory)
        self.label_scrap_percentage = self.findChild(QLabel, "label_scrap_percentage")
        self.label_cost_for_sheets = self.findChild(QLabel, "label_cost_for_sheets")
        self.label_cutting_cost = self.findChild(QLabel, "label_cutting_cost")
        self.verticalLayout_sheet_cut_time = self.findChild(QVBoxLayout, "verticalLayout_sheet_cut_time")
        self.doubleSpinBox_sheet_cut_time = MachineCutTimeDoubleSpinBox(self)
        self.verticalLayout_sheet_cut_time.addWidget(self.doubleSpinBox_sheet_cut_time)
        self.label_nest_cut_time = self.findChild(QLabel, "label_nest_cut_time")
        self.doubleSpinBox_sheet_count = self.findChild(QDoubleSpinBox, "doubleSpinBox_sheet_count")
        self.comboBox_material = self.findChild(QComboBox, "comboBox_material")
        self.comboBox_thickness = self.findChild(QComboBox, "comboBox_thickness")
        self.doubleSpinBox_length = self.findChild(QDoubleSpinBox, "doubleSpinBox_length")
        self.doubleSpinBox_width = self.findChild(QDoubleSpinBox, "doubleSpinBox_width")
        self.label_image = self.findChild(QLabel, "label_image")
        self.update_sheet_status()

    def add_new_sheet_to_inventory(self):
        add_sheet_dialog = AddSheetDialog(self.nest, None, self.sheets_inventory, self.sheet_settings, self)

        if add_sheet_dialog.exec():
            new_sheet = Sheet(
                "new_name",
                {
                    "quantity": add_sheet_dialog.get_quantity(),
                    "length": add_sheet_dialog.get_length(),
                    "width": add_sheet_dialog.get_width(),
                    "thickness": add_sheet_dialog.get_thickness(),
                    "material": add_sheet_dialog.get_material(),
                    "latest_change_quantity": f'{os.getlogin().title()} - Sheet was added via quote generator at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}',
                },
                self.sheets_inventory,
            )
            new_sheet.add_to_category(self.sheets_inventory.get_category(add_sheet_dialog.get_category()))
            for sheet in self.sheets_inventory.sheets:
                if new_sheet.get_name() == sheet.get_name():
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setWindowTitle("Exists")
                    msg.setText(f"'{new_sheet.get_name()}'\nAlready exists.")
                    msg.exec()
                    return
            self.sheet = new_sheet
            self.comboBox_thickness.setCurrentText(new_sheet.thickness)
            self.comboBox_material.setCurrentText(new_sheet.material)
            self.doubleSpinBox_length.setValue(new_sheet.length)
            self.doubleSpinBox_width.setValue(new_sheet.width)
            for laser_cut_part in self.nest.laser_cut_parts:
                laser_cut_part.gauge = new_sheet.thickness
                laser_cut_part.material = new_sheet.material
            self.updateLaserCutPartSettings.emit(self)
            self.sheets_inventory.add_sheet(new_sheet)
            self.sheets_inventory.save()
            self.sync_changes()
            self.changes_made()
            # self.nests_tool_box.setItemText(self.nest_items[nest]["tab_index"], nest.get_name())
            # self.update_laser_cut_parts_price()
            # self.update_scrap_percentage()
            # self.update_sheet_price()
            # self.load_nest_summary()
            self.update_sheet_status()

    def update_cutting_time(self):
        self.label_nest_cut_time.setText(self.nest.get_total_cutting_time())

    def update_sheet_status(self):
        if self.sheets_inventory.exists(self.nest.sheet):
            self.pushButton_add_sheet.setHidden(True)
            if sheet := self.sheets_inventory.get_sheet_by_name(self.nest.sheet.get_name()):
                self.label_sheet_status.setText(f"This sheet exists in sheets inventory with {sheet.quantity} in stock.")
        else:
            self.pushButton_add_sheet.setHidden(False)
            self.label_sheet_status.setText("This sheet does not exist in sheets inventory.")

    def sync_changes(self):
        self.parent.parent.sync_changes()

    def changes_made(self):
        self.parent.changes_made()
