from typing import TYPE_CHECKING

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog, QTableWidgetItem, QWidget, QTableWidget, QPushButton, QLabel

from utils.colors import darken_color, lighten_color
from utils.workspace.workspace import Workspace
from utils.workspace.assembly import Assembly
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart


if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class ViewAssemblyDialog(QDialog):
    def __init__(self, assembly: Assembly, workspace: Workspace, parent):
        super().__init__(parent)
        uic.loadUi("ui/dialogs/view_assembly_dialog.ui", self)

        self.assembly = assembly
        self.workspace = workspace

        self.label_assembly_image.setPixmap(QPixmap(self.assembly.assembly_image))
        self.label_assembly_name.setText(self.assembly.name)

        self.parent: MainWindow = parent

        self.tableWidget_components = self.findChild(QTableWidget, "tableWidget_components")
        self.tableWidget_laser_cut_parts = self.findChild(QTableWidget, "tableWidget_laser_cut_parts")

        self.apply_stylesheet_to_toggle_buttons(self.pushButton_components, self.widget_components)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_laser_cut_parts, self.widget_laser_cut_parts)

        self.load_components_table()
        self.load_laser_cut_parts_table()

        self.setWindowTitle(self.assembly.name)

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = self.assembly.color
        hover_color: str = lighten_color(base_color)
        pressed_color: str = darken_color(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            """
QPushButton#assembly_button_drop_menu {
    border: 1px solid rgba(71, 71, 71, 110);
    background-color: rgba(71, 71, 71, 110);
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
    color: #EAE9FC;
    text-align: left;
}

QPushButton:hover#assembly_button_drop_menu {
    background-color: rgba(76, 76, 76, 110);
    border: 1px solid %(base_color)s;
}

QPushButton:pressed#assembly_button_drop_menu {
    background-color: %(base_color)s;
    color: #EAE9FC;
}

QPushButton:!checked#assembly_button_drop_menu {
    color: #8C8C8C;
}

QPushButton:!checked:pressed#assembly_button_drop_menu {
    color: #EAE9FC;
}

QPushButton:checked#assembly_button_drop_menu {
    color: #EAE9FC;
    border-color: %(base_color)s;
    background-color: %(base_color)s;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}

QPushButton:checked:hover#assembly_button_drop_menu {
    background-color: %(hover_color)s;
}

QPushButton:checked:pressed#assembly_button_drop_menu {
    color: #EAE9FC;
    background-color: %(pressed_color)s;
}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": pressed_color,
            }
        )
        widget.setObjectName("assembly_widget_drop_menu")
        widget.setStyleSheet(
            """QWidget#assembly_widget_drop_menu{
            border: 1px solid %(base_color)s;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            };
            """
            % {"base_color": base_color}
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
        self.tableWidget_laser_cut_parts.setItem(current_row, 3, QTableWidgetItem("FILES_WIDGET"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 4, QTableWidgetItem(f"{laser_cut_part.quantity}"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 5, QTableWidgetItem(f"{laser_cut_part.flow_tag.get_name()}"))
        self.tableWidget_laser_cut_parts.setItem(current_row, 6, QTableWidgetItem("RECUT_BUTTON"))

    def load_laser_cut_parts_table(self):
        self.tableWidget_laser_cut_parts.setRowCount(0)
        for laser_cut_part in self.assembly.laser_cut_parts:
            self.add_laser_cut_part_to_table(laser_cut_part)
        self.tableWidget_laser_cut_parts.setFixedHeight((len(self.assembly.laser_cut_parts) + 1) * 70)
        self.tableWidget_laser_cut_parts.resizeColumnsToContents()

    def sync_changes(self):
        self.parent.sync_changes()
