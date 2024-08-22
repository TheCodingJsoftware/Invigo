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
from utils.workspace.assembly import Assembly
from utils.workspace.workspace import Workspace

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class ViewAssemblyDialog(QDialog, Ui_Form):
    def __init__(self, assembly: Assembly, workspace: Workspace, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.assembly = assembly
        self.workspace = workspace

        self.label_assembly_image.setPixmap(QPixmap(self.assembly.assembly_image))
        self.label_assembly_name.setText(self.assembly.name)

        self.parent: MainWindow = parent
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.apply_stylesheet_to_toggle_buttons(self.pushButton_components, self.widget_components)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_laser_cut_parts, self.widget_laser_cut_parts)

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
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        self.tableWidget_components.setRowHeight(current_row, new_height)
        self.tableWidget_components.setItem(current_row, 0, image_item)
        self.tableWidget_components.setItem(current_row, 1, QTableWidgetItem(component.name))
        self.tableWidget_components.setItem(current_row, 2, QTableWidgetItem(f"{component.quantity}"))

    def load_components_table(self):
        self.tableWidget_components.setRowCount(0)
        for component in self.assembly.components:
            self.add_component_to_table(component)
        self.tableWidget_components.setFixedHeight((len(self.assembly.components) + 1) * 70)
        self.tableWidget_components.resizeColumnsToContents()

    def add_laser_cut_part_to_table(self, laser_cut_part: LaserCutPart):
        current_row = self.tableWidget_laser_cut_parts.rowCount()
        new_height = 70
        self.tableWidget_laser_cut_parts.insertRow(current_row)
        image_item = QTableWidgetItem("")
        if laser_cut_part.image_index:
            image = QPixmap(laser_cut_part.image_index)
            original_width = image.width()
            original_height = image.height()
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        self.tableWidget_laser_cut_parts.setRowHeight(current_row, new_height)
        self.tableWidget_laser_cut_parts.setItem(current_row, 0, image_item)
        self.tableWidget_laser_cut_parts.setItem(current_row, 1, QTableWidgetItem(laser_cut_part.name))
        self.tableWidget_laser_cut_parts.setItem(current_row, 2, QTableWidgetItem(f"{laser_cut_part.gauge} {laser_cut_part.material}"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 3, QTableWidgetItem("TODO: FILES_WIDGET"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 4, QTableWidgetItem(f"{laser_cut_part.quantity}"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 5, QTableWidgetItem(f"{laser_cut_part.flowtag.get_flow_string()}"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 6, QTableWidgetItem("TODO: RECUT_BUTTON"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 7, QTableWidgetItem("TODO: RECOAT_BUTTON"))

    def load_laser_cut_parts_table(self):
        self.tableWidget_laser_cut_parts.setRowCount(0)
        for laser_cut_part in self.assembly.laser_cut_parts:
            self.add_laser_cut_part_to_table(laser_cut_part)
        self.tableWidget_laser_cut_parts.setFixedHeight((len(self.assembly.laser_cut_parts) + 1) * 70)
        self.tableWidget_laser_cut_parts.resizeColumnsToContents()

    def sync_changes(self):
        self.parent.sync_changes()
