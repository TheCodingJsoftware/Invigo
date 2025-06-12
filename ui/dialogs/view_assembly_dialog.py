from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog, QPushButton, QTableWidgetItem, QWidget

from ui.dialogs.view_assembly_dialog_UI import Ui_Form
from ui.icons import Icons
from ui.theme import theme_var
from utils.colors import get_contrast_text_color, lighten_color
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.structural_profile import StructuralProfile
from utils.workspace.assembly import Assembly
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class ViewAssemblyDialog(QDialog, Ui_Form):
    def __init__(self, assembly: Assembly, workspace: Workspace, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.assembly = assembly
        self.workspace = workspace
        self.laser_cut_inventory = self.workspace.laser_cut_inventory

        self.label_assembly_image.setPixmap(QPixmap(self.assembly.assembly_image))
        self.label_assembly_name.setText(self.assembly.name)

        self.parent: MainWindow = parent
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.verticalLayout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_8.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_12.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_components, self.widget_components
        )
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_laser_cut_parts, self.widget_laser_cut_parts
        )
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_structural_steel_items, self.widget_structural_steel_items
        )

        self.load_structural_steel_items_table()
        self.load_components_table()
        self.load_laser_cut_parts_table()

        self.setWindowTitle(self.assembly.name)

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = self.assembly.color
        hover_color = lighten_color(base_color)
        font_color = get_contrast_text_color(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            f"""
            QPushButton#assembly_button_drop_menu {{
                border: 1px solid {theme_var('surface')};
                background-color: {theme_var('surface')};
                border-radius: {theme_var('border-radius')};
                text-align: left;
            }}
            /* CLOSED */
            QPushButton:!checked#assembly_button_drop_menu {{
                color: {theme_var('on-surface')};
                border: 1px solid {theme_var('outline')};
            }}

            QPushButton:!checked:hover#assembly_button_drop_menu {{
                background-color: {theme_var('outline-variant')};
            }}
            QPushButton:!checked:pressed#assembly_button_drop_menu{{
                color: {theme_var('on-surface')};
                background-color: {theme_var('surface')};
            }}
            /* OPENED */
            QPushButton:checked#assembly_button_drop_menu {{
                color: {font_color};
                border-color: {base_color};
                background-color: {base_color};
                border-top-left-radius: {theme_var('border-radius')};
                border-top-right-radius: {theme_var('border-radius')};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}

            QPushButton:checked:hover#assembly_button_drop_menu {{
                background-color: {hover_color};
            }}

            QPushButton:checked:pressed#assembly_button_drop_menu {{
                background-color: {base_color};
            }}"""
        )
        widget.setObjectName("assembly_widget_drop_menu")
        widget.setStyleSheet(
            f"""QWidget#assembly_widget_drop_menu{{
            border: 1px solid {base_color};
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            background-color: {theme_var('background')};
            }}"""
        )

    def add_component_to_table(self, component: Component):
        current_row = self.tableWidget_components.rowCount()
        new_height = 70
        self.tableWidget_components.insertRow(current_row)
        image_item = QTableWidgetItem("")
        if component.image_path:
            image = QPixmap(component.image_path)
            original_width = image.width()
            original_height = image.height()
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(
                new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio
            )
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        self.tableWidget_components.setRowHeight(current_row, new_height)
        self.tableWidget_components.setItem(current_row, 0, image_item)
        self.tableWidget_components.setItem(
            current_row, 1, QTableWidgetItem(component.name)
        )
        self.tableWidget_components.setItem(
            current_row, 2, QTableWidgetItem(f"{component.quantity}")
        )

    def load_components_table(self):
        self.tableWidget_components.setRowCount(0)
        for component in self.assembly.components:
            self.add_component_to_table(component)
        # self.tableWidget_components.setFixedHeight(
        #     (len(self.assembly.components) + 1) * 70
        # )
        self.tableWidget_components.resizeColumnsToContents()

    def add_structural_steel_item_to_table(self, structural_steel_item: StructuralProfile):
        current_row = self.tableWidget_structural_steel_items.rowCount()
        new_height = 70
        self.tableWidget_structural_steel_items.insertRow(current_row)
        self.tableWidget_components.setRowHeight(current_row, new_height)
        self.tableWidget_structural_steel_items.setItem(
            current_row, 0, QTableWidgetItem(structural_steel_item.name)
        )
        self.tableWidget_structural_steel_items.setItem(
            current_row, 1, QTableWidgetItem(f"{structural_steel_item.quantity}")
        )
        self.tableWidget_structural_steel_items.setItem(
            current_row, 2, QTableWidgetItem(f"{structural_steel_item.quantity}")
        )

    def load_structural_steel_items_table(self):
        self.tableWidget_structural_steel_items.setRowCount(0)
        for structural_steel_item in self.assembly.structural_steel_items:
            self.add_structural_steel_item_to_table(structural_steel_item)
        # self.tableWidget_structural_steel_items.setFixedHeight(
        #     (len(self.assembly.components) + 1) * 70
        # )
        self.tableWidget_structural_steel_items.resizeColumnsToContents()


    def add_laser_cut_part_to_table(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        current_row = self.tableWidget_laser_cut_parts.rowCount()
        new_height = 70
        self.tableWidget_laser_cut_parts.insertRow(current_row)
        # PICTURE
        image_item = QTableWidgetItem("")
        if laser_cut_part_group.base_part.image_index:
            image = QPixmap(laser_cut_part_group.base_part.image_index)
            original_width = image.width()
            original_height = image.height()
            try:
                new_width = int(original_width * (new_height / original_height))
            except ZeroDivisionError:
                new_width = 0
            pixmap = image.scaled(
                new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio
            )
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        self.tableWidget_laser_cut_parts.setRowHeight(current_row, new_height)
        self.tableWidget_laser_cut_parts.setItem(current_row, 0, image_item)
        # NAME
        self.tableWidget_laser_cut_parts.setItem(
            current_row, 1, QTableWidgetItem(laser_cut_part_group.base_part.name)
        )
        # MATERIAL
        self.tableWidget_laser_cut_parts.setItem(
            current_row,
            2,
            QTableWidgetItem(f"{laser_cut_part_group.base_part.gauge} {laser_cut_part_group.base_part.material}"),
        )
        # FILES
        self.tableWidget_laser_cut_parts.setItem(
            current_row, 3, QTableWidgetItem("TODO: FILES_WIDGET")
        )
        # QUANTITY
        self.tableWidget_laser_cut_parts.setItem(
            current_row, 4, QTableWidgetItem(f"{laser_cut_part_group.get_quantity()}")
        )
        self.tableWidget_laser_cut_parts.item(current_row, 4).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # QUANTITY IN STOCK
        if inventory_part := self.laser_cut_inventory.get_laser_cut_part_by_name(
            laser_cut_part_group.base_part.name
        ):
            quantity_in_stock = inventory_part.quantity
        else:
            quantity_in_stock = 0
        self.tableWidget_laser_cut_parts.setItem(
            current_row, 5, QTableWidgetItem(f"{quantity_in_stock}")
        )
        self.tableWidget_laser_cut_parts.item(current_row, 5).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        # CURRENT FLOW TAG
        current_process = ""
        if laser_cut_part_group.base_part.recut:
            current_process = "Part is a Recut"
        elif laser_cut_part_group.base_part.recoat:
            current_process = "Part is a Recoat"
        elif laser_cut_part_group.base_part.is_process_finished():
            current_process = "Part is Finished"
        else:
            current_process = f"Part is currently in {laser_cut_part_group.get_current_tag().name}"

        # PROCESS TAG
        self.tableWidget_laser_cut_parts.setItem(
            current_row,
            6,
            QTableWidgetItem(f"{laser_cut_part_group.base_part.flowtag.get_flow_string()}\n\n{current_process}"),
        )
        # RECUT BUTTON
        self.tableWidget_laser_cut_parts.setItem(
            current_row, 7, QTableWidgetItem("TODO: RECUT_BUTTON")
        )
        # RECOAT BUTTON
        self.tableWidget_laser_cut_parts.setItem(
            current_row, 8, QTableWidgetItem("TODO: RECOAT_BUTTON")
        )

    def load_laser_cut_parts_table(self):
        self.tableWidget_laser_cut_parts.setRowCount(0)
        grouped_laser_cut_parts = self.workspace.get_grouped_laser_cut_parts(self.assembly.laser_cut_parts)
        for laser_cut_part_group in grouped_laser_cut_parts:
            self.add_laser_cut_part_to_table(laser_cut_part_group)
        # self.tableWidget_laser_cut_parts.setFixedHeight(
        #     (self.tableWidget_laser_cut_parts.rowCount() + 1) * 70
        # )
        self.tableWidget_laser_cut_parts.resizeColumnsToContents()

    def sync_changes(self):
        self.parent.sync_changes()
