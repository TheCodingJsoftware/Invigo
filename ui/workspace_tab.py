import contextlib
import os
from datetime import datetime
from functools import partial
from typing import Any

import sympy
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction, QCursor, QFont, QIcon
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QCompleter, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from ui.color_picker_dialog import ColorPicker
from ui.custom_widgets import AssemblyImage, AssemblyMultiToolBox, CustomTableWidget, DeletePushButton, DraggableButton, DropWidget, FilterTabWidget, HumbleDoubleSpinBox, ItemsGroupBox, MultiToolBox, NotesPlainTextEdit, RecordingWidget, ScrollPositionManager, SelectRangeCalendar, TimeSpinBox
from ui.generate_workorder_dialog import GenerateWorkorderDialog
from ui.generate_workspace_printout_dialog import GenerateWorkspacePrintoutDialog
from ui.recut_dialog import RecutDialog
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


class WorkspaceTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(WorkspaceTabWidget, self).__init__(parent)
        self.tab_order = []  # Stores the current order of tabs as strings
        self.tabBar().installEventFilter(self)
        self.wheelEvent = lambda event: None

    def dragMoveEvent(self, event):
        if event.source() == self.tabBar():
            event.ignore()
        else:
            super().dragMoveEvent(event)

    def update_tab_order(self):
        self.tab_order = [self.tabText(i) for i in range(self.count())]

    def get_tab_order(self) -> list[str]:
        self.update_tab_order()
        return self.tab_order

    def set_tab_order(self, order):
        self.blockSignals(True)
        for tab_name in order:
            index = self.find_tab_by_name(tab_name)
            if index != -1:
                self.tabBar().moveTab(index, order.index(tab_name))
        self.blockSignals(False)

    def find_tab_by_name(self, name: str) -> int:
        return next((i for i in range(self.count()) if self.tabText(i) == name), -1)


class WorkspaceTab(QWidget):
    def __init__(self, admin_workspace: Workspace, user_workspace: Workspace, history_workspace: Workspace, workspace_settings: WorkspaceSettings, components_inventory: ComponentsInventory, laser_cut_inventory: LaserCutInventory, paint_inventory: PaintInventory, parent: QWidget):
        super(WorkspaceTab, self).__init__(parent)
        uic.loadUi("ui/workspace_tab.ui", self)
        self.parent = parent
        self.admin_workspace = admin_workspace
        self.user_workspace = user_workspace
        self.history_workspace = history_workspace
        self.workspace_settings = workspace_settings
        self.components_inventory = components_inventory
        self.laser_cut_inventory = laser_cut_inventory
        self.paint_inventory = paint_inventory
        self.settings_file = Settings()
        self.trusted_user: bool = False
        self.username = os.getlogin().title()

        self.active_workspace_file: Workspace = self.admin_workspace
        self.tabs = {}
        self.tab_widget = WorkspaceTabWidget(self)
        self.tab_widget.currentChanged.connect(self.load_workspace)
        self.category: str = ""
        self.workspace_filter_tab_widget: FilterTabWidget = None
        self.workspace_tables: dict[CustomTableWidget, Assembly] = {}
        self.workspace_information = {}  # idk the type hint

        self.scroll_position_manager = ScrollPositionManager()

        self.workspace_filter = {}

        self.pushButton_this_week.clicked.connect(partial(self.set_filter_calendar_day, 7))
        self.pushButton_next_2_days.clicked.connect(partial(self.set_filter_calendar_day, 2))
        self.pushButton_next_4_days.clicked.connect(partial(self.set_filter_calendar_day, 4))
        self.pushButton_generate_workorder.clicked.connect(partial(self.generate_workorder_dialog, []))
        self.pushButton_generate_workspace_quote.clicked.connect(partial(self.generate_workspace_printout_dialog, []))

        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        trusted_users = get_trusted_users()
        check_trusted_user = (user for user in trusted_users if not self.trusted_user)
        for user in check_trusted_user:
            self.trusted_user = self.username.lower() == user.lower()

        self.load_tabs()

    def get_all_selected_workspace_parts(self, tab: CustomTableWidget) -> list[str]:
        selected_rows = tab.selectedItems()
        selected_items: list[str] = []
        for item in selected_rows:
            if item.column() == 0:
                selected_items.append(item.text())
        return selected_items

    # Workspace
    def get_all_flow_tags(self) -> list[str]:
        flow_tags: list[str] = []
        for flow_tag_name in self.workspace_settings.get_all_flow_tags().keys():
            flow_tags.append(flow_tag_name)
        return flow_tags

    # Workspace
    def get_all_statuses(self) -> list[str]:
        statuses: list[str] = []
        for status in self.workspace_settings.get_all_statuses():
            statuses.append(status.name)
        return statuses

    # Workspace
    def get_all_job_names(self) -> list[str]:
        # self.active_workspace_file.load_data()
        job_names: list[str] = [job.name for job in self.active_workspace_file.data]
        return job_names

    # Workspace
    def get_all_workspace_items(self) -> list[WorkspaceItem]:
        # self.active_workspace_file.load_data()
        all_items: list[WorkspaceItem] = []
        for assembly in self.active_workspace_file.data:
            all_items.extend(assembly.get_all_items())
        return all_items

    # Workspace
    def get_all_workspace_item_names(self) -> list[str]:
        all_items = self.get_all_workspace_items()
        unique_item_names = {item.name for item in all_items}
        return list(unique_item_names)

    # STAGING/EDITING
    def assembly_items_table_clicked(self, item: QTableWidgetItem) -> None:
        self.last_selected_assembly_item = item.text()

    # STAGING/EDITING
    def assembly_items_table_cell_changed(self, table: CustomTableWidget, assembly: Assembly, item: QTableWidgetItem) -> None:
        item_text = item.text()
        row = item.row()
        column = item.column()
        try:
            selected_item_name = table.item(row, 0).text()
        except AttributeError:
            return
        if column == 0:  # Item Name
            if row == table.rowCount() or assembly.exists(selected_item_name):
                return
            assembly_item = assembly.get_item(self.last_selected_assembly_item)
            assembly_item.rename(item_text)
            self.active_workspace_file.save()
            self.sync_changes()
        elif column == 8:  # Parts Per
            assembly_item = assembly.get_item(selected_item_name)
            item_text = item_text.replace(",", "").replace(" ", "")
            assembly_item.parts_per = float(sympy.sympify(item_text, evaluate=True))
            self.active_workspace_file.save()
            self.sync_changes()
            return
        elif column == 12:  # Shelf Number
            assembly_item = assembly.get_item(selected_item_name)
            assembly_item.shelf_number = item_text
            self.active_workspace_file.save()
            self.sync_changes()
            return
        plus_button = table.cellWidget(table.rowCount() - 1, 0)
        plus_button.setEnabled(not assembly.exists(""))

    def item_draggable_button_show_context_menu(
        self,
        btn: DraggableButton,
        assembly: Assembly,
        item: WorkspaceItem,
        file_category: str,
        file_name: str,
    ):
        contextMenu = QMenu(self)
        deleteAction = contextMenu.addAction("Delete file")
        action = contextMenu.exec(QCursor.pos())

        if action == deleteAction:
            all_files = item.get_all_files(file_category)

            for i, file in enumerate(all_files):
                if file_name in file:
                    all_files.pop(i)
                    break

            item.update_files(file_category, all_files)

            self.active_workspace_file.save()
            self.sync_changes()

            btn.hide()
            btn.deleteLater()

    # STAGING/EDITING
    def load_assemblies_items_file_layout(
        self,
        file_category: str,
        files_layout: QHBoxLayout,
        assembly: Assembly,
        item: WorkspaceItem,
        show_dropped_widget: bool = True,
    ) -> None:
        self.clear_layout(files_layout)
        files = item.get_all_files(file_category)
        for file in files:
            btn = DraggableButton(self)
            file_name = os.path.basename(file)
            file_ext = file_name.split(".")[-1].upper()
            file_path = f"{os.path.dirname(os.path.realpath(__file__))}/data/workspace/{file_ext}/{file_name}"
            btn.setFile(file_path)
            btn.setFixedWidth(30)
            btn.setText(file_ext)
            btn.setToolTip("Press to open")
            btn.buttonClicked.connect(partial(self.download_workspace_file, file, True))
            btn.customContextMenuRequested.connect(
                partial(
                    self.item_draggable_button_show_context_menu,
                    btn,
                    assembly,
                    item,
                    file_category,
                    file_name,
                )
            )
            files_layout.addWidget(btn)
        if show_dropped_widget:
            drop_widget = DropWidget(self, assembly, item, files_layout, file_category)
            files_layout.addWidget(drop_widget)

    # STAGING/EDITING
    def handle_dropped_file(
        self,
        label: QLabel,
        file_paths: list[str],
        assembly: Assembly,
        item: WorkspaceItem,
        files_layout: QHBoxLayout,
        file_category: str,
    ) -> None:
        files = set(item.get_all_files(file_category))
        for file_path in file_paths:
            files.add(file_path)
        item.update_files(file_category, list(files))
        self.upload_workspace_files(list(files))
        self.status_button.setText("Upload starting", color="lime")
        label.setText("Drag Here")
        label.setStyleSheet("background-color: rgba(30,30,30,100);")
        self.load_assemblies_items_file_layout(
            file_category=file_category,
            files_layout=files_layout,
            assembly=assembly,
            item=item,
        )
        self.active_workspace_file.save()
        self.sync_changes()

    # STAGING/EDITING
    def delete_workspace_item(self, assembly: Assembly, table: CustomTableWidget, row_index: int):
        item: WorkspaceItem = assembly.get_item(table.item(row_index, 0).text())
        assembly.remove_item(item=item)
        table.removeRow(row_index)
        for row in range(table.rowCount() - 1):
            # end of table, there is no delete button there
            delete_button: DeletePushButton = table.cellWidget(row, table.columnCount() - 1)
            delete_button.disconnect()
            delete_button.clicked.connect(partial(self.delete_workspace_item, assembly, table, row))
        self.active_workspace_file.save()
        self.sync_changes()

    # STAGING/EDITING
    def load_edit_assembly_items_table(self, assembly: Assembly) -> CustomTableWidget:
        headers: list[str] = [
            "Item Name",
            "Bending Files",
            "Welding Files",
            "CNC/Milling Files",
            "Thickness",
            "Material Type",
            "Paint Type",
            "Paint Color",
            "Parts Per",
            "Flow Tag",
            "Expected time to complete",
            "Notes",
            "Shelf #",
            "DEL",
        ]
        #     table.setStyleSheet(
        #     f"QTableView {{ gridline-color: #EAE9FC; }} QTableWidget::item {{ border-color: #EAE9FC; }}"
        # )

        table = CustomTableWidget()
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        def select_color(item: WorkspaceItem, color_button: QComboBox) -> str:
            color_button.disconnect()
            if color_button.currentText() == "Select Color":
                color = ColorPicker()
                color.show()
                if color.exec():
                    item.paint_color = color.getHex(True)
                    color_name = color.getColorName()
                    self.active_workspace_file.save()
                    self.sync_changes()
                    color_button.setStyleSheet(f'QComboBox{{border-radius: 0px; background-color: {item.paint_color}}} {"QMenu { background-color: rgb(22,22,22);}"}')
                    data = self.workspace_tags.get_data()
                    data["paint_colors"][color_name] = color.getHex(True)
                    self.workspace_tags.save_data(data)
                    self.workspace_tags.load_data()
                    color_button.clear()
                    color_button.addItems(list(self.workspace_tags.get_value("paint_colors").keys()))
                    color_button.addItem("Select Color")
                    color_button.setCurrentText(color_name)
            else:
                if color_button.currentText() == "None":
                    color_button.setStyleSheet(f'QComboBox{{border-radius: 0px; background-color: transparent}} {"QMenu { background-color: rgb(22,22,22);}"}')
                    color_button.setCurrentText("None")
                    item.paint_color = None
                else:
                    self.workspace_tags.load_data()
                    for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                        if color_code == self.workspace_tags.get_data()["paint_colors"][color_button.currentText()]:
                            color_button.setCurrentText(color_name)
                            item.paint_color = color_code
                    color_button.setStyleSheet(f'QComboBox{{border-radius: 0px; background-color: {self.workspace_tags.get_data()["paint_colors"][color_button.currentText()]}}} {"QMenu { background-color: rgb(22,22,22);}"}')
                self.active_workspace_file.save()
            self.sync_changes()
            color_button.currentTextChanged.connect(partial(select_color, item, color_button))

        # def set_timer(timer_box: QComboBox, item: Item) -> None:
        #     timer_box.disconnect()

        #     timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))

        def add_timers(table: CustomTableWidget, item: WorkspaceItem, timer_layout: QHBoxLayout) -> None:
            self.clear_layout(timer_layout)
            self.workspace_tags.load_data()
            for flow_tag in item.timers:
                try:
                    self.workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]
                except (KeyError, TypeError):
                    continue
                if self.workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]:
                    widget = QWidget()
                    layout = QVBoxLayout(widget)
                    widget.setLayout(layout)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(QLabel(flow_tag))
                    timer_box = TimeSpinBox(widget)
                    with contextlib.suppress(KeyError):
                        timer_box.setValue(item.get_timer(flow_tag))
                    timer_box.editingFinished.connect(
                        lambda flow_tag=flow_tag, timer_box=timer_box: (
                            item.set_timer(flow_tag=flow_tag, time=timer_box),
                            self.active_workspace_file.save(),
                            self.sync_changes(),
                        )
                    )
                    layout.addWidget(timer_box)
                    timer_layout.addWidget(widget)
                table.resizeColumnsToContents()

        def flow_tag_box_change(
            table: CustomTableWidget,
            tag_box: QComboBox,
            item: WorkspaceItem,
            timer_layout: QHBoxLayout,
        ) -> None:
            if tag_box.currentText() == "Select Flow Tag":
                return
            tag_box.setStyleSheet("QComboBox#tag_box{border-radius: 0px;}")
            item.flow_tag = tag_box.currentText().split(" ➜ ")
            timers = {}
            for tag in tag_box.currentText().split(" ➜ "):
                timers[tag] = {}
            item.timers = timers
            self.active_workspace_file.save()
            add_timers(table, item, timer_layout)
            self.sync_changes()

        def notes_change(table: CustomTableWidget, notes: NotesPlainTextEdit, item: WorkspaceItem) -> None:
            item.notes = notes.toPlainText()
            self.active_workspace_file.save()
            self.sync_changes()

        def add_item(row_index: int, item: WorkspaceItem):
            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            table.setItem(row_index, col_index, QTableWidgetItem(item.name))
            col_index += 1
            for file_column in ["Bending Files", "Welding Files", "CNC/Milling Files"]:
                button_widget = QWidget()
                files_layout = QHBoxLayout()
                files_layout.setContentsMargins(0, 0, 0, 0)
                files_layout.setSpacing(0)
                button_widget.setLayout(files_layout)
                self.load_assemblies_items_file_layout(
                    file_category=file_column,
                    files_layout=files_layout,
                    assembly=assembly,
                    item=item,
                )
                table.setCellWidget(row_index, col_index, button_widget)
                col_index += 1
            thickness_box = QComboBox(self)
            thickness_box.wheelEvent = lambda event: event.ignore()
            thickness_box.setObjectName("thickness_box")
            thickness_box.setStyleSheet("QComboBox#thickness_box{border-radius: 0px;}")
            if not item.thickness:
                thickness_box.addItem("Select Thickness")
            thickness_box.addItems(self.sheet_settings.get_thicknesses())
            thickness_box.setCurrentText(item.thickness)

            def update_item_thickness():
                item.thickness = thickness_box.currentText()
                self.active_workspace_file.save()
                self.sync_changes()

            thickness_box.currentTextChanged.connect(update_item_thickness)
            table.setCellWidget(row_index, col_index, thickness_box)
            col_index += 1
            material_box = QComboBox(self)
            material_box.wheelEvent = lambda event: event.ignore()
            material_box.setObjectName("material_box")
            material_box.setStyleSheet("QComboBox#material_box{border-radius: 0px;}")
            if not item.material:
                material_box.addItem("Select Material")
            material_box.addItems(self.sheet_settings.get_materials())
            material_box.setCurrentText(item.material)

            def update_item_material():
                item.material = material_box.currentText()
                self.active_workspace_file.save()
                self.sync_changes()

            material_box.currentTextChanged.connect(update_item_material)
            table.setCellWidget(row_index, col_index, material_box)
            col_index += 1
            button_paint_type = QComboBox(self)
            button_paint_type.wheelEvent = lambda event: event.ignore()
            if not item.paint_type:
                button_paint_type.addItem("Select Paint Type")
            button_paint_type.addItems(["None", "Powder", "Wet Paint"])
            button_paint_type.setCurrentText("None")
            button_paint_type.setStyleSheet("border-radius: 0px; ")
            button_paint_type.setCurrentText(item.paint_type)

            def update_item_paint_type():
                item.paint_type = button_paint_type.currentText()
                self.active_workspace_file.save()
                self.sync_changes()

            button_paint_type.currentTextChanged.connect(update_item_paint_type)
            table.setCellWidget(row_index, col_index, button_paint_type)
            col_index += 1
            button_color = QComboBox(self)
            button_color.wheelEvent = lambda event: event.ignore()
            button_color.addItem("None")
            button_color.addItems(list(self.workspace_tags.get_value("paint_colors").keys()) or ["Select Color"])
            button_color.addItem("Select Color")
            if item.paint_color != None:
                for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                    if color_code == item.paint_color:
                        button_color.setCurrentText(color_name)
                button_color.setStyleSheet(f'QComboBox{{border-radius: 0px; background-color: {item.paint_color}}} {"QMenu { background-color: rgb(22,22,22);}"}')
            else:
                button_color.setCurrentText("Set Color")
                button_color.setStyleSheet("border-radius: 0px; ")
            button_color.currentTextChanged.connect(partial(select_color, item, button_color))
            table.setCellWidget(row_index, col_index, button_color)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(item.parts_per)))
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1

            # timer_box = QComboBox(self)
            # timer_box.addItems(["Set Timer For"] + item.data["flow_tag"])
            # timer_box.setCurrentIndex(0)
            # timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))
            timer_widget = QWidget()
            timer_layout = QHBoxLayout(timer_widget)
            timer_layout.setContentsMargins(0, 0, 0, 0)
            timer_widget.setLayout(timer_layout)
            add_timers(table=table, item=item, timer_layout=timer_layout)

            tag_box = QComboBox(self)
            tag_box.wheelEvent = lambda event: event.ignore()
            tag_box.setObjectName("tag_box")
            tag_box.setStyleSheet("QComboBox#tag_box{border-radius: 0px;}")
            if not item.flow_tag:
                tag_box.addItem("Select Flow Tag")
                tag_box.setStyleSheet("QComboBox#tag_box{color: red; border-radius: 0px; border-color: darkred; background-color: #3F1E25;}")
            tag_box.addItems(self.get_all_flow_tags())
            if item.flow_tag:
                tag_box.setCurrentText(" ➜ ".join(item.flow_tag))
            tag_box.currentTextChanged.connect(partial(flow_tag_box_change, table, tag_box, item, timer_layout))
            table.setCellWidget(row_index, col_index, tag_box)
            col_index += 1
            table.setCellWidget(row_index, col_index, timer_widget)
            col_index += 1
            notes = NotesPlainTextEdit(self, item.notes, "Add notes...")
            notes.setFixedHeight(50)
            notes.textChanged.connect(partial(notes_change, table, notes, item))
            table.setCellWidget(row_index, col_index, notes)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(item.shelf_number))
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            delete_button = DeletePushButton(
                self,
                tool_tip=f"Delete {item.name} forever from {assembly.name}",
                icon=QIcon(f"icons/trash.png"),
            )
            delete_button.clicked.connect(partial(self.delete_workspace_item, assembly, table, row_index))
            delete_button.setStyleSheet("margin-top: 10px; margin-bottom: 10px; margin-right: 4px; margin-left: 4px;")
            table.setCellWidget(row_index, col_index, delete_button)

        row_index: int = 0
        for item in assembly.items:
            if not item.show:
                continue
            add_item(row_index, item)
            row_index += 1

        def add_new_item():
            input_dialog = AddWorkspaceItem(self.components_inventory, self.laser_cut_inventory, self)
            if input_dialog.exec():
                item_name = input_dialog.get_name()
                material = input_dialog.material
                thickness = input_dialog.thickness
                table.blockSignals(True)
                date_created: str = QDate().currentDate().toString("yyyy-MM-dd")
                inventory_item = self.admin_workspace.get_inventory_item(item_name)
                item = WorkspaceItem(inventory_item, data={})
                item.material = material
                item.thickness = thickness
                item.starting_date = date_created
                item.ending_date = date_created
                add_item(table.rowCount() - 1, item)
                assembly.add_item(item)
                self.active_workspace_file.save()
                self.sync_changes()
                item_group_box: QGroupBox = table.parentWidget()
                item_group_box.setFixedHeight(item_group_box.height() + 45)
                table.setFixedHeight(45 * (len(assembly.items) + 3))
                table.blockSignals(False)

        def add_item_button(on_load: bool = False):
            row_count = table.rowCount()
            if row_count > 0:
                table.removeCellWidget(row_count - 1, 0)
            plus_button = QPushButton(self)
            plus_button.setObjectName("plus_button")
            plus_button.setStyleSheet("QPushButton#plus_button{margin: 2px;}")
            plus_button.setText("Add Item")
            plus_button.clicked.connect(add_new_item)
            plus_button.clicked.connect(add_item_button)
            plus_button.setEnabled(not assembly.exists(""))
            if on_load:
                table.insertRow(table.rowCount())  # Insert a new row at the end
                table.setCellWidget(row_count, 0, plus_button)  # Add the button to the first column of the last row
            else:
                table.setCellWidget(table.rowCount() - 1, 0, plus_button)  # Add the button to the first column of the last row

        table.itemChanged.connect(partial(self.assembly_items_table_cell_changed, table, assembly))
        table.itemClicked.connect(self.assembly_items_table_clicked)

        add_item_button(on_load=True)

        table.set_editable_column_index([0, 8, 12])
        table.blockSignals(False)
        table.resizeColumnsToContents()
        self.workspace_tables[table] = assembly
        # header = table.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Set the first column to Fixed

        return table

    def assembly_image_show_context_menu(self, assembly_image: AssemblyImage, assembly: Assembly):
        contextMenu = QMenu(self)
        deleteAction = contextMenu.addAction("Clear image")
        action = contextMenu.exec(QCursor.pos())

        if action == deleteAction:
            assembly.assembly_image = None

            assembly_image.clear_image()

            self.active_workspace_file.save()
            self.sync_changes()

    # STAGING/EDITING
    def load_edit_assembly_widget(
        self,
        assembly: Assembly,
        workspace_information: dict,
        group_color: str,
        parent=None,
    ) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        assembly_image = AssemblyImage(widget)
        if assembly.assembly_image:
            assembly_image.set_new_image(assembly.assembly_image)

        assembly_image.clicked.connect(partial(self.open_assembly_image, assembly))

        def upload_assembly_image(path_to_image: str):
            file_ext = path_to_image.split(".")[-1].upper()
            file_name = os.path.basename(path_to_image)

            target_dir = f"data/workspace/{file_ext}"
            target_path = os.path.join(target_dir, file_name)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            shutil.copyfile(path_to_image, target_path)

            assembly_image.set_new_image(target_path)
            assembly.assembly_image = target_path
            self.upload_workspace_files([target_path])
            self.active_workspace_file.save()
            self.sync_changes()

        assembly_image.imagePathDropped.connect(upload_assembly_image)
        assembly_image.customContextMenuRequested.connect(partial(self.assembly_image_show_context_menu, assembly_image, assembly))

        h_layout.addWidget(assembly_image)

        layout.addLayout(h_layout)
        # widget.setLayout(h_layout)
        timer_widget = QWidget(widget)
        timer_layout = QHBoxLayout(timer_widget)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_widget.setLayout(timer_layout)

        color_widget = QWidget(widget)
        color_widget.setHidden(True)
        _color_layout = QVBoxLayout()
        paint_color_layout = QHBoxLayout()
        paint_color_layout.setContentsMargins(0, 0, 0, 0)
        _color_layout.addLayout(paint_color_layout)
        paint_type_layout = QHBoxLayout()
        paint_type_layout.setContentsMargins(0, 0, 0, 0)
        _color_layout.addLayout(paint_type_layout)
        paint_amount_layout = QHBoxLayout()
        paint_amount_layout.setContentsMargins(0, 0, 0, 0)
        _color_layout.addLayout(paint_amount_layout)
        color_widget.setLayout(_color_layout)
        # Create the "Items" group box
        if assembly.has_items:
            # TODO
            def load_excel_file(files: list[str]):
                total_data: dict[str, list[WorkspaceItem]] = {}
                for file in files:
                    monday_excel_file = MondayExcelFile(file)
                    total_data.update(monday_excel_file.get_data())
                for job_name, job_data in total_data.items():
                    for item in job_data:
                        assembly.add_item(item)
                self.active_workspace_file.save()
                self.sync_changes()
                self.load_workspace()

            items_groupbox = ItemsGroupBox(self)
            items_groupbox.filesDropped.connect(load_excel_file)
            items_groupbox.setAcceptDrops(True)
            # items_groupbox.setMinimumHeight(500)
            items_layout = QVBoxLayout()
            items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            items_groupbox.setLayout(items_layout)

        # Create and configure the table widget
        if assembly.has_items:
            table_widget = self.load_edit_assembly_items_table(assembly)
            table_widget.setFixedHeight(45 * (len(assembly.items) + 3))

        def select_color(assembly: Assembly, color_button: QComboBox) -> str:
            color_button.disconnect()
            if color_button.currentText() == "Select Color":
                self.workspace_tags.load_data()
                color = ColorPicker()
                color.show()
                if color.exec():
                    assembly.paint_color = color.getHex(True)
                    color_name = color.getColorName()
                    self.active_workspace_file.save()
                    self.sync_changes()
                    color_button.setStyleSheet(f'QComboBox{{background-color: {assembly.paint_color}}} {"QMenu { background-color: rgb(22,22,22);}"}')
                    data = self.workspace_tags.get_data()
                    data["paint_colors"][color_name] = color.getHex(True)
                    self.workspace_tags.save_data(data)
                    self.workspace_tags.load_data()
                    color_button.clear()
                    color_button.addItems(list(self.workspace_tags.get_value("paint_colors").keys()))
                    color_button.addItem("Select Color")
                    color_button.setCurrentText(color_name)
            else:
                if color_button.currentText() == "None":
                    color_button.setStyleSheet(f'QComboBox{{background-color: transparent}} {"QMenu { background-color: rgb(22,22,22);}"}')
                    color_button.setCurrentText("None")
                    assembly.paint_color = None
                else:
                    self.workspace_tags.load_data()
                    for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                        if color_code == self.workspace_tags.get_data()["paint_colors"][color_button.currentText()]:
                            color_button.setCurrentText(color_name)
                            assembly.paint_color = color_code
                    color_button.setStyleSheet(f'QComboBox{{background-color: {self.workspace_tags.get_data()["paint_colors"][color_button.currentText()]}}} {"QMenu { background-color: rgb(22,22,22);}"}')
                self.active_workspace_file.save()
            self.sync_changes()
            color_button.currentTextChanged.connect(partial(select_color, assembly, color_button))

        def add_timers(timer_layout: QHBoxLayout) -> None:
            self.clear_layout(timer_layout)
            self.workspace_tags.load_data()
            for flow_tag in assembly.flow_tag:
                try:
                    self.workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]
                except (KeyError, TypeError):
                    continue
                if self.workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]:
                    _widget = QWidget()
                    layout = QVBoxLayout(_widget)
                    # _widget.setLayout(layout)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(QLabel(flow_tag))
                    timer_box = TimeSpinBox()
                    with contextlib.suppress(KeyError, TypeError):
                        timer_box.setValue(assembly.timers[flow_tag]["time_to_complete"])
                    timer_box.editingFinished.connect(
                        lambda flow_tag=flow_tag, timer_box=timer_box: (
                            assembly.set_timer(flow_tag=flow_tag, time=timer_box),
                            self.active_workspace_file.save(),
                            self.sync_changes(),
                        )
                    )
                    layout.addWidget(timer_box)
                    timer_layout.addWidget(_widget)

        def flow_tag_change(
            timer_layout: QHBoxLayout,
            color_widget: QWidget,
            flow_tag_combobox: QComboBox,
        ):
            flow_tag_combobox.setStyleSheet("")
            assembly.flow_tag = flow_tag_combobox.currentText().split(" ➜ ")
            color_widget.setHidden(all(keyword not in flow_tag_combobox.currentText().lower() for keyword in ["paint", "powder"]))
            timers = {}
            for tag in flow_tag_combobox.currentText().split(" ➜ "):
                timers[tag] = {}
            assembly.timers = timers
            self.active_workspace_file.save()
            self.sync_changes()
            add_timers(timer_layout)

        def get_grid_widget() -> QWidget:
            # Add the table widget to the "Items" group box
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            time_box = TimeSpinBox()
            time_box.setValue(assembly.expected_time_to_complete)

            def update_expected_time_to_complete():
                assembly.expected_time_to_complete = time_box.value()
                self.active_workspace_file.save()
                self.sync_changes()

            time_box.editingFinished.connect(update_expected_time_to_complete)
            grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
            flow_tag_combobox = QComboBox()
            flow_tag_combobox.setObjectName("tag_box")
            flow_tag_combobox.wheelEvent = lambda event: event.ignore()
            if not assembly.flow_tag:
                flow_tag_combobox.addItem("Select Flow Tag")
                flow_tag_combobox.setStyleSheet("QComboBox#tag_box{color: red; border-color: darkred; background-color: #3F1E25;}")
            flow_tag_combobox.addItems(self.get_all_flow_tags())
            flow_tag_combobox.setCurrentText(" ➜ ".join(assembly.flow_tag))
            flow_tag_combobox.currentTextChanged.connect(partial(flow_tag_change, timer_layout, color_widget, flow_tag_combobox))
            grid.addWidget(QLabel("Expected time to complete:"), 0, 0)
            grid.addWidget(time_box, 0, 1)
            grid.addWidget(QLabel("Assembly Flow Tag:"), 1, 0)
            grid.addWidget(flow_tag_combobox, 1, 1)
            button_color = QComboBox(self)
            button_color.wheelEvent = lambda event: event.ignore()
            button_color.addItem("None")
            button_color.addItems(list(self.workspace_tags.get_value("paint_colors").keys()) or ["Select Color"])
            button_color.addItem("Select Color")
            if assembly.paint_color != None:
                for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                    if color_code == assembly.paint_color:
                        button_color.setCurrentText(color_name)
                button_color.setStyleSheet(f'QComboBox{{background-color: {assembly.paint_color}}} {"QMenu { background-color: rgb(22,22,22);}"}')
            else:
                button_color.setCurrentText("Set Color")
            button_color.currentTextChanged.connect(partial(select_color, assembly, button_color))
            paint_color_layout.addWidget(QLabel("Paint Color:"))
            paint_color_layout.addWidget(button_color)

            button_paint_type = QComboBox(self)
            button_paint_type.wheelEvent = lambda event: event.ignore()
            if not assembly.paint_type:
                button_paint_type.addItem("Select Paint Type")
            button_paint_type.addItems(["None", "Powder", "Wet Paint"])
            button_paint_type.setCurrentText("None")
            button_paint_type.setCurrentText(assembly.paint_type)

            def update_paint_type():
                assembly.paint_type = button_paint_type.currentText()
                self.active_workspace_file.save()
                self.sync_changes()

            button_paint_type.currentTextChanged.connect(update_paint_type)
            paint_type_layout.addWidget(QLabel("Paint Type:"))
            paint_type_layout.addWidget(button_paint_type)

            lineedit_paint_amount = HumbleDoubleSpinBox(self)
            with contextlib.suppress(TypeError):
                lineedit_paint_amount.setValue(assembly.paint_amount)
            lineedit_paint_amount.setSuffix(" gallons")

            def update_paint_amount():
                assembly.paint_amount = lineedit_paint_amount.value()
                self.active_workspace_file.save()
                self.sync_changes()

            lineedit_paint_amount.editingFinished.connect(update_paint_amount)
            paint_amount_layout.addWidget(QLabel("Paint Amount:"))
            paint_amount_layout.addWidget(lineedit_paint_amount)
            color_widget.setHidden(all(keyword not in flow_tag_combobox.currentText().lower() for keyword in ["paint", "powder"]))
            return grid_widget

        grid_widget = get_grid_widget()
        add_timers(timer_layout)

        if assembly.has_items:
            h_layout.addWidget(grid_widget)
            items_layout.addWidget(table_widget)
        else:
            h_layout.addWidget(grid_widget)
        h_layout.addWidget(timer_widget)
        h_layout.addWidget(color_widget)

        # Add the "Items" group box to the main layout
        if assembly.has_items:
            layout.addWidget(items_groupbox)

        # Create the "Add Sub Assembly" button
        pushButton_add_sub_assembly = QPushButton("Add Sub Assembly")
        pushButton_add_sub_assembly.setFixedWidth(120)

        if assembly.has_sub_assemblies:
            sub_assembly_groupbox = QGroupBox("Sub Assemblies")
            sub_assembly_groupbox_layout = QVBoxLayout()
            sub_assembly_groupbox.setLayout(sub_assembly_groupbox_layout)

        workspace_information.setdefault(assembly.name, {"tool_box": None, "sub_assemblies": {}})
        try:
            workspace_information[assembly.name]["tool_box"] = workspace_information[assembly.name]["tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        # Create the MultiToolBox for sub assemblies
        sub_assemblies_toolbox = AssemblyMultiToolBox()
        sub_assemblies_toolbox.layout().setSpacing(0)

        def add_sub_assembly():
            input_text, ok = QInputDialog.getText(self, "Add Sub Assembly", "Enter a name for a new sub assembly:")
            if input_text and ok:
                date_created: str = QDate().currentDate().toString("yyyy-MM-dd")
                new_assembly: Assembly = Assembly(
                    name=input_text,
                    assembly_data={
                        "has_items": True,
                        "starting_data": date_created,
                        "ending_date": date_created,
                    },
                )
                assembly.add_sub_assembly(new_assembly)
                self.active_workspace_file.save()
                self.sync_changes()
                workspace_information.setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
                sub_assembly_widget = self.load_edit_assembly_widget(
                    new_assembly,
                    workspace_information[new_assembly.name]["sub_assemblies"],
                    group_color=self.active_workspace_file.get_group_color(assembly.get_master_assembly().group),
                )  # Load the widget for the new assembly
                sub_assemblies_toolbox.addItem(sub_assembly_widget, new_assembly.name, base_color=group_color)  # Add the widget to the MultiToolBox
                delete_button = sub_assemblies_toolbox.getLastDeleteButton()
                delete_button.clicked.connect(partial(delete_sub_assembly, new_assembly, sub_assembly_widget))
                duplicate_button = sub_assemblies_toolbox.getLastDuplicateButton()
                duplicate_button.clicked.connect(partial(duplicate_sub_assembly, new_assembly))
                input_box = sub_assemblies_toolbox.getLastInputBox()
                input_box.editingFinished.connect(partial(rename_sub_assembly, new_assembly, input_box))
                self.load_edit_assembly_context_menus()
                # self.sync_changes()
                # self.load_categories()

        def delete_sub_assembly(sub_assembly_to_delete: Assembly, widget_to_delete: QWidget):
            assembly.delete_sub_assembly(sub_assembly_to_delete)
            self.active_workspace_file.save()
            self.sync_changes()
            sub_assemblies_toolbox.removeItem(widget_to_delete)

        def duplicate_sub_assembly(assembly_to_duplicate: Assembly):
            new_assembly = assembly.copy_sub_assembly(assembly_to_duplicate)
            assembly.add_sub_assembly(new_assembly)
            # new_assembly.set_assembly_data(key="widget_color", value=get_random_color())
            self.active_workspace_file.save()
            self.sync_changes()
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            workspace_information.setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
            assembly_widget = self.load_edit_assembly_widget(
                new_assembly,
                workspace_information[new_assembly.name]["sub_assemblies"],
                group_color=self.active_workspace_file.get_group_color(assembly.get_master_assembly().group),
            )
            sub_assemblies_toolbox.addItem(assembly_widget, new_assembly.name, base_color=group_color)
            delete_button = sub_assemblies_toolbox.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_sub_assembly, new_assembly, assembly_widget))
            duplicate_button = sub_assemblies_toolbox.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_sub_assembly, new_assembly))
            input_box = sub_assemblies_toolbox.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_sub_assembly, new_assembly, input_box))

            self.load_edit_assembly_context_menus()

        def rename_sub_assembly(assembly_to_rename: Assembly, input_box: QLineEdit):
            assembly_to_rename.rename(input_box.text())
            self.active_workspace_file.save()
            self.sync_changes()

        if assembly.has_sub_assemblies:
            pushButton_add_sub_assembly.clicked.connect(add_sub_assembly)
            # Add the sub assemblies MultiToolBox to the main layout
            sub_assembly_groupbox_layout.addWidget(pushButton_add_sub_assembly)
            sub_assembly_groupbox_layout.addWidget(sub_assemblies_toolbox)
            layout.addWidget(sub_assembly_groupbox)
            if len(assembly.sub_assemblies) > 0:
                for i, sub_assembly in enumerate(assembly.sub_assemblies):
                    # Load the sub assembly recursively and add it to the sub assemblies MultiToolBox
                    sub_assembly_widget = self.load_edit_assembly_widget(
                        sub_assembly,
                        workspace_information=workspace_information[assembly.name]["sub_assemblies"],
                        group_color=group_color,
                    )
                    sub_assemblies_toolbox.addItem(sub_assembly_widget, sub_assembly.name, base_color=group_color)
                    delete_button = sub_assemblies_toolbox.getLastDeleteButton()
                    delete_button.clicked.connect(partial(delete_sub_assembly, sub_assembly, sub_assembly_widget))
                    duplicate_button = sub_assemblies_toolbox.getLastDuplicateButton()
                    duplicate_button.clicked.connect(partial(duplicate_sub_assembly, sub_assembly))
                    input_box = sub_assemblies_toolbox.getLastInputBox()
                    input_box.editingFinished.connect(partial(rename_sub_assembly, sub_assembly, input_box))
                sub_assemblies_toolbox.close_all()
        if saved_workspace_prefs:
            sub_assemblies_toolbox.set_widgets_visibility(workspace_information[assembly.name]["tool_box"])
        workspace_information[assembly.name]["tool_box"] = sub_assemblies_toolbox
        return widget

    # STAGING/EDITING
    def load_edit_assembly_tab(self) -> None:
        with contextlib.suppress(AttributeError):
            self.workspace_filter_tab_widget.clear_selections("Flow Tags")
        self.workspace_information.setdefault(self.category, {"group_tool_box": None})
        try:
            self.workspace_information[self.category]["group_tool_box"] = self.workspace_information[self.category]["group_tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        scroll_area = QScrollArea(self)

        def save_scroll_position(tab_name: str, scroll: QScrollArea):
            self.scroll_position_manager.save_scroll_position(tab_name, scroll)

        scroll_area.verticalScrollBar().valueChanged.connect(
            partial(
                save_scroll_position,
                f"Workspace {self.category}",
                scroll_area,
            )
        )
        scroll_area.horizontalScrollBar().valueChanged.connect(
            partial(
                save_scroll_position,
                f"Workspace {self.category}",
                scroll_area,
            )
        )
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(scroll_area)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(1)
        scroll_area.setWidget(scroll_content)

        # workspace_data = self.active_workspace_file.get_data()
        self.active_workspace_file.get_filtered_data(self.workspace_filter)
        grouped_data = self.active_workspace_file.get_grouped_data()

        group_tool_boxes: dict[str, QWidget] = {}
        group_tool_box = AssemblyMultiToolBox(scroll_content)

        def set_assembly_inputbox_context_menu(
            input_box: QLineEdit,
            multi_tool_box: AssemblyMultiToolBox,
            assembly_widget: QWidget,
            assembly: Assembly,
        ) -> None:
            input_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(input_box)
            groups_menu = QMenu(menu)
            groups_menu.setTitle("Move to Group")
            for menu_group in self.active_workspace_file._get_all_groups():
                if menu_group == assembly.group:
                    continue
                action = QAction(groups_menu)
                action.triggered.connect(
                    partial(
                        move_to_group,
                        multi_tool_box,
                        assembly_widget,
                        assembly,
                        menu_group,
                        False,
                    )
                )
                action.setText(menu_group)
                groups_menu.addAction(action)
            action = QAction(groups_menu)
            action.triggered.connect(
                partial(
                    move_to_group,
                    multi_tool_box,
                    assembly_widget,
                    assembly,
                    "menu_group",
                    True,
                )
            )
            action.setText("Create Group")
            groups_menu.addAction(action)
            menu.addMenu(groups_menu)
            input_box.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        def add_job():
            input_dialog = AddJobDialog(self.active_workspace_file._get_all_groups(), self)

            if input_dialog.exec():
                (
                    job_name,
                    has_items,
                    has_sub_assemblies,
                ) = input_dialog.get_selected_items()
                group = input_dialog.get_group_name()
                group_color = get_random_color()
                if group in list(grouped_data.keys()):
                    for assembly in self.active_workspace_file.data:
                        if assembly.group == group:
                            group_color = assembly.group_color
                new_assembly: Assembly = Assembly(
                    name=job_name,
                    assembly_data={
                        "has_items": has_items,
                        "has_sub_assemblies": has_sub_assemblies,
                        "group": group,
                        "group_color": group_color,
                    },
                )
                try:
                    multi_tool_box = self.workspace_information[self.category][group]["tool_box"]
                except (KeyError, TypeError):
                    multi_tool_box = None

                if multi_tool_box is None:
                    group_widget = QWidget()
                    group_layout = QVBoxLayout(group_widget)
                    group_widget.setLayout(group_layout)
                    group_tool_box.addItem(group_widget, group, base_color=group_color)
                    # group_tool_box.open(len(group_tool_box.buttons) - 1)
                    delete_button = group_tool_box.getLastDeleteButton()
                    delete_button.clicked.connect(partial(delete_group, group_tool_box, group, group_widget))
                    duplicate_button = group_tool_box.getLastDuplicateButton()
                    duplicate_button.clicked.connect(partial(duplicate_group, group))
                    input_box = group_tool_box.getLastInputBox()
                    input_box.editingFinished.connect(partial(rename_group, group_tool_box, group, input_box))
                    group_tool_boxes[group] = group_widget
                    self.workspace_information[self.category].setdefault(
                        group,
                        {
                            "tool_box": None,
                            "sub_assemblies": {},
                            "group_tool_box": None,
                        },
                    )

                    multi_tool_box = AssemblyMultiToolBox()
                    multi_tool_box.layout().setSpacing(0)
                    group_tool_boxes[group].layout().addWidget(multi_tool_box)

                self.active_workspace_file.add_assembly(new_assembly)
                self.active_workspace_file.save()
                self.sync_changes()
                self.workspace_information[self.category][group].setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
                sub_assembly_widget = self.load_edit_assembly_widget(
                    assembly=new_assembly,
                    workspace_information=self.workspace_information[self.category][group][new_assembly.name]["sub_assemblies"],
                    group_color=group_color,
                )  # Load the widget for the new assembly
                multi_tool_box.addItem(sub_assembly_widget, new_assembly.name, base_color=group_color)  # Add the widget to the MultiToolBox
                # multi_tool_box.open_all()
                delete_button = multi_tool_box.getLastDeleteButton()
                delete_button.clicked.connect(
                    partial(
                        delete_assembly,
                        multi_tool_box,
                        new_assembly,
                        sub_assembly_widget,
                    )
                )
                duplicate_button = multi_tool_box.getLastDuplicateButton()
                duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, new_assembly))
                input_box = multi_tool_box.getLastInputBox()
                input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, new_assembly, input_box))

        def delete_assembly(
            multi_tool_box: AssemblyMultiToolBox,
            sub_assembly_to_delete: Assembly,
            widget_to_delete: QWidget,
        ):
            self.active_workspace_file.remove_assembly(sub_assembly_to_delete)
            self.active_workspace_file.save()
            self.sync_changes()
            multi_tool_box.removeItem(widget_to_delete)

        def duplicate_assembly(multi_tool_box: AssemblyMultiToolBox, assembly_to_duplicate: Assembly):
            new_assembly = self.active_workspace_file.duplicate_assembly(assembly_to_duplicate)
            self.active_workspace_file.save()
            self.sync_changes()
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            self.workspace_information.setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
            assembly_widget = self.load_edit_assembly_widget(
                new_assembly,
                workspace_information=self.workspace_information[new_assembly.name]["sub_assemblies"],
                group_color=self.active_workspace_file.get_group_color(assembly_to_duplicate.get_master_assembly().group),
            )
            multi_tool_box.addItem(
                assembly_widget,
                new_assembly.name,
                base_color=new_assembly.group_color,
            )
            delete_button = multi_tool_box.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, new_assembly, assembly_widget))
            duplicate_button = multi_tool_box.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, new_assembly))
            input_box = multi_tool_box.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, new_assembly, input_box))
            set_assembly_inputbox_context_menu(
                input_box=input_box,
                multi_tool_box=multi_tool_box,
                assembly_widget=assembly_widget,
                assembly=new_assembly,
            )

            multi_tool_box.close(len(multi_tool_box.buttons) - 1)

        def rename_sub_assembly(
            multi_tool_box: AssemblyMultiToolBox,
            assembly_to_rename: Assembly,
            input_box: QLineEdit,
        ):
            assembly_to_rename.rename(input_box.text())
            self.active_workspace_file.save()
            self.sync_changes()

        def delete_group(group_tool_box: AssemblyMultiToolBox, group: str, widget_to_delete: QWidget):
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()
            with contextlib.suppress(KeyError):
                for assembly in grouped_data[group]:
                    self.active_workspace_file.remove_assembly(assembly)
                self.active_workspace_file.save()
                self.sync_changes()
            group_tool_box.removeItem(widget_to_delete)
            del self.workspace_information[self.category][group]

        def duplicate_group(group: str):
            new_group_name: str = f"{group} - (Copy)"
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()
            group_color = get_random_color()
            for assembly in grouped_data[group]:
                new_assembly = self.active_workspace_file.duplicate_assembly(assembly)
                new_assembly.group = new_group_name
                new_assembly.group_color = group_color
                self.active_workspace_file.save()
            self.sync_changes()

            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()

            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_widget.setLayout(group_layout)
            group_tool_box.addItem(group_widget, new_group_name, base_color=group_color)
            # group_tool_box.open(len(group_tool_box.buttons) - 1)
            delete_button = group_tool_box.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_group, group_tool_box, new_group_name, group_widget))
            duplicate_button = group_tool_box.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_group, new_group_name))
            input_box = group_tool_box.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_group, group_tool_box, new_group_name, input_box))
            group_tool_boxes[new_group_name] = group_widget
            self.workspace_information[self.category].setdefault(
                new_group_name,
                {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None},
            )

            multi_tool_box = AssemblyMultiToolBox()
            multi_tool_box.layout().setSpacing(0)
            for i, assembly in enumerate(grouped_data[new_group_name]):
                assembly_widget = self.load_edit_assembly_widget(
                    assembly=assembly,
                    workspace_information=self.workspace_information[self.category][new_group_name]["sub_assemblies"],
                    group_color=group_color,
                )
                multi_tool_box.addItem(assembly_widget, assembly.name, base_color=group_color)
                delete_button = multi_tool_box.getDeleteButton(i)
                delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, assembly, assembly_widget))
                duplicate_button = multi_tool_box.getDuplicateButton(i)
                duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, assembly))
                input_box = multi_tool_box.getInputBox(i)
                input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, assembly, input_box))
                set_assembly_inputbox_context_menu(
                    input_box=input_box,
                    multi_tool_box=multi_tool_box,
                    assembly_widget=assembly_widget,
                    assembly=assembly,
                )

            multi_tool_box.close_all()
            # pushButton_add_job = QPushButton(scroll_content)
            # pushButton_add_job.setText("Add Job")
            # pushButton_add_job.clicked.connect(add_assembly)
            self.workspace_information[self.category][group]["tool_box"] = multi_tool_box
            group_tool_boxes[new_group_name].layout().addWidget(multi_tool_box)
            # group_tool_box.addItem()

        def rename_group(group_tool_box: AssemblyMultiToolBox, group: str, input_box: QLineEdit):
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()
            try:
                for assembly in grouped_data[group]:
                    assembly.group = input_box.text()
            except KeyError:  # The assembly mustve been deleted?
                return
            self.active_workspace_file.save()
            self.sync_changes()

        def move_to_group(
            multi_tool_box_to_move_from: AssemblyMultiToolBox,
            assembly_widget_to_move: QWidget,
            assembly: Assembly,
            group: str,
            prompt_group_name: bool = False,
        ):
            if prompt_group_name:
                input_text, ok = QInputDialog.getText(self, "Create Group", "Enter a name for a group:")
                if input_text and ok:
                    assembly.group = input_text
                    self.active_workspace_file.save()
                    self.sync_changes()
                    try:
                        multi_tool_box_to_move_to = self.workspace_information[self.category][group]["tool_box"]
                    except KeyError:  # The group does not exist because the user craeted a new one
                        group_widget = QWidget()
                        group_layout = QVBoxLayout(group_widget)
                        group_widget.setLayout(group_layout)
                        group_tool_box.addItem(group_widget, group)
                        # group_tool_box.open(len(group_tool_box.buttons) - 1)
                        delete_button = group_tool_box.getLastDeleteButton()
                        delete_button.clicked.connect(partial(delete_group, group_tool_box, group, group_widget))
                        duplicate_button = group_tool_box.getLastDuplicateButton()
                        duplicate_button.clicked.connect(partial(duplicate_group, group_tool_box, group))
                        input_box = group_tool_box.getLastInputBox()
                        input_box.editingFinished.connect(partial(rename_group, group_tool_box, group, input_box))
                        group_tool_boxes[group] = group_widget
                        self.workspace_information[self.category].setdefault(
                            group,
                            {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None},
                        )
                        multi_tool_box = AssemblyMultiToolBox()
                        multi_tool_box.layout().setSpacing(0)
                        self.workspace_information[self.category][group]["tool_box"] = multi_tool_box
                        group_tool_boxes[group].layout().addWidget(multi_tool_box)
                        multi_tool_box_to_move_to = multi_tool_box

            assembly_widget = self.load_edit_assembly_widget(
                assembly=assembly,
                workspace_information=self.workspace_information[self.category][group]["sub_assemblies"],
            )
            multi_tool_box_to_move_to.addItem(assembly_widget, assembly.name)
            delete_button = multi_tool_box_to_move_to.getLastDeleteButton()
            delete_button.clicked.connect(
                partial(
                    delete_assembly,
                    multi_tool_box_to_move_to,
                    assembly,
                    assembly_widget,
                )
            )
            duplicate_button = multi_tool_box_to_move_to.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box_to_move_to, assembly))
            input_box = multi_tool_box_to_move_to.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box_to_move_to, assembly, input_box))
            set_assembly_inputbox_context_menu(
                input_box=input_box,
                multi_tool_box=multi_tool_box_to_move_to,
                assembly_widget=assembly_widget,
                assembly=assembly,
            )
            multi_tool_box_to_move_to.close(len(multi_tool_box_to_move_to.buttons) - 1)
            multi_tool_box_to_move_from.removeItem(assembly_widget_to_move)

        for i, group in enumerate(self.active_workspace_file.get_all_groups()):
            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_widget.setLayout(group_layout)
            group_color = self.active_workspace_file.get_group_color(group)
            group_tool_box.addItem(group_widget, group, base_color=group_color)
            delete_button = group_tool_box.getDeleteButton(i)
            delete_button.clicked.connect(partial(delete_group, group_tool_box, group, group_widget))
            duplicate_button = group_tool_box.getDuplicateButton(i)
            duplicate_button.clicked.connect(partial(duplicate_group, group))
            input_box = group_tool_box.getInputBox(i)
            input_box.editingFinished.connect(partial(rename_group, group_tool_box, group, input_box))
            group_tool_boxes[group] = group_widget
            self.workspace_information[self.category].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})
        group_tool_box.close_all()
        if saved_workspace_prefs:
            group_tool_box.set_widgets_visibility(self.workspace_information[self.category]["group_tool_box"])
        self.workspace_information[self.category]["group_tool_box"] = group_tool_box
        if len(group_tool_box.buttons) == 0:
            scroll_layout.addWidget(QLabel("Nothing to show.", self))
        else:
            scroll_layout.addWidget(group_tool_box)
        for group in grouped_data:
            try:
                self.workspace_information[self.category][group]["tool_box"] = self.workspace_information[self.category][group]["tool_box"].get_widget_visibility()
                saved_workspace_prefs = True
            except (AttributeError, RuntimeError):
                saved_workspace_prefs = False
            multi_tool_box = AssemblyMultiToolBox()
            multi_tool_box.layout().setSpacing(0)
            group_color = self.active_workspace_file.get_group_color(group)
            for i, assembly in enumerate(grouped_data[group]):
                assembly_widget = self.load_edit_assembly_widget(
                    assembly=assembly,
                    workspace_information=self.workspace_information[self.category][group]["sub_assemblies"],
                    group_color=group_color,
                )
                multi_tool_box.addItem(assembly_widget, assembly.name, base_color=group_color)
                delete_button = multi_tool_box.getDeleteButton(i)
                delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, assembly, assembly_widget))
                duplicate_button = multi_tool_box.getDuplicateButton(i)
                duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, assembly))
                input_box = multi_tool_box.getInputBox(i)
                input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, assembly, input_box))
                set_assembly_inputbox_context_menu(
                    input_box=input_box,
                    multi_tool_box=multi_tool_box,
                    assembly_widget=assembly_widget,
                    assembly=assembly,
                )

            multi_tool_box.close_all()
            if saved_workspace_prefs:
                multi_tool_box.set_widgets_visibility(self.workspace_information[self.category][group]["tool_box"])
            # pushButton_add_job = QPushButton(scroll_content)
            # pushButton_add_job.setText("Add Job")
            # pushButton_add_job.clicked.connect(add_assembly)
            self.workspace_information[self.category][group]["tool_box"] = multi_tool_box
            group_tool_boxes[group].layout().addWidget(multi_tool_box)

        # multi_tool_box.close_all()
        # scroll_layout.addWidget(pushButton_add_job)

        self.pushButton_add_job.disconnect()
        self.pushButton_add_job.clicked.connect(add_job)
        self.tab_widget.currentWidget().layout().addWidget(scroll_area)
        self.scroll_position_manager.get_scroll_position(f"Workspace {self.category}")

    # USER
    def load_view_assembly_items_table(self, assembly: Assembly) -> CustomTableWidget:
        self.workspace_tags.load_data()
        headers: list[str] = [
            "Item Name",  # 0
            "Bending Files",  # 1
            "Welding Files",  # 2
            "CNC/Milling Files",  # 3
            "Thickness",  # 4
            "Material Type",  # 5
            "Paint Type",  # 6
            "Paint Color",  # 7
            "Quantity",  # 8
            "Flow Tag Controls",  # 9
            "Set Timers",  # 10
            "Shelf #",  # 11
            "Notes",  # 12
        ]
        #     table.setStyleSheet(
        #     f"QTableView {{ gridline-color: #EAE9FC; }} QTableWidget::item {{ border-color: #EAE9FC; }}"
        # )

        table = CustomTableWidget(self)
        # table.hideColumn()
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.hideColumn(1)
        table.hideColumn(2)
        table.hideColumn(3)
        table.hideColumn(6)
        table.hideColumn(7)
        table.hideColumn(10)

        def toggle_timer(
            item: WorkspaceItem,
            toggle_timer_button: QPushButton,
            recording_widget: RecordingWidget,
        ) -> None:
            item_flow_tag: str = item.get_current_flow_state()
            is_recording: bool = not item.timers[item_flow_tag]["recording"]
            toggle_timer_button.setChecked(is_recording)
            toggle_timer_button.setText("Stop" if is_recording else "Start")
            recording_widget.setHidden(not is_recording)
            item.timers[item_flow_tag]["recording"] = is_recording
            if is_recording:
                item.timers[item_flow_tag].setdefault("time_taken_intervals", [])
                item.timers[item_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
            else:
                item.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))

            self.user_workspace.save()
            self.sync_changes()

        def recut(item: WorkspaceItem) -> None:
            input_dialog = RecutDialog(f"Select or Input recut count for: {item.name}", item.parts_per, self)
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.ok:
                    recut_count = int(input_dialog.input_text)
                    parent_assembly = item.parent_assembly
                    inventory_item = self.user_workspace.get_inventory_item(item.name)
                    new_item = WorkspaceItem(
                        inventory_item,
                        data=item.to_dict(),
                    )
                    new_item.name = f"{item.name} - Recut #{item.recut_count + 1}"
                    new_item.parts_per = recut_count
                    new_item.complete = False
                    new_item.current_flow_state = new_item.flow_tag.index("Laser Cutting")
                    new_item.recut = True
                    parent_assembly.add_item(new_item)
                    item.recut_count += 1
                    item.parts_per -= recut_count
                    self.user_workspace.save()
                    self.sync_changes()
                    self.load_workspace()

        def move_to_next_flow(item: WorkspaceItem, row_index: int) -> None:
            item_flow_tag: str = item.get_current_flow_state()
            if self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                try:
                    item.timers[item_flow_tag]["recording"]
                except KeyError:
                    item.timers[item_flow_tag]["recording"] = False
                if item.timers[item_flow_tag]["recording"]:
                    item.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    item.timers[item_flow_tag]["recording"] = False
            if item_flow_tag == "Laser Cutting":
                item.recut = False
            item.current_flow_state += 1
            item.status = None
            if item.current_flow_state == len(item.flow_tag):
                item.completed = True
                item.date_completed = str(datetime.now())
                if assembly.current_flow_state == -1:  # NOTE Custom Job
                    completed_assemblies: list[Assembly] = []
                    self.history_workspace.load_data()
                    for main_assembly in self.user_workspace.data:
                        # Assembly is 100% complete
                        if self.user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                            main_assembly.completed = True
                            completed_assemblies.append(main_assembly)
                            self.history_workspace.add_assembly(main_assembly)
                            self.history_workspace.save()
                            self.parent.play_celebrate_sound()
                    for completed_assembly in completed_assemblies:
                        self.user_workspace.remove_assembly(completed_assembly)
            self.user_workspace.save()
            self.sync_changes()
            self.load_workspace()

        def item_status_changed(
            status_box: QComboBox,
            item: WorkspaceItem,
            row_index: int,
            toggle_timer_button: QPushButton,
        ) -> None:
            if self.workspace_tags.get_value("flow_tag_statuses")[item.get_current_flow_state()][status_box.currentText()]["start_timer"] and self.workspace_tags.get_value("attributes")[item.get_current_flow_state()]["is_timer_enabled"] and item.timers[item.get_current_flow_state()]["recording"] == False:
                toggle_timer_button.click()
            if self.workspace_tags.get_value("flow_tag_statuses")[item.get_current_flow_state()][status_box.currentText()]["completed"]:
                move_to_next_flow(item=item, row_index=row_index)
            else:
                item.status = status_box.currentText()

            self.user_workspace.save()
            self.sync_changes()

        def add_item(row_index: int, item: WorkspaceItem):
            if item.completed == False:
                try:
                    item_flow_tag: str = item.get_current_flow_state()
                except IndexError:  # This happens when an item was added from the Editing tab without a flow tag
                    return
            else:
                if assembly.current_flow_state >= 0:
                    item_flow_tag: str = assembly.get_current_flow_state()
                else:  # Custom Job
                    item_flow_tag: str = "Custom Job"

            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            table.setItem(row_index, col_index, QTableWidgetItem(item.name))  # 0
            col_index += 1
            for file_column in ["Bending Files", "Welding Files", "CNC/Milling Files"]:
                button_widget = QWidget()
                files_layout = QHBoxLayout()
                files_layout.setContentsMargins(0, 0, 0, 0)
                files_layout.setSpacing(0)
                button_widget.setLayout(files_layout)
                self.load_assemblies_items_file_layout(
                    file_category=file_column,
                    files_layout=files_layout,
                    assembly=assembly,
                    item=item,
                    show_dropped_widget=False,
                )
                table.setCellWidget(row_index, col_index, button_widget)
                col_index += 1
            if "bend" in item_flow_tag.lower():
                table.showColumn(1)
            if "weld" in item_flow_tag.lower():
                table.showColumn(2)
            if "cut" in item_flow_tag.lower():
                table.showColumn(3)
            if "paint" in item_flow_tag.lower():
                table.showColumn(6)
                table.showColumn(7)

            table.setItem(row_index, col_index, QTableWidgetItem(item.thickness))  # 4
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(item.material))  # 5
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(item.paint_type)))  # 6
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            button_color = QComboBox(self)
            button_color.setEnabled(False)
            if item.paint_color != None:
                for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                    if color_code == item.paint_color:
                        button_color.addItem(color_name)
                        button_color.setCurrentText(color_name)
                        button_color.setStyleSheet(f'QComboBox{{border-radius: 0px; background-color: {item.paint_color}}} {"QMenu { background-color: rgb(22,22,22);}"}')
                        break
            table.setCellWidget(row_index, col_index, button_color)  # 7
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(item.parts_per)))  # 8
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1

            # timer_box = QComboBox(self)
            # timer_box.addItems(["Set Timer For"] + item.data["flow_tag"])
            # timer_box.setCurrentIndex(0)
            # timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))
            # timer_widget = QWidget()
            # timer_layout = QHBoxLayout(timer_widget)
            # timer_layout.setContentsMargins(0, 0, 0, 0)
            # timer_widget.setLayout(timer_layout)

            # current_tag = QComboBox(self)
            # current_tag.wheelEvent = lambda event: event.ignore()
            # current_tag.setObjectName("tag_box")
            # current_tag.setStyleSheet("QComboBox#tag_box{margin: 2px;}")
            flow_tag_controls_widget = QWidget(self)
            h_layout = QHBoxLayout(flow_tag_controls_widget)
            flow_tag_controls_widget.setLayout(h_layout)
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 0)
            # TIMER WIDGET
            timer_widget = QWidget(self)
            timer_layout = QHBoxLayout(timer_widget)
            timer_widget.setLayout(timer_layout)
            recording_widget = RecordingWidget(timer_widget)
            toggle_timer_button = QPushButton(timer_widget)

            if item.completed == False:
                if not list(self.workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()):
                    try:
                        button_next_flow_state = QPushButton(self)
                        button_next_flow_state.setFixedHeight(50)
                        button_next_flow_state.setObjectName("flow_tag_button")
                        button_flow_state_name: str = "Mark as Done!"
                        if "bend" in item_flow_tag.lower():
                            button_flow_state_name = "Bent"
                        if "weld" in item_flow_tag.lower():
                            button_flow_state_name = "Welded"
                        if "cut" in item_flow_tag.lower():
                            button_flow_state_name = "Laser Cut"
                        if "paint" in item_flow_tag.lower():
                            button_flow_state_name = "Painted"
                        if "pick" in item_flow_tag.lower():
                            button_flow_state_name = "Picked"
                        if "assem" in item_flow_tag.lower():
                            button_flow_state_name = "Assembled"
                        button_next_flow_state.setText(button_flow_state_name)
                        button_next_flow_state.clicked.connect(partial(move_to_next_flow, item, row_index))
                        button_next_flow_state.setStyleSheet("border-radius: 0px;")
                        # QTableWidgetItem(item.data["flow_tag"][item.data["current_flow_state"]])
                        h_layout.addWidget(button_next_flow_state)
                        # table.setCellWidget(row_index, col_index, button_next_flow_state)
                    except IndexError:
                        table.setItem(row_index, col_index, QTableWidgetItem("Null"))
                        table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                else:
                    status_box = QComboBox(self)
                    status_box.setFixedHeight(50)
                    status_box.setObjectName("flow_tag_status_button")
                    status_box.addItems(list(self.workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()))
                    status_box.setCurrentText(item.status)
                    status_box.setStyleSheet("border-radius: 0px;")
                    status_box.currentTextChanged.connect(
                        partial(
                            item_status_changed,
                            status_box,
                            item,
                            row_index,
                            toggle_timer_button,
                        )
                    )
                    # table.setCellWidget(row_index, col_index, status_box)
                    h_layout.addWidget(status_box)
            # if ["paint", "quote", "ship"] not in item_flow_tag.lower():
            if all(tag not in item_flow_tag.lower() for tag in ["laser", "quote", "ship"]):  # tags where Recut should not be shown
                recut_button = QPushButton(self)
                recut_button.setText("Recut")
                recut_button.setObjectName("recut_button")
                recut_button.clicked.connect(partial(recut, item))
                h_layout.addWidget(recut_button)
            with contextlib.suppress(IndexError, KeyError):
                next_flow_tag = item.flow_tag[item.current_flow_state + 1]
                h_layout.addWidget(
                    QLabel(
                        self.workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"],
                        self,
                    )
                )
            # if item.get_value(key="recut_count") > 0:
            #     h_layout.addWidget(QLabel(f"Recut Count: {item.get_value(key='recut_count')}", self))

            table.setCellWidget(row_index, col_index, flow_tag_controls_widget)
            col_index += 1
            if item.completed == False and self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                is_recording: bool = item.timers[item_flow_tag].setdefault("recording", False)
                toggle_timer_button.setCheckable(True)
                toggle_timer_button.setChecked(is_recording)
                recording_widget.setHidden(not is_recording)
                toggle_timer_button.setObjectName("recording_button")
                toggle_timer_button.setText("Stop" if is_recording else "Start")
                toggle_timer_button.clicked.connect(partial(toggle_timer, item, toggle_timer_button, recording_widget))
                timer_layout.addWidget(toggle_timer_button)
                timer_layout.addWidget(recording_widget)
                table.setCellWidget(row_index, col_index, timer_widget)
                table.showColumn(10)

            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(item.shelf_number))  # 11
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(item.notes))  # 12
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        row_index: int = 0
        for item in assembly.items:
            if item.show == False:
                continue
            add_item(row_index, item)
            row_index += 1
        if row_index == 0:
            return QLabel("No Items to Show", self)

        table.itemChanged.connect(partial(self.assembly_items_table_cell_changed, table, assembly))
        table.itemClicked.connect(self.assembly_items_table_clicked)

        table.blockSignals(False)
        table.resizeColumnsToContents()
        self.workspace_tables[table] = assembly
        # header = table.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Set the first column to Fixed

        return table

    # USER
    def load_view_assembly_widget(
        self,
        assembly: Assembly,
        workspace_information: dict,
        group_color: str,
        parent=None,
    ) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        assembly_image = AssemblyImage(widget)
        if assembly.assembly_image:
            self.download_workspace_file(assembly.assembly_image, False)
            assembly_image.set_new_image(assembly.assembly_image)
        else:
            assembly_image.setText("No image provided")

        assembly_image.clicked.connect(partial(self.open_assembly_image, assembly))

        h_layout.addWidget(assembly_image)

        layout.addLayout(h_layout)
        # widget.setLayout(h_layout)
        timer_widget = QWidget()
        timer_layout = QHBoxLayout(timer_widget)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_widget.setLayout(timer_layout)
        # Create the "Items" group box
        items_groupbox = QGroupBox("Items")
        # items_groupbox.setMinimumHeight(500)
        items_layout = QVBoxLayout()
        items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        items_groupbox.setLayout(items_layout)

        # Create and configure the table widget
        if assembly.has_items:
            table_widget = self.load_view_assembly_items_table(assembly)
            table_widget.setFixedHeight(40 * (len(assembly.items) + 2))
            # if isinstance(table_widget, QLabel): # Its empty
            #     return QLabel("Empty", self)

        def get_grid_widget() -> QWidget:
            # Add the table widget to the "Items" group box
            grid_widget = QWidget(widget)
            grid = QGridLayout(grid_widget)

            timer_widget = QWidget()
            timer_layout = QHBoxLayout(timer_widget)
            timer_layout.setContentsMargins(0, 0, 0, 0)
            timer_widget.setLayout(timer_layout)

            grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(
                QLabel(f"Timeline: {assembly.starting_date} to {assembly.ending_date}, ({QDate.fromString(assembly.starting_date, 'yyyy-MM-dd').daysTo(QDate.fromString(assembly.ending_date, 'yyyy-MM-dd'))} days)"),
                0,
                0,
            )
            if assembly.all_sub_assemblies_complete() and assembly.all_items_complete():
                try:
                    assembly_flow_tag: str = assembly.get_current_flow_state()
                except IndexError:
                    return

                def toggle_timer(
                    assembly: Assembly,
                    toggle_timer_button: QPushButton,
                    recording_widget: RecordingWidget,
                ) -> None:
                    assembly_flow_tag: str = assembly.get_current_flow_state()
                    is_recording: bool = not assembly.timers[assembly_flow_tag]["recording"]
                    toggle_timer_button.setChecked(is_recording)
                    toggle_timer_button.setText("Stop" if is_recording else "Start")
                    recording_widget.setHidden(not is_recording)
                    assembly.timers[assembly_flow_tag]["recording"] = is_recording
                    if is_recording:
                        assembly.timers[assembly_flow_tag].setdefault("time_taken_intervals", [])
                        assembly.timers[assembly_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
                    else:
                        assembly.timers[assembly_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    self.user_workspace.save()
                    self.sync_changes()

                def move_to_next_flow(assembly: Assembly) -> None:
                    item_flow_tag: str = assembly.get_current_flow_state()
                    if self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                        try:
                            assembly.timers[item_flow_tag]["recording"]
                        except KeyError:
                            assembly.timers[item_flow_tag]["recording"] = False
                        if assembly.timers[item_flow_tag]["recording"]:
                            assembly.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                            assembly.timers[item_flow_tag]["recording"] = False
                    assembly.current_flow_state += 1
                    assembly.status = None
                    if assembly.current_flow_state == len(assembly.flow_tag):
                        assembly.completed = True
                        assembly.date_completed = str(datetime.now())
                        completed_assemblies: list[Assembly] = []
                        self.history_workspace.load_data()
                        for main_assembly in self.user_workspace.data:
                            # Assembly is 100% complete
                            if main_assembly.completed:
                                completed_assemblies.append(main_assembly)
                                self.history_workspace.add_assembly(main_assembly)
                                self.history_workspace.save()
                                self.parent.play_celebrate_sound()
                        for completed_assembly in completed_assemblies:
                            self.user_workspace.remove_assembly(completed_assembly)
                    self.user_workspace.save()
                    self.sync_changes()
                    self.load_workspace()

                def item_status_changed(
                    status_box: QComboBox,
                    assembly: Assembly,
                    toggle_timer_button: QPushButton,
                ) -> None:
                    if self.workspace_tags.get_value("flow_tag_statuses")[assembly.get_current_flow_state()][status_box.currentText()]["start_timer"] and self.workspace_tags.get_value("attributes")[assembly.get_current_flow_state()]["is_timer_enabled"] and assembly.timers[assembly.get_current_flow_state()]["recording"] == False:
                        toggle_timer_button.click()
                    if self.workspace_tags.get_value("flow_tag_statuses")[assembly.get_current_flow_state()][status_box.currentText()]["completed"]:
                        move_to_next_flow(assembly=assembly)
                    else:
                        assembly.status = status_box.currentText()
                    self.user_workspace.save()
                    self.sync_changes()

                timer_widget = QWidget(self)
                timer_layout = QHBoxLayout(timer_widget)
                timer_widget.setLayout(timer_layout)
                recording_widget = RecordingWidget(timer_widget)
                toggle_timer_button = QPushButton(timer_widget)
                if self.workspace_tags.get_value("attributes")[assembly_flow_tag]["is_timer_enabled"]:
                    is_recording: bool = assembly.timers[assembly_flow_tag].setdefault("recording", False)
                    toggle_timer_button.setCheckable(True)
                    toggle_timer_button.setChecked(is_recording)
                    recording_widget.setHidden(not is_recording)
                    toggle_timer_button.setObjectName("recording_button")
                    toggle_timer_button.setText("Stop" if is_recording else "Start")
                    toggle_timer_button.clicked.connect(
                        partial(
                            toggle_timer,
                            assembly,
                            toggle_timer_button,
                            recording_widget,
                        )
                    )
                    timer_layout.addWidget(toggle_timer_button)
                    timer_layout.addWidget(recording_widget)
                    grid.addWidget(QLabel("Timer:"), 1, 1)
                    grid.addWidget(timer_widget, 1, 2)

                flow_tag_controls_widget = QWidget(self)
                h_layout = QHBoxLayout(flow_tag_controls_widget)
                flow_tag_controls_widget.setLayout(h_layout)
                # h_layout.setSpacing(0)
                h_layout.setContentsMargins(0, 0, 0, 0)
                if not list(self.workspace_tags.get_value("flow_tag_statuses")[assembly_flow_tag].keys()):
                    with contextlib.suppress(IndexError):
                        button_next_flow_state = QPushButton(self)
                        button_next_flow_state.setObjectName("flow_tag_button")
                        button_flow_state_name: str = "Mark as Done!"
                        if "bend" in assembly_flow_tag.lower():
                            button_flow_state_name = "Bent"
                        if "weld" in assembly_flow_tag.lower():
                            button_flow_state_name = "Welded"
                        if "cut" in assembly_flow_tag.lower():
                            button_flow_state_name = "Laser Cut"
                        if "paint" in assembly_flow_tag.lower():
                            button_flow_state_name = "Painted"
                        if "pick" in assembly_flow_tag.lower():
                            button_flow_state_name = "Picked"
                        if "assem" in assembly_flow_tag.lower():
                            button_flow_state_name = "Assembled"
                        button_next_flow_state.setText(button_flow_state_name)
                        button_next_flow_state.clicked.connect(partial(move_to_next_flow, assembly))
                        # QTableWidgetItem(item.data["flow_tag"][item.data["current_flow_state"]])
                        h_layout.addWidget(button_next_flow_state)
                        grid.addWidget(QLabel("Flow Tag:"), 0, 1)
                        grid.addWidget(button_next_flow_state, 0, 2)
                        with contextlib.suppress(IndexError):
                            next_flow_tag = assembly.flow_tag[assembly.current_flow_state + 1]
                            grid.addWidget(
                                QLabel(
                                    self.workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"],
                                    self,
                                ),
                                0,
                                3,
                            )
                else:
                    status_box = QComboBox(self)
                    status_box.setObjectName("flow_tag_status_button")
                    status_box.addItems(list(self.workspace_tags.get_value("flow_tag_statuses")[assembly_flow_tag].keys()))
                    status_box.setCurrentText(assembly.status)
                    status_box.currentTextChanged.connect(
                        partial(
                            item_status_changed,
                            status_box,
                            assembly,
                            toggle_timer_button,
                        )
                    )
                    # table.setCellWidget(row_index, col_index, status_box)
                    grid.addWidget(QLabel("Status:"), 0, 1)
                    grid.addWidget(status_box, 0, 2)
                    with contextlib.suppress(IndexError, KeyError):
                        next_flow_tag = assembly.flow_tag[assembly.current_flow_state + 1]
                        grid.addWidget(
                            QLabel(
                                self.workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"],
                                self,
                            ),
                            0,
                            3,
                        )
                if all(keyword not in assembly_flow_tag for keyword in ["paint", "powder"]) and assembly.paint_color != None:
                    paint_color: str = "None"
                    for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                        if color_code == assembly.paint_color:
                            paint_color = color_name
                    paint_type: str = assembly.paint_type
                    paint_amount: float = assembly.paint_amount
                    grid.addWidget(
                        QLabel(f'Assembly needs to be painted "{paint_color}" using "{paint_type}", the expected amount is {paint_amount} gallons'),
                        0,
                        4,
                    )

            return grid_widget

        grid_widget = get_grid_widget()

        if assembly.has_items:
            items_layout.addWidget(table_widget)
        h_layout.addWidget(grid_widget)
        # h_layout.addWidget(timer_widget)

        # Add the "Items" group box to the main layout
        # if assembly.has_items and user_workspace.is_assembly_empty(assembly=assembly):
        #     layout.addWidget(items_groupbox)

        # Create the MultiToolBox for sub assemblies
        workspace_information.setdefault(assembly.name, {"tool_box": None, "sub_assemblies": {}})
        try:
            workspace_information[assembly.name]["tool_box"] = workspace_information[assembly.name]["tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        sub_assemblies_toolbox = MultiToolBox(widget)
        sub_assemblies_toolbox.layout().setSpacing(0)
        # if assembly.has_sub_assemblies:
        sub_assembly_groupbox = QGroupBox("Sub Assemblies")
        sub_assembly_groupbox_layout = QVBoxLayout()
        sub_assembly_groupbox.setLayout(sub_assembly_groupbox_layout)
        # Add the sub assemblies MultiToolBox to the main layout
        sub_assembly_groupbox_layout.addWidget(sub_assemblies_toolbox)
        # if len(assembly.sub_assemblies) > 0:
        if assembly.has_items:
            layout.addWidget(items_groupbox)
        # added_items_group_widget = True
        # if not added_sub_assemblies_group_widget:
        # added_sub_assemblies_group_widget = True
        for i, sub_assembly in enumerate(assembly.sub_assemblies):
            if sub_assembly.show == True and sub_assembly.completed == False:
                sub_assembly_widget = self.load_view_assembly_widget(
                    assembly=sub_assembly,
                    workspace_information=workspace_information[assembly.name]["sub_assemblies"],
                    group_color=group_color,
                )
                sub_assemblies_toolbox.addItem(sub_assembly_widget, f"{sub_assembly.name}", base_color=group_color)
                # sub_assemblies_toolbox.close(i)
        sub_assemblies_toolbox.close_all()
        if saved_workspace_prefs:
            sub_assemblies_toolbox.set_widgets_visibility(workspace_information[assembly.name]["tool_box"])
        workspace_information[assembly.name]["tool_box"] = sub_assemblies_toolbox
        if len(sub_assemblies_toolbox.widgets) > 0:
            layout.addWidget(sub_assembly_groupbox)
        return widget

    # USER
    def load_view_table_summary(self) -> None:
        selected_tab: str = self.tab_widget.tabText(self.tab_widget.currentIndex())
        if selected_tab == "Recut":
            self.workspace_filter["show_recut"] = True
            with contextlib.suppress(AttributeError):
                self.workspace_filter_tab_widget.clear_selections("Flow Tags")
        else:
            self.workspace_filter["show_recut"] = False
        scroll_area = QScrollArea()

        def save_scroll_position(tab_name: str, scroll: QScrollArea):
            self.scroll_position_manager.save_scroll_position(tab_name, scroll)

        scroll_area.verticalScrollBar().valueChanged.connect(
            partial(
                save_scroll_position,
                f"Workspace table_summary {self.category}",
                scroll_area,
            )
        )
        scroll_area.horizontalScrollBar().valueChanged.connect(
            partial(
                save_scroll_position,
                f"Workspace table_summary {self.category}",
                scroll_area,
            )
        )
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(self)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(1)
        scroll_area.setWidget(scroll_content)

        workspace_data = self.user_workspace.get_filtered_data(self.workspace_filter)
        grouped_items: WorkspaceItemGroup = self.user_workspace.get_grouped_items()
        # Need to all have same flow tag
        grouped_items.filter_items(flow_tag=self.category)

        headers: list[str] = [
            "Item Name",  # 0
            "Bending Files",  # 1
            "Welding Files",  # 2
            "CNC/Milling Files",  # 3
            "Thickness",  # 4
            "Material Type",  # 5
            "Paint Type",  # 6
            "Paint Color",  # 7
            "Quantity",  # 8
            "Flow Tag Controls",  # 9
            "Set Timers",  # 10
            "Shelf #",  # 11
            "Notes",  # 12
        ]

        table = CustomTableWidget(scroll_content)
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.hideColumn(1)
        table.hideColumn(2)
        table.hideColumn(3)
        table.hideColumn(6)
        table.hideColumn(7)
        table.hideColumn(10)

        def toggle_timer(
            item_name: str,
            toggle_timer_button: QPushButton,
            recording_widget: RecordingWidget,
        ) -> None:
            for item in grouped_items.data[item_name]:
                item_flow_tag: str = item.get_current_flow_state()
                try:
                    is_recording: bool = not item.timers[item_flow_tag]["recording"]
                except KeyError:
                    is_recording: bool = True
                toggle_timer_button.setChecked(is_recording)
                toggle_timer_button.setText("Stop" if is_recording else "Start")
                recording_widget.setHidden(not is_recording)
                item.timers[item_flow_tag]["recording"] = is_recording
                if is_recording:
                    item.timers[item_flow_tag].setdefault("time_taken_intervals", [])
                    item.timers[item_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
                else:
                    item.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))

            self.user_workspace.save()
            self.sync_changes()

        def recut(item_name: str) -> None:
            max_recut_count: int = 0
            item = grouped_items.get_item(item_name)
            for item in grouped_items.get_item_list(item_name):
                max_recut_count = item.parts_per
                if max_recut_count != 0:
                    break
            if max_recut_count == 0:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("No More Quantity")
                msg.setText("Quantity limit exceeded")
                msg.exec()
                return
            input_dialog = RecutDialog(f"Select or Input recut count for: {item.name}", max_recut_count, self)
            if input_dialog.exec():
                recut_count = int(input_dialog.input_text)
                parent_assembly = item.parent_assembly
                inventory_item = self.user_workspace.get_inventory_item(item.name)
                new_item = WorkspaceItem(
                    inventory_item,
                    data=item.to_dict(),
                )
                new_item.name = f"{item.name} - Recut #{item.recut_count + 1}"
                new_item.parts_per = recut_count
                new_item.current_flow_state = new_item.flow_tag.index("Laser Cutting")
                new_item.recut = True
                parent_assembly.add_item(new_item)
                item.recut_count = item.parts_per + 1
                item.parts_per -= recut_count
                self.user_workspace.save()
                self.sync_changes()
                self.load_workspace()

        def move_to_next_flow(item_name: str, row_index: int) -> None:
            for item in grouped_items.data[item_name]:
                item_flow_tag: str = item.get_current_flow_state()
                if self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                    try:
                        item.timers[item_flow_tag]["recording"]
                    except KeyError:
                        item.timers[item_flow_tag]["recording"] = False
                    if item.timers[item_flow_tag]["recording"]:
                        item.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                        item.timers[item_flow_tag]["recording"] = False
                if item_flow_tag == "Laser Cutting":
                    item.recut = False
                item.current_flow_state += 1
                item.status = None
                if item.current_flow_state == len(item.flow_tag):
                    item.completed = True
                    item.date_completed = str(datetime.now())
                    assembly: Assembly = item.parent_assembly
                    if assembly.current_flow_state == -1:  # NOTE Custom Job
                        completed_assemblies: list[Assembly] = []
                        self.history_workspace.load_data()
                        for main_assembly in self.user_workspace.data:
                            # Assembly is 100% complete
                            if self.user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                                main_assembly.completed = True
                                completed_assemblies.append(main_assembly)
                                self.history_workspace.add_assembly(main_assembly)
                                self.history_workspace.save()
                                self.parent.play_celebrate_sound()
                        for completed_assembly in completed_assemblies:
                            self.user_workspace.remove_assembly(completed_assembly)
            self.user_workspace.save()
            self.sync_changes()
            self.load_workspace()

        def item_status_changed(
            status_box: QComboBox,
            item_name: str,
            row_index: int,
            toggle_timer_button: QPushButton,
        ) -> None:
            for item in grouped_items.data[item_name]:
                if self.workspace_tags.get_value("flow_tag_statuses")[item.get_current_flow_state()][status_box.currentText()]["start_timer"] and self.workspace_tags.get_value("attributes")[item.get_current_flow_state()]["is_timer_enabled"] and item.timers[item.get_current_flow_state()]["recording"] == False:
                    toggle_timer_button.click()
                if self.workspace_tags.get_value("flow_tag_statuses")[item.get_current_flow_state()][status_box.currentText()]["completed"]:
                    # grouped_items.update_values(item_to_update=item_name, key="status", value=status_box.currentText())
                    move_to_next_flow(item_name=item.name, row_index=row_index)
                else:
                    item.status = status_box.currentText()
                    # grouped_items.update_values(item_to_update=item_name, key="status", value=status_box.currentText())

            self.user_workspace.save()
            self.sync_changes()

        def add_item(row_index: int, item_name: str):
            first_item: WorkspaceItem = grouped_items.get_item(item_name=item_name)
            item_flow_tag: str = first_item.get_current_flow_state()
            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            table.setItem(row_index, col_index, QTableWidgetItem(item_name))  # 0
            table.item(row_index, col_index).setToolTip(f"Items: {grouped_items.to_string(item_name)}")
            col_index += 1
            for file_column in ["Bending Files", "Welding Files", "CNC/Milling Files"]:
                button_widget = QWidget()
                files_layout = QHBoxLayout()
                files_layout.setContentsMargins(0, 0, 0, 0)
                files_layout.setSpacing(0)
                button_widget.setLayout(files_layout)
                self.load_assemblies_items_file_layout(
                    file_category=file_column,
                    files_layout=files_layout,
                    assembly=first_item.parent_assembly,
                    item=first_item,
                    show_dropped_widget=False,
                )
                table.setCellWidget(row_index, col_index, button_widget)
                col_index += 1
            if "bend" in item_flow_tag.lower():
                table.showColumn(1)
            elif "weld" in item_flow_tag.lower():
                table.showColumn(2)
            elif "cut" in item_flow_tag.lower():
                table.showColumn(3)
            if "paint" in item_flow_tag.lower():
                table.showColumn(6)
                table.showColumn(7)

            table.setItem(row_index, col_index, QTableWidgetItem(first_item.thickness))  # 4
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(first_item.material))  # 5
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(
                row_index,
                col_index,
                QTableWidgetItem(str(first_item.paint_type)),
            )  # 6
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            button_color = QComboBox(self)
            button_color.setEnabled(False)
            if first_item.paint_color != None:
                for color_name, color_code in self.workspace_tags.get_value("paint_colors").items():
                    if color_code == first_item.paint_color:
                        button_color.addItem(color_name)
                        button_color.setCurrentText(color_name)
                        button_color.setStyleSheet(f'QComboBox{{border-radius: 0px; background-color: {first_item.paint_color}}} {"QMenu { background-color: rgb(22,22,22);}"}')
                        break
            table.setCellWidget(row_index, col_index, button_color)  # 7
            col_index += 1
            table.setItem(
                row_index,
                col_index,
                QTableWidgetItem(str(grouped_items.get_total_quantity(item_name))),
            )  # 8
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1

            # timer_box = QComboBox(self)
            # timer_box.addItems(["Set Timer For"] + item.data["flow_tag"])
            # timer_box.setCurrentIndex(0)
            # timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))
            # timer_widget = QWidget()
            # timer_layout = QHBoxLayout(timer_widget)
            # timer_layout.setContentsMargins(0, 0, 0, 0)
            # timer_widget.setLayout(timer_layout)

            # current_tag = QComboBox(self)
            # current_tag.wheelEvent = lambda event: event.ignore()
            # current_tag.setObjectName("tag_box")
            # current_tag.setStyleSheet("QComboBox#tag_box{margin: 2px;}")
            flow_tag_controls_widget = QWidget(self)
            h_layout = QHBoxLayout(flow_tag_controls_widget)
            flow_tag_controls_widget.setLayout(h_layout)
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 0)

            timer_widget = QWidget(self)
            timer_layout = QHBoxLayout(timer_widget)
            timer_widget.setLayout(timer_layout)
            recording_widget = RecordingWidget(timer_widget)
            toggle_timer_button = QPushButton(timer_widget)

            if self.category != "Recut":
                if not list(self.workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()):
                    try:
                        button_next_flow_state = QPushButton(self)
                        button_next_flow_state.setFixedHeight(50)
                        button_next_flow_state.setObjectName("flow_tag_button")
                        button_flow_state_name: str = "Mark as Done!"
                        if "bend" in item_flow_tag.lower():
                            button_flow_state_name = "Bent"
                        if "weld" in item_flow_tag.lower():
                            button_flow_state_name = "Welded"
                        if "cut" in item_flow_tag.lower():
                            button_flow_state_name = "Laser Cut"
                        if "paint" in item_flow_tag.lower():
                            button_flow_state_name = "Painted"
                        if "pick" in item_flow_tag.lower():
                            button_flow_state_name = "Picked"
                        if "assem" in item_flow_tag.lower():
                            button_flow_state_name = "Assembled"
                        button_next_flow_state.setText(button_flow_state_name)
                        button_next_flow_state.clicked.connect(partial(move_to_next_flow, item_name, row_index))
                        button_next_flow_state.setStyleSheet("border-radius: 0px;")
                        h_layout.addWidget(button_next_flow_state)
                    except IndexError:
                        table.setItem(row_index, col_index, QTableWidgetItem("Null"))
                        table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                else:
                    status_box = QComboBox(self)
                    status_box.setFixedHeight(50)
                    status_box.setObjectName("flow_tag_status_button")
                    status_box.addItems(list(self.workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()))
                    status_box.setCurrentText(first_item.status)
                    status_box.setStyleSheet("border-radius: 0px;")
                    status_box.currentTextChanged.connect(
                        partial(
                            item_status_changed,
                            status_box,
                            item_name,
                            row_index,
                            toggle_timer_button,
                        )
                    )
                    # table.setCellWidget(row_index, col_index, status_box)
                    h_layout.addWidget(status_box)
            else:
                button_next_flow_state = QPushButton(self)
                button_next_flow_state.setObjectName("flow_tag_button")
                button_next_flow_state.setText("Laser Cut")
                button_next_flow_state.clicked.connect(partial(move_to_next_flow, item_name, row_index))
                button_next_flow_state.setStyleSheet("border-radius: 0px;")
                h_layout.addWidget(button_next_flow_state)
            if all(tag not in item_flow_tag.lower() for tag in ["laser", "quote", "ship"]):  # tags where Recut should not be shown
                recut_button = QPushButton(self)
                recut_button.setText("Recut")
                recut_button.setObjectName("recut_button")
                recut_button.clicked.connect(partial(recut, item_name))
                h_layout.addWidget(recut_button)
            with contextlib.suppress(IndexError, KeyError):
                next_flow_tag = first_item.flow_tag[first_item.current_flow_state + 1]
                h_layout.addWidget(
                    QLabel(
                        self.workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"],
                        self,
                    )
                )
            table.setCellWidget(row_index, col_index, flow_tag_controls_widget)
            col_index += 1

            if self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                is_recording: bool = first_item.timers[item_flow_tag].setdefault("recording", False)
                toggle_timer_button.setCheckable(True)
                toggle_timer_button.setChecked(is_recording)
                recording_widget.setHidden(not is_recording)
                toggle_timer_button.setObjectName("recording_button")
                toggle_timer_button.setText("Stop" if is_recording else "Start")
                toggle_timer_button.clicked.connect(partial(toggle_timer, item_name, toggle_timer_button, recording_widget))
                timer_layout.addWidget(toggle_timer_button)
                timer_layout.addWidget(recording_widget)
                table.setCellWidget(row_index, col_index, timer_widget)
                table.showColumn(10)

            col_index += 1
            table.setItem(
                row_index,
                col_index,
                QTableWidgetItem(str(first_item.shelf_number)),
            )  # 11
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(first_item.notes)))  # 12
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        row_index: int = 0
        for item_name, items in grouped_items.data.items():
            if len(items) == 0:
                continue
            # if item.get_value("show") == False or item.get_value("completed") == True:
            add_item(row_index, item_name)
            row_index += 1
        # Creating Context Menu
        table.blockSignals(False)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu = QMenu(self)
        if self.category != "Recut" and len(self.workspace_tags.get_value("flow_tag_statuses")[self.category]) > 0:
            set_status_menu = QMenu("Set Status", self)
            for status in self.workspace_tags.get_value("flow_tag_statuses")[self.category]:
                status_action = QAction(status, self)
                status_action.triggered.connect(
                    partial(
                        self.change_selected_table_items_status,
                        table,
                        grouped_items,
                        status,
                    )
                )
                set_status_menu.addAction(status_action)
            menu.addMenu(set_status_menu)
        done_action = QAction("Mark all as Done", self)
        done_action.triggered.connect(partial(self.move_selected_table_items_to_next_flow_state, table, grouped_items))
        menu.addAction(done_action)
        download_action = QAction("Download all files", self)
        download_action.triggered.connect(partial(self.download_all_selected_items_files, table, grouped_items))
        menu.addAction(download_action)
        table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        scroll_layout.addWidget(table)
        table.resizeColumnsToContents()

        if row_index == 0:
            self.tab_widget.currentWidget().layout().addWidget(QLabel("No Items to Show", self))
        else:
            self.tab_widget.currentWidget().layout().addWidget(scroll_area)
        self.scroll_position_manager.get_scroll_position(f"Workspace table_summary {self.category}")

    # USER
    def load_view_assembly_tab(self) -> None:
        selected_tab: str = self.tab_widget.tabText(self.tab_widget.currentIndex())
        self.workspace_filter["show_recut"] = selected_tab == "Recut"
        self.workspace_information.setdefault(selected_tab, {"group_tool_box": None})
        try:
            self.workspace_information[selected_tab]["group_tool_box"] = self.workspace_information[selected_tab]["group_tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        with contextlib.suppress(AttributeError):
            self.workspace_filter_tab_widget.clear_selections("Flow Tags")
            self.workspace_filter_tab_widget.enable_button(selected_tab)
        if self.pushButton_show_sub_assembly.isChecked():
            scroll_area = QScrollArea()

            def save_scroll_position(tab_name: str, scroll: QScrollArea):
                self.scroll_position_manager.save_scroll_position(tab_name, scroll)

            scroll_area.verticalScrollBar().valueChanged.connect(
                partial(
                    save_scroll_position,
                    f"Workspace {self.category}",
                    scroll_area,
                )
            )
            scroll_area.horizontalScrollBar().valueChanged.connect(
                partial(
                    save_scroll_position,
                    f"Workspace {self.category}",
                    scroll_area,
                )
            )
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget(self)
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            scroll_layout.setSpacing(1)
            scroll_area.setWidget(scroll_content)
            filtered_data = self.user_workspace.get_filtered_data(self.workspace_filter)
            group_tool_boxes: dict[str, QWidget] = {}
            group_tool_box = MultiToolBox(scroll_content)
            for group in self.user_workspace.get_all_groups():
                group_widget = QWidget()
                group_layout = QVBoxLayout(group_widget)
                group_widget.setLayout(group_layout)
                group_tool_box.addItem(
                    group_widget,
                    group,
                    base_color=self.user_workspace.get_group_color(group),
                )
                group_tool_boxes[group] = group_widget
                self.workspace_information[selected_tab].setdefault(
                    group,
                    {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None},
                )
            group_tool_box.close_all()
            if saved_workspace_prefs:
                group_tool_box.set_widgets_visibility(self.workspace_information[selected_tab]["group_tool_box"])
            self.workspace_information[selected_tab]["group_tool_box"] = group_tool_box
            if len(group_tool_box.buttons) == 0:
                scroll_layout.addWidget(QLabel("Nothing to show.", self))
            else:
                scroll_layout.addWidget(group_tool_box)
            grouped_data = self.user_workspace.get_grouped_data()
            for group in grouped_data:
                try:
                    self.workspace_information[selected_tab][group]["tool_box"] = self.workspace_information[selected_tab][group]["tool_box"].get_widget_visibility()
                    saved_workspace_prefs = True
                except (AttributeError, RuntimeError):
                    saved_workspace_prefs = False
                multi_tool_box = MultiToolBox()
                multi_tool_box.layout().setSpacing(0)
                for assembly in grouped_data[group]:
                    if assembly.show == True and assembly.completed == False:
                        assembly_widget = self.load_view_assembly_widget(
                            assembly=assembly,
                            workspace_information=self.workspace_information[selected_tab][group]["sub_assemblies"],
                            group_color=self.user_workspace.get_group_color(group),
                        )
                        multi_tool_box.addItem(
                            assembly_widget,
                            f"{assembly.display_name} - Items: {self.user_workspace.get_completion_percentage(assembly)[0]*100}% - Assemblies: {self.user_workspace.get_completion_percentage(assembly)[1]*100}%",
                            base_color=self.user_workspace.get_group_color(group),
                        )
                group_tool_boxes[group].layout().addWidget(multi_tool_box)
                multi_tool_box.close_all()
                if saved_workspace_prefs:
                    multi_tool_box.set_widgets_visibility(self.workspace_information[selected_tab][group]["tool_box"])
                # else:

                self.workspace_information[selected_tab][group]["tool_box"] = multi_tool_box
            self.tab_widget.currentWidget().layout().addWidget(scroll_area)
            self.scroll_position_manager.get_scroll_position(f"Workspace {self.category}")
        elif self.pushButton_show_item_summary.isChecked():
            self.load_view_table_summary()
        self.load_view_assembly_context_menus()

    # PLANNING
    def load_planning_assembly_items_table(self, assembly: Assembly) -> CustomTableWidget:
        self.workspace_tags.load_data()
        headers: list[str] = ["Name", "Set Date", "Current Timeline"]  # 0  # 1  # 2

        table = CustomTableWidget(self)
        # table.hideColumn()
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        item_group = WorkspaceItemGroup()

        for item in assembly.items:
            item_group.add_item_to_group(
                group_name=f"{item.material} {item.thickness}",
                item=item,
            )

        def get_date_edit_widget(row_index: int, group_name: str) -> QWidget:
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(h_layout)

            def set_time_line():
                timeline_dialog = SelectTimeLineDialog(
                    f"Set timeline for all items in {group}",
                    item_group.get_item(group).starting_date,
                    item_group.get_item(group).ending_date,
                    self,
                )
                if timeline_dialog.exec():
                    timeline = timeline_dialog.get_timeline()
                    start_time: QDate = timeline[0]
                    end_time: QDate = timeline[1]

                    string_start_time = start_time.toString("yyyy-MM-dd")
                    string_end_time = end_time.toString("yyyy-MM-dd")

                    for item in item_group.get_item_list(group_name):
                        item.starting_date = string_start_time
                        item.ending_date = string_end_time
                    self.user_workspace.save()
                    self.parent.upload_file(
                        [
                            "user_workspace.json",
                        ],
                    )

                    table.setItem(
                        row_index,
                        2,
                        QTableWidgetItem(f"{string_start_time} to {string_end_time}, ({start_time.daysTo(end_time)} days)"),
                    )  # 0

            set_date = QPushButton("Set Timeline")
            set_date.setFixedHeight(50)
            set_date.setStyleSheet("border-radius: none;")
            set_date.clicked.connect(set_time_line)

            h_layout.addWidget(set_date)

            return widget

        def add_item(row_index: int, group: str):
            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            items_count = len(item_group.get_item_list(group))
            table.setItem(
                row_index,
                col_index,
                QTableWidgetItem(f'{group} - ({items_count} item{"s" if items_count > 1 else ""})'),
            )  # 0
            items_tool_tip: str = ""
            for i, item in enumerate(item_group.get_item_list(group), start=1):
                items_tool_tip += f"{i}. {item.name}\n"
            table.item(row_index, col_index).setToolTip(items_tool_tip)
            col_index += 1
            table.setCellWidget(row_index, col_index, get_date_edit_widget(row_index, group))  # 4
            col_index += 1
            table.setItem(
                row_index,
                col_index,
                QTableWidgetItem(f'{item_group.get_item(group).starting_date} to {item_group.get_item(group).ending_date}, ({QDate.fromString(item_group.get_item(group).starting_date, "yyyy-MM-dd").daysTo(QDate.fromString(item_group.get_item(group).ending_date, "yyyy-MM-dd"))} days)'),
            )  # 0
            table.resizeColumnsToContents()

        row_index: int = 0
        for group in item_group.data:
            add_item(row_index, group)
            row_index += 1
        if row_index == 0:
            return QLabel("No Items to Show", self)

        table.blockSignals(False)
        table.resizeColumnsToContents()
        self.workspace_tables[table] = assembly
        # header = table.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Set the first column to Fixed

        return table

    # PLANNING
    def load_planning_assembly_widget(
        self,
        assembly: Assembly,
        workspace_information: dict,
        group_color: str,
        parent=None,
    ) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(h_layout)
        # widget.setLayout(h_layout)
        timer_widget = QWidget()
        timer_layout = QHBoxLayout(timer_widget)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_widget.setLayout(timer_layout)
        # Create the "Items" group box
        items_groupbox = QGroupBox("Items")
        # items_groupbox.setMinimumHeight(500)
        items_layout = QVBoxLayout()
        items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        items_groupbox.setLayout(items_layout)

        # Create and configure the table widget
        if assembly.has_items:
            table_widget = self.load_planning_assembly_items_table(assembly)
            table_widget.setFixedHeight(40 * (len(assembly.items) + 2))
            # if isinstance(table_widget, QLabel): # Its empty
            #     return QLabel("Empty", self)

        def get_grid_widget() -> QWidget:
            # Add the table widget to the "Items" group box
            grid_widget = QWidget(widget)
            grid = QGridLayout(grid_widget)
            grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
            timeline_label = QLabel(f"{assembly.starting_date} to {assembly.ending_date}, ({QDate.fromString(assembly.starting_date, 'yyyy-MM-dd').daysTo(QDate.fromString(assembly.ending_date, 'yyyy-MM-dd'))} days)")

            def set_time_line():
                timeline_dialog = SelectTimeLineDialog(
                    f"Set timeline for sub assembly: {assembly.name}",
                    assembly.starting_date,
                    assembly.ending_date,
                    self,
                )
                if timeline_dialog.exec():
                    timeline = timeline_dialog.get_timeline()
                    start_time: QDate = timeline[0]
                    end_time: QDate = timeline[1]

                    string_start_time = start_time.toString("yyyy-MM-dd")
                    string_end_time = end_time.toString("yyyy-MM-dd")

                    assembly.starting_date = string_start_time
                    assembly.ending_date = string_end_time

                    self.user_workspace.save()
                    self.parent.upload_file(
                        [
                            "user_workspace.json",
                        ],
                    )

                    timeline_label.setText(f"{string_start_time} to {string_end_time}, ({start_time.daysTo(end_time)} days)")

            set_date = QPushButton("Set Timeline")
            set_date.clicked.connect(set_time_line)
            grid.addWidget(set_date, 0, 1)
            grid.addWidget(timeline_label, 0, 2)

            return grid_widget

        grid_widget = get_grid_widget()

        if assembly.has_items:
            items_layout.addWidget(table_widget)
        h_layout.addWidget(grid_widget)
        # Create the MultiToolBox for sub assemblies
        workspace_information.setdefault(assembly.name, {"tool_box": None, "sub_assemblies": {}})
        try:
            workspace_information[assembly.name]["tool_box"] = workspace_information[assembly.name]["tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        sub_assemblies_toolbox = MultiToolBox(widget)
        sub_assemblies_toolbox.layout().setSpacing(0)
        # if assembly.has_sub_assemblies:
        sub_assembly_groupbox = QGroupBox("Sub Assemblies")
        sub_assembly_groupbox_layout = QVBoxLayout()
        sub_assembly_groupbox.setLayout(sub_assembly_groupbox_layout)
        # Add the sub assemblies MultiToolBox to the main layout
        sub_assembly_groupbox_layout.addWidget(sub_assemblies_toolbox)
        # if len(assembly.sub_assemblies) > 0:
        if assembly.has_items:
            layout.addWidget(items_groupbox)
        # added_items_group_widget = True
        # if not added_sub_assemblies_group_widget:
        # added_sub_assemblies_group_widget = True
        for i, sub_assembly in enumerate(assembly.sub_assemblies):
            if sub_assembly.show == True and sub_assembly.completed == False:
                sub_assembly_widget = self.load_planning_assembly_widget(
                    assembly=sub_assembly,
                    workspace_information=workspace_information[assembly.name]["sub_assemblies"],
                    group_color=group_color,
                )
                sub_assemblies_toolbox.addItem(sub_assembly_widget, f"{sub_assembly.name}", base_color=group_color)
                # sub_assemblies_toolbox.close(i)
        sub_assemblies_toolbox.close_all()
        if saved_workspace_prefs:
            sub_assemblies_toolbox.set_widgets_visibility(workspace_information[assembly.name]["tool_box"])
        workspace_information[assembly.name]["tool_box"] = sub_assemblies_toolbox
        if len(sub_assemblies_toolbox.widgets) > 0:
            layout.addWidget(sub_assembly_groupbox)
        return widget

    # PLANNING
    def load_planning_assembly_tab(self) -> None:
        self.workspace_information.setdefault("Planning", {"group_tool_box": None})
        try:
            self.workspace_information["Planning"]["group_tool_box"] = self.workspace_information["Planning"]["group_tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        with contextlib.suppress(AttributeError):
            self.workspace_filter_tab_widget.clear_selections("Flow Tags")
        scroll_area = QScrollArea()

        def save_scroll_position(tab_name: str, scroll: QScrollArea):
            self.scroll_position_manager.save_scroll_position(tab_name, scroll)

        scroll_area.verticalScrollBar().valueChanged.connect(
            partial(
                save_scroll_position,
                f"Workspace Planning",
                scroll_area,
            )
        )
        scroll_area.horizontalScrollBar().valueChanged.connect(
            partial(
                save_scroll_position,
                f"Workspace Planning",
                scroll_area,
            )
        )
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(self)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(1)
        scroll_area.setWidget(scroll_content)
        filtered_data = self.user_workspace.get_filtered_data(self.workspace_filter)
        group_tool_boxes: dict[str, QWidget] = {}
        group_tool_box = MultiToolBox(scroll_content)
        for group in self.user_workspace.get_all_groups():
            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_widget.setLayout(group_layout)
            group_tool_box.addItem(group_widget, group, base_color=self.user_workspace.get_group_color(group))
            group_tool_boxes[group] = group_widget
            self.workspace_information["Planning"].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})
        group_tool_box.close_all()
        if saved_workspace_prefs:
            group_tool_box.set_widgets_visibility(self.workspace_information["Planning"]["group_tool_box"])
        self.workspace_information["Planning"]["group_tool_box"] = group_tool_box
        if len(group_tool_box.buttons) == 0:
            scroll_layout.addWidget(QLabel("Nothing to show.", self))
        else:
            scroll_layout.addWidget(group_tool_box)
        grouped_data = self.user_workspace.get_grouped_data()
        for group in grouped_data:
            try:
                self.workspace_information["Planning"][group]["tool_box"] = self.workspace_information["Planning"][group]["tool_box"].get_widget_visibility()
                saved_workspace_prefs = True
            except (AttributeError, RuntimeError):
                saved_workspace_prefs = False
            multi_tool_box = MultiToolBox()
            multi_tool_box.layout().setSpacing(0)
            for assembly in grouped_data[group]:
                if assembly.show == True and assembly.completed == False:
                    assembly_widget = self.load_planning_assembly_widget(
                        assembly=assembly,
                        workspace_information=self.workspace_information["Planning"][group]["sub_assemblies"],
                        group_color=self.user_workspace.get_group_color(group),
                    )
                    multi_tool_box.addItem(
                        assembly_widget,
                        f"{assembly.display_name} - Items: {self.user_workspace.get_completion_percentage(assembly)[0]*100}% - Assemblies: {self.user_workspace.get_completion_percentage(assembly)[1]*100}%",
                        base_color=self.user_workspace.get_group_color(group),
                    )
            group_tool_boxes[group].layout().addWidget(multi_tool_box)
            multi_tool_box.close_all()
            if saved_workspace_prefs:
                multi_tool_box.set_widgets_visibility(self.workspace_information["Planning"][group]["tool_box"])
            # else:

            self.workspace_information["Planning"][group]["tool_box"] = multi_tool_box
        self.tab_widget.currentWidget().layout().addWidget(scroll_area)
        self.scroll_position_manager.get_scroll_position("Workspace Planning")

    # * \/ CONTEXT MENU \/
    # USER
    def move_selected_table_items_to_next_flow_state(self, table: CustomTableWidget, assembly: Assembly | WorkspaceItemGroup) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_workspace_parts(table)
        if isinstance(assembly, Assembly):
            items_to_update: list[WorkspaceItem] = [item for item in assembly.items if item.name in selected_items_from_table]
        elif isinstance(assembly, WorkspaceItemGroup):
            items_to_update = []
            for item in selected_items_from_table:
                items_to_update.extend(assembly.get_item_list(item))

        def move_to_next_flow(item: WorkspaceItem) -> None:
            item_flow_tag: str = item.get_current_flow_state()
            if self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                try:
                    item.timers[item_flow_tag]["recording"]
                except KeyError:
                    item.timers[item_flow_tag]["recording"] = False
                if item.timers[item_flow_tag]["recording"]:
                    item.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    item.timers[item_flow_tag]["recording"] = False
            if item_flow_tag == "Laser Cutting":
                item.recut = False
            item.current_flow_state += 1
            item.status = None
            if item.current_flow_state == len(item.flow_tag):
                item.completed = True
                item.data_completed = str(datetime.now())
                assembly: Assembly = item.parent_assembly
                if assembly.current_flow_state == -1:  # NOTE Custom Job
                    completed_assemblies: list[Assembly] = []
                    self.history_workspace.load_data()
                    for main_assembly in self.user_workspace.data:
                        # Assembly is 100% complete
                        if self.user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                            main_assembly.completed = True
                            completed_assemblies.append(main_assembly)
                            self.history_workspace.add_assembly(main_assembly)
                            self.history_workspace.save()
                            self.parent.play_celebrate_sound()
                    for completed_assembly in completed_assemblies:
                        self.user_workspace.remove_assembly(completed_assembly)

        for item in items_to_update:
            move_to_next_flow(item)
        self.user_workspace.save()
        self.sync_changes()
        self.load_workspace()

    # USER
    def change_selected_table_items_status(
        self,
        table: CustomTableWidget,
        assembly: Assembly | WorkspaceItemGroup,
        status: str,
    ) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_workspace_parts(table)
        if isinstance(assembly, Assembly):
            items_to_update: list[WorkspaceItem] = [item for item in assembly.items if item.name in selected_items_from_table]
        elif isinstance(assembly, WorkspaceItemGroup):
            items_to_update = []
            for item in selected_items_from_table:
                items_to_update.extend(assembly.get_item_list(item))

        def move_to_next_flow(item: WorkspaceItem) -> None:
            item_flow_tag: str = item.get_current_flow_state()
            if self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                try:
                    item.timers[item_flow_tag]["recording"]
                except KeyError:
                    item.timers[item_flow_tag]["recording"] = False
                if item.timers[item_flow_tag]["recording"]:
                    item.timers[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    item.timers[item_flow_tag]["recording"] = False
            if item_flow_tag == "Laser Cutting":
                item.recut = False
            item.current_flow_state += 1
            item.status = None
            if item.current_flow_state == len(item.flow_tag):
                item.completed = True
                item.date_completed = str(datetime.now())
                assembly: Assembly = item.parent_assembly
                if assembly.current_flow_state == -1:  # NOTE Custom Job
                    completed_assemblies: list[Assembly] = []
                    self.history_workspace.load_data()
                    for main_assembly in self.user_workspace.data:
                        # Assembly is 100% complete
                        if self.user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                            main_assembly.completed = True
                            completed_assemblies.append(main_assembly)
                            self.history_workspace.add_assembly(main_assembly)
                            self.history_workspace.save()
                            self.parent.play_celebrate_sound()
                    for completed_assembly in completed_assemblies:
                        self.user_workspace.remove_assembly(completed_assembly)

        for item in items_to_update:
            item_flow_tag: str = item.get_current_flow_state()
            if self.workspace_tags.get_value("flow_tag_statuses")[item_flow_tag][status]["start_timer"] and self.workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"] and item.timers[item_flow_tag]["recording"] == False:
                item.timers[item_flow_tag]["recording"] = True
                item.timers[item_flow_tag].setdefault("time_taken_intervals", [])
                item.timers[item_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
            if self.workspace_tags.get_value("flow_tag_statuses")[item_flow_tag][status]["completed"]:
                move_to_next_flow(item=item)
            else:
                item.status = status

        self.user_workspace.save()
        self.sync_changes()
        self.load_workspace()

    # USER
    def download_all_selected_items_files(self, table: CustomTableWidget, assembly: Assembly | WorkspaceItemGroup) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_workspace_parts(table)
        if isinstance(assembly, Assembly):
            items_to_update: list[WorkspaceItem] = [item for item in assembly.items if item.name in selected_items_from_table]
        elif isinstance(assembly, WorkspaceItemGroup):
            items_to_update = []
            for item in selected_items_from_table:
                items_to_update.extend(assembly.get_item_list(item))

        print("in progress")

    # USER
    def load_view_assembly_context_menus(self) -> None:
        for table, main_assembly in self.workspace_tables.items():
            # set context menu
            with contextlib.suppress(RuntimeError):
                if table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
                    table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                    menu = QMenu(self)
                    set_status_menu = QMenu("Set Status", self)
                    if len(self.workspace_tags.get_value("flow_tag_statuses")[self.category]) > 0:
                        for status in self.workspace_tags.get_value("flow_tag_statuses")[self.category]:
                            status_action = QAction(status, self)
                            status_action.triggered.connect(
                                partial(
                                    self.change_selected_table_items_status,
                                    table,
                                    main_assembly,
                                    status,
                                )
                            )
                            set_status_menu.addAction(status_action)
                        menu.addMenu(set_status_menu)
                    done_action = QAction("Mark all as Done", self)
                    done_action.triggered.connect(
                        partial(
                            self.move_selected_table_items_to_next_flow_state,
                            table,
                            main_assembly,
                        )
                    )
                    menu.addAction(done_action)
                    download_action = QAction("Download all files", self)
                    download_action.triggered.connect(partial(self.download_all_selected_items_files, table, main_assembly))
                    menu.addAction(download_action)
                    table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    # STAGING/EDITING
    def copy_items_to(
        self,
        table: CustomTableWidget,
        assembly_copy_from: Assembly,
        assembly_copy_to: Assembly,
    ) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_workspace_parts(table)
        items_to_copy: list[WorkspaceItem] = [item for item in assembly_copy_from.items if item.name in selected_items_from_table]

        for item_to_copy in items_to_copy:
            if item_to_copy.name in [other_item.name for other_item in assembly_copy_to.items]:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Duplicates")
                msg.setText(f"There are duplicate items in '{assembly_copy_to.name}'")
                msg.exec()
                return

        for item_to_copy in items_to_copy:
            assembly_copy_to.add_item(item_to_copy)

        self.active_workspace_file.save()
        self.sync_changes()
        self.load_workspace()

    # STAGING/EDITING
    def move_items_to(
        self,
        table: CustomTableWidget,
        assembly_copy_from: Assembly,
        assembly_copy_to: Assembly,
    ) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_workspace_parts(table)
        items_to_move: list[WorkspaceItem] = [item for item in assembly_copy_from.items if item.name in selected_items_from_table]

        for item_to_move in items_to_move:
            if item_to_move.name in [other_item.name for other_item in assembly_copy_to.items]:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Duplicates")
                msg.setText(f"There are duplicate items in '{assembly_copy_to.name}'")
                msg.exec()
                return

        for item_to_move in items_to_move:
            assembly_copy_to.add_item(item_to_move)
            assembly_copy_from.remove_item(item_to_move)

        self.active_workspace_file.save()
        self.sync_changes()
        self.load_workspace()

    # STAGING/EDITING
    def delete_selected_items_from_workspace(self, table: CustomTableWidget, assembly: Assembly) -> None:
        selected_indexes = table.selectedIndexes()
        selected_rows = list({selected_index.row() for selected_index in selected_indexes})
        delete_buttons: list[DeletePushButton] = [table.cellWidget(selected_row, table.columnCount() - 1) for selected_row in selected_rows if selected_row != table.rowCount() - 1]

        for delete_button in delete_buttons:
            delete_button.click()

    # STAGING/EDITING
    def generate_workorder_with_selected_items(self, table: CustomTableWidget, assembly: Assembly) -> None:
        selected_indexes = table.selectedIndexes()
        selected_rows = list({selected_index.row() for selected_index in selected_indexes})
        selected_items: list[WorkspaceItem] = []
        for item in assembly.items:
            for row in selected_rows:
                if item.name == table.item(row, 0).text():
                    selected_items.append(item)
                    continue
        self.user_workspace.load_data()
        group_color = get_random_color() if self.user_workspace.get_group_color("Custom Jobs") is None else self.user_workspace.get_group_color("Custom Jobs")
        date_created: str = QDate().currentDate().toString("yyyy-MM-dd")
        custom_assembly = Assembly(
            name=f"Custom Job ({len(selected_items)} items) - {datetime.now()}",
            assembly_data={
                "group": "Custom Jobs",
                "group_color": group_color,
                "display_name": f"Custom Job ({len(selected_items)} items)",
                "starting_date": date_created,
                "ending_date": date_created,
                "current_flow_state": -1,
            },
        )
        for item in selected_items:
            custom_assembly.add_item(item)
        custom_assembly.set_default_value_to_all_items(key="starting_date", value=date_created)
        custom_assembly.set_default_value_to_all_items(key="ending_date", value=date_created)
        custom_assembly.set_default_value_to_all_items(key="current_flow_state", value=0)
        custom_assembly.set_default_value_to_all_items(key="recoat", value=False)
        custom_assembly.set_default_value_to_all_items(key="status", value=None)
        custom_assembly.set_default_value_to_all_items(key="recut", value=False)
        custom_assembly.set_default_value_to_all_items(key="recut_count", value=0)
        custom_assembly.set_default_value_to_all_items(key="completed", value=False)
        self.user_workspace.add_assembly(custom_assembly)
        self.user_workspace.save()
        # NOTE This is because sync handels file uploads differently
        self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
        self.parent.upload_file(
            [
                "user_workspace.json",
            ],
        )

    # STAGING/EDITING
    def set_tables_selected_items_value(self, table: CustomTableWidget, assembly: Assembly, key: str, value: Any) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_workspace_parts(table)
        items_to_change: list[WorkspaceItem] = [item for item in assembly.items if item.name in selected_items_from_table]

        if key == "paint_color":
            value = self.workspace_tags.get_value("paint_colors")[value]
        elif key == "flow_tag":
            value: list[str] = value.split(" ➜ ")

        for item in items_to_change:
            if key == "material":
                item.material = value
            elif key == "thickness":
                item.thickness = value
            elif key == "flow_tag":
                item.flow_tag = value
            elif key == "paint_type":
                item.paint_type = value
            elif key == "paint_color":
                item.paint_color = value
        if self.category == "Staging" or self.category == "Editing":
            self.active_workspace_file.save()
        else:
            self.user_workspace.save()
        self.sync_changes()
        self.load_workspace()

    # STAGING/EDITING
    def load_edit_assembly_context_menus(self) -> None:
        for table, main_assembly in self.workspace_tables.items():
            # set context menu
            with contextlib.suppress(RuntimeError):
                if table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
                    table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                    menu = QMenu(self)
                    generate_workrder = QAction("Generate Workorder with Selected Items", self)
                    generate_workrder.triggered.connect(
                        partial(
                            self.generate_workorder_with_selected_items,
                            table,
                            main_assembly,
                        )
                    )
                    menu.addSeparator()
                    menu.addAction(generate_workrder)
                    copy_to_menu = QMenu(self)
                    copy_to_menu.setTitle("Copy items to")
                    move_to_menu = QMenu(self)
                    move_to_menu.setTitle("Move items to")

                    def get_all_assemblies_menu(menu: QMenu, action: str, assembly: Assembly = None) -> QMenu:
                        if assembly is None:
                            for assembly in self.active_workspace_file.data:
                                assembly_action = QAction(assembly.name, self)
                                if main_assembly == assembly:
                                    assembly_action.setText(f"{assembly_action.text()} - (You are Here)")
                                elif not assembly.has_items:
                                    assembly_action.setText(f"{assembly_action.text()} - (No Items)")
                                if not assembly.has_items or main_assembly == assembly:
                                    assembly_action.setEnabled(False)
                                # assembly_action.toggled.connect(self.copy_selected_items_to(table, assembly))
                                if action == "copy":
                                    assembly_action.triggered.connect(
                                        partial(
                                            self.copy_items_to,
                                            table,
                                            main_assembly,
                                            assembly,
                                        )
                                    )
                                elif action == "move":
                                    assembly_action.triggered.connect(
                                        partial(
                                            self.move_items_to,
                                            table,
                                            main_assembly,
                                            assembly,
                                        )
                                    )
                                menu.addAction(assembly_action)

                                if assembly.sub_assemblies:
                                    assembly_menu = menu.addMenu("Sub Assemblies")
                                    assembly_menu.addSeparator()
                                    create_sub_assemblies_submenu(assembly_menu, action, assembly.sub_assemblies)

                        return menu

                    def create_sub_assemblies_submenu(parent_menu: QMenu, action: str, sub_assemblies: list[Assembly]) -> None:
                        for sub_assembly in sub_assemblies:
                            assembly_action = QAction(sub_assembly.name, self)
                            if main_assembly == sub_assembly:
                                assembly_action.setText(f"{assembly_action.text()} - (You are Here)")
                            elif not sub_assembly.has_items:
                                assembly_action.setText(f"{assembly_action.text()} - (No Items)")
                            if not sub_assembly.has_items or main_assembly == sub_assembly:
                                assembly_action.setEnabled(False)
                            if action == "copy":
                                assembly_action.triggered.connect(
                                    partial(
                                        self.copy_items_to,
                                        table,
                                        main_assembly,
                                        sub_assembly,
                                    )
                                )
                            elif action == "move":
                                assembly_action.triggered.connect(
                                    partial(
                                        self.move_items_to,
                                        table,
                                        main_assembly,
                                        sub_assembly,
                                    )
                                )
                            parent_menu.addAction(assembly_action)
                            if sub_assembly.sub_assemblies:
                                sub_assembly_menu = parent_menu.addMenu("Sub Assemblies")
                                parent_menu.addSeparator()
                                create_sub_assemblies_submenu(
                                    sub_assembly_menu,
                                    action,
                                    sub_assembly.sub_assemblies,
                                )

                    menu.addMenu(get_all_assemblies_menu(menu=copy_to_menu, action="copy"))
                    menu.addMenu(get_all_assemblies_menu(menu=move_to_menu, action="move"))
                    menu.addSeparator()

                    materials_menu = QMenu(self)
                    materials_menu.setTitle("Set Materials")
                    for material in self.sheet_settings.get_materials():
                        material_action = QAction(material, self)
                        material_action.triggered.connect(
                            partial(
                                self.set_tables_selected_items_value,
                                table,
                                main_assembly,
                                "material",
                                material,
                            )
                        )
                        materials_menu.addAction(material_action)
                    menu.addMenu(materials_menu)

                    thickness_menu = QMenu(self)
                    thickness_menu.setTitle("Set Thicknesses")
                    for thickness in self.sheet_settings.get_thicknesses():
                        thickness_action = QAction(thickness, self)
                        thickness_action.triggered.connect(
                            partial(
                                self.set_tables_selected_items_value,
                                table,
                                main_assembly,
                                "thickness",
                                thickness,
                            )
                        )
                        thickness_menu.addAction(thickness_action)
                    menu.addMenu(thickness_menu)

                    flowtags_menu = QMenu(self)
                    flowtags_menu.setTitle("Set Flow Tag")
                    for flow_tag in self.get_all_flow_tags():
                        flowtag_action = QAction(flow_tag, self)
                        flowtag_action.triggered.connect(
                            partial(
                                self.set_tables_selected_items_value,
                                table,
                                main_assembly,
                                "flow_tag",
                                flow_tag,
                            )
                        )
                        flowtags_menu.addAction(flowtag_action)
                    menu.addMenu(flowtags_menu)

                    paint_color_menu = QMenu(self)
                    paint_color_menu.setTitle("Set Paint Color")
                    for color in list(self.workspace_tags.get_value("paint_colors").keys()):
                        color_action = QAction(color, self)
                        color_action.triggered.connect(
                            partial(
                                self.set_tables_selected_items_value,
                                table,
                                main_assembly,
                                "paint_color",
                                color,
                            )
                        )
                        paint_color_menu.addAction(color_action)
                    menu.addMenu(paint_color_menu)

                    paint_type_menu = QMenu(self)
                    paint_type_menu.setTitle("Set Paint Type")
                    for paint_type in ["None", "Powder", "Wet Paint"]:
                        paint_type_action = QAction(paint_type, self)
                        paint_type_action.triggered.connect(
                            partial(
                                self.set_tables_selected_items_value,
                                table,
                                main_assembly,
                                "paint_type",
                                paint_type,
                            )
                        )
                        paint_type_menu.addAction(paint_type_action)
                    menu.addMenu(paint_type_menu)

                    delete_selected_items = QAction("Delete Selected Items", self)
                    delete_selected_items.triggered.connect(
                        partial(
                            self.delete_selected_items_from_workspace,
                            table,
                            main_assembly,
                        )
                    )
                    menu.addSeparator()
                    menu.addAction(delete_selected_items)

                    # action = QAction(self)
                    # action.triggered.connect(partial(self.name_change, table))
                    # action.setText("Change part name")
                    # menu.addAction(action)
                    table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    # * /\ CONTEXT MENU /\

    # Workspace
    def open_assembly_image(self, assembly: Assembly) -> None:
        image_viewer = QImageViewer(self, assembly.assembly_image, assembly.name)
        image_viewer.show()

    def open_pdf(self, path: str) -> None:
        pdf_viewer = PDFViewer(path, self)
        pdf_viewer.show()

    # WORKSPACE
    def set_filter_calendar_day(self, days: int) -> None:
        calendar: SelectRangeCalendar = self.verticalLayout_calendar_select_range.layout().itemAt(0).widget()
        if not calendar.from_date:
            calendar.from_date = QDate().currentDate()
        if days != 7:
            to_date: QDate = calendar.from_date.addDays(days)
        else:
            current_date = QDate.currentDate()
            calendar.from_date = current_date.addDays(-current_date.dayOfWeek() + 1)
            to_date = calendar.from_date.addDays(4)
        calendar.set_range(to_date)
        calendar.setSelectedDate(to_date)
        self.load_workspace()

    # WORKSPACE
    def load_workspace_filter_tab(self) -> None:
        self.workspace_filter.clear()
        self.clear_layout(self.filter_layout)
        self.clear_layout(self.verticalLayout_calendar_select_range)

        self.workspace_filter_tab_widget = FilterTabWidget(columns=2, parent=self)
        self.workspace_filter_tab_widget.add_tab("Materials")
        self.workspace_filter_tab_widget.add_tab("Thicknesses")
        self.workspace_filter_tab_widget.add_tab("Paint")
        self.workspace_filter_tab_widget.add_tab("Statuses")
        self.workspace_filter_tab_widget.add_tab("Flow Tags")
        self.workspace_filter_tab_widget.add_buttons_to_tab("Flow Tags", self.workspace_tags.get_value("all_tags"))
        self.workspace_filter_tab_widget.add_buttons_to_tab("Statuses", self.get_all_statuses())
        self.workspace_filter_tab_widget.add_buttons_to_tab("Materials", self.sheet_settings.get_materials())
        self.workspace_filter_tab_widget.add_buttons_to_tab("Thicknesses", self.sheet_settings.get_thicknesses())
        self.workspace_filter_tab_widget.add_buttons_to_tab("Paint", list(self.workspace_tags.get_value("paint_colors").keys()))
        self.workspace_filter_tab_widget.update_tab_button_visibility(0)

        self.filter_layout.addWidget(self.workspace_filter_tab_widget)

        self.lineEdit_search.editingFinished.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))
        self.lineEdit_search.setCompleter(QCompleter(self.get_all_workspace_item_names(), self))
        self.lineEdit_search.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.pushButton_show_sub_assembly.clicked.connect(
            lambda: (
                self.pushButton_show_item_summary.setChecked(False),
                self.load_workspace(),
            )
        )
        self.pushButton_show_item_summary.clicked.connect(
            lambda: (
                self.pushButton_show_sub_assembly.setChecked(False),
                self.load_workspace(),
            )
        )

        self.horizontalLayout_23.setAlignment(Qt.AlignmentFlag.AlignRight)

        calendar = SelectRangeCalendar(self)
        calendar.clicked.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))
        self.groupBox_due_dates.toggled.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))
        self.verticalLayout_calendar_select_range.addWidget(calendar)

        self.workspace_filter["use_filter"] = self.pushButton_use_filter
        self.workspace_filter["search"] = self.lineEdit_search
        self.workspace_filter["materials"] = self.workspace_filter_tab_widget.get_buttons("Materials")
        self.workspace_filter["thicknesses"] = self.workspace_filter_tab_widget.get_buttons("Thicknesses")
        self.workspace_filter["flow_tags"] = self.workspace_filter_tab_widget.get_buttons("Flow Tags")
        self.workspace_filter["statuses"] = self.workspace_filter_tab_widget.get_buttons("Statuses")
        self.workspace_filter["paint"] = self.workspace_filter_tab_widget.get_buttons("Paint")
        self.workspace_filter["due_dates"] = self.groupBox_due_dates
        self.workspace_filter["calendar"] = calendar
        self.workspace_filter["show_recut"] = False

        self.pushButton_use_filter.toggled.connect(self.load_workspace)

        self.workspace_filter_tab_widget.filterButtonPressed.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))

    # USER
    def download_workspace_file(self, file_to_download: str, open_when_done: bool = False) -> None:
        self.status_button.setText(f'Downloading - {datetime.now().strftime("%r")}', "yellow")
        workspace_download_files = WorkspaceDownloadFile([file_to_download], open_when_done)
        self.threads.append(workspace_download_files)
        workspace_download_files.signal.connect(self.download_workspace_file_response)
        workspace_download_files.start()

    # USER
    def download_workspace_file_response(self, response) -> None:
        if "Successfully downloaded" in response:
            self.status_button.setText(
                f"Successfully downloaded file - {datetime.now().strftime('%r')}",
                "lime",
            )
            file = response.split(";")[1]
            open_when_done = True if response.split(";")[-1] == "True" else False
            file_name = os.path.basename(file)
            file_ext = file_name.split(".")[-1].upper()
            file_path = f"{os.path.dirname(os.path.realpath(__file__))}/data/workspace/{file_ext}/{file_name}"

            if open_when_done:
                if file_ext in ["PNG", "JPEG", "JPG"]:
                    self.open_image(path=file_path, title=file_name)
                if file_ext == "PDF":
                    self.open_pdf(path=file_path)
        else:
            self.status_button.setText(f"Error - {response} - {datetime.now().strftime('%r')}", "red")

    # STAGING/EDITING
    def upload_workspace_files(self, files_to_upload: list[str]) -> None:
        self.status_button.setText(f'Uploading - {datetime.now().strftime("%r")}', "yellow")
        workspace_upload_thread = WorkspaceUploadThread(files_to_upload)
        self.threads.append(workspace_upload_thread)
        workspace_upload_thread.signal.connect(self.upload_workspace_files_response)
        workspace_upload_thread.start()

    # STAGING/EDITING
    def upload_workspace_files_response(self, response) -> None:
        if response == "Successfully uploaded":
            self.status_button.setText(
                f"Successfully uploaded files - {datetime.now().strftime('%r')}",
                "lime",
            )
        else:
            self.status_button.setText(f"Error - {response}", "red")

    # WORKSPACE
    def generate_workorder_dialog(self, job_names: list[str] = None) -> None:
        workorder = GenerateWorkorderDialog(self.admin_workspace, job_names, self)
        if workorder.exec():
            self.generate_workorder(workorder.get_workorder())

    # WORKSPACE
    def get_required_images_from_workorder(self, workorder: dict[Assembly, dict[dict[str, int], dict[str, bool]]]) -> list[str]:
        all_items: list[WorkspaceItem] = []
        for assembly in workorder:
            all_items.extend(assembly.items)

        all_images: list[str] = [f"{item.name}.jpeg" for item in all_items]
        return all_images

    # WORKSPACE
    def generate_workspace_printout_dialog(self, job_names: list[str] = None) -> None:
        printout_dialog = GenerateWorkspacePrintoutDialog(job_names, self.admin_workspace, self)
        if printout_dialog.exec():
            file_name: str = f'Printout - {datetime.now().strftime("%A, %d %B %Y %H-%M-%S-%f")}'
            required_images = self.get_required_images_from_workorder(printout_dialog.get_workorder())
            self.download_required_images(required_images)
            generate_printout = GeneratePrintout(
                self.admin_workspace,
                file_name,
                "Workorder",
                printout_dialog.get_workorder(),
                self.order_number,
            )
            generate_printout.generate()
            path_to_save_workspace_printouts = self.config.get("GLOBAL VARIABLES", "path_to_save_workspace_printouts")
            self.open_folder(f"{path_to_save_workspace_printouts}/{file_name}.html")

    # WORKSPACE
    def generate_workorder(self, work_order: dict[Assembly, int]) -> None:
        if not self.admin_workspace.do_all_sub_assemblies_have_flow_tags():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Flow Tags not set")
            msg.setText("Sub-assemblies do not have flow tags set. All sub-assemblies need to have flow tags.")
            msg.exec()
            return
        # Workspace order begins here
        date_created: str = QDate().currentDate().toString("yyyy-MM-dd")
        group_name_date_created = datetime.now()
        # admin_workspace.load_data()
        for assembly, quantity in work_order.items():
            try:
                job_name = assembly.name
            except AttributeError:
                job_name = assembly
            for _ in range(quantity):
                self.user_workspace.load_data()
                try:
                    new_assembly = assembly.copy_assembly()
                except AttributeError:
                    continue
                # new_assembly: Assembly = admin_workspace.copy(job_name)
                if new_assembly is None:
                    continue
                new_assembly.rename(f"{job_name} - {datetime.now()}")
                # Job Assembly Data
                new_assembly.display_name = job_name
                new_assembly.starting_date = date_created
                new_assembly.ending_date = date_created
                new_assembly.group = f"{job_name} x {quantity} - {group_name_date_created}"
                new_assembly.group_color = get_random_color()
                # Sub-Assembly Data
                new_assembly.set_data_to_all_sub_assemblies(key="starting_date", value=date_created)
                new_assembly.set_data_to_all_sub_assemblies(key="ending_date", value=date_created)
                # All items in Assembly and Sub-Assembly
                new_assembly.set_default_value_to_all_items(key="starting_date", value=date_created)
                new_assembly.set_default_value_to_all_items(key="ending_date", value=date_created)

                self.user_workspace.add_assembly(new_assembly)
                self.user_workspace.save()
        # NOTE because sync handles uploading logic differently
        self.parent.upload_file(
            [
                "user_workspace.json",
            ],
        )

    def load_tabs(self):
        self.clear_layout(self.workspace_layout)
        self.tab_widget = WorkspaceTabWidget(self)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.workspace_layout.addWidget(self.tab_widget)
        if self.trusted_user:
            edit_tabs = ["Staging", "Planning", "Editing", "Recut"]
        else:
            edit_tabs = ["Recut"]
        for category in edit_tabs + self.workspace_settings.get_all_tags():
            tab = QWidget(self)
            layout = QVBoxLayout(tab)
            tab.setLayout(layout)
            self.tabs[category] = tab
            self.tab_widget.addTab(tab, category)

    def tab_changed(self):
        self.category = self.tab_widget.tabText(self.tab_widget.currentIndex())
        self.load_workspace()

    # WORKSPACE
    def load_workspace(self) -> None:
        self.admin_workspace.load_data()
        self.user_workspace.load_data()
        if self.category == "Staging" or self.category == "Editing":
            if self.category == "Staging":  # Staging
                self.active_workspace_file = self.admin_workspace
            else:  # Editing
                self.active_workspace_file = self.user_workspace
            self.load_workspace_filter_tab()
            if self.category == "Staging":  # Staging
                self.pushButton_use_filter.setChecked(False)
                self.pushButton_add_job.setHidden(False)
                self.pushButton_generate_workorder.setHidden(False)
                self.pushButton_generate_workspace_quote.setHidden(False)
                self.pushButton_show_item_summary.setEnabled(True)
                self.pushButton_show_sub_assembly.setEnabled(True)
            else:  # Editing
                self.pushButton_use_filter.setEnabled(False)
                self.pushButton_use_filter.setChecked(False)
                self.pushButton_add_job.setHidden(True)
                self.pushButton_generate_workorder.setHidden(True)
                self.pushButton_generate_workspace_quote.setHidden(True)
                self.pushButton_show_item_summary.setEnabled(False)
                self.pushButton_show_sub_assembly.setEnabled(False)
            self.pushButton_use_filter.setEnabled(True)
            self.pushButton_show_item_summary.setEnabled(True)
            self.pushButton_show_sub_assembly.setEnabled(True)
            self.workspace_tables.clear()
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.tab_widget.widget(self.tab_widget.currentIndex())
            self.clear_layout(self.tab_widget.currentWidget().layout())
            self.load_edit_assembly_tab()
            self.load_edit_assembly_context_menus()
            QApplication.restoreOverrideCursor()
        elif self.category == "Planning":
            self.workspace_tables.clear()
            self.pushButton_add_job.setHidden(True)
            self.pushButton_generate_workorder.setHidden(True)
            self.pushButton_generate_workspace_quote.setHidden(True)
            self.pushButton_use_filter.setEnabled(False)
            self.pushButton_use_filter.setChecked(False)
            self.pushButton_show_item_summary.setEnabled(False)
            self.pushButton_show_sub_assembly.setEnabled(False)
            self.pushButton_show_item_summary.setChecked(False)
            self.pushButton_show_sub_assembly.setChecked(True)
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.tab_widget.widget(self.tab_widget.currentIndex())
            self.clear_layout(self.tab_widget.currentWidget().layout())
            self.load_planning_assembly_tab()
            QApplication.restoreOverrideCursor()
        else:
            self.workspace_tables.clear()
            self.pushButton_add_job.setHidden(True)
            self.pushButton_generate_workorder.setHidden(True)
            self.pushButton_generate_workspace_quote.setHidden(True)
            self.pushButton_use_filter.setEnabled(False)
            self.pushButton_use_filter.setChecked(True)
            self.pushButton_show_item_summary.setEnabled(True)
            self.pushButton_show_sub_assembly.setEnabled(True)
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.tab_widget.widget(self.tab_widget.currentIndex())
            self.clear_layout(self.tab_widget.currentWidget().layout())
            self.load_view_assembly_tab()
            QApplication.restoreOverrideCursor()

    def sync_changes(self):
        self.parent.sync_changes()

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
