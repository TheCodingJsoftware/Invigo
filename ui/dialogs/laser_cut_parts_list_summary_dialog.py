from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QComboBox, QDialog, QTableWidgetItem, QWidget

from ui.custom.flowtag_data_widget import FlowtagDataButton
from ui.custom.laser_cut_part_files_widget import LaserCutPartFilesWidget
from ui.custom.laser_cut_parts_planning_table_widget import (
    LaserCutPartsPlanningTableWidget,
    LaserCutTableColumns,
)
from ui.dialogs.laser_cut_parts_list_summary_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.workspace.assembly import Assembly
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup


class LaserCutPartsListSummaryTable(LaserCutPartsPlanningTableWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        columns_to_hide = [
            LaserCutTableColumns.PAINTING,
            LaserCutTableColumns.PAINT_SETTINGS,
            LaserCutTableColumns.FLOW_TAG,
            LaserCutTableColumns.FLOW_TAG_DATA,
        ]
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
        self.laser_cut_part_table_items: dict[
            WorkspaceLaserCutPartGroup,
            dict[str, QTableWidgetItem | QComboBox | QWidget | int | FlowtagDataButton],
        ] = {}

        self.settings_file = Settings()

        self.tables_font = QFont()
        self.tables_font.setFamily(
            self.settings_file.get_value("tables_font")["family"]
        )
        self.tables_font.setPointSize(
            self.settings_file.get_value("tables_font")["pointSize"]
        )
        self.tables_font.setWeight(
            self.settings_file.get_value("tables_font")["weight"]
        )
        self.tables_font.setItalic(
            self.settings_file.get_value("tables_font")["italic"]
        )

        self.resize(1000, 500)
        self.load_laser_cut_parts_table()

    def group_laser_cut_parts(self) -> list[WorkspaceLaserCutPartGroup]:
        all_assembly_laser_cut_parts: dict[LaserCutPart, dict[str, int]] = {}
        grouped_laser_cut_parts: list[WorkspaceLaserCutPartGroup] = []
        for assembly in self.assemblies:
            for laser_cut_part in assembly.get_all_laser_cut_parts():
                all_assembly_laser_cut_parts.setdefault(laser_cut_part, {}).update(
                    {"assembly_quantity": assembly.quantity}
                )

        for laser_cut_part, part_data in all_assembly_laser_cut_parts.items():
            for workspace_laser_cut_part_group in grouped_laser_cut_parts:
                if workspace_laser_cut_part_group.base_part.name == laser_cut_part.name:
                    for _ in range(int(part_data["assembly_quantity"])):
                        workspace_laser_cut_part_group.add_laser_cut_part(
                            laser_cut_part
                        )
                    break
            else:
                grouped_laser_cut_parts.append(WorkspaceLaserCutPartGroup())
                for _ in range(int(part_data["assembly_quantity"])):
                    grouped_laser_cut_parts[-1].add_laser_cut_part(laser_cut_part)
        return grouped_laser_cut_parts

    def load_laser_cut_parts_table(self):
        self.laser_cut_parts_table.blockSignals(True)
        self.laser_cut_part_table_items.clear()
        self.laser_cut_parts_table.setRowCount(0)
        for workspace_laser_cut_part_group in self.group_laser_cut_parts():
            self.add_workspace_laser_cut_part_to_table(workspace_laser_cut_part_group)
        self.laser_cut_parts_table.blockSignals(False)
        self.laser_cut_parts_table.resizeColumnsToContents()
        self.laser_cut_parts_table.resizeRowsToContents()

    def add_workspace_laser_cut_part_to_table(
        self, workspace_laser_cut_part_group: WorkspaceLaserCutPartGroup
    ):
        current_row = self.laser_cut_parts_table.rowCount()
        self.laser_cut_part_table_items.update({workspace_laser_cut_part_group: {}})
        self.laser_cut_part_table_items[workspace_laser_cut_part_group].update(
            {"row": current_row}
        )
        self.laser_cut_parts_table.insertRow(current_row)
        self.laser_cut_parts_table.setRowHeight(
            current_row, self.laser_cut_parts_table.row_height
        )

        image_item = QTableWidgetItem()
        try:
            if "images" not in workspace_laser_cut_part_group.base_part.image_index:
                workspace_laser_cut_part_group.base_part.image_index = (
                    "images/" + workspace_laser_cut_part_group.base_part.image_index
                )
            if not workspace_laser_cut_part_group.base_part.image_index.endswith(
                ".jpeg"
            ):
                workspace_laser_cut_part_group.base_part.image_index += ".jpeg"
            image = QPixmap(workspace_laser_cut_part_group.base_part.image_index)
            if image.isNull():
                image = QPixmap("images/404.jpeg")
            original_width = image.width()
            original_height = image.height()
            new_width = int(
                original_width
                * (self.laser_cut_parts_table.row_height / original_height)
            )
            pixmap = image.scaled(
                new_width,
                self.laser_cut_parts_table.row_height,
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        except Exception as e:
            image_item.setText(f"Error: {e}")
        self.laser_cut_parts_table.setRowHeight(
            current_row, self.laser_cut_parts_table.row_height
        )
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.PICTURE.value, image_item
        )

        part_name_item = QTableWidgetItem(workspace_laser_cut_part_group.base_part.name)
        part_name_item.setFont(self.tables_font)
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.PART_NAME.value, part_name_item
        )

        # Files
        bending_files_widget = LaserCutPartFilesWidget(
            workspace_laser_cut_part_group, ["bending_files"], self
        )
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.BENDING_FILES.value,
            bending_files_widget,
        )

        cnc_milling_files_widget = LaserCutPartFilesWidget(
            workspace_laser_cut_part_group, ["cnc_milling_files"], self
        )
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.CNC_MILLING_FILES.value,
            cnc_milling_files_widget,
        )
        welding_files_widget = LaserCutPartFilesWidget(
            workspace_laser_cut_part_group, ["welding_files"], self
        )
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.WELDING_FILES.value,
            welding_files_widget,
        )

        material_item = QTableWidgetItem(
            workspace_laser_cut_part_group.base_part.material
        )
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.MATERIAL.value, material_item
        )

        thickness_item = QTableWidgetItem(
            workspace_laser_cut_part_group.base_part.gauge
        )
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.THICKNESS.value, thickness_item
        )

        notes_item = QTableWidgetItem(workspace_laser_cut_part_group.base_part.notes)
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.NOTES.value, notes_item
        )

        shelf_number_item = QTableWidgetItem(
            workspace_laser_cut_part_group.base_part.shelf_number
        )
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.SHELF_NUMBER.value, shelf_number_item
        )

        quantity_item = QTableWidgetItem(
            f"{int(workspace_laser_cut_part_group.get_quantity()):,}"
        )
        self.laser_cut_parts_table.setItem(
            current_row, LaserCutTableColumns.QUANTITY.value, quantity_item
        )
