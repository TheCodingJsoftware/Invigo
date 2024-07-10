import contextlib
import os
from datetime import datetime
from functools import partial
from typing import Any, TYPE_CHECKING, Union

import sympy
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction, QCursor, QFont, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import (
    AssemblyImage,
    AssemblyMultiToolBox,
    CustomTableWidget,
    DeletePushButton,
    DraggableButton,
    DropWidget,
    FilterTabWidget,
    HumbleDoubleSpinBox,
    ItemsGroupBox,
    MultiToolBox,
    NotesPlainTextEdit,
    RecordingWidget,
    ScrollPositionManager,
    SelectRangeCalendar,
    TimeSpinBox,
)
from ui.dialogs.color_picker_dialog import ColorPicker
from ui.dialogs.recut_dialog import RecutDialog
from utils.colors import get_random_color
from utils.dialog_buttons import DialogButtons
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.paint_inventory import PaintInventory
from utils.settings import Settings
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.threads.workspace_upload_file_thread import WorkspaceUploadThread
from utils.trusted_users import get_trusted_users
from utils.workspace.assembly import Assembly
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_item import WorkspaceItem
from utils.workspace.workspace_item_group import WorkspaceItemGroup
from utils.workspace.workspace_settings import WorkspaceSettings
from ui.custom.workspace_parts_table_widget import WorkspacePartsTableColumns, WorkspacePartsTableWidget
from ui.custom.workspace_assembly_table_widget import WorkspaceAssemblyTableColumns, WorkspaceAssemblyTableWidget

if TYPE_CHECKING:
    from ui.widgets.workspace_tab_widget import WorkspaceTabWidget

class WorkspaceWidget(QWidget):
    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        uic.loadUi("ui/widgets/workspace_widget.ui", self)
        self.parent: WorkspaceTabWidget = parent
        self.workspace = self.parent.workspace
        self.workspace_settings = self.parent.workspace_settings
        self.settings_file = Settings()

        self.username = os.getlogin().title()

        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.load_ui()

    def load_ui(self):
        self.parts_table_widget = WorkspacePartsTableWidget(self)
        self.assemblies_table_widget = WorkspaceAssemblyTableWidget(self)

        self.lineEdit_search = self.findChild(QLineEdit, "lineEdit_search")
        self.pushButton_view_parts = self.findChild(QPushButton, "pushButton_view_parts")
        self.pushButton_view_parts.clicked.connect(self.view_parts_table)
        self.pushButton_view_assemblies = self.findChild(QPushButton, "pushButton_view_assemblies")
        self.pushButton_view_assemblies.clicked.connect(self.view_assemblies_table)

        self.parts_widget = self.findChild(QWidget, "parts_widget")
        self.parts_layout = self.findChild(QVBoxLayout, "parts_layout")
        self.parts_layout.addWidget(self.parts_table_widget)
        self.assembly_widget = self.findChild(QWidget, "assembly_widget")
        self.assembly_widget.setHidden(True)
        self.assembly_layout = self.findChild(QVBoxLayout, "assembly_layout")
        self.assembly_layout.addWidget(self.assemblies_table_widget)

        self.filter_layout = self.findChild(QVBoxLayout, "filter_layout")
        self.groupBox_due_dates = self.findChild(QGroupBox, "groupBox_due_dates")
        self.pushButton_next_2_days = self.findChild(QPushButton, "pushButton_next_2_days")
        self.pushButton_next_4_days = self.findChild(QPushButton, "pushButton_next_4_days")
        self.pushButton_this_week = self.findChild(QPushButton, "pushButton_this_week")
        self.workspace_layout = self.findChild(QVBoxLayout, "workspace_layout")

        # self.pushButton_this_week.clicked.connect(partial(self.set_filter_calendar_day, 7))
        # self.pushButton_next_2_days.clicked.connect(partial(self.set_filter_calendar_day, 2))
        # self.pushButton_next_4_days.clicked.connect(partial(self.set_filter_calendar_day, 4))
        # self.pushButton_generate_workorder.clicked.connect(partial(self.generate_workorder_dialog, []))
        # self.pushButton_generate_workspace_quote.clicked.connect(partial(self.generate_workspace_printout_dialog, []))

    def view_parts_table(self):
        self.pushButton_view_assemblies.setChecked(False)
        self.pushButton_view_parts.setEnabled(False)
        self.pushButton_view_assemblies.setEnabled(True)

    def view_assemblies_table(self):
        self.pushButton_view_parts.setChecked(False)
        self.pushButton_view_assemblies.setEnabled(False)
        self.pushButton_view_parts.setEnabled(True)

    def get_filtered_parts(self) -> list[LaserCutPart]:
        parts: list[LaserCutPart] = []
        return parts

    def get_filtered_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        return assemblies

    def add_part_to_table(self, laser_cut_part: LaserCutPart):
        pass

    def load_parts_table(self):
        for laser_cut_part in self.get_filtered_parts():
            self.add_part_to_table(laser_cut_part)

    def add_assembly_to_table(self, assembly: Assembly):
        pass

    def load_assembly_table(self):
        for assembly in self.get_filtered_assemblies():
            self.add_assembly_to_table(assembly)

    def clear_layout(self, layout: Union[QVBoxLayout, QWidget]) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
