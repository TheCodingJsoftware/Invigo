import contextlib
import os
from datetime import datetime
from functools import partial
from typing import Optional, TYPE_CHECKING, Union, Literal

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
from ui.custom.file_button import FileButton

from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
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
from ui.custom.workspace_parts_table_widget import (
    WorkspacePartsTableColumns,
    WorkspacePartsTableWidget,
)
from ui.custom.workspace_assembly_table_widget import (
    WorkspaceAssemblyTableColumns,
    WorkspaceAssemblyTableWidget,
)

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

        self.filter = self.parent.filter

        self.selected_tag: str = None
        self.settings_file = Settings()

        self.username = os.getlogin().title()

        self.parts_table_items: dict[LaserCutPart, dict[str, Union[QTableWidgetItem]]] = {}
        self.assemblies_table_items: dict[LaserCutPart, dict[str, Union[QTableWidgetItem]]] = {}

        self.parts_table_rows: dict[int, LaserCutPart] = {}
        self.assemblies_table_rows: dict[int, Assembly] = {}

        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.load_ui()

    def load_ui(self):
        self.parts_table_widget = WorkspacePartsTableWidget(self)
        self.parts_table_widget.rowChanged.connect(self.parts_table_row_changed)

        self.assemblies_table_widget = WorkspaceAssemblyTableWidget(self)
        self.assemblies_table_widget.rowChanged.connect(self.assemblies_table_row_changed)

        self.parts_widget = self.findChild(QWidget, "parts_widget")
        self.parts_layout = self.findChild(QVBoxLayout, "parts_layout")
        self.parts_layout.addWidget(self.parts_table_widget)

        self.assembly_widget = self.findChild(QWidget, "assembly_widget")
        self.assembly_widget.setHidden(True)
        self.assembly_layout = self.findChild(QVBoxLayout, "assembly_layout")
        self.assembly_layout.addWidget(self.assemblies_table_widget)

    def view_parts_table(self):
        self.parts_widget.setVisible(True)
        self.assembly_widget.setVisible(False)

    def view_assemblies_table(self):
        self.parts_widget.setVisible(False)
        self.assembly_widget.setVisible(True)

    def get_filtered_parts(self) -> list[LaserCutPart]:
        parts: list[LaserCutPart] = []
        for laser_cut_part in self.workspace.get_all_laser_cut_parts():
            if current_tag := laser_cut_part.get_current_tag():
                if current_tag.name != self.filter.current_tag:
                    continue

            search_text = self.filter.search_text.lower()
            paint_text = laser_cut_part.get_all_paints().lower()
            if search_text:
                name_match = search_text in laser_cut_part.name.lower()
                material_match = search_text in f"{laser_cut_part.gauge} {laser_cut_part.material}".lower()
                paint_match = search_text in paint_text

                if not (name_match or material_match or paint_match):
                    continue

            parts.append(laser_cut_part)
        return parts

    def get_filtered_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        for assembly in self.workspace.get_all_assemblies():
            if current_tag := assembly.get_current_tag():
                if current_tag.name != self.filter.current_tag:
                    continue
            if self.filter.search_text.lower() not in assembly.name.lower():
                continue

            assemblies.append(assembly)
        return assemblies

    # PARTS
    def add_part_to_table(self, laser_cut_part: LaserCutPart):
        current_row = self.parts_table_widget.rowCount()
        self.parts_table_rows.update({current_row: laser_cut_part})
        self.parts_table_items.update({laser_cut_part: {}})
        self.parts_table_widget.insertRow(current_row)
        self.parts_table_widget.setRowHeight(current_row, self.parts_table_widget.row_height)

        # PART NAME
        part_name_item = QTableWidgetItem(laser_cut_part.name)
        part_name_item.setFont(self.tables_font)
        self.parts_table_items[laser_cut_part].update({"part_name": part_name_item})
        self.parts_table_widget.setItem(current_row, WorkspacePartsTableColumns.PART_NAME.value, part_name_item)

        # FILES
        if any(keyword in laser_cut_part.get_current_tag().name.lower() for keyword in ["weld", "assembly"]):
            files_widget, files_layout = self.create_file_layout(laser_cut_part, ["welding_files"])
        elif any(keyword in laser_cut_part.get_current_tag().name.lower() for keyword in ["bend", "break"]):
            files_widget, files_layout = self.create_file_layout(laser_cut_part, ["bending_files"])
        elif any(keyword in laser_cut_part.get_current_tag().name.lower() for keyword in ["cnc", "laser", "cutting", "milling", "thread"]):
            files_widget, files_layout = self.create_file_layout(laser_cut_part, ["cnc_milling_files"])
        else:
            files_widget = QLabel("No files", self.parts_table_widget)
        self.parts_table_widget.setCellWidget(
            current_row,
            WorkspacePartsTableColumns.FILES.value,
            files_widget,
        )
        self.parts_table_items[laser_cut_part].update({"files": files_widget})

        # MATERIAL
        material_item = QTableWidgetItem(f"{laser_cut_part.gauge} {laser_cut_part.material}")
        material_item.setFont(self.tables_font)
        self.parts_table_widget.setItem(current_row, WorkspacePartsTableColumns.MATERIAL.value, material_item)
        self.parts_table_items[laser_cut_part].update({"material": material_item})

        # PAINT
        paint_item = self.get_paint_widget(laser_cut_part)
        self.parts_table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.PAINT.value, paint_item)
        self.parts_table_items[laser_cut_part].update({"paint": paint_item})

        # QUANTITY
        quantity_item = QTableWidgetItem(f"{laser_cut_part.quantity}")
        quantity_item.setFont(self.tables_font)
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parts_table_widget.setItem(current_row, WorkspacePartsTableColumns.QUANTITY.value, quantity_item)
        self.parts_table_items[laser_cut_part].update({"quantity": quantity_item})

        # PROCESS CONTROLS
        flow_tag_controls_widget = self.get_flow_tag_controls(laser_cut_part)
        self.parts_table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.PROCESS_CONTROLS.value, flow_tag_controls_widget)
        self.parts_table_items[laser_cut_part].update({"flow_tag_controls": flow_tag_controls_widget})

        # SHELF NUMBER
        if not laser_cut_part.notes:
            shelf_number_item = QTableWidgetItem("NA")
        else:
            shelf_number_item = QTableWidgetItem(laser_cut_part.notes)
        shelf_number_item.setFont(self.tables_font)
        shelf_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parts_table_widget.setItem(current_row, WorkspacePartsTableColumns.SHELF_NUMBER.value, shelf_number_item)
        self.parts_table_items[laser_cut_part].update({"shelf_number": shelf_number_item})

        # NOTES
        if not laser_cut_part.notes:
            notes_item = QTableWidgetItem("No notes provided")
        else:
            notes_item = QTableWidgetItem(laser_cut_part.notes)
        notes_item.setFont(self.tables_font)
        self.parts_table_widget.setItem(current_row, WorkspacePartsTableColumns.NOTES.value, notes_item)
        self.parts_table_items[laser_cut_part].update({"notes": notes_item})

    def get_paint_widget(self, laser_cut_part: LaserCutPart) -> QWidget:
        widget = QWidget(self.parts_table_widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        if laser_cut_part.uses_primer and laser_cut_part.primer_item:
            primer_label = QLabel(f"{laser_cut_part.primer_item.name}", widget)
            layout.addWidget(primer_label)
        if laser_cut_part.uses_paint and laser_cut_part.paint_item:
            paint_label = QLabel(f"{laser_cut_part.paint_item.name}", widget)
            layout.addWidget(paint_label)
        if laser_cut_part.uses_powder and laser_cut_part.powder_item:
            powder_label = QLabel(f"{laser_cut_part.powder_item.name}", widget)
            layout.addWidget(powder_label)
        return widget

    def add_laser_cut_part_drag_file_widget(
        self,
        laser_cut_part: LaserCutPart,
        file_category: str,
        files_layout: QHBoxLayout,
        file_path: str,
    ):
        file_button = FileButton(f"{os.getcwd()}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.laser_cut_part_file_clicked, laser_cut_part, file_path))
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)
        self.parts_table_widget.resizeColumnsToContents()

    def create_file_layout(
        self,
        laser_cut_part: LaserCutPart,
        file_types: list[
            Union[
                Literal["bending_files"],
                Literal["welding_files"],
                Literal["cnc_milling_files"],
            ]
        ],
    ) -> tuple[QWidget, QHBoxLayout]:
        main_widget = QWidget(self.parts_table_widget)
        main_widget.setObjectName("main_widget")
        main_widget.setStyleSheet("QWidget#main_widget{background-color: transparent;}")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        files_widget = QWidget()
        files_widget.setObjectName("files_widget")
        files_widget.setStyleSheet("QWidget#files_widget{background-color: transparent;}")
        files_layout = QHBoxLayout(files_widget)
        files_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        files_layout.setContentsMargins(0, 0, 6, 0)
        files_layout.setSpacing(6)

        scroll_area = QScrollArea(self.parts_table_widget)
        scroll_area.setWidget(files_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(100)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        main_layout.addWidget(scroll_area)

        for file_type in file_types:
            file_list: list[str] = getattr(laser_cut_part, file_type)
            for file in file_list:
                self.add_laser_cut_part_drag_file_widget(laser_cut_part, file_type, files_layout, file)
        return main_widget, files_layout

    def laser_cut_part_get_all_file_types(self, laser_cut_part: LaserCutPart, file_ext: str) -> list[str]:
        files: set[str] = set()
        for bending_file in laser_cut_part.bending_files:
            if bending_file.lower().endswith(file_ext):
                files.add(bending_file)
        for welding_file in laser_cut_part.welding_files:
            if welding_file.lower().endswith(file_ext):
                files.add(welding_file)
        for cnc_milling_file in laser_cut_part.cnc_milling_files:
            if cnc_milling_file.lower().endswith(file_ext):
                files.add(cnc_milling_file)
        return list(files)

    def laser_cut_part_file_clicked(self, laser_cut_part: LaserCutPart, file_path: str):
        self.download_file_thread = WorkspaceDownloadFile([file_path], True)
        self.download_file_thread.signal.connect(self.file_downloaded)
        self.download_file_thread.start()
        self.download_file_thread.wait()
        if file_path.lower().endswith(".pdf"):
            self.open_pdf(
                self.laser_cut_part_get_all_file_types(laser_cut_part, ".pdf"),
                file_path,
            )

    def load_parts_table(self):
        self.parts_table_widget.blockSignals(True)
        self.parts_table_items.clear()
        self.parts_table_rows.clear()
        self.parts_table_widget.setRowCount(0)
        for laser_cut_part in self.get_filtered_parts():
            self.add_part_to_table(laser_cut_part)
        self.parts_table_widget.blockSignals(False)
        self.parts_table_widget.resizeColumnsToContents()

    def parts_table_row_changed(self, row: int):
        pass

    # ASSEMBLIES
    def add_assembly_to_table(self, assembly: Assembly):
        current_row = self.assemblies_table_widget.rowCount()
        self.assemblies_table_rows.update({current_row: assembly})
        self.assemblies_table_items.update({assembly: {}})
        self.assemblies_table_widget.insertRow(current_row)
        self.assemblies_table_widget.setRowHeight(current_row, self.assemblies_table_widget.row_height)

        part_name_item = QTableWidgetItem(assembly.name)
        part_name_item.setFont(self.tables_font)
        self.assemblies_table_items[assembly].update({"name": part_name_item})
        self.assemblies_table_widget.setItem(current_row, WorkspacePartsTableColumns.PART_NAME.value, part_name_item)

    def load_assembly_table(self):
        self.assemblies_table_widget.blockSignals(True)
        self.assemblies_table_items.clear()
        self.assemblies_table_rows.clear()
        self.assemblies_table_widget.setRowCount(0)
        for assembly in self.get_filtered_assemblies():
            self.add_assembly_to_table(assembly)
        self.assemblies_table_widget.blockSignals(False)
        self.assemblies_table_widget.resizeColumnsToContents()

    def assemblies_table_row_changed(self, row: int):
        pass

    # OTHER STUFF
    def get_flow_tag_controls(self, item: Union[LaserCutPart, Assembly]) -> Union[QComboBox, QPushButton]:
        current_tag = item.get_current_tag()
        if current_tag.statuses:
            flowtag_combobox = QComboBox(self)
            flowtag_combobox.setToolTip(current_tag.attribute.next_flow_tag_message)
            for status in current_tag.statuses:
                flowtag_combobox.addItem(status.name)
            return flowtag_combobox
        else:
            try:
                button_text = f"Move to {item.flow_tag.tags[item.current_flow_tag_index + 1].name}"
            except IndexError:
                button_text = "Mark as done"
            flowtag_button = QPushButton(button_text, self)
            flowtag_button.setToolTip(current_tag.attribute.next_flow_tag_message)
            return flowtag_button

    def file_downloaded(self, file_ext: Optional[str], file_name: str, open_when_done: bool):
        if file_ext is None:
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "Error",
                f"Failed to download file: {file_name}",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.show()
            return
        if open_when_done:
            if file_ext in {"PNG", "JPG", "JPEG"}:
                local_path = f"data/workspace/{file_ext}/{file_name}"
                self.open_image(local_path, file_name)

    def open_pdf(self, files, file_path: str):
        pdf_viewer = PDFViewer(files, file_path, self)
        pdf_viewer.show()

    def open_image(self, path: str, title: str) -> None:
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def sync_changes(self):
        self.parent.sync_changes()

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
