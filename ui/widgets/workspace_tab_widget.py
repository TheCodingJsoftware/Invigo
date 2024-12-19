import contextlib
from functools import partial
from typing import TYPE_CHECKING, Union

from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ui.custom.calendar_button import CalendarButton
from ui.custom.filter_button import FilterButton
from ui.custom.sort_button import SortButton
from ui.custom_widgets import TabButton
from ui.icons import Icons
from ui.widgets.workspace_tab_widget_UI import Ui_Form
from ui.widgets.workspace_widget import WorkspaceWidget
from utils.settings import Settings
from utils.workspace.workspace_filter import SortingMethod

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class WorkspaceTabWidget(QWidget, Ui_Form):
    tabChanged = pyqtSignal(str)

    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.parent: MainWindow = parent

        self.workspace = self.parent.workspace
        self.workspace_settings = self.parent.workspace_settings
        self.sheet_settings = self.parent.sheet_settings
        self.paint_inventory = self.parent.paint_inventory
        self.settings_file = Settings()

        self.workspace_filter = self.workspace.workspace_filter

        self.tag_buttons: list[TabButton] = []
        self.last_selected_tag: str = None
        self.has_searched = True

        self.load_ui()

    def load_ui(self):
        view_parts = self.settings_file.get_value("user_workspace_settings").get(
            "view_parts", True
        )
        view_assemblies = self.settings_file.get_value("user_workspace_settings").get(
            "view_assemblies", True
        )

        self.pushButton_view_parts.clicked.connect(self.view_parts_table)
        self.pushButton_view_parts.setVisible(view_parts)
        self.pushButton_view_parts.setChecked(
            True if view_parts and not view_assemblies else False
        )

        self.pushButton_view_assemblies.clicked.connect(self.view_assemblies_table)
        self.pushButton_view_assemblies.setVisible(view_assemblies)
        self.pushButton_view_assemblies.setChecked(
            True if view_assemblies and not view_parts else False
        )

        self.pushButton_search.clicked.connect(self.search_pressed)

        self.lineEdit_search.returnPressed.connect(self.search_pressed)
        self.lineEdit_search.textChanged.connect(self.search_typing)

        self.pushButton_clear_search.clicked.connect(self.clear_search)

        self.workspace_widget = WorkspaceWidget(self)
        self.workspace_layout.addWidget(self.workspace_widget)

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

    def user_workspace_settings_changed(self):
        self.settings_file.load_data()
        view_parts = self.settings_file.get_value("user_workspace_settings").get(
            "view_parts", True
        )
        view_assemblies = self.settings_file.get_value("user_workspace_settings").get(
            "view_assemblies", True
        )

        self.pushButton_view_parts.setVisible(view_parts)
        self.pushButton_view_assemblies.setVisible(view_assemblies)
        self.load_tags()
        self.tag_buttons[0].setChecked(True)
        self.tag_button_pressed(self.tag_buttons[0])

    def load_tags(self):
        self.clear_layout(self.tags_layout)
        self.tag_buttons.clear()
        selected_tags = self.settings_file.get_value("user_workspace_settings").get(
            "visible_process_tags", []
        )
        for tag in self.workspace_settings.get_all_tags():
            if tag not in selected_tags:
                continue
            tag_button = TabButton(tag, self)
            tag_button.clicked.connect(partial(self.tag_button_pressed, tag_button))
            self.tags_layout.addWidget(tag_button)
            self.tag_buttons.append(tag_button)
        if not self.last_selected_tag:
            self.tag_buttons[0].setChecked(True)
            self.tag_button_pressed(self.tag_buttons[0])

    def load_menu_buttons(self):
        self.clear_layout(self.menu_buttons_layout)

        self.materials_menu_button = FilterButton(
            "Materials", self.sheet_settings.get_materials()
        )
        self.materials_menu_button.setIcon(Icons.filter_icon)
        self.materials_menu_button.checkbox_states_changed.connect(
            self.filter_button_changed
        )
        self.workspace_filter.material_filter = (
            self.materials_menu_button.dropdown.checkbox_states
        )

        self.thickness_menu_button = FilterButton(
            "Thicknesses", self.sheet_settings.get_thicknesses()
        )
        self.thickness_menu_button.setIcon(Icons.filter_icon)
        self.thickness_menu_button.checkbox_states_changed.connect(
            self.filter_button_changed
        )
        self.workspace_filter.thickness_filter = (
            self.thickness_menu_button.dropdown.checkbox_states
        )

        self.paint_menu_button = FilterButton(
            "Paint",
            self.paint_inventory.get_all_paints()
            + self.paint_inventory.get_all_primers()
            + self.paint_inventory.get_all_powders(),
        )
        self.paint_menu_button.setIcon(Icons.filter_icon)
        self.paint_menu_button.checkbox_states_changed.connect(
            self.filter_button_changed
        )
        self.workspace_filter.paint_filter = (
            self.paint_menu_button.dropdown.checkbox_states
        )

        self.calendar_button = CalendarButton("Date Range")
        self.calendar_button.setIcon(Icons.date_range_icon)
        self.calendar_button.date_range_changed.connect(self.date_range_changed)
        self.calendar_button.date_range_toggled.connect(self.date_range_toggled)
        self.workspace_filter.date_range = (QDate().currentDate(), None)

        self.menu_buttons_layout.addWidget(self.materials_menu_button)
        self.menu_buttons_layout.addWidget(self.thickness_menu_button)
        self.menu_buttons_layout.addWidget(self.paint_menu_button)
        self.menu_buttons_layout.addWidget(self.calendar_button)

    def filter_button_changed(self, states: dict[str, bool]):
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_parts_tree()
        self.workspace_widget.load_assembly_tree()

    def date_range_changed(self, dates: dict[QDate, QDate]):
        self.workspace_filter.date_range = dates
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_parts_tree()
        self.workspace_widget.load_assembly_tree()

    def date_range_toggled(self, checked: bool):
        self.workspace_filter.enable_date_range = checked
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_parts_tree()
        self.workspace_widget.load_assembly_tree()

    def load_sort_button(self):
        self.clear_layout(self.sort_layout)

        self.sort_button = SortButton()
        self.sort_button.setIcon(Icons.sort_fill_icon)
        self.sort_button.sorting_method_selected.connect(self.sort)
        self.sort_layout.addWidget(self.sort_button)

    def sort(self, method: SortingMethod):
        self.workspace_filter.sorting_method = method
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_parts_tree()
        self.workspace_widget.load_assembly_tree()

    def search_typing(self):
        self.workspace_filter.search_text = self.lineEdit_search.text()
        self.has_searched = False

    def search_pressed(self):
        if not self.has_searched:
            self.workspace_widget.load_parts_table()
            self.workspace_widget.load_parts_tree()
            self.workspace_widget.load_assembly_tree()
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
        self.last_selected_tag = pressed_tag_button.text()
        self.workspace_filter.current_tag = pressed_tag_button.text()
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_parts_tree()
        self.workspace_widget.load_assembly_tree()
        self.tabChanged.emit(pressed_tag_button.text())

    def set_current_tab(self, tab_name: str):
        for tag_button in self.tag_buttons:
            if tag_button.text() == tab_name:
                tag_button.setChecked(True)
                tag_button.setEnabled(False)
            else:
                tag_button.setChecked(False)
                tag_button.setEnabled(True)
        self.last_selected_tag = tab_name
        self.workspace_filter.current_tag = tab_name
        self.workspace_widget.load_parts_table()
        self.workspace_widget.load_parts_tree()
        self.workspace_widget.load_assembly_tree()
        self.tabChanged.emit(tab_name)

    def workspace_settings_changed(self):
        self.workspace.load_data()
        self.set_current_tab(self.last_selected_tag)

    def sync_changes(self):
        self.parent.sync_changes("workspace_tab")

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
