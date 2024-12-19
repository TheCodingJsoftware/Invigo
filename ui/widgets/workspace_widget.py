import contextlib
import os
import shutil
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Literal, Optional, Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCursor, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom.file_button import FileButton
from ui.custom.workspace_assembly_table_widget import (
    WorkspaceAssemblyTableColumns,
    WorkspaceAssemblyTableWidget,
)
from ui.custom.workspace_assembly_tree_widget import (
    WorkspaceAssemblyTreeColumns,
    WorkspaceAssemblyTreeWidget,
)
from ui.custom.workspace_parts_table_widget import (
    WorkspacePartsTableColumns,
    WorkspacePartsTableWidget,
)
from ui.custom.workspace_parts_tree_widget import (
    WorkspacePartsTreeColumns,
    WorkspacePartsTreeWidget,
)
from ui.dialogs.recut_dialog import RecutDialog
from ui.dialogs.select_files_to_download_dialog import SelectFilesToDownloadDialog
from ui.dialogs.view_assembly_dialog import ViewAssemblyDialog
from ui.icons import Icons
from ui.widgets.workspace_widget_UI import Ui_Form
from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.threads.upload_thread import UploadThread
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.workspace.assembly import Assembly
from utils.workspace.workspace_assemply_group import WorkspaceAssemblyGroup
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup

if TYPE_CHECKING:
    from ui.widgets.workspace_tab_widget import WorkspaceTabWidget


class WorkspaceWidget(QWidget, Ui_Form):
    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.parent: WorkspaceTabWidget = parent
        self.workspace = self.parent.workspace
        self.workspace_settings = self.parent.workspace_settings
        self.workspace_filter = self.parent.workspace_filter

        self.laser_cut_inventory = self.workspace.laser_cut_inventory

        self.settings_file = Settings()

        self.username = os.getlogin().title()

        self.recut_parts_table_items: dict[
            WorkspaceLaserCutPartGroup, dict[str, Union[QTableWidgetItem]]
        ] = {}
        self.recoat_parts_table_items: dict[
            WorkspaceLaserCutPartGroup, dict[str, Union[QTableWidgetItem]]
        ] = {}
        self.parts_table_items: dict[
            WorkspaceLaserCutPartGroup, dict[str, Union[QTableWidgetItem]]
        ] = {}

        self.recut_parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.recoat_parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}

        self.parts_tree_index: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.parts_parent_tree_items: dict[
            str, dict[str, Union[bool, QTreeWidgetItem]]
        ] = {}

        self.assemblies_tree_index: dict[int, WorkspaceAssemblyGroup] = {}
        self.assemblies_parent_tree_items: dict[
            str, dict[str, Union[bool, QTreeWidgetItem]]
        ] = {}

        self.tables_font = QFont()
        self.tables_font.setFamily(
            self.settings_file.get_value("tables_font")["family"]
        )
        self.tables_font.setPointSize(
            self.settings_file.get_value("tables_font")["pointSize"]
        )
        self.tables_font.setWeight(
            self.settings_file.get_value("tables_font")["weight"]
        )
        self.tables_font.setItalic(
            self.settings_file.get_value("tables_font")["italic"]
        )

        self.load_ui()

    def load_ui(self):
        self.parts_tree_widget = WorkspacePartsTreeWidget(self)
        self.parts_tree_widget.itemExpanded.connect(self.tree_parts_item_expanded)
        self.parts_tree_widget.itemCollapsed.connect(self.tree_parts_item_collapsed)

        self.assemblies_tree_widget = WorkspaceAssemblyTreeWidget(self)
        self.assemblies_tree_widget.itemExpanded.connect(
            self.tree_assemblies_item_expanded
        )
        self.assemblies_tree_widget.itemCollapsed.connect(
            self.tree_assemblies_item_collapsed
        )

        self.recut_parts_table_widget = WorkspacePartsTableWidget(self)
        self.recut_parts_table_widget.hideColumn(
            WorkspacePartsTableColumns.RECOAT.value
        )

        self.recoat_parts_table_widget = WorkspacePartsTableWidget(self)

        self.parts_layout.addWidget(self.parts_tree_widget)

        self.recut_parts_layout.addWidget(self.recut_parts_table_widget)

        self.recoat_parts_layout.addWidget(self.recoat_parts_table_widget)

        self.assembly_widget.setHidden(True)
        self.assembly_layout.addWidget(self.assemblies_tree_widget)

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
            return

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
        table_widget.setItem(
            current_row, WorkspacePartsTableColumns.PART_NAME.value, part_name_item
        )

        # FILES
        if any(
            keyword in group.base_part.get_current_tag().name.lower()
            for keyword in ["weld", "assembly"]
        ):
            files_widget, files_layout = self.create_file_layout(
                group, ["welding_files"]
            )
        elif any(
            keyword in group.base_part.get_current_tag().name.lower()
            for keyword in ["bend", "break", "form"]
        ):
            files_widget, files_layout = self.create_file_layout(
                group, ["bending_files"]
            )
        elif any(
            keyword in group.base_part.get_current_tag().name.lower()
            for keyword in ["cnc", "laser", "cutting", "milling", "thread"]
        ):
            files_widget, files_layout = self.create_file_layout(
                group, ["cnc_milling_files"]
            )
        else:
            files_widget = QLabel("No files", table_widget)
        table_widget.setCellWidget(
            current_row,
            WorkspacePartsTableColumns.FILES.value,
            files_widget,
        )
        table_items[group].update({"files": files_widget})

        # MATERIAL
        material_item = QTableWidgetItem(
            f"{group.base_part.gauge} {group.base_part.material}"
        )
        material_item.setFont(self.tables_font)
        table_widget.setItem(
            current_row, WorkspacePartsTableColumns.MATERIAL.value, material_item
        )
        table_items[group].update({"material": material_item})

        # PAINT
        paint_item = self.get_paint_widget(group.base_part)
        table_items[group].update({"paint": paint_item})
        table_widget.setCellWidget(
            current_row, WorkspacePartsTableColumns.PAINT.value, paint_item
        )

        # QUANTITY
        quantity_item = QTableWidgetItem(f"{group.get_count()}")
        quantity_item.setFont(self.tables_font)
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(
            current_row, WorkspacePartsTableColumns.QUANTITY.value, quantity_item
        )
        table_items[group].update({"quantity": quantity_item})

        # QUANTITY IN STOCK
        if inventory_part := self.laser_cut_inventory.get_laser_cut_part_by_name(
            group.base_part.name
        ):
            quantity_in_stock = inventory_part.quantity
        else:
            quantity_in_stock = 0
        quantity_in_stock_item = QTableWidgetItem(f"{quantity_in_stock}")
        quantity_in_stock_item.setFont(self.tables_font)
        quantity_in_stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(
            current_row,
            WorkspacePartsTableColumns.QUANTITY_IN_STOCK.value,
            quantity_in_stock_item,
        )
        table_items[group].update({"quantity_in_stock": quantity_in_stock_item})

        # PROCESS CONTROLS
        if not group.base_part.recut:
            flow_tag_controls_widget = self.get_flow_tag_controls(group)
            table_items[group].update({"flow_tag_controls": flow_tag_controls_widget})
            table_widget.setCellWidget(
                current_row,
                WorkspacePartsTableColumns.PROCESS_CONTROLS.value,
                flow_tag_controls_widget,
            )

        # SHELF NUMBER
        if not group.base_part.shelf_number:
            shelf_number_item = QTableWidgetItem("NA")
        else:
            shelf_number_item = QTableWidgetItem(group.base_part.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        shelf_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(
            current_row,
            WorkspacePartsTableColumns.SHELF_NUMBER.value,
            shelf_number_item,
        )
        table_items[group].update({"shelf_number": shelf_number_item})

        # NOTES
        if not group.base_part.notes:
            notes_item = QTableWidgetItem("No notes provided")
        else:
            notes_item = QTableWidgetItem(group.base_part.notes)
        notes_item.setFont(self.tables_font)
        table_widget.setItem(
            current_row, WorkspacePartsTableColumns.NOTES.value, notes_item
        )
        table_items[group].update({"notes": notes_item})

        # RECUT
        recut_button = QPushButton("Recut", self)

        if group.base_part.recut:
            recut_button.setToolTip("Part is recut. (set recut=False)")
            recut_button.setIcon(Icons.check_fill_icon)
        else:
            recut_button.setToolTip("Request part to be recut. (set recut=True)")
            recut_button.setIcon(Icons.recut_icon)
        recut_button.setFixedWidth(100)
        recut_button.clicked.connect(partial(self.recut_pressed, group))
        table_widget.setCellWidget(
            current_row, WorkspacePartsTableColumns.RECUT.value, recut_button
        )

        # RECOAT
        recoat_button = QPushButton("Recoat", self)
        if group.base_part.recoat:
            recoat_button.setToolTip("Part is recoated. (set recoat=False)")
            recoat_button.setIcon(Icons.check_fill_icon)
        else:
            recoat_button.setToolTip("Request part to be recoat. (set recoat=True)")
            recoat_button.setIcon(Icons.recut_icon)
        recoat_button.setFixedWidth(100)
        recoat_button.clicked.connect(partial(self.recoat_pressed, group))
        table_widget.setCellWidget(
            current_row, WorkspacePartsTableColumns.RECOAT.value, recoat_button
        )

    def add_part_group_to_tree(
        self, group: WorkspaceLaserCutPartGroup, parent: QTreeWidgetItem
    ):
        if group.base_part.recut or group.base_part.recoat:
            return
        # PART NAME
        part_tree_widget_item = QTreeWidgetItem(parent)
        parent.addChild(part_tree_widget_item)
        self.parts_tree_index.update({id(part_tree_widget_item): group})
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.PART_NAME.value, group.base_part.name
        )
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.MATERIAL.value,
            f"{group.base_part.gauge} {group.base_part.material}",
        )
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.QUANTITY.value, f"{group.get_count():,.2f}"
        )

        if inventory_part := self.laser_cut_inventory.get_laser_cut_part_by_name(
            group.base_part.name
        ):
            quantity_in_stock = inventory_part.quantity
        else:
            quantity_in_stock = 0

        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value,
            f"{quantity_in_stock:,.2f}",
        )
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.NOTES.value, f"{group.base_part.notes}"
        )
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.SHELF_NUMBER.value,
            f"{group.base_part.shelf_number}",
        )

        # PAINT
        paint_item = self.get_paint_widget(group.base_part)
        self.parts_tree_widget.setItemWidget(
            part_tree_widget_item, WorkspacePartsTreeColumns.PAINT.value, paint_item
        )
        # FILES
        if any(
            keyword in group.base_part.get_current_tag().name.lower()
            for keyword in ["weld", "assembly"]
        ):
            files_widget, files_layout = self.create_file_layout(
                group, ["welding_files"]
            )
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.FILES.value,
                files_widget,
            )
        elif any(
            keyword in group.base_part.get_current_tag().name.lower()
            for keyword in ["bend", "break", "form"]
        ):
            files_widget, files_layout = self.create_file_layout(
                group, ["bending_files"]
            )
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.FILES.value,
                files_widget,
            )
        elif any(
            keyword in group.base_part.get_current_tag().name.lower()
            for keyword in ["cnc", "laser", "cutting", "milling", "thread"]
        ):
            files_widget, files_layout = self.create_file_layout(
                group, ["cnc_milling_files"]
            )
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.FILES.value,
                files_widget,
            )
        else:
            part_tree_widget_item.setText(
                WorkspacePartsTreeColumns.FILES.value, "No files"
            )

        # PROCESS CONTROLS
        if not group.base_part.recut:
            flow_tag_controls_widget = self.get_flow_tag_controls(group)
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                flow_tag_controls_widget,
            )

        # RECUT
        recut_button = QPushButton("Recut", self)
        if group.base_part.recut:
            recut_button.setToolTip("Part is recut. (set recut=False)")
            recut_button.setIcon(Icons.check_fill_icon)
        else:
            recut_button.setToolTip("Request part to be recut. (set recut=True)")
            recut_button.setIcon(Icons.recut_icon)
        recut_button.setFixedWidth(100)
        recut_button.clicked.connect(partial(self.recut_pressed, group))
        self.parts_tree_widget.setItemWidget(
            part_tree_widget_item, WorkspacePartsTreeColumns.RECUT.value, recut_button
        )

        # RECOAT
        recoat_button = QPushButton("Recoat", self)
        if group.base_part.recoat:
            recoat_button.setToolTip("Part is recoated. (set recoat=False)")
            recoat_button.setIcon(Icons.check_fill_icon)
        else:
            recoat_button.setToolTip("Request part to be recoat. (set recoat=True)")
            recoat_button.setIcon(Icons.recoat_icon)
        recoat_button.setFixedWidth(100)
        recoat_button.clicked.connect(partial(self.recoat_pressed, group))
        self.parts_tree_widget.setItemWidget(
            part_tree_widget_item, WorkspacePartsTreeColumns.RECOAT.value, recoat_button
        )

    def tree_parts_item_expanded(self, item: QTreeWidgetItem):
        self.parts_parent_tree_items[item.text(0)]["is_expanded"] = item.isExpanded()
        job = self.parts_parent_tree_items[item.text(0)]["job"]

        if not (filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)):
            return

        parent_job_item = self.parts_parent_tree_items[item.text(0)]["item"]
        grouped_parts = self.workspace.get_grouped_laser_cut_parts(filtered_parts)
        for laser_cut_part_group in grouped_parts:
            self.add_part_group_to_tree(laser_cut_part_group, parent_job_item)

    def tree_parts_item_collapsed(self, item: QTreeWidgetItem):
        self.parts_parent_tree_items[item.text(0)]["is_expanded"] = item.isExpanded()
        item.takeChildren()

    def recut_pressed(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        if laser_cut_part_group.base_part.recut:
            laser_cut_part_group.unmark_as_recut()
            self.load_parts_table()
            self.load_parts_tree()
            self.workspace.save()
            self.sync_changes()
        else:
            dialog = RecutDialog(
                f"Recut: {laser_cut_part_group.base_part.name}",
                laser_cut_part_group.get_count(),
                self,
            )
            if dialog.exec():
                if not (recut_count := dialog.get_quantity()):
                    return
                for i in range(recut_count):
                    laser_cut_part_group.laser_cut_parts[i].mark_as_recut()
                    new_part = LaserCutPart(
                        laser_cut_part_group.laser_cut_parts[i].to_dict(),
                        self.laser_cut_inventory,
                    )
                    new_part.modified_date = f"Added from Workspace at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                    self.laser_cut_inventory.add_recut_part(new_part)
                    self.laser_cut_inventory.save()
                    self.upload_files([f"{self.laser_cut_inventory.filename}.json"])
                self.load_parts_table()
                self.load_parts_tree()
                self.workspace.save()
                self.sync_changes()

    def recoat_pressed(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        if laser_cut_part_group.base_part.recoat:
            laser_cut_part_group.unmark_as_recoat()
            self.load_parts_table()
            self.load_parts_tree()
            self.workspace.save()
            self.sync_changes()
        else:
            dialog = RecutDialog(
                f"Recoat: {laser_cut_part_group.base_part.name}",
                laser_cut_part_group.get_count(),
                self,
            )
            if dialog.exec():
                if not (recut_count := dialog.get_quantity()):
                    return
                for i in range(recut_count):
                    laser_cut_part_group.laser_cut_parts[i].mark_as_recoat()
                self.load_parts_table()
                self.load_parts_tree()
                self.workspace.save()
                self.sync_changes()

    def get_paint_widget(self, item: Union[Assembly, LaserCutPart]) -> QWidget:
        widget = QWidget(self)
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
        item: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
        file_category: str,
        files_layout: QHBoxLayout,
        file_path: str,
    ):
        file_button = FileButton(f"{os.getcwd()}\\{file_path}", self)
        file_button.buttonClicked.connect(
            partial(self.laser_cut_part_file_clicked, item, file_path)
        )
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)

    def create_file_layout(
        self,
        item: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
        file_types: list[
            Union[
                Literal["bending_files"],
                Literal["welding_files"],
                Literal["cnc_milling_files"],
                Literal["assembly_files"],
            ]
        ],
    ) -> tuple[QWidget, QHBoxLayout]:
        main_widget = QWidget(self)
        main_widget.setObjectName("main_widget")
        main_widget.setStyleSheet("QWidget#main_widget{background-color: transparent;}")
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        files_widget = QWidget()
        files_widget.setObjectName("files_widget")
        files_widget.setStyleSheet(
            "QWidget#files_widget{background-color: transparent;}"
        )
        files_layout = QHBoxLayout(files_widget)
        files_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        files_layout.setContentsMargins(0, 0, 6, 0)
        files_layout.setSpacing(6)

        scroll_area = QScrollArea()
        scroll_area.setWidget(files_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(100)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        main_layout.addWidget(scroll_area)

        for file_type in file_types:
            if isinstance(item, WorkspaceAssemblyGroup):
                file_list: list[str] = item.get_all_files()
            elif isinstance(item, WorkspaceLaserCutPartGroup):
                file_list = item.get_files(file_type)
            for file in file_list:
                self.add_laser_cut_part_drag_file_widget(
                    item, file_type, files_layout, file
                )
        return main_widget, files_layout

    def laser_cut_part_file_clicked(
        self,
        item: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
        file_path: str,
    ):
        self.download_file_thread = WorkspaceDownloadFile([file_path], True)
        self.download_file_thread.signal.connect(self.file_downloaded)
        self.download_file_thread.start()
        self.download_file_thread.wait()
        if file_path.lower().endswith(".pdf"):
            if isinstance(item, WorkspaceLaserCutPartGroup):
                self.open_pdf(
                    item.get_all_files_with_ext(".pdf"),
                    file_path,
                )
            elif isinstance(item, WorkspaceAssemblyGroup):
                self.open_pdf(
                    item.get_files(".pdf"),
                    file_path,
                )

    def load_parts_tree(self):
        if any(
            keyword in self.workspace_filter.current_tag.lower()
            for keyword in ["laser"]
        ):
            self.parts_tree_widget.showColumn(
                WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value
            )
            self.parts_tree_widget.hideColumn(WorkspacePartsTreeColumns.RECUT.value)
            self.recut_parts_widget.setVisible(True)
        else:
            self.parts_tree_widget.hideColumn(
                WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value
            )
            self.parts_tree_widget.showColumn(WorkspacePartsTreeColumns.RECUT.value)
            self.recut_parts_widget.setHidden(True)
        if any(
            keyword in self.workspace_filter.current_tag.lower()
            for keyword in ["powder", "coating", "liquid", "paint", "gloss", "prime"]
        ):
            self.parts_tree_widget.showColumn(WorkspacePartsTreeColumns.RECOAT.value)
            self.recoat_parts_widget.setVisible(True)
        else:
            self.parts_tree_widget.hideColumn(WorkspacePartsTreeColumns.RECOAT.value)
            self.recoat_parts_widget.setHidden(True)

        self.parts_tree_widget.blockSignals(True)
        self.parts_tree_widget.clear()
        self.parts_tree_index.clear()

        font = QFont()
        font.setPointSize(15)

        for job in self.workspace.jobs:
            if not (filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)):
                continue

            parent_job_item = QTreeWidgetItem(self.parts_tree_widget)
            parent_job_item.setText(
                0,
                f"{job.name} #{job.order_number}: {job.starting_date} - {job.ending_date}",
            )
            parent_job_item.setFont(0, font)
            parent_job_item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )
            parent_job_item.setFirstColumnSpanned(True)
            self.parts_parent_tree_items.setdefault(
                parent_job_item.text(0),
                {"job": job, "item": parent_job_item, "is_expanded": False},
            )
            self.parts_parent_tree_items[parent_job_item.text(0)]["item"] = (
                parent_job_item
            )
            self.parts_tree_widget.addTopLevelItem(parent_job_item)

            if self.parts_parent_tree_items[parent_job_item.text(0)].get(
                "is_expanded", False
            ):
                self.parts_tree_widget.expandItem(parent_job_item)
                grouped_parts = self.workspace.get_grouped_laser_cut_parts(
                    filtered_parts
                )
                for laser_cut_part_group in grouped_parts:
                    self.add_part_group_to_tree(laser_cut_part_group, parent_job_item)

        self.parts_tree_widget.setColumnWidth(
            WorkspacePartsTreeColumns.PART_NAME.value, 200
        )
        self.parts_tree_widget.setColumnWidth(
            WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value, 100
        )
        self.parts_tree_widget.setColumnWidth(
            WorkspacePartsTreeColumns.MATERIAL.value, 150
        )
        self.parts_tree_widget.setColumnWidth(
            WorkspacePartsTreeColumns.PROCESS_CONTROLS.value, 150
        )
        self.parts_tree_widget.setColumnWidth(
            WorkspacePartsTreeColumns.PAINT.value, 100
        )
        self.parts_tree_widget.blockSignals(False)
        self.parts_tree_widget.resizeColumnToContents(
            WorkspacePartsTreeColumns.NOTES.value
        )

    def load_parts_table(self):
        if any(
            keyword in self.workspace_filter.current_tag.lower()
            for keyword in ["laser"]
        ):
            self.recut_parts_widget.setVisible(True)
        else:
            self.recut_parts_widget.setHidden(True)

        if any(
            keyword in self.workspace_filter.current_tag.lower()
            for keyword in ["powder", "coating", "liquid", "paint", "gloss", "prime"]
        ):
            self.recoat_parts_widget.setVisible(True)
        else:
            self.recoat_parts_widget.setHidden(True)

        self.recut_parts_table_widget.blockSignals(True)
        self.recoat_parts_table_widget.blockSignals(True)
        self.parts_table_items.clear()

        self.recut_parts_table_items.clear()
        self.recut_parts_table_rows.clear()
        self.recut_parts_table_widget.setRowCount(0)

        self.recoat_parts_table_items.clear()
        self.recoat_parts_table_rows.clear()
        self.recoat_parts_table_widget.setRowCount(0)

        for job in self.workspace.jobs:
            font = QFont()
            font.setPointSize(15)

            if not (filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)):
                continue
            job_title_item = QTableWidgetItem(job.name)
            job_title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            job_title_item.setFont(font)
            grouped_parts = self.workspace.get_grouped_laser_cut_parts(filtered_parts)
            for laser_cut_part_group in grouped_parts:
                self.add_part_group_to_table(laser_cut_part_group)
        self.recut_parts_table_widget.blockSignals(False)
        self.recoat_parts_table_widget.blockSignals(False)
        self.recut_parts_table_widget.resizeColumnsToContents()
        self.recoat_parts_table_widget.resizeColumnsToContents()
        self.recut_parts_table_widget.setFixedHeight(
            (self.recut_parts_table_widget.rowCount() + 1)
            * self.recut_parts_table_widget.row_height
        )
        self.recoat_parts_table_widget.setFixedHeight(
            (self.recoat_parts_table_widget.rowCount() + 1)
            * self.recoat_parts_table_widget.row_height
        )
        self.load_parts_table_context_menu()

    def load_parts_table_context_menu(self):
        if (
            self.parts_tree_widget.contextMenuPolicy()
            == Qt.ContextMenuPolicy.CustomContextMenu
        ):
            return
        self.parts_tree_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        menu = QMenu(self)

        move_to_next_process_action = QAction("Move to Next Process", self)
        move_to_next_process_action.triggered.connect(self.move_parts_to_next_process)

        download_files_action = QAction("Download files", self)
        download_files_action.triggered.connect(self.download_files)

        menu.addAction(move_to_next_process_action)
        menu.addAction(download_files_action)

        self.parts_tree_widget.customContextMenuRequested.connect(
            partial(self.open_context_menu, menu)
        )

    def move_parts_to_next_process(self):
        if selected_items := self.parts_tree_get_selected_items():
            for selected_item in selected_items:
                selected_item.move_to_next_process()
            self.check_if_assemblies_are_ready_to_start_timer()
            self.load_parts_table()
            self.load_parts_tree()
            self.workspace.save()
            self.laser_cut_inventory.save()
            self.sync_changes()

    def download_files(self):
        files: set[str] = set()
        if selected_items := self.parts_tree_get_selected_items():
            for selected_item in selected_items:
                files.update(selected_item.get_all_files())

        files_dialog = SelectFilesToDownloadDialog(files, self)
        if files_dialog.exec():
            self.files_to_download = files_dialog.get_selected_items()
            self.download_directory = files_dialog.get_download_directory()
            if self.files_to_download and self.download_directory:
                self.download_thread = WorkspaceDownloadFile(
                    self.files_to_download,
                    False,
                    download_directory=self.download_directory,
                )
                self.download_thread.signal.connect(self.download_thread_response)
                self.download_thread.start()
            else:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Error")
                msg.setText("Please select files to download and a download directory.")
                msg.exec()

    def download_thread_response(self, response: str):
        os.startfile(self.download_directory)

    def parts_tree_get_selected_items(self) -> list[WorkspaceLaserCutPartGroup]:
        selected_items: list[WorkspaceLaserCutPartGroup] = []
        for item in self.parts_tree_widget.selectedItems():
            if item.parent() is not None:
                selected_items.append(self.parts_tree_index[id(item)])
        return selected_items

    # ASSEMBLIES
    def add_assembly_group_to_tree(
        self, group: WorkspaceAssemblyGroup, parent: QTreeWidgetItem
    ):
        assembly_tree_widget_item = QTreeWidgetItem(parent)
        parent.addChild(assembly_tree_widget_item)

        self.assemblies_tree_index.update({id(assembly_tree_widget_item): group})

        assembly_tree_widget_item.setText(
            WorkspaceAssemblyTreeColumns.ASSEMBLY_NAME.value,
            f"{group.base_assembly.name}",
        )
        assembly_tree_widget_item.setText(
            WorkspaceAssemblyTreeColumns.QUANTITY.value, f"{group.get_quantity()}"
        )
        assembly_tree_widget_item.setFont(
            WorkspaceAssemblyTreeColumns.ASSEMBLY_NAME.value, self.tables_font
        )
        assembly_tree_widget_item.setFont(
            WorkspaceAssemblyTreeColumns.QUANTITY.value, self.tables_font
        )

        # PICTURE
        if group.base_assembly.assembly_image:
            image = QPixmap(group.base_assembly.assembly_image)
            original_width = image.width()
            original_height = image.height()
            new_height = self.assemblies_tree_widget.ROW_HEIGHT
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(
                new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio
            )
            icon = QIcon(pixmap)
            assembly_tree_widget_item.setIcon(
                WorkspaceAssemblyTreeColumns.PICTURE.value, icon
            )

        # VIEW FILES BUTTON
        view_parts_button = QPushButton("View Parts", self)
        view_parts_button.clicked.connect(
            partial(self.view_assembly_parts, group.base_assembly)
        )
        self.assemblies_tree_widget.setItemWidget(
            assembly_tree_widget_item,
            WorkspaceAssemblyTreeColumns.ASSEMBLY_PARTS_BUTTON.value,
            view_parts_button,
        )

        # FILES
        if group.get_all_files():
            files_widget, files_layout = self.create_file_layout(
                group, ["assembly_files"]
            )
            self.assemblies_tree_widget.setItemWidget(
                assembly_tree_widget_item,
                WorkspaceAssemblyTreeColumns.ASSEMBLY_FILES.value,
                files_widget,
            )
        else:
            assembly_tree_widget_item.setText(
                WorkspaceAssemblyTreeColumns.ASSEMBLY_FILES.value, "No files"
            )

        # PROCESS CONTROLS
        flow_tag_controls_widget = self.get_flow_tag_controls(group)
        self.assemblies_tree_widget.setItemWidget(
            assembly_tree_widget_item,
            WorkspaceAssemblyTreeColumns.PROCESS_CONTROLS.value,
            flow_tag_controls_widget,
        )

        # PAINT
        paint_item = self.get_paint_widget(group.base_assembly)
        self.assemblies_tree_widget.setItemWidget(
            assembly_tree_widget_item,
            WorkspaceAssemblyTreeColumns.PAINT.value,
            paint_item,
        )

    def tree_assemblies_item_expanded(self, item: QTreeWidgetItem):
        self.assemblies_parent_tree_items[item.text(0)]["is_expanded"] = (
            item.isExpanded()
        )
        job = self.assemblies_parent_tree_items[item.text(0)]["job"]

        if not (filtered_parts := self.workspace.get_filtered_assemblies(job)):
            return

        parent_job_item = self.assemblies_parent_tree_items[item.text(0)]["item"]
        grouped_assemblies = self.workspace.get_grouped_assemblies(filtered_parts)
        for assembly_group in grouped_assemblies:
            self.add_assembly_group_to_tree(assembly_group, parent_job_item)

    def tree_assemblies_item_collapsed(self, item: QTreeWidgetItem):
        self.assemblies_parent_tree_items[item.text(0)]["is_expanded"] = (
            item.isExpanded()
        )
        item.takeChildren()

    def load_assembly_tree(self):
        self.assemblies_tree_widget.blockSignals(True)
        self.assemblies_tree_widget.clear()
        self.assemblies_tree_index.clear()

        font = QFont()
        font.setPointSize(15)

        for job in self.workspace.jobs:
            if not (filtered_assemblies := self.workspace.get_filtered_assemblies(job)):
                continue

            parent_job_item = QTreeWidgetItem(self.assemblies_tree_widget)
            parent_job_item.setText(
                0,
                f"{job.name} #{job.order_number}: {job.starting_date} - {job.ending_date}",
            )
            parent_job_item.setFont(0, font)
            parent_job_item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )
            parent_job_item.setFirstColumnSpanned(True)
            self.assemblies_parent_tree_items.setdefault(
                parent_job_item.text(0),
                {"job": job, "item": parent_job_item, "is_expanded": False},
            )
            self.assemblies_parent_tree_items[parent_job_item.text(0)]["item"] = (
                parent_job_item
            )
            self.assemblies_tree_widget.addTopLevelItem(parent_job_item)

            if self.assemblies_parent_tree_items[parent_job_item.text(0)].get(
                "is_expanded", False
            ):
                self.assemblies_tree_widget.expandItem(parent_job_item)
                grouped_assemblies = self.workspace.get_grouped_assemblies(
                    filtered_assemblies
                )
                for assembly_group in grouped_assemblies:
                    self.add_assembly_group_to_tree(assembly_group, parent_job_item)

        self.assemblies_tree_widget.setColumnWidth(
            WorkspaceAssemblyTreeColumns.ASSEMBLY_NAME.value, 200
        )
        self.assemblies_tree_widget.setColumnWidth(
            WorkspaceAssemblyTreeColumns.QUANTITY.value, 100
        )
        self.assemblies_tree_widget.setColumnWidth(
            WorkspaceAssemblyTreeColumns.PAINT.value, 100
        )
        self.assemblies_tree_widget.setColumnWidth(
            WorkspaceAssemblyTreeColumns.PROCESS_CONTROLS.value, 150
        )
        self.assemblies_tree_widget.blockSignals(False)
        self.load_assemblies_table_context_menu()

    def load_assemblies_table_context_menu(self):
        if (
            self.assemblies_tree_widget.contextMenuPolicy()
            == Qt.ContextMenuPolicy.CustomContextMenu
        ):
            return
        self.assemblies_tree_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        menu = QMenu(self)
        action = QAction("Move to Next Process", self)
        action.triggered.connect(self.move_assemblies_to_next_process)
        menu.addAction(action)

        self.assemblies_tree_widget.customContextMenuRequested.connect(
            partial(self.open_context_menu, menu)
        )

    def move_assemblies_to_next_process(self):
        if selected_items := self.assemblies_tree_get_selected_items():
            for selected_item in selected_items:
                selected_item.move_to_next_process()
            self.check_if_assemblies_are_ready_to_start_timer()
            self.load_assembly_tree()
            self.workspace.save()
            self.sync_changes()

    def assemblies_tree_get_selected_items(self) -> list[WorkspaceAssemblyGroup]:
        selected_items: list[WorkspaceAssemblyGroup] = []
        for item in self.assemblies_tree_widget.selectedItems():
            if item.parent() is not None:
                selected_items.append(self.assemblies_tree_index[id(item)])
        return selected_items

    def assemblies_table_row_changed(self, row: int):
        pass

    def view_assembly_parts(self, assembly: Assembly):
        view_assembly_dialog = ViewAssemblyDialog(assembly, self.workspace, self)
        view_assembly_dialog.exec()

    # OTHER STUFF
    def open_context_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def get_flow_tag_controls(
        self,
        part_group_or_assembly_group: Union[
            WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup
        ],
    ) -> Union[QComboBox, QPushButton]:
        if isinstance(part_group_or_assembly_group, WorkspaceLaserCutPartGroup):
            item = part_group_or_assembly_group.base_part
        elif isinstance(part_group_or_assembly_group, WorkspaceAssemblyGroup):
            item = part_group_or_assembly_group.base_assembly
        current_tag = part_group_or_assembly_group.get_current_tag()
        if current_tag.statuses:
            flowtag_combobox = QComboBox(self)
            flowtag_combobox.setToolTip(current_tag.attributes.next_flow_tag_message)
            flowtag_combobox.wheelEvent = lambda event: self.parent.wheelEvent(event)
            for status in current_tag.statuses:
                flowtag_combobox.addItem(status.name)
            flowtag_combobox.setCurrentIndex(item.current_flow_tag_status_index)
            flowtag_combobox.currentIndexChanged.connect(
                partial(
                    self.flowtag_combobox_changed,
                    flowtag_combobox,
                    part_group_or_assembly_group,
                )
            )
            return flowtag_combobox
        else:
            try:
                flowtag_button = QPushButton(
                    f"Move to {item.flowtag.tags[item.current_flow_tag_index + 1].name}",
                    self,
                )
                flowtag_button.setIcon(Icons.arrow_right_fill_icon)
            except IndexError:
                flowtag_button = QPushButton("Mark as done", self)
                flowtag_button.setIcon(Icons.check_fill_icon)
            flowtag_button.setToolTip(current_tag.attributes.next_flow_tag_message)
            flowtag_button.clicked.connect(
                partial(self.move_item_process_forward, part_group_or_assembly_group)
            )
            return flowtag_button

    def flowtag_combobox_changed(
        self,
        flowtag_combobox: QComboBox,
        part_group_or_assembly: Union[
            WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup
        ],
    ):
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
        elif isinstance(part_group_or_assembly, WorkspaceAssemblyGroup):
            item = part_group_or_assembly
            status_index = flowtag_combobox.currentIndex()
            if item_flowtag := item.get_current_tag():
                current_status = item_flowtag.statuses[status_index]
                if current_status.marks_complete:
                    item.set_flow_tag_status_index(0)
                    self.move_item_process_forward(item)
                else:
                    item.set_flow_tag_status_index(status_index)
        self.workspace.save()
        self.sync_changes()

    def move_item_process_forward(
        self,
        part_group_or_assembly: Union[
            WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup
        ],
    ):
        part_group_or_assembly.move_to_next_process()
        self.check_if_assemblies_are_ready_to_start_timer()
        self.load_assembly_tree()
        self.load_parts_table()
        self.load_parts_tree()
        self.workspace.save()
        self.laser_cut_inventory.save()
        self.sync_changes()

    def check_if_assemblies_are_ready_to_start_timer(self):
        for assembly in self.workspace.get_all_assemblies():
            if (
                assembly.all_laser_cut_parts_complete()
                and not assembly.timer.has_started_timer()
            ):
                assembly.timer.start_timer()

    def file_downloaded(
        self, file_ext: Optional[str], file_name: str, open_when_done: bool
    ):
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
