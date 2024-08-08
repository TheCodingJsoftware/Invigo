import contextlib
import os
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Literal, Optional, Union

from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction, QCursor, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QCompleter, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from ui.custom.file_button import FileButton
from ui.custom.workspace_assembly_table_widget import WorkspaceAssemblyTableColumns, WorkspaceAssemblyTableWidget
from ui.custom.workspace_parts_table_widget import WorkspacePartsTableColumns, WorkspacePartsTableWidget
from ui.dialogs.recut_dialog import RecutDialog
from ui.dialogs.view_assembly_dialog import ViewAssemblyDialog
from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.threads.upload_thread import UploadThread
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup

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
        self.workspace_history = self.parent.workspace_history
        self.workspace_filter = self.parent.workspace_filter

        self.laser_cut_inventory = self.workspace.laser_cut_inventory

        self.settings_file = Settings()

        self.username = os.getlogin().title()

        self.recut_parts_table_items: dict[WorkspaceLaserCutPartGroup, dict[str, Union[QTableWidgetItem]]] = {}
        self.recoat_parts_table_items: dict[WorkspaceLaserCutPartGroup, dict[str, Union[QTableWidgetItem]]] = {}
        self.parts_table_items: dict[WorkspaceLaserCutPartGroup, dict[str, Union[QTableWidgetItem]]] = {}
        self.assemblies_table_items: dict[Assembly, dict[str, Union[QTableWidgetItem]]] = {}

        self.recut_parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.recoat_parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.assemblies_table_rows: dict[int, Assembly] = {}

        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.load_ui()

    def load_ui(self):
        self.parts_table_widget = WorkspacePartsTableWidget(self)
        # self.parts_table_widget.rowChanged.connect(self.parts_table_row_changed)

        self.recut_parts_table_widget = WorkspacePartsTableWidget(self)
        self.recut_parts_table_widget.hideColumn(WorkspacePartsTableColumns.RECOAT.value)
        # self.recut_parts_table_widget.rowChanged.connect(self.parts_table_row_changed)

        self.recoat_parts_table_widget = WorkspacePartsTableWidget(self)
        # self.recoat_parts_table_widget.rowChanged.connect(self.parts_table_row_changed)

        self.assemblies_table_widget = WorkspaceAssemblyTableWidget(self)
        # self.assemblies_table_widget.rowChanged.connect(self.assemblies_table_row_changed)

        self.parts_widget = self.findChild(QWidget, "parts_widget")
        self.parts_layout = self.findChild(QVBoxLayout, "parts_layout")
        self.parts_layout.addWidget(self.parts_table_widget)

        self.recut_parts_widget = self.findChild(QGroupBox, "recut_parts_widget")
        self.recut_parts_layout = self.findChild(QVBoxLayout, "recut_parts_layout")
        self.recut_parts_layout.addWidget(self.recut_parts_table_widget)

        self.recoat_parts_widget = self.findChild(QGroupBox, "recoat_parts_widget")
        self.recoat_parts_layout = self.findChild(QVBoxLayout, "recoat_parts_layout")
        self.recoat_parts_layout.addWidget(self.recoat_parts_table_widget)

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

    # PARTS
    def add_part_group_to_table(self, group: WorkspaceLaserCutPartGroup):
        if group.base_part.recut and group.base_part.recoat:
            table_rows = self.recut_parts_table_rows
            table_widget = self.recut_parts_table_widget
            table_items = self.recut_parts_table_items
        elif group.base_part.recut:
            table_rows = self.recut_parts_table_rows
            table_widget = self.recut_parts_table_widget
            table_items = self.recut_parts_table_items
        elif group.base_part.recoat:
            table_rows = self.recoat_parts_table_rows
            table_widget = self.recoat_parts_table_widget
            table_items = self.recoat_parts_table_items
        else:
            table_rows = self.parts_table_rows
            table_widget = self.parts_table_widget
            table_items = self.parts_table_items

        current_row = table_widget.rowCount()
        table_rows.update({current_row: group})
        table_items.update({group: {}})
        table_widget.insertRow(current_row)
        table_widget.setRowHeight(current_row, table_widget.row_height)

        # PART NAME
        part_name_item = QTableWidgetItem(group.base_part.name)
        part_name_item.setFont(self.tables_font)
        part_name_item.setToolTip(group.get_parts_list())
        table_items[group].update({"part_name": part_name_item})
        table_widget.setItem(current_row, WorkspacePartsTableColumns.PART_NAME.value, part_name_item)

        # FILES
        if any(keyword in group.base_part.get_current_tag().name.lower() for keyword in ["weld", "assembly"]):
            files_widget, files_layout = self.create_file_layout(group, ["welding_files"])
        elif any(keyword in group.base_part.get_current_tag().name.lower() for keyword in ["bend", "break"]):
            files_widget, files_layout = self.create_file_layout(group, ["bending_files"])
        elif any(keyword in group.base_part.get_current_tag().name.lower() for keyword in ["cnc", "laser", "cutting", "milling", "thread"]):
            files_widget, files_layout = self.create_file_layout(group, ["cnc_milling_files"])
        else:
            files_widget = QLabel("No files", table_widget)
        table_widget.setCellWidget(
            current_row,
            WorkspacePartsTableColumns.FILES.value,
            files_widget,
        )
        table_items[group].update({"files": files_widget})

        # MATERIAL
        material_item = QTableWidgetItem(f"{group.base_part.gauge} {group.base_part.material}")
        material_item.setFont(self.tables_font)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.MATERIAL.value, material_item)
        table_items[group].update({"material": material_item})

        # PAINT
        paint_item = self.get_paint_widget(group.base_part)
        table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.PAINT.value, paint_item)
        table_items[group].update({"paint": paint_item})

        # QUANTITY
        quantity_item = QTableWidgetItem(f"{group.get_quantity()}")
        quantity_item.setFont(self.tables_font)
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.QUANTITY.value, quantity_item)
        table_items[group].update({"quantity": quantity_item})

        # QUANTITY IN STOCK
        if inventory_part := self.laser_cut_inventory.get_laser_cut_part_by_name(group.base_part.name):
            quantity_in_stock = inventory_part.quantity
        else:
            quantity_in_stock = 0
        quantity_in_stock_item = QTableWidgetItem(f"{quantity_in_stock}")
        quantity_in_stock_item.setFont(self.tables_font)
        quantity_in_stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.QUANTITY_IN_STOCK.value, quantity_in_stock_item)
        table_items[group].update({"quantity_in_stock": quantity_in_stock_item})

        # PROCESS CONTROLS
        if not group.base_part.recut:
            flow_tag_controls_widget = self.get_flow_tag_controls(group)
            table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.PROCESS_CONTROLS.value, flow_tag_controls_widget)
            table_items[group].update({"flow_tag_controls": flow_tag_controls_widget})

        # SHELF NUMBER
        if not group.base_part.shelf_number:
            shelf_number_item = QTableWidgetItem("NA")
        else:
            shelf_number_item = QTableWidgetItem(group.base_part.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        shelf_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.SHELF_NUMBER.value, shelf_number_item)
        table_items[group].update({"shelf_number": shelf_number_item})

        # NOTES
        if not group.base_part.notes:
            notes_item = QTableWidgetItem("No notes provided")
        else:
            notes_item = QTableWidgetItem(group.base_part.notes)
        notes_item.setFont(self.tables_font)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.NOTES.value, notes_item)
        table_items[group].update({"notes": notes_item})

        # RECUT
        recut_button = QPushButton("Recut", self)
        if group.base_part.recut:
            recut_button.setToolTip("Part is recut. (recut=False)")
        else:
            recut_button.setToolTip("Request part to be recut. (recut=True)")
        recut_button.setFixedWidth(100)
        recut_button.clicked.connect(partial(self.recut_pressed, group))
        table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.RECUT.value, recut_button)

        # RECOAT
        recoat_button = QPushButton("Recoat", self)
        if group.base_part.recoat:
            recoat_button.setToolTip("Part is recoat. (recoat=False)")
        else:
            recoat_button.setToolTip("Request part to be recoat. (recoat=True)")
        recoat_button.setFixedWidth(100)
        recoat_button.clicked.connect(partial(self.recoat_pressed, group))
        table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.RECOAT.value, recoat_button)

    def recut_pressed(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        if laser_cut_part_group.base_part.recut:
            laser_cut_part_group.unmark_as_recut()
            self.load_parts_table()
            self.workspace.save()
            self.sync_changes()
        else:
            dialog = RecutDialog(f"Recut: {laser_cut_part_group.base_part.name}", laser_cut_part_group.get_quantity(), self)
            if dialog.exec():
                if not (recut_count := dialog.get_quantity()):
                    return
                for i in range(recut_count):
                    laser_cut_part_group.laser_cut_parts[i].mark_as_recut()
                    new_part = LaserCutPart(laser_cut_part_group.laser_cut_parts[i].to_dict(), self.laser_cut_inventory)
                    new_part.modified_date = f"Added from Workspace at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                    self.laser_cut_inventory.add_recut_part(new_part)
                    self.laser_cut_inventory.save()
                    self.upload_files([f"{self.laser_cut_inventory.filename}.json"])
                self.load_parts_table()
                self.workspace.save()
                self.sync_changes()

    def recoat_pressed(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        if laser_cut_part_group.base_part.recoat:
            laser_cut_part_group.unmark_as_recoat()
            self.load_parts_table()
            self.workspace.save()
            self.sync_changes()
        else:
            dialog = RecutDialog(f"Recoat: {laser_cut_part_group.base_part.name}", laser_cut_part_group.get_quantity(), self)
            if dialog.exec():
                if not (recut_count := dialog.get_quantity()):
                    return
                for i in range(recut_count):
                    laser_cut_part_group.laser_cut_parts[i].mark_as_recoat()
                self.load_parts_table()
                self.workspace.save()
                self.sync_changes()

    def get_paint_widget(self, item: Union[Assembly, LaserCutPart]) -> QWidget:
        widget = QWidget(self.parts_table_widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        if item.uses_primer and item.primer_item:
            primer_label = QLabel(f"{item.primer_item.name}", widget)
            layout.addWidget(primer_label)
        if item.uses_paint and item.paint_item:
            paint_label = QLabel(f"{item.paint_item.name}", widget)
            layout.addWidget(paint_label)
        if item.uses_powder and item.powder_item:
            powder_label = QLabel(f"{item.powder_item.name}", widget)
            layout.addWidget(powder_label)
        if not (item.uses_powder or item.uses_paint or item.uses_primer):
            label = QLabel("Not painted")
            layout.addWidget(label)
        return widget

    def add_laser_cut_part_drag_file_widget(
        self,
        item: Union[WorkspaceLaserCutPartGroup, Assembly],
        file_category: str,
        files_layout: QHBoxLayout,
        file_path: str,
    ):
        file_button = FileButton(f"{os.getcwd()}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.laser_cut_part_file_clicked, item, file_path))
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)
        self.parts_table_widget.resizeColumnsToContents()

    def create_file_layout(
        self,
        item: Union[WorkspaceLaserCutPartGroup, Assembly],
        file_types: list[
            Union[
                Literal["bending_files"],
                Literal["welding_files"],
                Literal["cnc_milling_files"],
                Literal["assembly_files"],
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
            if isinstance(item, Assembly):
                file_list: list[str] = getattr(item, file_type)
            elif isinstance(item, WorkspaceLaserCutPartGroup):
                file_list = item.get_files(file_type)
            for file in file_list:
                self.add_laser_cut_part_drag_file_widget(item, file_type, files_layout, file)
        return main_widget, files_layout

    def laser_cut_part_file_clicked(self, item: Union[WorkspaceLaserCutPartGroup, Assembly], file_path: str):
        self.download_file_thread = WorkspaceDownloadFile([file_path], True)
        self.download_file_thread.signal.connect(self.file_downloaded)
        self.download_file_thread.start()
        self.download_file_thread.wait()
        if file_path.lower().endswith(".pdf"):
            if isinstance(item, WorkspaceLaserCutPartGroup):
                self.open_pdf(
                    item.get_all_files(".pdf"),
                    file_path,
                )
            elif isinstance(item, Assembly):
                self.open_pdf(
                    item.assembly_files,
                    file_path,
                )

    def load_parts_table(self):
        if any(keyword in self.workspace_filter.current_tag.lower() for keyword in ["laser"]):
            self.parts_table_widget.showColumn(WorkspacePartsTableColumns.QUANTITY_IN_STOCK.value)
            self.recut_parts_widget.setVisible(True)
        else:
            self.parts_table_widget.hideColumn(WorkspacePartsTableColumns.QUANTITY_IN_STOCK.value)
            self.recut_parts_widget.setHidden(True)

        if any(keyword in self.workspace_filter.current_tag.lower() for keyword in ["powder", "coating", "liquid", "paint", "gloss", "prime"]):
            self.parts_table_widget.showColumn(WorkspacePartsTableColumns.RECOAT.value)
            self.recoat_parts_widget.setVisible(True)
        else:
            self.parts_table_widget.hideColumn(WorkspacePartsTableColumns.RECOAT.value)
            self.recoat_parts_widget.setHidden(True)

        self.parts_table_widget.blockSignals(True)
        self.recut_parts_table_widget.blockSignals(True)
        self.recoat_parts_table_widget.blockSignals(True)

        self.parts_table_items.clear()
        self.parts_table_rows.clear()
        self.parts_table_widget.setRowCount(0)

        self.recut_parts_table_items.clear()
        self.recut_parts_table_rows.clear()
        self.recut_parts_table_widget.setRowCount(0)

        self.recoat_parts_table_items.clear()
        self.recoat_parts_table_rows.clear()
        self.recoat_parts_table_widget.setRowCount(0)

        for job in self.workspace.jobs:
            if not (filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)):
                continue
            current_row = self.parts_table_widget.rowCount()
            self.parts_table_widget.insertRow(current_row)
            job_title_item = QTableWidgetItem(job.name)
            job_title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPointSize(15)
            job_title_item.setFont(font)
            self.parts_table_widget.setItem(current_row, 0, job_title_item)
            self.parts_table_widget.setSpan(current_row, 0, 1, self.parts_table_widget.columnCount())
            self.parts_table_widget.setRowHeight(current_row, self.parts_table_widget.row_height)
            grouped_parts = self.workspace.get_grouped_laser_cut_parts(filtered_parts)
            for laser_cut_part_group in grouped_parts:
                self.add_part_group_to_table(laser_cut_part_group)
        self.parts_table_widget.blockSignals(False)
        self.recut_parts_table_widget.blockSignals(False)
        self.recoat_parts_table_widget.blockSignals(False)
        self.parts_table_widget.resizeColumnsToContents()
        self.recut_parts_table_widget.resizeColumnsToContents()
        self.recoat_parts_table_widget.resizeColumnsToContents()

        self.parts_table_widget.setFixedHeight((self.parts_table_widget.rowCount() + 1) * self.parts_table_widget.row_height)
        self.recut_parts_table_widget.setFixedHeight((self.recut_parts_table_widget.rowCount() + 1) * self.recut_parts_table_widget.row_height)
        self.recoat_parts_table_widget.setFixedHeight((self.recoat_parts_table_widget.rowCount() + 1) * self.recoat_parts_table_widget.row_height)
        self.load_parts_table_context_menu()

    def load_parts_table_context_menu(self):
        if self.parts_table_widget.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
            return
        self.parts_table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        menu = QMenu(self)
        action = QAction("Move to Next Process", self)
        action.triggered.connect(self.move_parts_to_next_process)
        menu.addAction(action)

        self.parts_table_widget.customContextMenuRequested.connect(partial(self.open_context_menu, menu))

    def get_workspace_part_group_from_row(self, row: int) -> Optional[WorkspaceLaserCutPartGroup]:
        try:
            return self.parts_table_rows[row]
        except KeyError:
            return None

    def move_parts_to_next_process(self):
        for selected_row in self.parts_table_get_selected_rows():
            if not (selected_workspace_group := self.get_workspace_part_group_from_row(selected_row)):
                continue
            selected_workspace_group.move_to_next_process()
        self.check_if_jobs_are_complete()
        self.check_if_assemblies_are_ready_to_start_timer()
        self.load_parts_table()
        self.workspace.save()
        self.sync_changes()

    def parts_table_get_selected_rows(self) -> list[int]:
        selected_rows: set[int] = {item.row() for item in self.parts_table_widget.selectedItems()}
        return list(selected_rows)

    def parts_table_row_changed(self, row: int):
        pass

    # ASSEMBLIES
    def add_assembly_to_table(self, assembly: Assembly):
        current_row = self.assemblies_table_widget.rowCount()
        self.assemblies_table_rows.update({current_row: assembly})
        self.assemblies_table_items.update({assembly: {}})
        self.assemblies_table_widget.insertRow(current_row)
        self.assemblies_table_widget.setRowHeight(current_row, self.assemblies_table_widget.row_height)

        # PICTURE
        image_item = QTableWidgetItem("")
        if assembly.assembly_image:
            image = QPixmap(assembly.assembly_image)
            original_width = image.width()
            original_height = image.height()
            new_height = self.assemblies_table_widget.row_height
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.assemblies_table_widget.setRowHeight(current_row, new_height)
        self.assemblies_table_widget.setItem(current_row, WorkspaceAssemblyTableColumns.PICTURE.value, image_item)

        # NAME
        part_name_item = QTableWidgetItem(assembly.name)
        part_name_item.setFont(self.tables_font)
        self.assemblies_table_widget.setItem(current_row, WorkspaceAssemblyTableColumns.ASSEMBLY_NAME.value, part_name_item)
        self.assemblies_table_items[assembly].update({"name": part_name_item})

        # VIEW FILES BUTTON
        view_parts_button = QPushButton("View Parts", self)
        view_parts_button.clicked.connect(partial(self.view_assembly_parts, assembly))
        self.assemblies_table_widget.setCellWidget(current_row, WorkspaceAssemblyTableColumns.ASSEMBLY_PARTS_BUTTON.value, view_parts_button)

        # FILES
        if assembly.assembly_files:
            files_widget, files_layout = self.create_file_layout(assembly, ["assembly_files"])
        else:
            files_widget = QLabel("No files", self.assemblies_table_widget)
        self.assemblies_table_widget.setCellWidget(
            current_row,
            WorkspaceAssemblyTableColumns.ASSEMBLY_FILES.value,
            files_widget,
        )
        self.assemblies_table_items[assembly].update({"files": files_widget})

        # PROCESS CONTROLS
        flow_tag_controls_widget = self.get_flow_tag_controls(assembly)
        self.assemblies_table_widget.setCellWidget(current_row, WorkspaceAssemblyTableColumns.PROCESS_CONTROLS.value, flow_tag_controls_widget)
        self.assemblies_table_items[assembly].update({"flow_tag_controls": flow_tag_controls_widget})

        # PAINT
        paint_item = self.get_paint_widget(assembly)
        self.assemblies_table_widget.setCellWidget(current_row, WorkspaceAssemblyTableColumns.PAINT.value, paint_item)
        self.assemblies_table_items[assembly].update({"paint": paint_item})

    def load_assembly_table(self):
        self.assemblies_table_widget.blockSignals(True)
        self.assemblies_table_items.clear()
        self.assemblies_table_rows.clear()
        self.assemblies_table_widget.setRowCount(0)
        for job in self.workspace.jobs:
            if not (filtered_assemblies := self.workspace.get_filtered_assemblies(job)):
                continue
            current_row = self.assemblies_table_widget.rowCount()
            self.assemblies_table_widget.insertRow(current_row)
            job_title_item = QTableWidgetItem(job.name)
            job_title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPointSize(15)
            job_title_item.setFont(font)
            self.assemblies_table_widget.setItem(current_row, 0, job_title_item)
            self.assemblies_table_widget.setSpan(current_row, 0, 1, self.assemblies_table_widget.columnCount())
            self.assemblies_table_widget.setRowHeight(current_row, self.assemblies_table_widget.row_height)
            for assembly in filtered_assemblies:
                self.add_assembly_to_table(assembly)
        self.assemblies_table_widget.blockSignals(False)
        self.assemblies_table_widget.resizeColumnsToContents()
        self.assemblies_table_widget.setFixedHeight((self.assemblies_table_widget.rowCount() + 1) * self.assemblies_table_widget.row_height)
        self.load_assemblies_table_context_menu()

    def load_assemblies_table_context_menu(self):
        if self.assemblies_table_widget.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
            return
        self.assemblies_table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        menu = QMenu(self)
        action = QAction("Move to Next Process", self)
        action.triggered.connect(self.move_assemblies_to_next_process)
        menu.addAction(action)

        self.assemblies_table_widget.customContextMenuRequested.connect(partial(self.open_context_menu, menu))

    def get_assembly_from_row(self, row: int) -> Optional[Assembly]:
        try:
            return self.assemblies_table_rows[row]
        except KeyError:
            return None

    def move_assemblies_to_next_process(self):
        for selected_row in self.assemblies_table_get_selected_rows():
            if not (selected_assembly := self.get_assembly_from_row(selected_row)):
                continue
            selected_assembly.move_to_next_process()
        self.check_if_jobs_are_complete()
        self.check_if_assemblies_are_ready_to_start_timer()
        self.load_assembly_table()
        self.workspace.save()
        self.sync_changes()

    def assemblies_table_get_selected_rows(self) -> list[int]:
        selected_rows: set[int] = {item.row() for item in self.assemblies_table_widget.selectedItems()}
        return list(selected_rows)

    def assemblies_table_row_changed(self, row: int):
        pass

    def view_assembly_parts(self, assembly: Assembly):
        view_assembly_dialog = ViewAssemblyDialog(assembly, self.workspace, self)
        view_assembly_dialog.exec()

    # OTHER STUFF
    def open_context_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def get_flow_tag_controls(self, part_group_or_assembly: Union[WorkspaceLaserCutPartGroup, Assembly]) -> Union[QComboBox, QPushButton]:
        if isinstance(part_group_or_assembly, WorkspaceLaserCutPartGroup):
            item = part_group_or_assembly.base_part
        elif isinstance(part_group_or_assembly, Assembly):
            item = part_group_or_assembly
        current_tag = item.get_current_tag()
        if current_tag.statuses:
            flowtag_combobox = QComboBox(self)
            flowtag_combobox.setToolTip(current_tag.attribute.next_flow_tag_message)
            for status in current_tag.statuses:
                flowtag_combobox.addItem(status.name)
            flowtag_combobox.setCurrentIndex(item.current_flow_tag_status_index)
            if isinstance(part_group_or_assembly, WorkspaceLaserCutPartGroup):
                flowtag_combobox.currentIndexChanged.connect(partial(self.flowtag_combobox_changed, flowtag_combobox, part_group_or_assembly))
            elif isinstance(part_group_or_assembly, Assembly):
                flowtag_combobox.currentIndexChanged.connect(partial(self.flowtag_combobox_changed, flowtag_combobox, item))
            return flowtag_combobox
        else:
            try:
                button_text = f"Move to {item.flowtag.tags[item.current_flow_tag_index + 1].name}"
            except IndexError:
                button_text = "Mark as done"
            flowtag_button = QPushButton(button_text, self)
            flowtag_button.setToolTip(current_tag.attribute.next_flow_tag_message)
            if isinstance(part_group_or_assembly, WorkspaceLaserCutPartGroup):
                flowtag_button.clicked.connect(partial(self.move_item_process_forward, part_group_or_assembly))
            elif isinstance(part_group_or_assembly, Assembly):
                flowtag_button.clicked.connect(partial(self.move_item_process_forward, item))
            return flowtag_button

    def flowtag_combobox_changed(self, flowtag_combobox: QComboBox, part_group_or_assembly: Union[WorkspaceLaserCutPartGroup, Assembly]):
        if isinstance(part_group_or_assembly, WorkspaceLaserCutPartGroup):
            item = part_group_or_assembly
            status_index = flowtag_combobox.currentIndex()
            if item_flowtag := item.get_current_tag():
                current_status = item_flowtag.statuses[status_index]
                if current_status.marks_complete:
                    item.set_flow_tag_status_index(0)
                    self.move_item_process_forward(item)
                else:
                    item.set_flow_tag_status_index(status_index)
        elif isinstance(part_group_or_assembly, Assembly):
            item = part_group_or_assembly
            status_index = flowtag_combobox.currentIndex()
            if item_flowtag := item.get_current_tag():
                current_status = item_flowtag.statuses[status_index]
                if current_status.marks_complete:
                    item.current_flow_tag_status_index = 0
                    self.move_item_process_forward(item)
                else:
                    item.current_flow_tag_status_index = status_index
        self.workspace.save()
        self.sync_changes()

    def move_item_process_forward(self, part_group_or_assembly: Union[WorkspaceLaserCutPartGroup, Assembly]):
        if isinstance(part_group_or_assembly, WorkspaceLaserCutPartGroup):
            part_group_or_assembly.move_to_next_process()
        elif isinstance(part_group_or_assembly, Assembly):
            part_group_or_assembly.move_to_next_process()
        self.check_if_jobs_are_complete()
        self.check_if_assemblies_are_ready_to_start_timer()
        self.load_assembly_table()
        self.load_parts_table()
        self.workspace.save()
        self.sync_changes()

    def check_if_assemblies_are_ready_to_start_timer(self):
        for assembly in self.workspace.get_all_assemblies():
            if assembly.all_laser_cut_parts_complete() and not assembly.timer.has_started_timer():
                assembly.timer.start_timer()

    def check_if_jobs_are_complete(self):
        completed_jobs: list[Job] = []
        for job in self.workspace.jobs:
            if job.is_job_finished():
                self.workspace_history.add_job(job)
                completed_jobs.append(job)

        if completed_jobs:
            for job in completed_jobs:
                self.workspace.remove_job(job)
            self.workspace_history.save()

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

    def open_image(self, path: str, title: str):
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def sync_changes(self):
        self.parent.sync_changes()

    def upload_files(self, files_to_upload: list[str]):
        self.upload_thread = UploadThread(files_to_upload)
        self.upload_thread.start()

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
