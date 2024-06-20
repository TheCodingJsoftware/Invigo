import contextlib
import math
import os
from datetime import datetime
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QKeySequence, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from ui.add_component_dialog import AddComponentDialog
from ui.assembly_widget import AssemblyWidget
from ui.custom_widgets import AssemblyMultiToolBox, QScrollArea, ClickableLabel, CustomTableWidget, DeletePushButton, MachineCutTimeSpinBox, MultiToolBox, QLineEdit, RecutButton
from ui.image_viewer import QImageViewer
from utils.calulations import calculate_overhead
from utils.components_inventory.component import Component
from utils.components_inventory.components_inventory import ComponentsInventory
from utils.inventory.category import Category
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.workspace.assembly import Assembly
from utils.workspace.group import Group


class GroupWidget(QWidget):
    def __init__(self, group: Group, parent) -> None:
        super(GroupWidget, self).__init__(parent)
        uic.loadUi("ui/group_widget.ui", self)

        self.parent = parent
        self.group = group

        self.assembly_widgets: list[AssemblyWidget] = []

        self.load_ui()

    def load_ui(self):
        self.assemblies_widget = self.findChild(QWidget, "assemblies_widget")
        self.assemblies_widget.setStyleSheet(
            """
QWidget#assemblies_widget {
border: 1px solid %(base_color)s;
border-bottom-left-radius: 10px;
border-bottom-right-radius: 10px;
border-top-right-radius: 0px;
border-top-left-radius: 0px;
}"""
            % {"base_color": self.group.color}
        )
        self.assemblies_layout = self.findChild(QVBoxLayout, "assemblies_layout")
        self.assemblies_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.add_assembly_button = self.findChild(QPushButton, "add_assembly_button")
        self.add_assembly_button.clicked.connect(self.add_assembly)

        self.assemblies_toolbox = AssemblyMultiToolBox(self)
        self.assemblies_layout.addWidget(self.assemblies_toolbox)

    def workspace_settings_changed(self):
        for assembly_widget in self.assembly_widgets:
            assembly_widget.workspace_settings_changed()

    def add_assembly(self, new_assembly: Assembly = None) -> AssemblyWidget:
        if not new_assembly:
            assembly = Assembly(f"Enter Assembly Name{len(self.group.assemblies)}", {}, self.group)
            self.group.add_assembly(assembly)
            self.changes_made()
        else:
            assembly = new_assembly

        assembly_widget = AssemblyWidget(assembly, self)
        self.assemblies_toolbox.addItem(assembly_widget, assembly.name, self.group.color)

        name_input: QLineEdit = self.assemblies_toolbox.getLastInputBox()
        name_input.textChanged.connect(partial(self.assembly_name_renamed, assembly, name_input))

        duplicate_button = self.assemblies_toolbox.getLastDuplicateButton()
        duplicate_button.clicked.connect(partial(self.duplicate_assembly, assembly))

        delete_button = self.assemblies_toolbox.getLastDeleteButton()
        delete_button.clicked.connect(partial(self.delete_assembly, assembly_widget))

        self.assembly_widgets.append(assembly_widget)
        return assembly_widget

    def load_assembly(self, assembly: Assembly):
        assembly_widget = self.add_assembly(assembly)
        for sub_assembly in assembly.sub_assemblies:
            sub_assembly.group = self.group
            assembly_widget.load_sub_assembly(sub_assembly)

    def assembly_name_renamed(self, assembly: Assembly, new_assembly_name: QLineEdit):
        assembly.name = new_assembly_name.text()
        self.changes_made()

    def duplicate_assembly(self, assembly: Assembly):
        new_assembly = Assembly(f"{assembly.name} - (Copy)", assembly.to_dict(), self.group)
        self.load_assembly(new_assembly)
        self.group.add_assembly(new_assembly)
        self.changes_made()

    def delete_assembly(self, assembly_widget: AssemblyWidget):
        self.assembly_widgets.remove(assembly_widget)
        self.assemblies_toolbox.removeItem(assembly_widget)
        self.group.remove_assembly(assembly_widget.assembly)
        self.changes_made()

    def changes_made(self):
        self.parent.changes_made()

    def update_tables(self):
        for assembly_widget in self.assembly_widgets:
            assembly_widget.update_tables()

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
