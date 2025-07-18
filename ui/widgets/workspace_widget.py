import contextlib
import os
import platform
import subprocess
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Literal, Optional, Union

import msgspec
from PyQt6.QtCore import Qt, QThread, QThreadPool, pyqtSignal
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
from PyQt6.sip import isdeleted

from config.environments import Environment
from ui.custom.file_button import FileButton
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
from ui.theme import theme_var
from ui.widgets.workspace_widget_UI import Ui_Form
from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
from utils.colors import get_on_color_from_primary, lighten_color
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.threads.upload_thread import UploadThread
from utils.workers.workspace.download_file import WorkspaceDownloadWorker
from utils.workers.workspace.get_all_workspace_jobs import (
    GetAllWorkspaceJobsWorker,
)
from utils.workers.workspace.get_recut_parts_from_workspace import (
    GetRecutPartsFromWorkspaceWorker,
)
from utils.workers.workspace.load_job_from_workspace import (
    LoadJobFromWorkspaceWorker,
)
from utils.workers.workspace.update_workspace_entries import (
    UpdateWorkspaceEntriesWorker,
)
from utils.workers.workspace.update_workspace_entry import (
    UpdateWorkspaceEntryWorker,
)
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_assemply_group import WorkspaceAssemblyGroup
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup

if TYPE_CHECKING:
    from ui.widgets.workspace_tab_widget import WorkspaceTabWidget


class WorkspaceWidget(QWidget, Ui_Form):
    loadedAllJobs = pyqtSignal(list)

    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self._parent_widget: WorkspaceTabWidget = parent
        self.workspace: Workspace = self._parent_widget.workspace
        self.workspace_settings = self._parent_widget.workspace_settings
        self.workspace_filter = self._parent_widget.workspace_filter
        self.threads: list[QThread] = []
        self.laser_cut_inventory = self.workspace.laser_cut_inventory
        self.components_inventory = self.workspace.components_inventory
        self.job_manager = self.workspace.job_manager

        self.settings_file = Settings()

        self.username = os.getlogin().title()
        self.get_workspace_job = None

        self.recut_parts_table_items: dict[WorkspaceLaserCutPartGroup, dict[str, QTableWidgetItem]] = {}
        self.recoat_parts_table_items: dict[WorkspaceLaserCutPartGroup, dict[str, QTableWidgetItem]] = {}
        self.parts_table_items: dict[WorkspaceLaserCutPartGroup, dict[str, QTableWidgetItem]] = {}

        self.recut_parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.recoat_parts_table_rows: dict[int, WorkspaceLaserCutPartGroup] = {}

        self.parts_tree_index: dict[int, WorkspaceLaserCutPartGroup] = {}
        self.parts_parent_tree_items: dict[
            str,
            dict[
                str,
                Union[
                    bool,
                    list[dict[str, Union[QTreeWidgetItem, WorkspaceLaserCutPartGroup]]],
                    QTreeWidgetItem,
                ],
            ],
        ] = {}

        self.assemblies_tree_index: dict[int, WorkspaceAssemblyGroup] = {}
        self.assemblies_parent_tree_items: dict[
            str,
            dict[
                str,
                Union[
                    bool,
                    list[dict[str, Union[QTreeWidgetItem, WorkspaceAssemblyGroup]]],
                    QTreeWidgetItem,
                ],
            ],
        ] = {}

        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.load_ui()

    def load_ui(self):
        self.parts_tree_widget = WorkspacePartsTreeWidget(self)
        self.parts_tree_widget.itemExpanded.connect(self.tree_parts_item_expanded)
        self.parts_tree_widget.itemCollapsed.connect(self.tree_parts_item_collapsed)

        self.assemblies_tree_widget = WorkspaceAssemblyTreeWidget(self)
        self.assemblies_tree_widget.itemExpanded.connect(self.tree_assemblies_item_expanded)
        self.assemblies_tree_widget.itemCollapsed.connect(self.tree_assemblies_item_collapsed)

        self.recut_parts_table_widget = WorkspacePartsTableWidget(self)
        self.recut_parts_table_widget.hideColumn(WorkspacePartsTableColumns.RECOAT.value)

        self.recoat_parts_table_widget = WorkspacePartsTableWidget(self)

        self.parts_layout.addWidget(self.parts_tree_widget)

        self.recut_parts_layout.addWidget(self.recut_parts_table_widget)
        self.recoat_parts_layout.addWidget(self.recoat_parts_table_widget)

        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_recoat, self.widget_2)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_recut, self.widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_jobs, self.widget_3)

        self.assembly_widget.setHidden(True)
        self.assembly_layout.addWidget(self.assemblies_tree_widget)

        # self.get_all_workspace_jobs_thread()

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = theme_var("primary")
        hover_color = lighten_color(base_color)
        font_color = get_on_color_from_primary(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            f"""
            QPushButton#assembly_button_drop_menu {{
                border: 1px solid {theme_var("surface")};
                background-color: {theme_var("surface")};
                border-radius: {theme_var("border-radius")};
                text-align: left;
            }}
            /* CLOSED */
            QPushButton:!checked#assembly_button_drop_menu {{
                color: {theme_var("on-surface")};
                border: 1px solid {theme_var("outline")};
            }}

            QPushButton:!checked:hover#assembly_button_drop_menu {{
                background-color: {theme_var("outline-variant")};
            }}
            QPushButton:!checked:pressed#assembly_button_drop_menu{{
                color: {theme_var("on-surface")};
                background-color: {theme_var("surface")};
            }}
            /* OPENED */
            QPushButton:checked#assembly_button_drop_menu {{
                color: {font_color};
                border-color: {base_color};
                background-color: {base_color};
                border-top-left-radius: {theme_var("border-radius")};
                border-top-right-radius: {theme_var("border-radius")};
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
            background-color: {theme_var("background")};
            }}"""
        )

    def view_parts_table(self):
        self.parts_widget.setVisible(True)
        self.assembly_widget.setVisible(False)

    def view_assemblies_table(self):
        self.parts_widget.setVisible(False)
        self.assembly_widget.setVisible(True)

    # PARTS
    # TODO: This needs to accept the new format from WorkspaceDB
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
        table_widget.setItem(current_row, WorkspacePartsTableColumns.PART_NAME.value, part_name_item)

        # FILES
        current_tag = group.base_part.get_current_tag()
        if current_tag and any(keyword in current_tag.name.lower() for keyword in ["weld", "assembly"]):
            files_widget, files_layout = self.create_file_layout(group, ["welding_files"])
        elif current_tag and any(keyword in current_tag.name.lower() for keyword in ["bend", "break", "form"]):
            files_widget, files_layout = self.create_file_layout(group, ["bending_files"])
        elif any(keyword in current_tag.name.lower() for keyword in ["cnc", "laser", "cutting", "milling", "thread"]):
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
        material_item = QTableWidgetItem(f"{group.base_part.meta_data.gauge} {group.base_part.meta_data.material}")
        material_item.setFont(self.tables_font)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.MATERIAL.value, material_item)
        table_items[group].update({"material": material_item})

        # PAINT
        paint_text = self.get_paint_text(group.base_part)
        paint_item = QTableWidgetItem(paint_text)
        paint_item.setFont(self.tables_font)
        paint_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.PAINT.value, paint_item)
        table_items[group].update({"paint": paint_text})

        # QUANTITY
        quantity_item = QTableWidgetItem(f"{group.get_count()}")
        quantity_item.setFont(self.tables_font)
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.QUANTITY.value, quantity_item)
        table_items[group].update({"quantity": quantity_item})

        # QUANTITY IN STOCK
        if inventory_part := self.laser_cut_inventory.get_laser_cut_part_by_name(group.base_part.name):
            quantity_in_stock = inventory_part.inventory_data.quantity
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
        if not group.base_part.meta_data.shelf_number:
            shelf_number_item = QTableWidgetItem("NA")
        else:
            shelf_number_item = QTableWidgetItem(group.base_part.meta_data.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        shelf_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table_widget.setItem(
            current_row,
            WorkspacePartsTableColumns.SHELF_NUMBER.value,
            shelf_number_item,
        )
        table_items[group].update({"shelf_number": shelf_number_item})

        # NOTES
        if not group.base_part.meta_data.notes:
            notes_item = QTableWidgetItem("No notes provided")
        else:
            notes_item = QTableWidgetItem(group.base_part.meta_data.notes)
        notes_item.setFont(self.tables_font)
        table_widget.setItem(current_row, WorkspacePartsTableColumns.NOTES.value, notes_item)
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
        table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.RECUT.value, recut_button)

        # RECOAT
        recoat_button = QPushButton("Recoat", self)
        if group.base_part.recoat:
            recoat_button.setToolTip("Part is recoated. (set recoat=False)")
            recoat_button.setIcon(Icons.check_fill_icon)
        else:
            recoat_button.setToolTip("Request part to be recoated. (set recoat=True)")
            recoat_button.setIcon(Icons.recut_icon)
        recoat_button.setFixedWidth(100)
        recoat_button.clicked.connect(partial(self.recoat_pressed, group))
        table_widget.setCellWidget(current_row, WorkspacePartsTableColumns.RECOAT.value, recoat_button)

    def add_part_group_to_tree(self, group: WorkspaceLaserCutPartGroup, parent: QTreeWidgetItem):
        part_tree_widget_item = QTreeWidgetItem(parent)
        self.parts_parent_tree_items[parent.text(0)]["children"].append({"item": part_tree_widget_item, "group": group})
        parent.addChild(part_tree_widget_item)
        self.update_part_tree_widget_item(group, part_tree_widget_item)

    def update_part_tree_widget_item(self, group: WorkspaceLaserCutPartGroup, part_tree_widget_item: QTreeWidgetItem):
        # PART NAME
        # TODO: Consider flow tag
        # if group.base_part.recut or group.base_part.recoat or group.base_part.is_process_finished():

        if part_tree_widget_item is None or isdeleted(part_tree_widget_item):
            return

        # ! TODO: This throws C++ Runtime Error when updating entries.
        part_tree_widget_item.setDisabled(True)
        self.parts_tree_index.update({id(part_tree_widget_item): group})
        part_tree_widget_item.setText(WorkspacePartsTreeColumns.PART_NAME.value, group.base_part.name)
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.MATERIAL.value,
            f"{group.base_part.meta_data.gauge} {group.base_part.meta_data.material}",
        )
        part_tree_widget_item.setText(WorkspacePartsTreeColumns.QUANTITY.value, f"{group.get_count():,.2f}")

        if inventory_part := self.laser_cut_inventory.get_laser_cut_part_by_name(group.base_part.name):
            quantity_in_stock = inventory_part.inventory_data.quantity
        else:
            quantity_in_stock = 0

        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value,
            f"{quantity_in_stock:,.2f}",
        )
        part_tree_widget_item.setText(WorkspacePartsTreeColumns.NOTES.value, f"{group.base_part.meta_data.notes}")
        part_tree_widget_item.setText(
            WorkspacePartsTreeColumns.SHELF_NUMBER.value,
            f"{group.base_part.meta_data.shelf_number}",
        )

        # PAINT
        paint_text = self.get_paint_text(group.base_part)
        part_tree_widget_item.setText(WorkspacePartsTreeColumns.PAINT.value, paint_text)

        # FILES
        current_tag = group.base_part.get_current_tag()
        if current_tag and any(keyword in current_tag.name.lower() for keyword in ["weld", "assembly"]):
            files_widget, files_layout = self.create_file_layout(group, ["welding_files"])
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.FILES.value,
                files_widget,
            )
        elif current_tag and any(keyword in current_tag.name.lower() for keyword in ["bend", "break", "form"]):
            files_widget, files_layout = self.create_file_layout(group, ["bending_files"])
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.FILES.value,
                files_widget,
            )
        elif current_tag and any(keyword in current_tag.name.lower() for keyword in ["cnc", "laser", "cutting", "milling", "thread"]):
            files_widget, files_layout = self.create_file_layout(group, ["cnc_milling_files"])
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.FILES.value,
                files_widget,
            )
        else:
            part_tree_widget_item.setText(WorkspacePartsTreeColumns.FILES.value, "No files")

        # PROCESS CONTROLS
        existing_process_control_widget = self.parts_tree_widget.itemWidget(part_tree_widget_item, WorkspacePartsTreeColumns.PROCESS_CONTROLS.value)
        if existing_process_control_widget:
            self.parts_tree_widget.removeItemWidget(part_tree_widget_item, WorkspacePartsTreeColumns.PROCESS_CONTROLS.value)

        if group.base_part.recut:
            part_tree_widget_item.setText(WorkspacePartsTreeColumns.PROCESS_CONTROLS.value, "Part is a Recut")
        elif group.base_part.recoat:
            part_tree_widget_item.setText(WorkspacePartsTreeColumns.PROCESS_CONTROLS.value, "Part is a Recoat")
        elif group.base_part.is_process_finished():
            part_tree_widget_item.setText(WorkspacePartsTreeColumns.PROCESS_CONTROLS.value, "Part is Finished")
        elif current_tag and current_tag.name.lower() != self.workspace_filter.current_tag.lower():
            part_tree_widget_item.setText(
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                f"Part is currently in {current_tag.name}",
            )
        else:
            flow_tag_controls_widget = self.get_flow_tag_controls(group)
            self.parts_tree_widget.setItemWidget(
                part_tree_widget_item,
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                flow_tag_controls_widget,
            )
            part_tree_widget_item.setDisabled(False)

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
        self.parts_tree_widget.setItemWidget(part_tree_widget_item, WorkspacePartsTreeColumns.RECUT.value, recut_button)

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
        self.parts_tree_widget.setItemWidget(part_tree_widget_item, WorkspacePartsTreeColumns.RECOAT.value, recoat_button)

        job = self.get_job_from_tree_item(part_tree_widget_item)
        part_tree_widget_item.setHidden(self.workspace.is_part_group_hidden(group, job))

    # TODO: Get jobs from workspace DB before loading UI
    def tree_parts_item_expanded(self, item: QTreeWidgetItem):
        self.parts_parent_tree_items[item.text(0)]["is_expanded"] = item.isExpanded()
        job = self.parts_parent_tree_items[item.text(0)]["job"]
        job_id = self.parts_parent_tree_items[item.text(0)]["id"]

        self.load_workspace_job_thread(job, job_id, item)

    def load_workspace_job_thread(self, job: Job, job_id: int, item: QTreeWidgetItem):
        # if not self.get_workspace_job:
        get_workspace_job = LoadJobFromWorkspaceWorker(job, item, job_id, self.laser_cut_inventory, self.components_inventory)
        get_workspace_job.signals.success.connect(self.load_workspace_job_response)
        QThreadPool.globalInstance().start(get_workspace_job)

    def load_workspace_job_response(self, response: tuple[Job, QTreeWidgetItem, dict, int]):
        job, item, response, status_code = response
        if status_code == 200:
            if self._parent_widget.pushButton_view_parts.isChecked():
                all_laser_cut_parts = job.get_all_laser_cut_parts()
                if not all_laser_cut_parts:
                    return
                # if not (
                #     filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)
                # ):
                #     return

                parent_job_item = self.parts_parent_tree_items[job.get_workspace_name()]["item"]
                grouped_parts = self.workspace.get_grouped_laser_cut_parts(all_laser_cut_parts)
                self.parts_parent_tree_items[job.get_workspace_name()]["children"].clear()
                for laser_cut_part_group in grouped_parts:
                    self.add_part_group_to_tree(laser_cut_part_group, parent_job_item)
                self.update_parts_visibility()
            elif self._parent_widget.pushButton_view_assemblies.isChecked():
                if not (filtered_assemblies := self.workspace.get_filtered_assemblies(job)):
                    return

                parent_job_item = self.assemblies_parent_tree_items[job.get_workspace_name()]["item"]
                grouped_assemblies = self.workspace.get_grouped_assemblies(filtered_assemblies)
                self.assemblies_parent_tree_items[job.get_workspace_name()]["children"].clear()
                for assmebly_group in grouped_assemblies:
                    self.add_assembly_group_to_tree(assmebly_group, parent_job_item)
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Error loading job")
            msg.setText(f"{response}")
            msg.exec()

    def tree_parts_item_collapsed(self, item: QTreeWidgetItem):
        self.parts_parent_tree_items[item.text(0)]["is_expanded"] = item.isExpanded()
        item.takeChildren()

    # TODO: How to handle callback such that it loads what is being loaded by the thread?
    def recut_pressed(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        if laser_cut_part_group.base_part.recut:
            laser_cut_part_group.unmark_as_recut()
            # self.load_parts_table()
            # self.load_parts_tree()
            self.update_entries(laser_cut_part_group.laser_cut_parts)
            # for laser_cut_part in laser_cut_part_group.laser_cut_parts:
            #     self.update_entry(laser_cut_part.id, laser_cut_part)
            # self.workspace.save()
            # self.sync_changes()
        else:
            dialog = RecutDialog(
                f"Recut: {laser_cut_part_group.base_part.name}",
                laser_cut_part_group.get_count(),
                self,
            )
            if dialog.exec():
                if not (recut_count := dialog.get_quantity()):
                    return
                laser_cut_parts_to_update = []
                for i in range(recut_count):
                    laser_cut_part_group.laser_cut_parts[i].mark_as_recut()
                    new_part = LaserCutPart(
                        laser_cut_part_group.laser_cut_parts[i].to_dict(),
                        self.laser_cut_inventory,
                    )
                    new_part.meta_data.modified_date = f"Added from Workspace at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                    self.laser_cut_inventory.add_recut_part(new_part)
                    # self.laser_cut_inventory.save_local_copy()
                    # self.upload_files([f"{self.laser_cut_inventory.filename}.json"])
                    laser_cut_parts_to_update.append(laser_cut_part_group.laser_cut_parts[i])
                self.laser_cut_inventory.save_laser_cut_parts(laser_cut_parts_to_update)
                self.update_entries(laser_cut_parts_to_update)
                # self.load_parts_table()
                # self.load_parts_tree()
                # self.workspace.save()
                # self.sync_changes()

    # TODO: How to handle callback such that it loads what is being loaded by the thread?
    def recoat_pressed(self, laser_cut_part_group: WorkspaceLaserCutPartGroup):
        if laser_cut_part_group.base_part.recoat:
            laser_cut_part_group.unmark_as_recoat()
            # self.load_parts_table()
            # self.load_parts_tree()
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
                laser_cut_parts_to_update = []
                for i in range(recut_count):
                    laser_cut_part_group.laser_cut_parts[i].mark_as_recoat()
                    laser_cut_parts_to_update.append(laser_cut_part_group.laser_cut_parts[i])
                # self.laser_cut_inventory.save_laser_cut_parts(laser_cut_parts_to_update)
                self.update_entries(laser_cut_parts_to_update)
                # self.load_parts_table()
                # self.load_parts_tree()
                # self.workspace.save()
                # self.sync_changes()

    def update_entries(
        self,
        entries: list[Job | Assembly | LaserCutPart | Component],
    ):
        update_workspace_entries_worker = UpdateWorkspaceEntriesWorker(entries)
        update_workspace_entries_worker.signals.success.connect(self.update_entries_response)
        QThreadPool.globalInstance().start(update_workspace_entries_worker)

    # TODO: HANDLE Assemblies
    def update_entries_response(self, response: dict):
        for job_id, part_names in response["job_name_map"].items():
            for part_name in part_names:
                (
                    workspace_laser_cut_part_group,
                    workspace_laser_cut_part_group_item,
                ) = self.get_workspace_laser_cut_part_group_item_by_name(part_name)
                if workspace_laser_cut_part_group and workspace_laser_cut_part_group_item:
                    self.update_part_tree_widget_item(
                        workspace_laser_cut_part_group,
                        workspace_laser_cut_part_group_item,
                    )
        # self.load_parts_table()
        # self.update_tree_entry()
        # self.load_parts_tree()

    def get_paint_text(self, item: Union[Assembly, LaserCutPart]) -> str:
        text: list[str] = []
        if item.primer_data.uses_primer and item.primer_data.primer_item:
            text.append(item.primer_data.primer_item.part_name)
        if item.paint_data.uses_paint and item.paint_data.paint_item:
            text.append(item.paint_data.paint_item.part_name)
        if item.powder_data.uses_powder and item.powder_data.powder_item:
            text.append(item.powder_data.powder_item.part_name)
        if not (item.powder_data.uses_powder or item.paint_data.uses_paint or item.primer_data.uses_primer):
            return "Not painted"
        return "\n".join(text)

    def add_laser_cut_part_drag_file_widget(
        self,
        item: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
        file_category: str,
        files_layout: QHBoxLayout,
        file_path: str,
    ):
        file_button = FileButton(f"{Environment.DATA_PATH}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.laser_cut_part_file_clicked, item, file_path))
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
        files_widget.setStyleSheet("QWidget#files_widget{background-color: transparent;}")
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
                self.add_laser_cut_part_drag_file_widget(item, file_type, files_layout, file)
        return main_widget, files_layout

    def laser_cut_part_file_clicked(
        self,
        item: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
        file_path: str,
    ):
        download_worker = WorkspaceDownloadWorker([file_path], True)
        download_worker.signals.success.connect(self.file_downloaded)
        QThreadPool.globalInstance().start(download_worker)
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

    def load_parts_tree(self, jobs: list[dict]):
        if any(keyword in self.workspace_filter.current_tag.lower() for keyword in ["laser"]):
            self.parts_tree_widget.showColumn(WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value)
            self.parts_tree_widget.hideColumn(WorkspacePartsTreeColumns.RECUT.value)
            self.recut_parts_widget.setVisible(True)
        else:
            self.parts_tree_widget.hideColumn(WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value)
            self.parts_tree_widget.showColumn(WorkspacePartsTreeColumns.RECUT.value)
            self.recut_parts_widget.setHidden(True)
        if any(keyword in self.workspace_filter.current_tag.lower() for keyword in ["powder", "coating", "liquid", "paint", "gloss", "prime"]):
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

        for job_data in jobs:
            job = Job({"job_data": msgspec.json.decode(job_data["data"])}, self.job_manager)
            job.id = job_data["id"]
            self.workspace.add_job(job)
            # if not (filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)):
            #     continue

            parent_job_item = QTreeWidgetItem(self.parts_tree_widget)
            parent_job_item.setText(
                0,
                f"{job.get_workspace_name()}",
            )
            parent_job_item.setFont(0, font)
            parent_job_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            parent_job_item.setFirstColumnSpanned(True)
            self.parts_parent_tree_items.setdefault(
                job.get_workspace_name(),
                {
                    "job": job,
                    "item": parent_job_item,
                    "id": job_data["id"],
                    "is_expanded": False,
                    "children": [],
                },
            )
            self.parts_parent_tree_items[job.get_workspace_name()]["item"] = parent_job_item
            self.parts_tree_widget.addTopLevelItem(parent_job_item)

            if self.parts_parent_tree_items[job.get_workspace_name()].get("is_expanded", False):
                self.parts_tree_widget.expandItem(parent_job_item)
                self.load_workspace_job_thread(job, job_data["id"], parent_job_item)
                # grouped_parts = self.workspace.get_grouped_laser_cut_parts(
                #     job.get_all_laser_cut_parts()
                # )
                # for laser_cut_part_group in grouped_parts:
                #     self.add_part_group_to_tree(laser_cut_part_group, parent_job_item)

        self.parts_tree_widget.setColumnWidth(WorkspacePartsTreeColumns.PART_NAME.value, 200)
        self.parts_tree_widget.setColumnWidth(WorkspacePartsTreeColumns.QUANTITY_IN_STOCK.value, 100)
        self.parts_tree_widget.setColumnWidth(WorkspacePartsTreeColumns.MATERIAL.value, 150)
        self.parts_tree_widget.setColumnWidth(WorkspacePartsTreeColumns.PROCESS_CONTROLS.value, 170)
        self.parts_tree_widget.setColumnWidth(WorkspacePartsTreeColumns.PAINT.value, 150)
        self.parts_tree_widget.blockSignals(False)
        self.parts_tree_widget.resizeColumnToContents(WorkspacePartsTreeColumns.NOTES.value)

    # TODO: This needs to accept the new format from WorkspaceDB
    def load_recut_or_recoat_parts_table(self, parts_data: list[dict]):
        if any(keyword in self.workspace_filter.current_tag.lower() for keyword in ["laser"]):
            self.recut_parts_widget.setVisible(True)
        else:
            self.recut_parts_widget.setHidden(True)

        if any(keyword in self.workspace_filter.current_tag.lower() for keyword in ["powder", "coating", "liquid", "paint", "gloss", "prime"]):
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

        font = QFont()
        font.setPointSize(15)

        for part_data in parts_data:
            job_id = part_data["path"][0].split(":")[1]
            # job = self.workspace.get_job_by_id(job_id)
            laser_cut_part = LaserCutPart(part_data["data"], self.laser_cut_inventory)
            laser_cut_part.id = part_data["id"]

            laser_cut_part_group = WorkspaceLaserCutPartGroup()
            laser_cut_part_group.add_laser_cut_part(laser_cut_part)
            # if not (filtered_parts := self.workspace.get_filtered_laser_cut_parts(job)):
            #     continue

            # job_title_item = QTableWidgetItem(job.name)
            # job_title_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # job_title_item.setFont(font)
            # grouped_parts = self.workspace.get_grouped_laser_cut_parts(filtered_parts)
            # for laser_cut_part_group in grouped_parts:
            self.add_part_group_to_table(laser_cut_part_group)
        self.recut_parts_table_widget.blockSignals(False)
        self.recoat_parts_table_widget.blockSignals(False)
        self.recut_parts_table_widget.resizeColumnsToContents()
        self.recoat_parts_table_widget.resizeColumnsToContents()
        self.recut_parts_table_widget.setFixedHeight((self.recut_parts_table_widget.rowCount() + 1) * self.recut_parts_table_widget.row_height)
        self.recoat_parts_table_widget.setFixedHeight((self.recoat_parts_table_widget.rowCount() + 1) * self.recoat_parts_table_widget.row_height)
        self.load_parts_table_context_menu()

    def load_parts_table_context_menu(self):
        if self.parts_tree_widget.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
            return
        self.parts_tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        menu = QMenu(self)

        move_to_next_process_action = QAction("Move to Next Process", self)
        move_to_next_process_action.triggered.connect(self.move_parts_to_next_process)

        download_files_action = QAction("Download files", self)
        download_files_action.triggered.connect(self.download_files)

        menu.addAction(move_to_next_process_action)
        menu.addAction(download_files_action)

        self.parts_tree_widget.customContextMenuRequested.connect(partial(self.open_context_menu, menu))

    # TODO: How to handle callback such that it loads what is being loaded by the thread?
    def move_parts_to_next_process(self):
        laser_cut_parts_to_update = []
        if selected_items := self.parts_tree_get_selected_items():
            for selected_item in selected_items:
                selected_item.move_to_next_process()
                laser_cut_parts_to_update.extend(selected_item.laser_cut_parts)
                # for part in selected_item:
                #     self.update_entry(part.id, part)
            self.update_entries(laser_cut_parts_to_update)
            self.check_if_assemblies_are_ready_to_start_timer()
            # self.load_parts_table()
            # self.load_parts_tree()
            # self.workspace.save()
            # self.laser_cut_inventory.save_local_copy()
            # self.sync_changes()

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
                download_worker = WorkspaceDownloadWorker(self.files_to_download, False, self.download_directory)
                download_worker.signals.success.connect(self.download_thread_response)
                QThreadPool.globalInstance().start(download_worker)
                # self.download_thread = WorkspaceDownloadFile(
                #     self.files_to_download,
                #     False,
                #     download_directory=self.download_directory,
                # )
                # self.download_thread.signal.connect(self.download_thread_response)
                # self.download_thread.start()
            else:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Error")
                msg.setText("Please select files to download and a download directory.")
                msg.exec()

    def download_thread_response(self, response: str):
        if platform.system() == "Windows":
            os.startfile(self.download_directory)
        else:
            subprocess.run(["xdg-open", self.download_directory])

    def parts_tree_get_selected_items(self) -> list[WorkspaceLaserCutPartGroup]:
        selected_items: list[WorkspaceLaserCutPartGroup] = []
        for item in self.parts_tree_widget.selectedItems():
            if item.parent() is not None:
                selected_items.append(self.parts_tree_index[id(item)])
        return selected_items

    def update_tree_entry(self, entry_data: dict[str, dict | bytes | bytearray]):
        entry_type = entry_data["type"]
        if entry_type == "assembly":
            for parent_tree_item in self.assemblies_parent_tree_items.values():
                for child in parent_tree_item["children"]:
                    if child["group"].update_entry(entry_data):
                        self.update_assembly_tree_widget_item(child["group"], child["item"])
        elif entry_type == "laser_cut_part":
            for parent_tree_item in self.parts_parent_tree_items.values():
                for child in parent_tree_item["children"]:
                    if child["group"].update_entry(entry_data):
                        self.update_part_tree_widget_item(child["group"], child["item"])

    def get_workspace_laser_cut_part_group_item_by_name(
        self, name: str
    ) -> (
        tuple[
            WorkspaceLaserCutPartGroup,
            QTreeWidgetItem,
        ]
        | None
    ):
        for parent_tree_item in self.parts_parent_tree_items.values():
            for child in parent_tree_item["children"]:
                if child["group"].base_part.name == name:
                    return child["group"], child["item"]
        return None

    def get_workspace_assembly_group_item_by_name(
        self,
        name: str,
    ) -> (
        tuple[
            WorkspaceAssemblyGroup,
            QTreeWidgetItem,
        ]
        | None
    ):
        for parent_tree_item in self.assemblies_parent_tree_items.values():
            for child in parent_tree_item["children"]:
                if child["group"].base_assembly.name == name:
                    return child["group"], child["item"]
        return None

    def update_tree_entries(self, entries_data: list[dict[str, str | bytes | bytearray]]):
        if not entries_data:
            return

        entries_to_update = {
            "laser_cut_part": {},
            "assembly": {},
        }

        for entry_data in entries_data:
            part_name = str(entry_data["name"])
            part_type = str(entry_data["type"])

            if part_type == "laser_cut_part":
                if result := self.get_workspace_laser_cut_part_group_item_by_name(part_name):
                    group, item = result
                    group.update_entry(entry_data)
                    entries_to_update[part_type].update({part_name: (group, item)})
                    # self.update_part_tree_widget_item(group, item)
            elif part_type == "assembly":
                if result := self.get_workspace_assembly_group_item_by_name(part_name):
                    group, item = result
                    group.update_entry(entry_data)
                    entries_to_update[part_type].update({part_name: (group, item)})
                    # self.update_assembly_tree_widget_item(group, item)
        for part_type, entries in entries_to_update.items():
            for part_name, (group, item) in entries.items():
                if part_type == "laser_cut_part":
                    self.update_part_tree_widget_item(group, item)
                elif part_type == "assembly":
                    self.update_assembly_tree_widget_item(group, item)
                else:
                    raise ValueError(f"Unknown part type: {part_type}")

    # ASSEMBLIES
    def add_assembly_group_to_tree(self, group: WorkspaceAssemblyGroup, parent: QTreeWidgetItem):
        assembly_tree_widget_item = QTreeWidgetItem(parent)
        self.assemblies_parent_tree_items[parent.text(0)]["children"].append({"item": assembly_tree_widget_item, "group": group})
        parent.addChild(assembly_tree_widget_item)
        self.update_assembly_tree_widget_item(group, assembly_tree_widget_item)
        # self.assemblies_tree_index.update({id(assembly_tree_widget_item): group})

    def update_assembly_tree_widget_item(self, group: WorkspaceAssemblyGroup, assembly_tree_widget_item: QTreeWidgetItem):
        assembly_tree_widget_item.setDisabled(True)
        self.assemblies_tree_index.update({id(assembly_tree_widget_item): group})
        assembly_tree_widget_item.setText(
            WorkspaceAssemblyTreeColumns.ASSEMBLY_NAME.value,
            f"{group.base_assembly.name}",
        )
        assembly_tree_widget_item.setText(WorkspaceAssemblyTreeColumns.QUANTITY.value, f"{group.get_quantity()}")
        assembly_tree_widget_item.setFont(WorkspaceAssemblyTreeColumns.ASSEMBLY_NAME.value, self.tables_font)
        assembly_tree_widget_item.setFont(WorkspaceAssemblyTreeColumns.QUANTITY.value, self.tables_font)

        # PICTURE
        if group.base_assembly.assembly_image:
            image = QPixmap(group.base_assembly.assembly_image)
            original_width = image.width()
            original_height = image.height()
            new_height = self.assemblies_tree_widget.ROW_HEIGHT
            try:
                new_width = int(original_width * (new_height / original_height))
            except ZeroDivisionError:
                new_width = original_width
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            icon = QIcon(pixmap)
            assembly_tree_widget_item.setIcon(WorkspaceAssemblyTreeColumns.PICTURE.value, icon)

        # VIEW FILES BUTTON
        view_parts_button = QPushButton("View Parts", self)
        view_parts_button.clicked.connect(partial(self.view_assembly_parts, group.base_assembly))
        self.assemblies_tree_widget.setItemWidget(
            assembly_tree_widget_item,
            WorkspaceAssemblyTreeColumns.ASSEMBLY_PARTS_BUTTON.value,
            view_parts_button,
        )

        # FILES
        current_tag = group.base_assembly.get_current_tag()
        if group.get_all_files():
            files_widget, files_layout = self.create_file_layout(group, ["assembly_files"])
            self.assemblies_tree_widget.setItemWidget(
                assembly_tree_widget_item,
                WorkspaceAssemblyTreeColumns.ASSEMBLY_FILES.value,
                files_widget,
            )
        else:
            assembly_tree_widget_item.setText(WorkspaceAssemblyTreeColumns.ASSEMBLY_FILES.value, "No files")

        # PROCESS CONTROLS
        existing_process_control_widget = self.assemblies_tree_widget.itemWidget(assembly_tree_widget_item, WorkspacePartsTreeColumns.PROCESS_CONTROLS.value)
        if existing_process_control_widget:
            self.assemblies_tree_widget.removeItemWidget(
                assembly_tree_widget_item,
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
            )
        if group.base_assembly.is_assembly_finished():
            assembly_tree_widget_item.setText(WorkspacePartsTreeColumns.PROCESS_CONTROLS.value, "Assembly is Finished")
        elif not group.base_assembly.all_sub_assemblies_complete() and group.base_assembly.sub_assemblies:
            assembly_tree_widget_item.setText(
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                "Not all Sub-Assemblies are Complete",
            )
        elif not group.base_assembly.all_laser_cut_parts_complete():
            assembly_tree_widget_item.setText(
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                "Not all Parts are Complete",
            )
        elif current_tag and current_tag.name.lower() != self.workspace_filter.current_tag.lower():
            assembly_tree_widget_item.setText(
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                f"Assembly is currently in {current_tag.name}",
            )
        else:
            flow_tag_controls_widget = self.get_flow_tag_controls(group)
            self.assemblies_tree_widget.setItemWidget(
                assembly_tree_widget_item,
                WorkspacePartsTreeColumns.PROCESS_CONTROLS.value,
                flow_tag_controls_widget,
            )
            assembly_tree_widget_item.setDisabled(False)

        # PAINT
        paint_text = self.get_paint_text(group.base_assembly)
        assembly_tree_widget_item.setText(WorkspaceAssemblyTreeColumns.PAINT.value, paint_text)

    def tree_assemblies_item_expanded(self, item: QTreeWidgetItem):
        self.assemblies_parent_tree_items[item.text(0)]["is_expanded"] = item.isExpanded()
        job = self.assemblies_parent_tree_items[item.text(0)]["job"]
        job_id = self.assemblies_parent_tree_items[item.text(0)]["id"]

        self.load_workspace_job_thread(job, job_id, item)

    def tree_assemblies_item_collapsed(self, item: QTreeWidgetItem):
        self.assemblies_parent_tree_items[item.text(0)]["is_expanded"] = item.isExpanded()
        item.takeChildren()

    def load_assembly_tree(self, jobs: list[dict]):
        self.assemblies_tree_widget.blockSignals(True)
        self.assemblies_tree_widget.clear()
        self.assemblies_tree_index.clear()

        font = QFont()
        font.setPointSize(15)

        for job_data in jobs:
            job = Job({"job_data": msgspec.json.decode(job_data["data"])}, self.job_manager)
            job.id = job_data["id"]
            self.workspace.add_job(job)
            # if not (filtered_assemblies := self.workspace.get_filtered_assemblies(job)):
            #     continue

            parent_job_item = QTreeWidgetItem(self.assemblies_tree_widget)
            parent_job_item.setText(
                0,
                f"{job.get_workspace_name()}",
            )
            parent_job_item.setFont(0, font)
            parent_job_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            parent_job_item.setFirstColumnSpanned(True)
            self.assemblies_parent_tree_items.setdefault(
                parent_job_item.text(0),
                {
                    "job": job,
                    "item": parent_job_item,
                    "id": job_data["id"],
                    "is_expanded": False,
                    "children": [],
                },
            )
            self.assemblies_parent_tree_items[job.get_workspace_name()]["item"] = parent_job_item
            self.assemblies_tree_widget.addTopLevelItem(parent_job_item)

            if self.assemblies_parent_tree_items[parent_job_item.text(0)].get("is_expanded", False):
                self.assemblies_tree_widget.expandItem(parent_job_item)
                self.load_workspace_job_thread(job, job_data["id"], parent_job_item)
                # grouped_assemblies = self.workspace.get_grouped_assemblies(
                #     filtered_assemblies
                # )
                # for assembly_group in grouped_assemblies:
                #     self.add_assembly_group_to_tree(assembly_group, parent_job_item)

        self.assemblies_tree_widget.setColumnWidth(WorkspaceAssemblyTreeColumns.ASSEMBLY_NAME.value, 200)
        self.assemblies_tree_widget.setColumnWidth(WorkspaceAssemblyTreeColumns.QUANTITY.value, 100)
        self.assemblies_tree_widget.setColumnWidth(WorkspaceAssemblyTreeColumns.PAINT.value, 100)
        self.assemblies_tree_widget.setColumnWidth(WorkspaceAssemblyTreeColumns.PROCESS_CONTROLS.value, 150)
        self.assemblies_tree_widget.blockSignals(False)
        self.load_assemblies_table_context_menu()

    def load_assemblies_table_context_menu(self):
        if self.assemblies_tree_widget.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
            return
        self.assemblies_tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        menu = QMenu(self)
        action = QAction("Move to Next Process", self)
        action.triggered.connect(self.move_assemblies_to_next_process)
        menu.addAction(action)

        self.assemblies_tree_widget.customContextMenuRequested.connect(partial(self.open_context_menu, menu))

    def move_assemblies_to_next_process(self):
        if selected_items := self.assemblies_tree_get_selected_items():
            assemblies_to_update = []
            for selected_item in selected_items:
                selected_item.move_to_next_process()
                assemblies_to_update.extend(selected_item.assemblies)
            self.update_entries(assemblies_to_update)
            self.check_if_assemblies_are_ready_to_start_timer()
            # self.load_assembly_tree()
            # self.workspace.save()
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
        part_group_or_assembly_group: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
    ) -> Union[QComboBox, QPushButton]:
        if isinstance(part_group_or_assembly_group, WorkspaceLaserCutPartGroup):
            item = part_group_or_assembly_group.base_part
        elif isinstance(part_group_or_assembly_group, WorkspaceAssemblyGroup):
            item = part_group_or_assembly_group.base_assembly
        current_tag = part_group_or_assembly_group.get_current_tag()
        if current_tag.statuses:
            flowtag_combobox = QComboBox(self)
            flowtag_combobox.setToolTip(current_tag.attributes.next_flow_tag_message)
            flowtag_combobox.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
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
                    f"Move to {item.workspace_data.flowtag.tags[item.current_flow_tag_index + 1].name}",
                    self,
                )
                flowtag_button.setIcon(Icons.arrow_right_fill_icon)
            except IndexError:
                flowtag_button = QPushButton("Mark as done", self)
                flowtag_button.setIcon(Icons.check_fill_icon)
            flowtag_button.setToolTip(current_tag.attributes.next_flow_tag_message)
            flowtag_button.clicked.connect(partial(self.move_item_process_forward, part_group_or_assembly_group))
            return flowtag_button

    def flowtag_combobox_changed(
        self,
        flowtag_combobox: QComboBox,
        part_group_or_assembly: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
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
                self.update_entries(item.laser_cut_parts)
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
                self.update_entries(item.assemblies)
        # self.workspace.save()
        self.sync_changes()

    # TODO: How to handle callback such that it loads what is being loaded by the thread?
    def move_item_process_forward(
        self,
        part_group_or_assembly: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup],
    ):
        part_group_or_assembly.move_to_next_process()
        self.check_if_assemblies_are_ready_to_start_timer()
        # self.load_assembly_tree()
        # self.load_parts_table()
        # self.load_parts_tree()
        if isinstance(part_group_or_assembly, WorkspaceLaserCutPartGroup):
            self.update_entries(part_group_or_assembly.laser_cut_parts)
        elif isinstance(part_group_or_assembly, WorkspaceAssemblyGroup):
            self.update_entries(part_group_or_assembly.assemblies)
        # self.workspace.save()
        # self.laser_cut_inventory.save_local_copy()
        # self.sync_changes()

    def check_if_assemblies_are_ready_to_start_timer(self):
        assemblies_to_update = []
        for assembly in self.workspace.get_all_assemblies():
            if assembly.all_laser_cut_parts_complete() and not assembly.timer.has_started_timer():
                assembly.timer.start_timer()
                assemblies_to_update.append(assembly)
        self.update_entries(assemblies_to_update)

    def file_downloaded(self, response: tuple[str, str, bool]):
        if response:
            file_ext, file_name, open_when_done = response
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
        self._parent_widget.sync_changes()

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

    def get_all_recut_parts_thread(self):
        get_recut_parts_worker = GetRecutPartsFromWorkspaceWorker()
        get_recut_parts_worker.signals.success.connect(self.get_all_recut_parts_response)
        QThreadPool.globalInstance().start(get_recut_parts_worker)
        # get_all_recut_parts = GetRecutPartsFromWorkspace()
        # get_all_recut_parts.signal.connect(self.get_all_recut_parts_response)
        # get_all_recut_parts.finished.connect(
        #     get_all_recut_parts.deleteLater
        # )  # Auto cleanup
        # self.threads.append(get_all_recut_parts)
        # get_all_recut_parts.start()

    def get_all_recut_parts_response(self, data: list[dict]):
        self.load_recut_or_recoat_parts_table(data)

    def get_job_from_tree_item(self, tree_item: QTreeWidgetItem) -> Job | None:
        for job_name, job_data in self.parts_parent_tree_items.items():
            job = job_data["job"]
            for children in job_data["children"]:
                if children["item"] == tree_item:
                    return job
        return None

    def reload_all_entries(self):
        for job_name, job_data in self.parts_parent_tree_items.items():
            for children in job_data["children"]:
                tree_widget_item = children["item"]
                group = children["group"]
                self.update_part_tree_widget_item(group, tree_widget_item)

    def update_parts_visibility(self):
        for job_name, job_data in self.parts_parent_tree_items.items():
            job = job_data["job"]
            for children in job_data["children"]:
                part_tree_widget_item = children["item"]
                group = children["group"]
                part_tree_widget_item.setHidden(self.workspace.is_part_group_hidden(group, job))

    def get_all_workspace_jobs_thread(self):
        get_all_workspace_jobs_worker = GetAllWorkspaceJobsWorker()
        get_all_workspace_jobs_worker.signals.success.connect(self.jobs_loaded)
        QThreadPool.globalInstance().start(get_all_workspace_jobs_worker)
        # get_all_workspace_jobs = GetAllJobsFromWorkspaceThread()
        # get_all_workspace_jobs.signal.connect(self.get_all_workspace_jobs_response)
        # get_all_workspace_jobs.finished.connect(
        #     get_all_workspace_jobs.deleteLater
        # )  # Auto cleanup
        # self.threads.append(get_all_workspace_jobs)
        # get_all_workspace_jobs.start()

    def jobs_loaded(self, response: dict[str, list[dict]]):
        jobs = response["jobs"]
        if self._parent_widget.pushButton_view_parts.isChecked():
            self.load_parts_tree(jobs)
        elif self._parent_widget.pushButton_view_assemblies.isChecked():
            self.load_assembly_tree(jobs)
