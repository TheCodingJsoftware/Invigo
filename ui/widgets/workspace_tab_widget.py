import contextlib
import os
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Union

import sympy
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCursor, QFont, QIcon
from PyQt6.QtWidgets import QAbstractItemView, QComboBox, QCompleter, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QSplitter, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from ui.custom.filter_button import FilterButton
from ui.custom.sort_button import SortButton
from ui.custom.calendar_button import CalendarButton
from ui.widgets.workspace_widget import WorkspaceWidget
from utils.inventory.paint_inventory import PaintInventory
from utils.settings import Settings
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.threads.workspace_upload_file_thread import WorkspaceUploadThread
from utils.trusted_users import get_trusted_users
from utils.workspace.assembly import Assembly
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_filter import SortingMethod
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class WorkspaceTabWidget(QWidget):
    tabChanged = pyqtSignal(str)

    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        uic.loadUi("ui/widgets/workspace_tab_widget.ui", self)
        self.parent: MainWindow = parent
        self.workspace = self.parent.workspace
        self.workspace_settings = self.parent.workspace_settings
        self.workspace_history = self.parent.workspace_history
        self.sheet_settings = self.parent.sheet_settings
        self.paint_inventory = self.parent.paint_inventory

        self.workspace_filter = self.workspace.workspace_filter

        self.tag_buttons: list[QPushButton] = []
        self.last_selected_tag_button: QPushButton = None
        self.has_searched = True

        self.load_ui()

    def load_ui(self):
        self.tags_layout = self.findChild(QHBoxLayout, "tags_layout")
        self.workspace_layout = self.findChild(QVBoxLayout, "workspace_layout")

        self.pushButton_view_parts = self.findChild(QPushButton, "pushButton_view_parts")
        self.pushButton_view_parts.clicked.connect(self.view_parts_table)

        self.pushButton_view_assemblies = self.findChild(QPushButton, "pushButton_view_assemblies")
        self.pushButton_view_assemblies.clicked.connect(self.view_assemblies_table)

        self.pushButton_search = self.findChild(QPushButton, "pushButton_search")
        self.pushButton_search.clicked.connect(self.search_pressed)

        self.lineEdit_search = self.findChild(QLineEdit, "lineEdit_search")
        self.lineEdit_search.returnPressed.connect(self.search_pressed)
        self.lineEdit_search.textChanged.connect(self.search_typing)

        self.pushButton_clear_search = self.findChild(QPushButton, "pushButton_clear_search")
        self.pushButton_clear_search.clicked.connect(self.clear_search)

        self.workspace_widget = WorkspaceWidget(self)
        self.workspace_layout.addWidget(self.workspace_widget)

        self.menu_buttons_layout = self.findChild(QHBoxLayout, "menu_buttons_layout")
        self.sort_layout = self.findChild(QHBoxLayout, "sort_layout")

        self.nests_layout = self.findChild(QVBoxLayout, "nests_layout")

        self.load_tags()
        self.load_menu_buttons()
        self.load_sort_button()

    def view_parts_table(self):
        self.lineEdit_search.setPlaceholderText("Search parts...")

        self.pushButton_view_parts.setChecked(True)
        self.pushButton_view_assemblies.setChecked(False)

        self.pushButton_view_parts.setEnabled(False)
        self.pushButton_view_assemblies.setEnabled(True)

        self.workspace_widget.view_parts_table()

    def view_assemblies_table(self):
        self.lineEdit_search.setPlaceholderText("Search assemblies...")

        self.pushButton_view_parts.setChecked(False)
        self.pushButton_view_assemblies.setChecked(True)

        self.pushButton_view_parts.setEnabled(True)
        self.pushButton_view_assemblies.setEnabled(False)

        self.workspace_widget.view_assemblies_table()

    def load_tags(self):
        font = QFont()
        font.setBold(True)
        self.clear_layout(self.tags_layout)
        self.tag_buttons.clear()
        for tag in self.workspace_settings.get_all_tags():
            tag_button = QPushButton(tag, self)
            tag_button.setFont(font)
            tag_button.setCheckable(True)
            tag_button.clicked.connect(partial(self.tag_button_pressed, tag_button))
            self.tags_layout.addWidget(tag_button)
            self.tag_buttons.append(tag_button)
        if not self.last_selected_tag_button:
            self.tag_buttons[0].setChecked(True)
            self.tag_button_pressed(self.tag_buttons[0])

    def load_menu_buttons(self):
        self.clear_layout(self.menu_buttons_layout)

        self.materials_menu_button = FilterButton("Materials", self.sheet_settings.get_materials())
        self.materials_menu_button.checkbox_states_changed.connect(self.filter_button_changed)
        self.workspace_filter.material_filter = self.materials_menu_button.dropdown.checkbox_states

        self.thickness_menu_button = FilterButton("Thicknesses", self.sheet_settings.get_thicknesses())
        self.thickness_menu_button.checkbox_states_changed.connect(self.filter_button_changed)
        self.workspace_filter.thickness_filter = self.thickness_menu_button.dropdown.checkbox_states

        self.paint_menu_button = FilterButton("Paint", self.paint_inventory.get_all_paints() + self.paint_inventory.get_all_primers() + self.paint_inventory.get_all_powders())
        self.paint_menu_button.checkbox_states_changed.connect(self.filter_button_changed)
        self.workspace_filter.paint_filter = self.paint_menu_button.dropdown.checkbox_states

        self.calendar_button = CalendarButton("Date Range")
        self.calendar_button.date_range_changed.connect(self.date_range_changed)
        self.calendar_button.date_range_toggled.connect(self.date_range_toggled)
        self.workspace_filter.date_range = (QDate().currentDate(), None)

        self.menu_buttons_layout.addWidget(self.materials_menu_button)
        self.menu_buttons_layout.addWidget(self.thickness_menu_button)
        self.menu_buttons_layout.addWidget(self.paint_menu_button)
        self.menu_buttons_layout.addWidget(self.calendar_button)

    def filter_button_changed(self, states: dict[str, bool]):
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()

    def date_range_changed(self, dates: dict[QDate, QDate]):
        self.workspace_filter.date_range = dates
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()

    def date_range_toggled(self, checked: bool):
        self.workspace_filter.enable_date_range = checked
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()

    def load_sort_button(self):
        self.clear_layout(self.sort_layout)

        self.sort_button = SortButton()
        self.sort_button.sorting_method_selected.connect(self.sort)
        self.sort_layout.addWidget(self.sort_button)

    def sort(self, method: SortingMethod):
        self.workspace_filter.sorting_method = method
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()

    def search_typing(self):
        self.workspace_filter.search_text = self.lineEdit_search.text()
        self.has_searched = False

    def search_pressed(self):
        if not self.has_searched:
            self.workspace_widget.load_parts_table()
            self.workspace_widget.load_assembly_table()
            self.has_searched = True

    def clear_search(self):
        self.lineEdit_search.setText("")
        self.search_pressed()

    def tag_button_pressed(self, pressed_tag_button: QPushButton):
        pressed_tag_button.setEnabled(False)
        for tag_button in self.tag_buttons:
            if tag_button != pressed_tag_button:
                tag_button.setChecked(False)
                tag_button.setEnabled(True)
        self.last_selected_tag_button = pressed_tag_button
        self.workspace_filter.current_tag = pressed_tag_button.text()
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()
        self.tabChanged.emit(pressed_tag_button.text())

    def workspace_settings_changed(self):
        self.workspace.load_data()
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_assembly_table()

    def sync_changes(self):
        self.parent.sync_changes()

    def clear_layout(self, layout: Union[QVBoxLayout, QWidget]):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
