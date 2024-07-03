import os
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from ui.custom.machine_cut_time_double_spin_box import MachineCutTimeDoubleSpinBox
from ui.dialogs.add_sheet_dialog import AddSheetDialog
from utils.inventory.sheets_inventory import Sheet
from utils.quote.nest import Nest

if TYPE_CHECKING:
    from ui.custom.job_widget import JobWidget


class NestWidget(QWidget):
    updateNestSummary = pyqtSignal()
    updateLaserCutPartSettings = pyqtSignal(Nest)

    def __init__(self, nest: Nest, parent: QWidget) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/nest_widget.ui", self)

        self.parent: JobWidget = parent
        self.nest = nest
        self.sheet = self.nest.sheet
        self.sheets_inventory = self.parent.parent.job_manager.sheets_inventory
        self.sheet_settings = self.parent.parent.job_manager.sheet_settings

        self.load_ui()

    def load_ui(self):
        self.label_sheet_status = self.findChild(QLabel, "label_sheet_status")

        self.pushButton_add_sheet = self.findChild(QPushButton, "pushButton_add_sheet")
        self.pushButton_add_sheet.clicked.connect(self.add_new_sheet_to_inventory)

        self.label_scrap_percentage = self.findChild(QLabel, "label_scrap_percentage")
        self.label_scrap_percentage.setText(f"{self.nest.scrap_percentage:,.2f}%")

        self.label_cost_for_sheets = self.findChild(QLabel, "label_cost_for_sheets")

        self.label_cutting_cost = self.findChild(QLabel, "label_cutting_cost")

        self.verticalLayout_sheet_cut_time = self.findChild(
            QVBoxLayout, "verticalLayout_sheet_cut_time"
        )

        self.doubleSpinBox_sheet_cut_time = MachineCutTimeDoubleSpinBox(self)
        self.doubleSpinBox_sheet_cut_time.wheelEvent = lambda event: None
        self.doubleSpinBox_sheet_cut_time.setValue(self.nest.sheet_cut_time)
        self.doubleSpinBox_sheet_cut_time.setToolTip(
            f"Original: {self.get_sheet_cut_time()}"
        )
        self.verticalLayout_sheet_cut_time.addWidget(self.doubleSpinBox_sheet_cut_time)

        self.label_nest_cut_time = self.findChild(QLabel, "label_nest_cut_time")

        self.doubleSpinBox_sheet_count = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_sheet_count"
        )
        self.doubleSpinBox_sheet_count.wheelEvent = lambda event: None

        self.comboBox_material = self.findChild(QComboBox, "comboBox_material")
        self.comboBox_material.wheelEvent = lambda event: None
        self.comboBox_material.addItems(self.sheet_settings.get_materials())
        self.comboBox_material.setCurrentText(self.sheet.material)
        self.comboBox_material.currentTextChanged.connect(self.sheet_changed)

        self.comboBox_thickness = self.findChild(QComboBox, "comboBox_thickness")
        self.comboBox_thickness.wheelEvent = lambda event: None
        self.comboBox_thickness.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_thickness.setCurrentText(self.sheet.thickness)
        self.comboBox_thickness.currentTextChanged.connect(self.sheet_changed)

        self.doubleSpinBox_length = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_length"
        )
        self.doubleSpinBox_length.wheelEvent = lambda event: None
        self.doubleSpinBox_length.setValue(self.sheet.length)
        self.doubleSpinBox_length.valueChanged.connect(self.sheet_changed)

        self.doubleSpinBox_width = self.findChild(QDoubleSpinBox, "doubleSpinBox_width")
        self.doubleSpinBox_width.wheelEvent = lambda event: None
        self.doubleSpinBox_width.setValue(self.sheet.width)
        self.doubleSpinBox_width.valueChanged.connect(self.sheet_changed)

        self.image_widget = self.findChild(QWidget, "image_widget")
        self.image_widget.setHidden(True)

        self.label_image = self.findChild(QLabel, "label_image")
        if "404" not in self.nest.image_path:
            self.image_widget.setHidden(False)
            self.label_image.setFixedSize(485, 345)
            pixmap = QPixmap(self.nest.image_path)
            scaled_pixmap = pixmap.scaled(
                self.label_image.size(),
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            )
            self.label_image.setPixmap(scaled_pixmap)

        self.update_sheet_status()

    def update_ui_values(self):
        self.doubleSpinBox_length.blockSignals(True)
        self.doubleSpinBox_width.blockSignals(True)
        self.comboBox_thickness.blockSignals(True)
        self.comboBox_material.blockSignals(True)
        self.doubleSpinBox_length.setValue(self.sheet.length)
        self.doubleSpinBox_width.setValue(self.sheet.width)
        self.comboBox_thickness.setCurrentText(self.sheet.thickness)
        self.comboBox_material.setCurrentText(self.sheet.material)
        self.doubleSpinBox_length.blockSignals(False)
        self.doubleSpinBox_width.blockSignals(False)
        self.comboBox_thickness.blockSignals(False)
        self.comboBox_material.blockSignals(False)

    def sheet_changed(self):
        self.sheet.length = self.doubleSpinBox_length.value()
        self.sheet.width = self.doubleSpinBox_width.value()
        self.sheet.material = self.comboBox_material.currentText()
        self.sheet.thickness = self.comboBox_thickness.currentText()

    def nest_changed(self):
        self.nest.sheet_count = self.doubleSpinBox_sheet_count.value()
        self.nest.sheet_cut_time = self.doubleSpinBox_sheet_cut_time.value()
        self.update_nest_cut_time()

    def set_cost_for_sheets(self, cost: float):
        self.label_cost_for_sheets.setText(f"${cost:,.2f}")

    def set_cutting_cost(self, cost: float):
        self.label_cutting_cost.setText(f"${cost:,.2f}")

    def update_nest_cut_time(self):
        self.label_nest_cut_time.setText(self.get_total_cutting_time())

    def get_sheet_cut_time(self) -> str:
        total_seconds = self.nest.sheet_cut_time
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def get_total_cutting_time(self) -> str:
        total_seconds = self.nest.sheet_cut_time * self.nest.sheet_count
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def add_new_sheet_to_inventory(self):
        add_sheet_dialog = AddSheetDialog(
            self.sheet, None, self.sheets_inventory, self.sheet_settings, self
        )

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
            new_sheet.add_to_category(
                self.sheets_inventory.get_category(add_sheet_dialog.get_category())
            )
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
            if sheet := self.sheets_inventory.get_sheet_by_name(
                self.nest.sheet.get_name()
            ):
                self.label_sheet_status.setText(
                    f"This sheet exists in sheets inventory with {sheet.quantity} in stock."
                )
        else:
            self.pushButton_add_sheet.setHidden(False)
            self.label_sheet_status.setText(
                "This sheet does not exist in sheets inventory."
            )

    def sync_changes(self):
        self.parent.parent.sync_changes()

    def changes_made(self):
        self.parent.changes_made()
