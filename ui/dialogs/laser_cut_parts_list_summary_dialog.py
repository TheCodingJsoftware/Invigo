import os
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QScrollArea, QComboBox, QMessageBox

from functools import partial

from ui.custom.file_button import FileButton
from ui.custom.flowtag_data_widget import FlowtagDataButton
from ui.custom.laser_cut_part_file_drop_widget import LaserCutPartFileDropWidget
from ui.custom.laser_cut_part_paint_settings_widget import LasserCutPartPaintSettingsWidget
from ui.custom.laser_cut_part_paint_widget import LaserCutPartPaintWidget
from ui.custom.laser_cut_parts_planning_table_widget import LaserCutPartsPlanningTableWidget, LaserCutTableColumns
from ui.dialogs.laser_cut_parts_list_summary_dialog_UI import Ui_Form
from ui.icons import Icons
from ui.theme import theme_var
from ui.windows.pdf_viewer import PDFViewer
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.threads.workspace_upload_file_thread import WorkspaceUploadThread
from utils.workspace.assembly import Assembly
from ui.custom.laser_cut_part_files_widget import LaserCutPartFilesWidget


class LaserCutPartsListSummaryTable(LaserCutPartsPlanningTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        columns_to_hide = [LaserCutTableColumns.PAINTING, LaserCutTableColumns.PAINT_SETTINGS, LaserCutTableColumns.FLOW_TAG, LaserCutTableColumns.FLOW_TAG_DATA]
        self.hide_columns(columns_to_hide)


class LaserCutPartsListSummaryDialog(QDialog, Ui_Form):
    def __init__(self, assemblies: list[Assembly], parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.assemblies = assemblies
        self.setWindowTitle("Laser Cut Parts List Summary")
        self.setWindowIcon(QIcon(Icons.invigo_icon))
        self.laser_cut_parts_table = LaserCutPartsListSummaryTable(self)
        self.table_layout.addWidget(self.laser_cut_parts_table)
        self.laser_cut_part_table_items: dict[LaserCutPart, dict[str, QTableWidgetItem | QComboBox | QWidget | int | FlowtagDataButton]] = {}

        self.settings_file = Settings()

        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.resize(1000, 500)
        self.load_laser_cut_parts_table()

    def load_laser_cut_parts_table(self):
        self.laser_cut_parts_table.blockSignals(True)
        self.laser_cut_part_table_items.clear()
        self.laser_cut_parts_table.setRowCount(0)
        for assembly in self.assemblies:
            for laser_cut_part in assembly.get_all_laser_cut_parts():
                self.add_laser_cut_part_to_table(laser_cut_part, assembly.quantity)
        self.laser_cut_parts_table.blockSignals(False)
        self.laser_cut_parts_table.resizeColumnsToContents()
        self.laser_cut_parts_table.resizeRowsToContents()

    def add_laser_cut_part_to_table(self, laser_cut_part: LaserCutPart, assembly_quantity: int):
        current_row = self.laser_cut_parts_table.rowCount()
        self.laser_cut_part_table_items.update({laser_cut_part: {}})
        self.laser_cut_part_table_items[laser_cut_part].update({"row": current_row})
        self.laser_cut_parts_table.insertRow(current_row)
        self.laser_cut_parts_table.setRowHeight(current_row, self.laser_cut_parts_table.row_height)

        image_item = QTableWidgetItem()
        try:
            if "images" not in laser_cut_part.image_index:
                laser_cut_part.image_index = "images/" + laser_cut_part.image_index
            if not laser_cut_part.image_index.endswith(".jpeg"):
                laser_cut_part.image_index += ".jpeg"
            image = QPixmap(laser_cut_part.image_index)
            if image.isNull():
                image = QPixmap("images/404.jpeg")
            original_width = image.width()
            original_height = image.height()
            new_height = self.laser_cut_parts_table.row_height
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        except Exception as e:
            image_item.setText(f"Error: {e}")
        self.laser_cut_parts_table.setRowHeight(current_row, new_height)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PICTURE.value, image_item)

        part_name_item = QTableWidgetItem(laser_cut_part.name)
        part_name_item.setFont(self.tables_font)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PART_NAME.value, part_name_item)

        # Files
        bending_files_widget = LaserCutPartFilesWidget(laser_cut_part, ["bending_files"], self)
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.BENDING_FILES.value,
            bending_files_widget,
        )

        cnc_milling_files_widget = LaserCutPartFilesWidget(laser_cut_part, ["cnc_milling_files"], self)
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.CNC_MILLING_FILES.value,
            cnc_milling_files_widget,
        )
        welding_files_widget = LaserCutPartFilesWidget(laser_cut_part, ["welding_files"], self)
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.WELDING_FILES.value,
            welding_files_widget,
        )

        material_item = QTableWidgetItem(laser_cut_part.material)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.MATERIAL.value, material_item)

        thickness_item = QTableWidgetItem(laser_cut_part.gauge)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.THICKNESS.value, thickness_item)

        notes_item = QTableWidgetItem(laser_cut_part.notes)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.NOTES.value, notes_item)

        shelf_number_item = QTableWidgetItem(laser_cut_part.shelf_number)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.SHELF_NUMBER.value, shelf_number_item)

        unit_quantity_item = QTableWidgetItem(f"{int(laser_cut_part.quantity):,}")
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.UNIT_QUANTITY.value, unit_quantity_item)

        quantity_item = QTableWidgetItem(f"{int(laser_cut_part.quantity * assembly_quantity):,}")
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.QUANTITY.value, quantity_item)
