import contextlib
from typing import TYPE_CHECKING, Union

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
from utils.colors import darken_color, lighten_color
from utils.workspace.assembly import Assembly
from utils.workspace.job_preferences import JobPreferences

if TYPE_CHECKING:
    from ui.widgets.group_widget import GroupWidget


class AssemblyWidget(QWidget):
    def __init__(self, assembly: Assembly, parent) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/assembly_widget.ui", self)
        self.parent: Union["AssemblyWidget", GroupWidget] = parent

        self.assembly = assembly
        self.job_preferences: JobPreferences = self.parent.job_preferences
        self.sheet_settings = self.assembly.group.job.sheet_settings
        self.workspace_settings = self.assembly.group.job.workspace_settings
        self.components_inventory = self.assembly.group.job.components_inventory
        self.laser_cut_inventory = self.assembly.group.job.laser_cut_inventory
        self.price_calculator = self.parent.price_calculator

        self.assembly_widget = self.findChild(QWidget, "assembly_widget")
        self.assembly_widget.setStyleSheet(
            """
QWidget#assembly_widget {
border: 1px solid %(base_color)s;
border-bottom-left-radius: 10px;
border-bottom-right-radius: 10px;
border-top-right-radius: 0px;
border-top-left-radius: 0px;
}"""
            % {"base_color": self.assembly.group.color}
        )
        self.verticalLayout_14 = self.findChild(QVBoxLayout, "verticalLayout_14")
        self.verticalLayout_14.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_3 = self.findChild(QVBoxLayout, "verticalLayout_3")
        self.verticalLayout_3.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_4 = self.findChild(QVBoxLayout, "verticalLayout_4")
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_10 = self.findChild(QVBoxLayout, "verticalLayout_10")
        self.verticalLayout_10.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pushButton_laser_cut_parts = self.findChild(QPushButton, "pushButton_laser_cut_parts")
        self.laser_cut_widget = self.findChild(QWidget, "laser_cut_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_laser_cut_parts, self.laser_cut_widget)

        self.pushButton_components = self.findChild(QPushButton, "pushButton_components")
        self.component_widget = self.findChild(QWidget, "component_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_components, self.component_widget)

        self.pushButton_sub_assemblies = self.findChild(QPushButton, "pushButton_sub_assemblies")
        self.sub_assemblies_widget = self.findChild(QWidget, "sub_assemblies_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_sub_assemblies, self.sub_assemblies_widget)

        self.label_total_cost_for_assembly = self.findChild(QLabel, "label_total_cost_for_assembly")

        self.image_layout = self.findChild(QVBoxLayout, "image_layout")
        self.doubleSpinBox_quantity = self.findChild(QDoubleSpinBox, "doubleSpinBox_quantity")
        self.doubleSpinBox_quantity.wheelEvent = lambda event: None
        self.assembly_files_layout = self.findChild(QHBoxLayout, "assembly_files_layout")
        self.paint_widget = self.findChild(QWidget, "paint_widget")
        self.paint_layout = self.findChild(QHBoxLayout, "paint_layout")
        self.comboBox_assembly_flow_tag = self.findChild(QComboBox, "comboBox_assembly_flow_tag")
        self.laser_cut_parts_layout = self.findChild(QVBoxLayout, "laser_cut_parts_layout")
        self.add_laser_cut_part_button = self.findChild(QPushButton, "add_laser_cut_part_button")
        self.components_layout = self.findChild(QVBoxLayout, "components_layout")
        self.add_component_button = self.findChild(QPushButton, "add_component_button")
        self.sub_assembly_layout = self.findChild(QVBoxLayout, "sub_assembly_layout")
        self.sub_assembly_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.add_new_sub_assembly_button = self.findChild(QPushButton, "add_new_sub_assembly_button")
        self.add_existing_assembly_button = self.findChild(QPushButton, "add_existing_assembly_button")

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = self.assembly.group.color
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

    def open_assembly_image(self):
        self.open_image(self.assembly.assembly_image, self.assembly.name)

    def open_image(self, path: str, title: str) -> None:
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def open_pdf(self, files, file_path: str):
        pdf_viewer = PDFViewer(files, file_path, self)
        pdf_viewer.show()

    def open_group_menu(self, menu: QMenu) -> None:
        menu.exec(QCursor.pos())

    def set_table_row_color(self, table: QTableWidget, row_index: int, color: str):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def changes_made(self):
        self.parent.changes_made()

    def clear_layout(self, layout: QVBoxLayout | QWidget) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
