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
from ui.widgets.workspace_widget import WorkspaceWidget

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow

class WorkspaceTabWidget(QWidget):
    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        uic.loadUi("ui/widgets/workspace_tab_widget.ui", self)
        self.parent: MainWindow = parent
        self.workspace = self.parent.workspace
        self.workspace_settings = self.parent.workspace_settings

        self.tag_buttons: list[QPushButton] = []
        self.last_selected_tag_button: QPushButton = None

        self.load_ui()

    def load_ui(self):
        self.tags_layout = self.findChild(QHBoxLayout, "tags_layout")
        self.workspace_layout = self.findChild(QVBoxLayout, "workspace_layout")

        self.workspace_widget = WorkspaceWidget(self)
        self.workspace_layout.addWidget(self.workspace_widget)

        self.load_tags()

    def load_tags(self):
        self.clear_layout(self.tags_layout)
        self.tag_buttons.clear()
        for tag in self.workspace_settings.get_all_tags():
            tag_button = QPushButton(tag, self)
            tag_button.setCheckable(True)
            tag_button.clicked.connect(partial(self.tag_button_pressed, tag_button))
            self.tags_layout.addWidget(tag_button)
            self.tag_buttons.append(tag_button)
        if not self.last_selected_tag_button:
            self.tag_buttons[0].setChecked(True)
            self.tag_button_pressed(self.tag_buttons[0])

    def tag_button_pressed(self, pressed_tag_button):
        for tag_button in self.tag_buttons:
            if tag_button != pressed_tag_button:
                tag_button.setChecked(False)
        self.last_selected_tag_button = pressed_tag_button
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()

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
