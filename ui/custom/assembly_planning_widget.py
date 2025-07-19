import contextlib
import os
import shutil
import time
from functools import partial
from typing import Literal, Optional, Union, override

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtGui import QAction, QCursor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QScrollArea,
    QTableWidgetItem,
    QWidget,
)

from config.environments import Environment
from ui.custom.assembly_file_drop_widget import AssemblyFileDropWidget
from ui.custom.assembly_image import AssemblyImage
from ui.custom.assembly_paint_settings_widget import AssemblyPaintSettingsWidget
from ui.custom.assembly_paint_widget import AssemblyPaintWidget
from ui.custom.components_planning_table_widget import (
    ComponentsPlanningTableWidget,
    ComponentsTableColumns,
)
from ui.custom.file_button import FileButton
from ui.custom.flowtag_data_widget import FlowtagDataButton
from ui.custom.laser_cut_part_file_drop_widget import LaserCutPartFileDropWidget
from ui.custom.laser_cut_part_paint_settings_widget import (
    LasserCutPartPaintSettingsWidget,
)
from ui.custom.laser_cut_part_paint_widget import LaserCutPartPaintWidget
from ui.custom.laser_cut_parts_planning_table_widget import (
    LaserCutPartsPlanningTableWidget,
    LaserCutTableColumns,
)
from ui.custom.time_double_spin_box import TimeSpinBox
from ui.custom_widgets import AssemblyMultiToolBox
from ui.dialogs.add_component_dialog import AddComponentDialog
from ui.dialogs.add_laser_cut_part_dialog import AddLaserCutPartDialog
from ui.theme import theme_var
from ui.widgets.assembly_widget import AssemblyWidget
from utils.dxf_analyzer import DxfAnalyzer
from utils.get_bend_hits import get_bend_hits
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.threads.upload_thread import UploadThread
from utils.workers.workspace.download_file import WorkspaceDownloadWorker
from utils.workers.workspace.upload_file import WorkspaceUploadWorker
from utils.workspace.assembly import Assembly


class AssemblyPlanningWidget(AssemblyWidget):
    def __init__(self, assembly: Assembly, parent):
        super().__init__(assembly, parent)
        self.sub_assembly_widgets: list[AssemblyPlanningWidget] = []
        self.laser_cut_part_table_items: dict[
            LaserCutPart,
            dict[str, QTableWidgetItem | QComboBox | QWidget | int | FlowtagDataButton],
        ] = {}
        self.components_table_items: dict[Component, dict[str, QTableWidgetItem | int]] = {}

        self.upload_images_thread: UploadThread = None
        self.upload_files_thread: WorkspaceUploadWorker = None
        self.download_file_thread: WorkspaceDownloadWorker = None

        self.settings_file = Settings()
        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.load_ui()
        self.load_laser_cut_parts_table()
        self.load_components_table()

    def load_ui(self):
        assembly_files_widget, assembly_files_layout = self.create_assembly_file_layout()
        self.assembly_files_layout.addWidget(assembly_files_widget)

        self.label_total_cost_for_assembly.setHidden(True)

        self.assembly_image = AssemblyImage(self)

        if self.assembly.meta_data.assembly_image:
            self.assembly_image.set_new_image(self.assembly.meta_data.assembly_image)

        self.assembly_image.clicked.connect(self.open_assembly_image)
        self.assembly_image.imagePathDropped.connect(self.upload_assembly_image)
        self.assembly_image.customContextMenuRequested.connect(self.assembly_image_show_context_menu)

        self.doubleSpinBox_quantity.setValue(self.assembly.meta_data.quantity)
        self.doubleSpinBox_quantity.valueChanged.connect(self.assembly_quantity_changed)

        self.doubleSpinBox_expected_time_to_complete = TimeSpinBox(self)
        self.doubleSpinBox_expected_time_to_complete.setEnabled(False)
        self.doubleSpinBox_expected_time_to_complete.setValue(int(self.assembly.get_expected_time_to_complete()))
        self.expected_time_to_complete_layout.addWidget(self.doubleSpinBox_expected_time_to_complete)

        self.paint_widget.setVisible(self.assembly.workspace_data.flowtag.contains(["paint", "powder", "coating", "liquid"]))

        self.assembly_setting_paint_widget = AssemblyPaintSettingsWidget(self.assembly, self)
        self.assembly_setting_paint_widget.settingsChanged.connect(self.changes_made)
        self.assembly_paint_widget = AssemblyPaintWidget(self.assembly, self.assembly_setting_paint_widget, self)
        self.assembly_paint_widget.settingsChanged.connect(self.changes_made)
        self.paint_layout.addWidget(self.assembly_paint_widget)
        self.paint_layout.addWidget(self.assembly_setting_paint_widget)

        self.image_layout.addWidget(self.assembly_image)

        if str(self.assembly.workspace_data.flowtag.name):
            self.comboBox_assembly_flow_tag.addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_assembly_flow_tags().values())])
        else:
            self.comboBox_assembly_flow_tag.addItems(["Select flow tag"] + [f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_assembly_flow_tags().values())])
        self.comboBox_assembly_flow_tag.setCurrentText(str(self.assembly.workspace_data.flowtag))
        self.comboBox_assembly_flow_tag.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
        self.comboBox_assembly_flow_tag.currentTextChanged.connect(self.assembly_flow_tag_changed)
        self.comboBox_assembly_flow_tag.setFixedWidth(200)
        self.comboBox_assembly_flow_tag.setToolTip(self.assembly.workspace_data.flowtag.get_tooltip())

        self.flowtag_data_widget.setVisible(True)
        self.assembly_flowtag_data_widget = FlowtagDataButton(self.assembly.workspace_data.flowtag_data, self)
        self.flowtag_data_layout.addWidget(self.assembly_flowtag_data_widget)

        self.laser_cut_parts_table = LaserCutPartsPlanningTableWidget(self)
        self.laser_cut_parts_table.rowChanged.connect(self.laser_cut_parts_table_changed)
        self.laser_cut_parts_layout.addWidget(self.laser_cut_parts_table)
        self.add_laser_cut_part_button.clicked.connect(self.add_laser_cut_part)
        self.load_laser_cut_parts_table_context_menu()

        self.components_table = ComponentsPlanningTableWidget(self)
        self.components_table.rowChanged.connect(self.components_table_changed)
        self.components_table.imagePasted.connect(self.component_image_pasted)
        self.load_components_table_context_menu()

        self.components_layout.addWidget(self.components_table)

        self.add_component_button.clicked.connect(self.add_component)

        self.add_new_sub_assembly_button.clicked.connect(self.add_sub_assembly)
        self.add_existing_assembly_button.clicked.connect(self.add_existing_sub_assembly)

        self.sub_assemblies_toolbox = AssemblyMultiToolBox(self)
        self.sub_assembly_layout.addWidget(self.sub_assemblies_toolbox)

    def workspace_settings_changed(self):
        assembly_selected_flow_tag = self.comboBox_assembly_flow_tag.currentText()
        self.comboBox_assembly_flow_tag.blockSignals(True)
        self.comboBox_assembly_flow_tag.clear()
        self.comboBox_assembly_flow_tag.addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_assembly_flow_tags().values())])
        self.comboBox_assembly_flow_tag.setCurrentText(assembly_selected_flow_tag)
        self.comboBox_assembly_flow_tag.setToolTip(self.assembly.workspace_data.flowtag.get_tooltip())
        self.comboBox_assembly_flow_tag.blockSignals(False)
        for _, table_items in self.laser_cut_part_table_items.items():
            selected_flow_tag = table_items["flow_tag"].currentText()
            table_items["flow_tag"].blockSignals(True)
            table_items["flow_tag"].clear()
            table_items["flow_tag"].addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())])
            table_items["flow_tag"].setCurrentText(selected_flow_tag)
            table_items["flow_tag"].setToolTip(str(selected_flow_tag))
            table_items["flow_tag"].blockSignals(False)
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.workspace_settings_changed()
        self.changes_made()

    # ASSEMBLY STUFF
    def assembly_quantity_changed(self):
        self.assembly.meta_data.quantity = self.doubleSpinBox_quantity.value()
        self.update_laser_cut_parts_table_quantity()
        self.update_component_table_quantity()
        self.changes_made()

    def create_assembly_file_layout(self) -> tuple[QWidget, QHBoxLayout]:
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

        drop_widget = AssemblyFileDropWidget(files_layout, main_widget)
        drop_widget.fileDropped.connect(self.assembly_file_dropped)
        main_layout.addWidget(drop_widget)

        scroll_area = QScrollArea(self)
        scroll_area.setWidget(files_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # scroll_area.setStyleSheet("QWidget#scrollAreaWidgetContents{background-color: rgba(20, 20, 20, 0.5);} QAbstractScrollArea{background-color: rgba(20, 20, 20, 0.5);}")

        main_layout.addWidget(scroll_area)

        for file in self.assembly.workspace_data.assembly_files:
            self.add_assembly_drag_file_widget(files_layout, file)

        return main_widget, files_layout

    def upload_assembly_image(self, path_to_image: str, save_image: bool = True):
        file_name = os.path.basename(path_to_image)

        target_path = os.path.join("images", file_name)

        if save_image:
            self.copy_file_with_overwrite(path_to_image, target_path)

        self.assembly_image.set_new_image(target_path)
        self.assembly.meta_data.assembly_image = target_path
        self.upload_images([target_path])
        self.changes_made()

    def assembly_image_show_context_menu(self):
        contextMenu = QMenu(self)
        delete_action = contextMenu.addAction("Clear image")
        paste_action = contextMenu.addAction("Paste image from clipboard")

        action = contextMenu.exec(QCursor.pos())

        if action == delete_action:
            self.assembly.meta_data.assembly_image = None
            self.assembly_image.clear_image()
            self.changes_made()
        elif action == paste_action:
            clipboard = QApplication.clipboard()
            image = clipboard.image()
            if not image.isNull():
                temp_path = f"images/{self.assembly.name}.png"
                image.save(temp_path)
                self.upload_assembly_image(temp_path, False)

    def assembly_flow_tag_changed(self):
        if not (new_flowtag := self.workspace_settings.get_flow_tag_by_name(self.comboBox_assembly_flow_tag.currentText())):
            msg = QMessageBox(
                QMessageBox.Icon.Warning,
                "Not a flowtag",
                "Not a valid flowtag",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return
        self.assembly.workspace_data.flowtag = new_flowtag
        self.assembly.workspace_data.flowtag_data.flowtag = new_flowtag
        self.assembly.workspace_data.flowtag_data.load_data(self.assembly.workspace_data.flowtag_data.to_dict())
        self.assembly_flowtag_data_widget.dropdown.load_ui()

        try:
            self.paint_widget.setVisible(self.assembly.workspace_data.flowtag.contains(["paint", "glosspowder", "coating", "liquid"]))
        except AttributeError:  # There is no flow tag selected
            self.paint_widget.setHidden(True)
        self.changes_made()

    def add_assembly_drag_file_widget(self, files_layout: QHBoxLayout, file_path: str):
        file_button = FileButton(f"{os.path.dirname(os.path.realpath(__file__))}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.assembly_file_clicked, file_path))
        file_button.deleteFileClicked.connect(partial(self.assembly_delete_file, file_path, file_button))
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)

    def assembly_file_clicked(self, file_path: str):
        self.download_file_thread = WorkspaceDownloadFile([file_path], True)
        self.download_file_thread.signal.connect(self.file_downloaded)
        self.download_file_thread.start()
        self.download_file_thread.wait()
        if file_path.lower().endswith(".pdf"):
            self.open_pdf(self.assembly_get_all_file_types(".pdf"), file_path)

    def assembly_delete_file(self, file_path: str, file_button: FileButton):
        self.assembly.workspace_data.assembly_files.remove(file_path)
        file_button.deleteLater()
        self.changes_made()

    def assembly_file_dropped(self, files_layout: QHBoxLayout, file_paths: list[str]):
        for file_path in file_paths:
            file_ext = file_path.split(".")[-1].upper()
            file_name = os.path.basename(file_path)

            target_dir = f"data\\workspace\\{file_ext}"
            target_path = os.path.join(target_dir, file_name)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            self.copy_file_with_overwrite(file_path, target_path)

            self.assembly.workspace_data.assembly_files.append(target_path)
            self.add_assembly_drag_file_widget(files_layout, target_path)
        self.upload_files(file_paths)
        self.changes_made()

    def assembly_get_all_file_types(self, file_ext: str) -> list[str]:
        files: set[str] = {file for file in self.assembly.workspace_data.assembly_files if file.lower().endswith(file_ext)}
        return list(files)

    # COMPONENT STUFF
    def load_components_table(self):
        self.components_table.blockSignals(True)
        self.components_table_items.clear()
        self.components_table.setRowCount(0)
        for component in self.assembly.components:
            self.add_component_to_table(component)
        self.components_table.blockSignals(False)
        self.components_table.resizeColumnsToContents()
        self.update_components_table_height()

    def component_image_pasted(self, image_file_name: str, row: int):
        component_name = self.components_table.item(row, ComponentsTableColumns.PART_NUMBER.value).text()
        component = self.get_component_by_name(component_name)

        target_path = os.path.join("images", f"{component.name}.png")

        self.copy_file_with_overwrite(image_file_name, target_path)

        component.image_path = target_path

        # Update parts in the inventory
        if component_in_inventory := self.components_inventory.get_component_by_name(component.name):
            component_in_inventory.image_path = target_path
        self.upload_images([target_path])
        self.changes_made()

    def add_component_to_table(self, component: Component):
        self.components_table.blockSignals(True)
        current_row = self.components_table.rowCount()
        self.components_table_items.update({component: {}})
        self.components_table_items[component].update({"row": current_row})
        self.components_table.insertRow(current_row)
        self.components_table.setRowHeight(current_row, self.components_table.row_height)

        image_item = QTableWidgetItem("")
        if component.image_path:
            image = QPixmap(component.image_path)
            original_width = image.width()
            original_height = image.height()
            new_height = self.components_table.row_height
            try:
                new_width = int(original_width * (new_height / original_height))
            except ZeroDivisionError:
                new_width = original_width
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.components_table.setRowHeight(current_row, new_height)

        self.components_table.setItem(current_row, ComponentsTableColumns.PICTURE.value, image_item)

        part_name_item = QTableWidgetItem(component.part_name)
        part_name_item.setFont(self.tables_font)
        if self.components_inventory.get_component_by_name(component.name):
            component_inventory_status = f"{component.name} exists in inventory."
            self.set_table_row_color(self.components_table, current_row, f"{theme_var('background')}")
        else:
            component_inventory_status = f"{component.name} does NOT exist in inventory."
            self.set_table_row_color(self.components_table, current_row, f"{theme_var('table-red-quantity')}")
        part_name_item.setToolTip(component_inventory_status)
        self.components_table.setItem(current_row, ComponentsTableColumns.PART_NAME.value, part_name_item)
        self.components_table_items[component].update({"part_name": part_name_item})

        part_number_item = QTableWidgetItem(component.part_number)
        part_number_item.setFont(self.tables_font)
        part_number_item.setToolTip(component_inventory_status)
        self.components_table.setItem(current_row, ComponentsTableColumns.PART_NUMBER.value, part_number_item)
        self.components_table_items[component].update({"part_number": part_number_item})

        unit_quantity_item = QTableWidgetItem(str(component.quantity))
        unit_quantity_item.setFont(self.tables_font)
        self.components_table.setItem(current_row, ComponentsTableColumns.UNIT_QUANTITY.value, unit_quantity_item)
        self.components_table_items[component].update({"unit_quantity": unit_quantity_item})

        quantity_item = QTableWidgetItem(str(component.quantity * self.assembly.meta_data.quantity))
        quantity_item.setFont(self.tables_font)
        self.components_table.setItem(current_row, ComponentsTableColumns.QUANTITY.value, quantity_item)
        self.components_table_items[component].update({"quantity": quantity_item})

        notes_item = QTableWidgetItem(component.notes)
        notes_item.setFont(self.tables_font)
        notes_item.setToolTip(component.notes)
        self.components_table.setItem(current_row, ComponentsTableColumns.NOTES.value, notes_item)
        self.components_table_items[component].update({"notes": notes_item})

        shelf_number_item = QTableWidgetItem(component.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        self.components_table.setItem(current_row, ComponentsTableColumns.SHELF_NUMBER.value, shelf_number_item)
        self.components_table_items[component].update({"shelf_number": shelf_number_item})
        self.components_table.blockSignals(False)
        self.update_components_table_height()

    def update_component_table_quantity(self):
        self.components_table.blockSignals(True)
        for component, table_data in self.components_table_items.items():
            table_data["quantity"].setText(str(component.quantity * self.assembly.meta_data.quantity))
        self.components_table.blockSignals(False)

    def components_table_changed(self, row: int):
        changed_component = next(
            (component for component, table_data in self.components_table_items.items() if table_data["row"] == row),
            None,
        )
        if not changed_component:
            return
        changed_component.part_name = self.components_table_items[changed_component]["part_name"].text()
        if self.components_inventory.get_component_by_name(changed_component.name):
            component_inventory_status = f"{changed_component.name} exists in inventory."
            self.set_table_row_color(
                self.components_table,
                self.components_table_items[changed_component]["row"],
                f"{theme_var('background')}",
            )
        else:
            component_inventory_status = f"{changed_component.name} does NOT exist in inventory."
            self.set_table_row_color(
                self.components_table,
                self.components_table_items[changed_component]["row"],
                f"{theme_var('table-red-quantity')}",
            )
        self.components_table_items[changed_component]["part_name"].setToolTip(component_inventory_status)
        self.components_table_items[changed_component]["part_number"].setToolTip(component_inventory_status)
        changed_component.part_number = self.components_table_items[changed_component]["part_number"].text()
        changed_component.quantity = float(self.components_table_items[changed_component]["unit_quantity"].text())
        changed_component.notes = self.components_table_items[changed_component]["notes"].text()
        changed_component.shelf_number = self.components_table_items[changed_component]["shelf_number"].text()
        self.update_component_table_quantity()
        self.changes_made()

    def get_component_by_name(self, component_name: str) -> Component | None:
        return next(
            (component for component in self.assembly.components if component.name == component_name),
            None,
        )

    def add_component(self):
        add_item_dialog = AddComponentDialog(self.components_inventory, self)
        if add_item_dialog.exec():
            if components := add_item_dialog.get_selected_components():
                for component in components:
                    new_component = Component(component.to_dict(), self.components_inventory)
                    new_component.quantity = 1.0
                    self.assembly.add_component(new_component)
                    self.add_component_to_table(new_component)
            else:
                new_component = Component(
                    {
                        "part_name": add_item_dialog.get_name(),
                        "part_number": add_item_dialog.get_name(),
                    },
                    self.components_inventory,
                )
                new_component.quantity = add_item_dialog.get_current_quantity()
                self.assembly.add_component(new_component)
                self.add_component_to_table(new_component)

    def update_components_table_height(self):
        self.components_table.setFixedHeight((len(self.assembly.components) + 1) * self.components_table.row_height)

    def get_selected_component(self) -> Component:
        if selected_components := self.get_selected_components():
            return selected_components[0]
        else:
            return None

    def get_selected_components(self) -> list[Component]:
        selected_components: list[Component] = []
        selected_rows = self.get_selected_component_rows()
        selected_components.extend(component for component, table_items in self.components_table_items.items() if table_items["row"] in selected_rows)
        return selected_components

    def get_selected_component_rows(self) -> list[int]:
        rows: set[int] = {item.row() for item in self.components_table.selectedItems()}
        return list(rows)

    def delete_selected_components(self):
        if selected_components := self.get_selected_components():
            for component in selected_components:
                self.assembly.components.remove(component)
        self.changes_made()
        self.load_components_table()

    def load_components_table_context_menu(self):
        if self.components_table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            self.components_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

            menu = QMenu(self)

            set_quantity_menu = QMenu("Set Quantity", menu)
            for number in range(10):
                action = QAction(str(number), set_quantity_menu)
                action.triggered.connect(
                    partial(
                        self.handle_components_table_context_menu,
                        "SET_QUANTITY",
                        number,
                    )
                )
                set_quantity_menu.addAction(action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_selected_components)

            menu.addMenu(set_quantity_menu)
            menu.addAction(delete_action)

            self.components_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    def handle_components_table_context_menu(self, ACTION: str, selection: str | float | int):
        if not (selected_components := self.get_selected_components()):
            return
        for component in selected_components:
            if ACTION == "SET_QUANTITY":
                component.quantity = float(selection)
        self.load_components_table()
        self.changes_made()

    # LASER CUT PART STUFF
    def load_laser_cut_parts_table(self):
        self.laser_cut_parts_table.blockSignals(True)
        self.laser_cut_part_table_items.clear()
        self.laser_cut_parts_table.setRowCount(0)
        for laser_cut_part in self.assembly.laser_cut_parts:
            self.add_laser_cut_part_to_table(laser_cut_part)
        self.laser_cut_parts_table.blockSignals(False)
        self.laser_cut_parts_table.resizeColumnsToContents()
        self.laser_cut_parts_table.resizeRowsToContents()
        self.update_laser_cut_parts_table_height()

    def add_laser_cut_part_to_table(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts_table.blockSignals(True)

        def create_file_layout(file_type) -> tuple[QWidget, QHBoxLayout]:
            main_widget = QWidget(self.laser_cut_parts_table)
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

            drop_widget = LaserCutPartFileDropWidget(laser_cut_part, files_layout, file_type, main_widget)
            drop_widget.fileDropped.connect(self.laser_cut_part_file_dropped)
            main_layout.addWidget(drop_widget)

            scroll_area = QScrollArea(self.laser_cut_parts_table)
            scroll_area.setWidget(files_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFixedWidth(100)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            # scroll_area.setStyleSheet("QWidget#scrollAreaWidgetContents{background-color: rgba(20, 20, 20, 0.5);} QAbstractScrollArea{background-color: rgba(20, 20, 20, 0.5);}")

            main_layout.addWidget(scroll_area)

            file_list = getattr(laser_cut_part, file_type)
            for file in file_list:
                self.add_laser_cut_part_drag_file_widget(laser_cut_part, file_type, files_layout, file)

            return main_widget, files_layout

        current_row = self.laser_cut_parts_table.rowCount()
        self.laser_cut_part_table_items.update({laser_cut_part: {}})
        self.laser_cut_part_table_items[laser_cut_part].update({"row": current_row})
        self.laser_cut_parts_table.insertRow(current_row)
        self.laser_cut_parts_table.setRowHeight(current_row, self.laser_cut_parts_table.row_height)

        image_item = QTableWidgetItem()
        try:
            if "images" not in laser_cut_part.meta_data.image_index:
                laser_cut_part.meta_data.image_index = "images/" + laser_cut_part.meta_data.image_index
            if not laser_cut_part.meta_data.image_index.endswith(".jpeg"):
                laser_cut_part.meta_data.image_index += ".jpeg"
            image = QPixmap(laser_cut_part.meta_data.image_index)
            if image.isNull():
                image = QPixmap("images/404.jpeg")
            original_width = image.width()
            original_height = image.height()
            new_height = self.laser_cut_parts_table.row_height
            try:
                new_width = int(original_width * (new_height / original_height))
            except ZeroDivisionError:
                new_width = original_width
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        except Exception as e:
            image_item.setText(f"Error: {e}")

        self.laser_cut_parts_table.setRowHeight(current_row, new_height)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PICTURE.value, image_item)

        part_name_item = QTableWidgetItem(laser_cut_part.name)
        part_name_item.setFont(self.tables_font)
        if self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.name):
            laser_cut_part_inventory_status = f"{laser_cut_part.name} exists in inventory."
            self.set_table_row_color(self.laser_cut_parts_table, current_row, f"{theme_var('background')}")
        else:
            laser_cut_part_inventory_status = f"{laser_cut_part.name} does NOT exist in inventory."
            self.set_table_row_color(
                self.laser_cut_parts_table,
                current_row,
                f"{theme_var('table-red-quantity')}",
            )

        part_name_item.setToolTip(laser_cut_part_inventory_status)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PART_NAME.value, part_name_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"part_name": part_name_item})

        # Bending files
        bending_files_widget, bending_files_layout = create_file_layout("bending_files")
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.BENDING_FILES.value,
            bending_files_widget,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"bending_files": bending_files_widget})

        # Welding files
        welding_files_widget, welding_files_layout = create_file_layout("welding_files")
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.WELDING_FILES.value,
            welding_files_widget,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"welding_files": welding_files_widget})

        # CNC milling files
        cnc_milling_files_widget, cnc_milling_files_layout = create_file_layout("cnc_milling_files")
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.CNC_MILLING_FILES.value,
            cnc_milling_files_widget,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"cnc_milling_files": cnc_milling_files_widget})

        materials_combobox = QComboBox(self)
        materials_combobox.setStyleSheet("border-radius: 0px;")
        materials_combobox.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
        materials_combobox.addItems(self.sheet_settings.get_materials())
        materials_combobox.setCurrentText(laser_cut_part.meta_data.material)
        materials_combobox.currentTextChanged.connect(partial(self.laser_cut_parts_table_changed, current_row))
        self.laser_cut_parts_table.setCellWidget(current_row, LaserCutTableColumns.MATERIAL.value, materials_combobox)
        self.laser_cut_part_table_items[laser_cut_part].update({"material": materials_combobox})

        thicknesses_combobox = QComboBox(self)
        thicknesses_combobox.setStyleSheet("border-radius: 0px;")
        thicknesses_combobox.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
        thicknesses_combobox.addItems(self.sheet_settings.get_thicknesses())
        thicknesses_combobox.setCurrentText(laser_cut_part.meta_data.gauge)
        thicknesses_combobox.currentTextChanged.connect(partial(self.laser_cut_parts_table_changed, current_row))
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.THICKNESS.value,
            thicknesses_combobox,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"thickness": thicknesses_combobox})

        unit_quantity_item = QTableWidgetItem(str(laser_cut_part.inventory_data.quantity))
        unit_quantity_item.setFont(self.tables_font)
        unit_quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.UNIT_QUANTITY.value, unit_quantity_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"unit_quantity": unit_quantity_item})

        quantity_item = QTableWidgetItem(str(laser_cut_part.inventory_data.quantity * self.assembly.meta_data.quantity))
        quantity_item.setFont(self.tables_font)
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.QUANTITY.value, quantity_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"quantity": quantity_item})

        painting_settings_widget = LasserCutPartPaintSettingsWidget(laser_cut_part, self.laser_cut_parts_table)
        painting_settings_widget.settingsChanged.connect(self.changes_made)
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.PAINT_SETTINGS.value,
            painting_settings_widget,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"painting_settings_widget": painting_settings_widget})

        painting_widget = LaserCutPartPaintWidget(laser_cut_part, painting_settings_widget, self.laser_cut_parts_table)
        painting_widget.settingsChanged.connect(self.changes_made)
        self.laser_cut_parts_table.setCellWidget(current_row, LaserCutTableColumns.PAINTING.value, painting_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"painting_widget": painting_widget})

        flow_tag_combobox = QComboBox(self)
        flow_tag_combobox.setStyleSheet("border-radius: 0px;")
        flow_tag_combobox.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
        if str(laser_cut_part.workspace_data.flowtag.name):
            flow_tag_combobox.addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())])
        else:
            flow_tag_combobox.addItems(["Select flow tag"] + [f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())])
        flow_tag_combobox.setCurrentText(str(laser_cut_part.workspace_data.flowtag))
        flow_tag_combobox.setFixedWidth(200)
        flow_tag_combobox.setToolTip(laser_cut_part.workspace_data.flowtag.get_tooltip())
        flow_tag_combobox.currentTextChanged.connect(partial(self.laser_cut_part_flow_tag_changed, laser_cut_part, flow_tag_combobox))
        self.laser_cut_parts_table.setCellWidget(current_row, LaserCutTableColumns.FLOW_TAG.value, flow_tag_combobox)
        self.laser_cut_part_table_items[laser_cut_part].update({"flow_tag": flow_tag_combobox})

        notes_item = QTableWidgetItem(laser_cut_part.meta_data.notes)
        notes_item.setFont(self.tables_font)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.NOTES.value, notes_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"notes": notes_item})

        shelf_number_item = QTableWidgetItem(laser_cut_part.meta_data.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.SHELF_NUMBER.value,
            shelf_number_item,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"shelf_number": shelf_number_item})
        self.laser_cut_parts_table.blockSignals(False)
        self.update_laser_cut_parts_table_height()

        flowtag_data_widget = FlowtagDataButton(laser_cut_part.workspace_data.flowtag_data, self)
        if tag := laser_cut_part.workspace_data.flowtag.get_tag_with_similar_name("laser"):
            laser_cut_part.workspace_data.flowtag_data.set_tag_data(tag, "expected_time_to_complete", int(laser_cut_part.meta_data.machine_time * 60))
        elif tag := laser_cut_part.workspace_data.flowtag.get_tag_with_similar_name("picking"):
            laser_cut_part.workspace_data.flowtag_data.set_tag_data(tag, "expected_time_to_complete", laser_cut_part.meta_data.weight)
        self.laser_cut_parts_table.setCellWidget(current_row, LaserCutTableColumns.FLOW_TAG_DATA.value, flowtag_data_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"flowtag_data_button": flowtag_data_widget})

    def update_laser_cut_parts_table_quantity(self):
        self.laser_cut_parts_table.blockSignals(True)
        for laser_cut_part, table_data in self.laser_cut_part_table_items.items():
            table_data["quantity"].setText(str(laser_cut_part.inventory_data.quantity * self.assembly.meta_data.quantity))
        self.laser_cut_parts_table.blockSignals(False)

    def laser_cut_parts_table_changed(self, row: int):
        changed_laser_cut_part = next(
            (laser_cut_part for laser_cut_part, table_data in self.laser_cut_part_table_items.items() if table_data["row"] == row),
            None,
        )
        if not changed_laser_cut_part:
            return
        changed_laser_cut_part.name = self.laser_cut_part_table_items[changed_laser_cut_part]["part_name"].text()
        if self.laser_cut_inventory.get_laser_cut_part_by_name(changed_laser_cut_part.name):
            laser_cut_part_inventory_status = f"{changed_laser_cut_part.name} exists in inventory."
            self.set_table_row_color(
                self.laser_cut_parts_table,
                self.laser_cut_part_table_items[changed_laser_cut_part]["row"],
                f"{theme_var('background')}",
            )
        else:
            laser_cut_part_inventory_status = f"{changed_laser_cut_part.name} does NOT exist in inventory."
            self.set_table_row_color(
                self.laser_cut_parts_table,
                self.laser_cut_part_table_items[changed_laser_cut_part]["row"],
                f"{theme_var('table-red-quantity')}",
            )
        self.laser_cut_part_table_items[changed_laser_cut_part]["part_name"].setToolTip(laser_cut_part_inventory_status)
        changed_laser_cut_part.meta_data.material = self.laser_cut_part_table_items[changed_laser_cut_part]["material"].currentText()
        changed_laser_cut_part.meta_data.gauge = self.laser_cut_part_table_items[changed_laser_cut_part]["thickness"].currentText()
        changed_laser_cut_part.meta_data.weight = changed_laser_cut_part.calculate_weight()
        with contextlib.suppress(ValueError):
            changed_laser_cut_part.inventory_data.quantity = float(self.laser_cut_part_table_items[changed_laser_cut_part]["unit_quantity"].text())
        changed_laser_cut_part.meta_data.notes = self.laser_cut_part_table_items[changed_laser_cut_part]["notes"].text()
        changed_laser_cut_part.meta_data.shelf_number = self.laser_cut_part_table_items[changed_laser_cut_part]["shelf_number"].text()
        self.update_laser_cut_parts_table_quantity()
        self.changes_made()

    def laser_cut_part_flow_tag_changed(self, laser_cut_part: LaserCutPart, flow_tag_combobox: QComboBox):
        if not (new_flowtag := self.workspace_settings.get_flow_tag_by_name(flow_tag_combobox.currentText())):
            msg = QMessageBox(
                QMessageBox.Icon.Warning,
                "Not a flowtag",
                "Not a valid flowtag",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return
        laser_cut_part.workspace_data.flowtag = new_flowtag
        laser_cut_part.workspace_data.flowtag_data.flowtag = new_flowtag
        laser_cut_part.workspace_data.flowtag_data.load_data(laser_cut_part.workspace_data.flowtag_data.to_dict())
        if tag := laser_cut_part.workspace_data.flowtag.get_tag_with_similar_name("laser"):
            laser_cut_part.workspace_data.flowtag_data.set_tag_data(tag, "expected_time_to_complete", int(laser_cut_part.meta_data.machine_time * 60))
        elif tag := laser_cut_part.workspace_data.flowtag.get_tag_with_similar_name("picking"):
            laser_cut_part.workspace_data.flowtag_data.set_tag_data(tag, "expected_time_to_complete", laser_cut_part.meta_data.weight)
        self.laser_cut_part_table_items[laser_cut_part]["flowtag_data_button"].dropdown.load_ui()
        self.laser_cut_parts_table.resizeRowsToContents()
        self.laser_cut_parts_table.resizeColumnsToContents()
        flow_tag_combobox.setToolTip(laser_cut_part.workspace_data.flowtag.get_tooltip())
        self.update_laser_cut_parts_table_height()
        self.changes_made()

    def add_laser_cut_part_drag_file_widget(
        self,
        laser_cut_part: LaserCutPart,
        file_category: Literal["bending_files", "welding_files", "cnc_milling_files"],
        files_layout: QHBoxLayout,
        file_path: str,
    ):
        file_button = FileButton(f"{Environment.DATA_PATH}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.laser_cut_part_file_clicked, laser_cut_part, file_path))
        file_button.deleteFileClicked.connect(
            partial(
                self.laser_cut_part_delete_file,
                laser_cut_part,
                file_category,
                file_path,
                file_button,
            )
        )
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)
        self.laser_cut_parts_table.resizeColumnsToContents()

    def add_laser_cut_part(self):
        add_item_dialog = AddLaserCutPartDialog(self.laser_cut_inventory, self)
        if add_item_dialog.exec():
            if laser_cut_parts := add_item_dialog.get_selected_laser_cut_parts():
                for laser_cut_part in laser_cut_parts:
                    new_laser_cut_part = LaserCutPart(
                        laser_cut_part.to_dict(),
                        self.laser_cut_inventory,
                    )
                    new_laser_cut_part.inventory_data.quantity = add_item_dialog.get_current_quantity()
                    self.assembly.add_laser_cut_part(new_laser_cut_part)
                    self.add_laser_cut_part_to_table(new_laser_cut_part)
            else:
                new_laser_cut_part = LaserCutPart({"name": add_item_dialog.get_name()}, self.laser_cut_inventory)
                new_laser_cut_part.inventory_data.quantity = add_item_dialog.get_current_quantity()
                self.assembly.add_laser_cut_part(new_laser_cut_part)
                self.add_laser_cut_part_to_table(new_laser_cut_part)

    def update_laser_cut_parts_table_height(self):
        total_height = 0
        for row in range(self.laser_cut_parts_table.rowCount()):
            total_height += self.laser_cut_parts_table.rowHeight(row)
        self.laser_cut_parts_table.setFixedHeight(total_height + 70)

    def laser_cut_part_get_all_file_types(self, laser_cut_part: LaserCutPart, file_ext: str) -> list[str]:
        files: set[str] = set()
        for bending_file in laser_cut_part.workspace_data.bending_files:
            if bending_file.lower().endswith(file_ext):
                files.add(bending_file)
        for welding_file in laser_cut_part.workspace_data.welding_files:
            if welding_file.lower().endswith(file_ext):
                files.add(welding_file)
        for cnc_milling_file in laser_cut_part.workspace_data.cnc_milling_files:
            if cnc_milling_file.lower().endswith(file_ext):
                files.add(cnc_milling_file)
        return list(files)

    def laser_cut_part_file_clicked(self, laser_cut_part: LaserCutPart, file_path: str):
        def open_pdf(files: list[str]):
            if file_path.lower().endswith(".pdf"):
                self.open_pdf(
                    self.laser_cut_part_get_all_file_types(laser_cut_part, ".pdf"),
                    file_path,
                )

        self.download_file_thread = WorkspaceDownloadWorker([file_path], True)
        self.download_file_thread.signals.success.connect(self.file_downloaded)
        self.download_file_thread.signals.success.connect(open_pdf)
        QThreadPool.globalInstance().start(self.download_file_thread)

    def get_selected_laser_cut_part(self) -> LaserCutPart:
        if selected_laser_cut_parts := self.get_selected_laser_cut_parts():
            return selected_laser_cut_parts[0]
        else:
            return None

    def get_selected_laser_cut_parts(self) -> list[LaserCutPart]:
        selected_laser_cut_parts: list[LaserCutPart] = []
        selected_rows = self.get_selected_laser_cut_part_rows()
        selected_laser_cut_parts.extend(component for component, table_items in self.laser_cut_part_table_items.items() if table_items["row"] in selected_rows)
        return selected_laser_cut_parts

    def get_selected_laser_cut_part_rows(self) -> list[int]:
        rows: set[int] = {item.row() for item in self.laser_cut_parts_table.selectedItems()}
        return list(rows)

    def delete_selected_laser_cut_parts(self):
        if selected_laser_cut_parts := self.get_selected_laser_cut_parts():
            for laser_cut_part in selected_laser_cut_parts:
                self.assembly.laser_cut_parts.remove(laser_cut_part)
        self.changes_made()
        self.load_laser_cut_parts_table()

    def load_laser_cut_parts_table_context_menu(self):
        try:
            # Disconnect the existing context menu if already connected
            self.laser_cut_parts_table.customContextMenuRequested.disconnect()
        except TypeError:
            # If not connected, do nothing
            pass

        self.laser_cut_parts_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        menu = QMenu(self)

        material_menu = QMenu("Set Material", menu)
        for material in self.sheet_settings.get_materials():
            action = QAction(material, material_menu)
            action.triggered.connect(
                partial(
                    self.handle_laser_cut_parts_table_context_menu,
                    "SET_MATERIAL",
                    material,
                )
            )
            material_menu.addAction(action)

        thickness_menu = QMenu("Set Thickness", menu)
        for thickness in self.sheet_settings.get_thicknesses():
            action = QAction(thickness, thickness_menu)
            action.triggered.connect(
                partial(
                    self.handle_laser_cut_parts_table_context_menu,
                    "SET_THICKNESS",
                    thickness,
                )
            )
            thickness_menu.addAction(action)

        set_quantity_menu = QMenu("Set Quantity", menu)
        for number in range(10):
            action = QAction(str(number), set_quantity_menu)
            action.triggered.connect(
                partial(
                    self.handle_laser_cut_parts_table_context_menu,
                    "SET_QUANTITY",
                    number,
                )
            )
            set_quantity_menu.addAction(action)

        flow_tag_menu = QMenu("Set Flow Tag", menu)
        for flow_tag in [f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())]:
            action = QAction(flow_tag, flow_tag_menu)
            action.triggered.connect(
                partial(
                    self.handle_laser_cut_parts_table_context_menu,
                    "SET_FLOW_TAG",
                    flow_tag,
                )
            )
            flow_tag_menu.addAction(action)

        add_to_menu = QMenu("Add part to", menu)
        for assembly_widget in self.job_tab.get_active_job_widget().get_all_assembly_widgets():
            action = QAction(assembly_widget.assembly.name, add_to_menu)
            if assembly_widget == self:
                action.setText(action.text() + " - (You are here)")
                action.setEnabled(False)
            action.triggered.connect(
                partial(
                    self.handle_laser_cut_parts_table_context_menu,
                    "ADD_PART_TO_ASSEMBLY",
                    assembly_widget,
                )
            )
            add_to_menu.addAction(action)

        move_to_menu = QMenu("Move part to", menu)
        for assembly_widget in self.job_tab.get_active_job_widget().get_all_assembly_widgets():
            action = QAction(assembly_widget.assembly.name, move_to_menu)
            if assembly_widget == self:
                action.setText(action.text() + " - (You are here)")
                action.setEnabled(False)
            action.triggered.connect(
                partial(
                    self.handle_laser_cut_parts_table_context_menu,
                    "MOVE_PART_TO_ASSEMBLY",
                    assembly_widget,
                )
            )
            move_to_menu.addAction(action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_selected_laser_cut_parts)

        menu.addMenu(material_menu)
        menu.addMenu(thickness_menu)
        menu.addMenu(set_quantity_menu)
        menu.addMenu(flow_tag_menu)
        menu.addMenu(add_to_menu)
        menu.addMenu(move_to_menu)
        menu.addAction(delete_action)

        self.laser_cut_parts_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    def handle_laser_cut_parts_table_context_menu(self, ACTION: str, selection: Union[str, int, float, "AssemblyPlanningWidget"]):
        should_update_assembly_widget_tables = False
        if not (selected_laser_cut_parts := self.get_selected_laser_cut_parts()):
            return
        for laser_cut_part in selected_laser_cut_parts:
            if ACTION == "SET_MATERIAL":
                laser_cut_part.meta_data.material = selection
            elif ACTION == "SET_THICKNESS":
                laser_cut_part.meta_data.gauge = selection
            elif ACTION == "SET_QUANTITY":
                laser_cut_part.inventory_data.quantity = float(selection)
            elif ACTION == "SET_FLOW_TAG":
                laser_cut_part.workspace_data.flowtag = self.workspace_settings.get_flow_tag_by_name(selection)
                laser_cut_part.workspace_data.flowtag_data.load_data(laser_cut_part.workspace_data.flowtag_data.to_dict())
                if tag := laser_cut_part.workspace_data.flowtag.get_tag_with_similar_name("laser"):
                    laser_cut_part.workspace_data.flowtag_data.set_tag_data(
                        tag,
                        "expected_time_to_complete",
                        int(laser_cut_part.meta_data.machine_time * 60),
                    )
                elif tag := laser_cut_part.workspace_data.flowtag.get_tag_with_similar_name("picking"):
                    laser_cut_part.workspace_data.flowtag_data.set_tag_data(tag, "expected_time_to_complete", laser_cut_part.meta_data.weight)
                self.laser_cut_part_table_items[laser_cut_part]["flowtag_data_button"].dropdown.load_ui()
                self.laser_cut_parts_table.resizeRowsToContents()
                self.laser_cut_parts_table.resizeColumnsToContents()
                self.update_laser_cut_parts_table_height()
            elif ACTION == "ADD_PART_TO_ASSEMBLY":
                should_update_assembly_widget_tables = True
                assmebly_widget: AssemblyPlanningWidget = selection
                assembly: Assembly = assmebly_widget.assembly
                new_part = LaserCutPart(laser_cut_part.to_dict(), self.laser_cut_inventory)
                new_part.inventory_data.quantity = laser_cut_part.inventory_data.quantity
                assembly.add_laser_cut_part(new_part)
            elif ACTION == "MOVE_PART_TO_ASSEMBLY":
                should_update_assembly_widget_tables = True
                assmebly_widget: AssemblyPlanningWidget = selection
                assembly: Assembly = assmebly_widget.assembly
                self.assembly.remove_laser_cut_part(laser_cut_part)
                assembly.add_laser_cut_part(laser_cut_part)

        if should_update_assembly_widget_tables:
            selection.update_tables()

        self.load_laser_cut_parts_table()
        self.changes_made()

    # OTHER STUFF
    def get_all_sub_assembly_widgets(self) -> list["AssemblyPlanningWidget"]:
        widgets: list["AssemblyPlanningWidget"] = []
        widgets.extend(self.sub_assembly_widgets)
        for sub_assembly_widget in self.sub_assembly_widgets:
            widgets.extend(sub_assembly_widget.get_all_sub_assembly_widgets())
        return widgets

    def copy_file_with_overwrite(self, source: str, target: str, retry_interval=1, max_retries=10):
        source = os.path.abspath(source)
        target = os.path.abspath(target)

        if os.path.normcase(source) == os.path.normcase(target):
            # Source and target are literally the same path
            return

        retries = 0
        while retries < max_retries:
            try:
                if os.path.exists(target):
                    # Explicitly remove target first
                    os.remove(target)

                shutil.copyfile(source, target)
                return

            except PermissionError as e:
                if hasattr(e, "winerror") and e.winerror == 32:
                    # Windows: file in use
                    retries += 1
                    time.sleep(retry_interval)
                else:
                    raise
            except Exception as e:
                raise e

        raise PermissionError(f"Failed to copy file from {source} to {target} after {max_retries} retries.")

    def file_downloaded(self, response: tuple[str, str, bool]):
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

    def laser_cut_part_delete_file(
        self,
        laser_cut_part: LaserCutPart,
        file_category: str,
        file_path: str,
        file_button: FileButton,
    ):
        if file_category == "bending_files":
            laser_cut_part.workspace_data.bending_files.remove(file_path)
        elif file_category == "welding_files":
            laser_cut_part.workspace_data.welding_files.remove(file_path)
        elif file_category == "cnc_milling_files":
            laser_cut_part.workspace_data.cnc_milling_files.remove(file_path)
        file_button.deleteLater()
        self.changes_made()

    def laser_cut_part_file_dropped(
        self,
        files_layout: QHBoxLayout,
        laser_cut_part: LaserCutPart,
        file_category: Literal["bending_files", "welding_files", "cnc_milling_files"],
        file_paths: list[str],
    ):
        for file_path in file_paths:
            file_ext = file_path.split(".")[-1].upper()
            file_name = os.path.basename(file_path)

            if "dxf" in file_ext.lower() and file_category == "cnc_milling_files":
                laser_cut_part.meta_data.file_name = file_name.split(".")[0]
                dxf_analyzer = DxfAnalyzer(file_path)
                dxf_analyzer.save_preview_image(f"images/{laser_cut_part.meta_data.file_name}.jpeg")
                laser_cut_part.meta_data.image_index = f"{laser_cut_part.meta_data.file_name}.jpeg"
                self.upload_images([laser_cut_part.meta_data.image_index])
                are_you_sure = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Are you sure?",
                    f"The following information is extracted from the DXF file:\n{dxf_analyzer}\n\nDo you want to use these settings?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    self,
                )
                if are_you_sure.exec() == QMessageBox.StandardButton.Yes:
                    laser_cut_part.load_dxf_settings(dxf_analyzer)

                if existing_laser_cut_part := self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.meta_data.file_name):
                    are_you_sure = QMessageBox(
                        QMessageBox.Icon.Question,
                        "Are you sure?",
                        f"The laser cut part '{existing_laser_cut_part.name}' already exists in the inventory. Do you want to use the settings from the existing laser cut part?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                        self,
                    )
                    if are_you_sure.exec() == QMessageBox.StandardButton.Yes:
                        # self.laser_cut_part_table_items[laser_cut_part]["material"].setCurrentText(existing_laser_cut_part.material)
                        # self.laser_cut_part_table_items[laser_cut_part]["thickness"].setCurrentText(existing_laser_cut_part.gauge)
                        laser_cut_part.meta_data.material = existing_laser_cut_part.meta_data.material
                        laser_cut_part.meta_data.gauge = existing_laser_cut_part.meta_data.gauge
                        laser_cut_part.meta_data.machine_time = existing_laser_cut_part.meta_data.machine_time
                        laser_cut_part.meta_data.weight = existing_laser_cut_part.meta_data.weight
                        laser_cut_part.meta_data.surface_area = existing_laser_cut_part.meta_data.surface_area
                        laser_cut_part.meta_data.cutting_length = existing_laser_cut_part.meta_data.cutting_length
                        laser_cut_part.meta_data.piercing_time = existing_laser_cut_part.meta_data.piercing_time
                        laser_cut_part.meta_data.piercing_points = existing_laser_cut_part.meta_data.piercing_points
                        laser_cut_part.meta_data.shelf_number = existing_laser_cut_part.meta_data.shelf_number
                        laser_cut_part.meta_data.sheet_dim = existing_laser_cut_part.meta_data.sheet_dim
                        laser_cut_part.meta_data.part_dim = existing_laser_cut_part.meta_data.part_dim
                        laser_cut_part.meta_data.geofile_name = existing_laser_cut_part.meta_data.geofile_name
                        laser_cut_part.meta_data.modified_date = existing_laser_cut_part.meta_data.modified_date
                        laser_cut_part.meta_data.notes = existing_laser_cut_part.meta_data.notes
                        laser_cut_part.prices.price = existing_laser_cut_part.prices.price
                        laser_cut_part.prices.cost_of_goods = existing_laser_cut_part.prices.cost_of_goods
                        laser_cut_part.prices.bend_cost = existing_laser_cut_part.prices.bend_cost
                        laser_cut_part.prices.labor_cost = existing_laser_cut_part.prices.labor_cost
                        laser_cut_part.primer_data.uses_primer = existing_laser_cut_part.primer_data.uses_primer
                        laser_cut_part.primer_data.primer_name = existing_laser_cut_part.primer_data.primer_name
                        laser_cut_part.primer_data.primer_overspray = existing_laser_cut_part.primer_data.primer_overspray
                        laser_cut_part.prices.cost_for_primer = existing_laser_cut_part.prices.cost_for_primer
                        laser_cut_part.paint_data.uses_paint = existing_laser_cut_part.paint_data.uses_paint
                        laser_cut_part.paint_data.paint_name = existing_laser_cut_part.paint_data.paint_name
                        laser_cut_part.paint_data.paint_overspray = existing_laser_cut_part.paint_data.paint_overspray
                        laser_cut_part.prices.cost_for_paint = existing_laser_cut_part.prices.cost_for_paint
                        laser_cut_part.powder_data.uses_powder = existing_laser_cut_part.powder_data.uses_powder
                        laser_cut_part.powder_data.powder_name = existing_laser_cut_part.powder_data.powder_name
                        laser_cut_part.powder_data.powder_transfer_efficiency = existing_laser_cut_part.powder_data.powder_transfer_efficiency
                        laser_cut_part.prices.cost_for_powder_coating = existing_laser_cut_part.prices.cost_for_powder_coating
                        # with contextlib.suppress(KeyError):
                        self.laser_cut_part_table_items[laser_cut_part]["painting_widget"].update_checkboxes()
                        self.laser_cut_part_table_items[laser_cut_part]["painting_settings_widget"].update_inputs()
                        self.laser_cut_part_table_items[laser_cut_part]["flowtag_data_button"].dropdown.load_ui()
                        # laser_cut_part.bending_files = existing_laser_cut_part.bending_files
                        # laser_cut_part.welding_files = existing_laser_cut_part.welding_files
                        # laser_cut_part.cnc_milling_files = existing_laser_cut_part.cnc_milling_files

                current_row = self.laser_cut_part_table_items[laser_cut_part]["row"]

                image_item = QTableWidgetItem()
                try:
                    if "images" not in laser_cut_part.meta_data.image_index:
                        laser_cut_part.meta_data.image_index = "images/" + laser_cut_part.meta_data.image_index
                    if not laser_cut_part.meta_data.image_index.endswith(".jpeg"):
                        laser_cut_part.meta_data.image_index += ".jpeg"
                    image = QPixmap(laser_cut_part.meta_data.image_index)
                    if image.isNull():
                        image = QPixmap("images/404.jpeg")
                    original_width = image.width()
                    original_height = image.height()
                    new_height = self.laser_cut_parts_table.row_height
                    try:
                        new_width = int(original_width * (new_height / original_height))
                    except ZeroDivisionError:
                        new_width = original_width
                    pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
                    image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
                except Exception as e:
                    image_item.setText(f"Error: {e}")

                self.laser_cut_parts_table.setRowHeight(current_row, new_height)
                self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PICTURE.value, image_item)
                self.laser_cut_parts_table.item(current_row, LaserCutTableColumns.PART_NAME.value).setText(laser_cut_part.meta_data.file_name)
            elif "pdf" in file_ext.lower() and file_category == "bending_files":
                laser_cut_part.meta_data.bend_hits = get_bend_hits(file_path)

            target_dir = os.path.join("data", "workspace", file_ext)
            target_path = os.path.join(target_dir, file_name)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            self.copy_file_with_overwrite(file_path, target_path)
            getattr(laser_cut_part, file_category).append(target_path)
            # if file_category == "bending_files":
            #     laser_cut_part.bending_files.append(target_path)
            # elif file_category == "welding_files":
            #     laser_cut_part.welding_files.append(target_path)
            # elif file_category == "cnc_milling_files":
            #     laser_cut_part.cnc_milling_files.append(target_path)

            self.add_laser_cut_part_drag_file_widget(laser_cut_part, file_category, files_layout, target_path)
        self.upload_files(file_paths)
        self.changes_made()

    def upload_files(self, files: list[str]):
        self.upload_files_thread = WorkspaceUploadWorker(files)
        QThreadPool.globalInstance().start(self.upload_files_thread)

    def upload_images(self, files: list[str]):
        self.upload_images_thread = UploadThread(files)
        self.upload_images_thread.start()

    def get_laser_cut_part_by_name(self, laser_cut_part_name: str) -> LaserCutPart:
        return next(
            (laser_cut_part_name for laser_cut_part_name in self.assembly.laser_cut_parts if laser_cut_part_name.name == laser_cut_part_name),
            None,
        )

    def add_existing_sub_assembly(self):
        if assemblies_to_add := self.get_assemblies_dialog():
            for assembly in assemblies_to_add:
                new_assembly = Assembly(assembly.to_dict(), self.assembly.job)
                self.assembly.add_sub_assembly(new_assembly)
                self.load_sub_assembly(new_assembly)

    def add_sub_assembly(self, new_sub_assembly: Optional[Assembly] = None) -> "AssemblyPlanningWidget":
        if not new_sub_assembly:
            sub_assembly = Assembly({}, self.assembly.job)
            sub_assembly.name = f"Enter Sub Assembly Name{len(self.assembly.sub_assemblies)}"
            self.assembly.add_sub_assembly(sub_assembly)
        else:
            sub_assembly = new_sub_assembly
        sub_assembly.meta_data.color = self.assembly.meta_data.color

        sub_assembly_widget = AssemblyPlanningWidget(sub_assembly, self._parent_widget)
        self.sub_assemblies_toolbox.addItem(sub_assembly_widget, sub_assembly.name, self.assembly.meta_data.color)

        toggle_button = self.sub_assemblies_toolbox.getLastToggleButton()

        name_input = self.sub_assemblies_toolbox.getLastInputBox()
        name_input.textChanged.connect(partial(self.sub_assembly_name_renamed, sub_assembly, name_input))

        name_input.textChanged.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                sub_assembly_widget.pushButton_laser_cut_parts,
                sub_assembly_widget.pushButton_components,
                sub_assembly_widget.pushButton_structural_steel_items,
                sub_assembly_widget.pushButton_sub_assemblies,
            )
        )
        toggle_button.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                sub_assembly_widget.pushButton_laser_cut_parts,
                sub_assembly_widget.pushButton_components,
                sub_assembly_widget.pushButton_structural_steel_items,
                sub_assembly_widget.pushButton_sub_assemblies,
            )
        )

        duplicate_button = self.sub_assemblies_toolbox.getLastDuplicateButton()
        duplicate_button.clicked.connect(partial(self.duplicate_sub_assembly, sub_assembly))

        delete_button = self.sub_assemblies_toolbox.getLastDeleteButton()
        delete_button.clicked.connect(partial(self.delete_sub_assembly, sub_assembly_widget))

        sub_assembly_widget.pushButton_laser_cut_parts.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                sub_assembly_widget.pushButton_laser_cut_parts,
                sub_assembly_widget.pushButton_components,
                sub_assembly_widget.pushButton_structural_steel_items,
                sub_assembly_widget.pushButton_sub_assemblies,
            )
        )
        sub_assembly_widget.pushButton_components.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                sub_assembly_widget.pushButton_laser_cut_parts,
                sub_assembly_widget.pushButton_components,
                sub_assembly_widget.pushButton_structural_steel_items,
                sub_assembly_widget.pushButton_sub_assemblies,
            )
        )
        sub_assembly_widget.pushButton_structural_steel_items.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                sub_assembly_widget.pushButton_laser_cut_parts,
                sub_assembly_widget.pushButton_components,
                sub_assembly_widget.pushButton_structural_steel_items,
                sub_assembly_widget.pushButton_sub_assemblies,
            )
        )
        sub_assembly_widget.pushButton_sub_assemblies.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                sub_assembly_widget.pushButton_laser_cut_parts,
                sub_assembly_widget.pushButton_components,
                sub_assembly_widget.pushButton_structural_steel_items,
                sub_assembly_widget.pushButton_sub_assemblies,
            )
        )

        self.sub_assembly_widgets.append(sub_assembly_widget)

        if self.job_preferences.is_assembly_closed(sub_assembly.name):
            self.sub_assemblies_toolbox.closeLastToolBox()
        else:
            self.sub_assemblies_toolbox.openLastToolBox()

        sub_assembly_widget.pushButton_laser_cut_parts.setChecked(self.job_preferences.is_assembly_laser_cut_closed(sub_assembly.name))
        sub_assembly_widget.laser_cut_widget.setHidden(not self.job_preferences.is_assembly_laser_cut_closed(sub_assembly.name))
        sub_assembly_widget.pushButton_structural_steel_items.setChecked(self.job_preferences.is_structural_steel_closed(sub_assembly.name))
        sub_assembly_widget.structural_steel_items_widget.setHidden(not self.job_preferences.is_structural_steel_closed(sub_assembly.name))
        sub_assembly_widget.pushButton_components.setChecked(self.job_preferences.is_assembly_component_closed(sub_assembly.name))
        sub_assembly_widget.component_widget.setHidden(not self.job_preferences.is_assembly_component_closed(sub_assembly.name))
        sub_assembly_widget.pushButton_sub_assemblies.setChecked(self.job_preferences.is_assembly_sub_assembly_closed(sub_assembly.name))
        sub_assembly_widget.sub_assemblies_widget.setHidden(not self.job_preferences.is_assembly_sub_assembly_closed(sub_assembly.name))

        self.update_context_menu()
        return sub_assembly_widget

    def load_sub_assemblies(self):
        for sub_assembly in self.assembly.sub_assemblies:
            sub_assembly.job = self.assembly.job
            sub_assembly.meta_data.color = self.assembly.meta_data.color
            self.load_sub_assembly(sub_assembly)

    def load_sub_assembly(self, assembly: Assembly):
        sub_assembly_widget = self.add_sub_assembly(assembly)
        sub_assembly_widget.load_sub_assemblies()

    def sub_assembly_name_renamed(self, sub_assembly: Assembly, new_sub_assembly_name: QLineEdit):
        sub_assembly.name = new_sub_assembly_name.text()
        self.update_context_menu()
        self.changes_made()

    def duplicate_sub_assembly(self, sub_assembly: Assembly):
        new_sub_assembly = Assembly(sub_assembly.to_dict(), self.assembly.job)
        new_sub_assembly.name = f"{sub_assembly.name} - (Copy)"
        new_sub_assembly.meta_data.color = self.assembly.meta_data.color
        self.load_sub_assembly(new_sub_assembly)
        self.assembly.add_sub_assembly(new_sub_assembly)
        self.update_context_menu()
        self.changes_made()

    def delete_sub_assembly(self, sub_assembly_widget: "AssemblyPlanningWidget"):
        self.sub_assembly_widgets.remove(sub_assembly_widget)
        self.sub_assemblies_toolbox.removeItem(sub_assembly_widget)
        self.assembly.remove_sub_assembly(sub_assembly_widget.assembly)
        self.update_context_menu()
        self.changes_made()

    def update_tables(self):
        self.load_components_table()
        self.load_laser_cut_parts_table()
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.update_tables()

    def reload_context_menu(self):
        self.load_laser_cut_parts_table_context_menu()
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.reload_context_menu()

    @override
    def changes_made(self):
        self.doubleSpinBox_expected_time_to_complete.setValue(int(self.assembly.get_expected_time_to_complete()))
        super().changes_made()
