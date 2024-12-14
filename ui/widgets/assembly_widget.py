import contextlib
from typing import TYPE_CHECKING, Optional, Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtWidgets import QMenu, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ui.dialogs.add_assembly_dialog import AddAssemblyDialog
from ui.dialogs.laser_cut_parts_list_summary_dialog import LaserCutPartsListSummaryDialog
from ui.theme import theme_var
from ui.widgets.assembly_widget_UI import Ui_Form
from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
from utils.colors import get_contrast_text_color, lighten_color
from utils.workspace.assembly import Assembly
from utils.workspace.job_preferences import JobPreferences

if TYPE_CHECKING:
    from ui.custom.job_tab import JobTab
    from ui.widgets.job_widget import JobWidget


class AssemblyWidget(QWidget, Ui_Form):
    def __init__(self, assembly: Assembly, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent: Union["AssemblyWidget", JobWidget] = parent

        self.assembly = assembly
        self.job_preferences: JobPreferences = self.parent.job_preferences
        self.sheet_settings = self.assembly.job.sheet_settings
        self.workspace_settings = self.assembly.job.workspace_settings
        self.components_inventory = self.assembly.job.components_inventory
        self.laser_cut_inventory = self.assembly.job.laser_cut_inventory
        self.price_calculator = self.parent.price_calculator
        self.job_tab: JobTab = self.parent.parent

        self.assembly_widget.setStyleSheet(
            f"""
QWidget#assembly_widget {{
border: 1px solid %(base_color)s;
border-bottom-left-radius: 10px;
border-bottom-right-radius: 10px;
border-top-right-radius: 0px;
border-top-left-radius: 0px;
background-color: {theme_var('surface')};
}}"""
            % {"base_color": self.assembly.color}
        )
        self.verticalLayout_14.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_3.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_10.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_laser_cut_parts, self.laser_cut_widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_components, self.component_widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_sub_assemblies, self.sub_assemblies_widget)
        self.doubleSpinBox_quantity.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.sub_assembly_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.checkBox_not_part_of_process.setChecked(self.assembly.not_part_of_process)
        self.checkBox_not_part_of_process.clicked.connect(self.changes_made)

        self.pushButton_show_parts_list_summary.clicked.connect(self.show_parts_list_summary)

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

    def show_parts_list_summary(self):
        dialog = LaserCutPartsListSummaryDialog([self.assembly], self)
        dialog.show()

    def open_assembly_image(self):
        self.open_image(self.assembly.assembly_image, self.assembly.name)

    def open_image(self, path: str, title: str):
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def open_pdf(self, files, file_path: str):
        pdf_viewer = PDFViewer(files, file_path, self)
        pdf_viewer.show()

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def set_table_row_color(self, table: QTableWidget, row_index: int, color: str):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def get_assemblies_dialog(self) -> Optional[list[Assembly]]:
        dialog = AddAssemblyDialog(self.job_tab.get_active_jobs(), self)
        if dialog.exec():
            return dialog.get_selected_assemblies()
        return None

    def update_context_menu(self):
        self.parent.update_context_menu()

    def changes_made(self):
        self.assembly.not_part_of_process = self.checkBox_not_part_of_process.isChecked()
        self.parent.changes_made()

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
