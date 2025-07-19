import contextlib
import os
import shutil
import time
from datetime import datetime
from functools import partial
from typing import Optional, Union

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
from ui.custom.assembly_image import AssemblyImage
from ui.custom.assembly_paint_settings_widget import AssemblyPaintSettingsWidget
from ui.custom.assembly_paint_widget import AssemblyPaintWidget
from ui.custom.components_quoting_table_widget import (
    ComponentsQuotingTableWidget,
    ComponentsTableColumns,
)
from ui.custom.file_button import FileButton
from ui.custom.laser_cut_part_paint_settings_widget import (
    LasserCutPartPaintSettingsWidget,
)
from ui.custom.laser_cut_part_paint_widget import LaserCutPartPaintWidget
from ui.custom.laser_cut_parts_quoting_table_widget import (
    LaserCutPartsQuotingTableWidget,
    LaserCutTableColumns,
)
from ui.custom_widgets import AssemblyMultiToolBox
from ui.dialogs.add_component_dialog import AddComponentDialog
from ui.dialogs.add_laser_cut_part_dialog import AddLaserCutPartDialog
from ui.theme import theme_var
from ui.widgets.assembly_widget import AssemblyWidget
from utils.inventory.category import Category
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.threads.upload_thread import UploadThread
from utils.workers.workspace.download_file import WorkspaceDownloadWorker
from utils.workers.workspace.upload_file import WorkspaceUploadWorker
from utils.workspace.assembly import Assembly


class AssemblyQuotingWidget(AssemblyWidget):
    def __init__(self, assembly: Assembly, parent):
        super().__init__(assembly, parent)

        self.sub_assembly_widgets: list[AssemblyQuotingWidget] = []
        self.laser_cut_part_table_items: dict[LaserCutPart, dict[str, QTableWidgetItem | QComboBox | QWidget | int]] = {}
        self.components_table_items: dict[Component, dict[str, QTableWidgetItem | int]] = {}

        self.upload_images_thread: UploadThread | None = None
        self.upload_files_thread: WorkspaceUploadWorker | None = None
        self.download_file_thread: WorkspaceDownloadWorker | None = None

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

        self.label_total_cost_for_assembly.setHidden(False)

        self.assembly_image = AssemblyImage(self)

        if self.assembly.meta_data.assembly_image:
            self.assembly_image.set_new_image(self.assembly.meta_data.assembly_image)

        self.assembly_image.clicked.connect(self.open_assembly_image)

        self.assembly_image.imagePathDropped.connect(self.upload_assembly_image)
        self.assembly_image.customContextMenuRequested.connect(self.assembly_image_show_context_menu)

        self.doubleSpinBox_quantity.setValue(self.assembly.meta_data.quantity)
        self.doubleSpinBox_quantity.valueChanged.connect(self.assembly_quantity_changed)

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
        self.comboBox_assembly_flow_tag.setEnabled(False)

        self.flowtag_data_widget.setHidden(True)

        self.laser_cut_parts_table = LaserCutPartsQuotingTableWidget(self)
        self.laser_cut_parts_table.rowChanged.connect(self.laser_cut_parts_table_changed)
        self.laser_cut_parts_layout.addWidget(self.laser_cut_parts_table)
        self.add_laser_cut_part_button.clicked.connect(self.add_laser_cut_part)
        self.load_laser_cut_parts_table_context_menu()

        self.components_table = ComponentsQuotingTableWidget(self)
        self.components_table.rowChanged.connect(self.components_table_changed)
        self.components_table.imagePasted.connect(self.component_image_pasted)
        self.load_components_table_context_menu()

        self.components_layout.addWidget(self.components_table)

        self.add_component_button.clicked.connect(self.add_component)

        self.add_new_sub_assembly_button.clicked.connect(self.add_sub_assembly)
        self.add_existing_assembly_button.clicked.connect(self.add_existing_sub_assembly)

        self.sub_assemblies_toolbox = AssemblyMultiToolBox(self)
        self.sub_assembly_layout.addWidget(self.sub_assemblies_toolbox)

        self.label_total_cost_for_assembly.setText(f"Total Cost for Assembly: ${self.price_calculator.get_assembly_cost(self.assembly):,.2f}")

    def workspace_settings_changed(self):
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

        # drop_widget = AssemblyFileDropWidget(files_layout, main_widget)
        # drop_widget.fileDropped.connect(self.assembly_file_dropped)
        # main_layout.addWidget(drop_widget)

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
        self.assembly.workspace_data.flowtag = self.workspace_settings.get_flow_tag_by_name(self.comboBox_assembly_flow_tag.currentText())
        self.paint_widget.setVisible(self.assembly.workspace_data.flowtag.contains(["paint", "powder", "coating", "liquid"]))
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
        self.download_file_thread = WorkspaceDownloadWorker([file_path], True)
        self.download_file_thread.signals.success.connect(self.file_downloaded)
        QThreadPool.globalInstance().start(self.download_file_thread)
        # self.download_file_thread.signal.connect(self.file_downloaded)
        # self.download_file_thread.start()
        # self.download_file_thread.wait()
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

            with contextlib.suppress(shutil.SameFileError):
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
        unit_quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.components_table.setItem(current_row, ComponentsTableColumns.UNIT_QUANTITY.value, unit_quantity_item)
        self.components_table_items[component].update({"unit_quantity": unit_quantity_item})

        quantity_item = QTableWidgetItem(f"{(component.quantity * self.assembly.meta_data.quantity):,.2f}")
        quantity_item.setFont(self.tables_font)
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.components_table.setItem(current_row, ComponentsTableColumns.QUANTITY.value, quantity_item)
        self.components_table_items[component].update({"quantity": quantity_item})

        unit_price_item = QTableWidgetItem(f"${(component.price):,.2f}")
        unit_price_item.setFont(self.tables_font)
        unit_price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.components_table.setItem(current_row, ComponentsTableColumns.UNIT_PRICE.value, unit_price_item)
        self.components_table_items[component].update({"unit_price": unit_price_item})

        price_item = QTableWidgetItem(f"${(component.price * component.quantity * self.assembly.meta_data.quantity):,.2f}")
        price_item.setFont(self.tables_font)
        price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.components_table.setItem(current_row, ComponentsTableColumns.PRICE.value, price_item)
        self.components_table_items[component].update({"price": price_item})

        shelf_number_item = QTableWidgetItem(component.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        shelf_number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.components_table.setItem(current_row, ComponentsTableColumns.SHELF_NUMBER.value, shelf_number_item)
        self.components_table_items[component].update({"shelf_number": shelf_number_item})

        notes_item = QTableWidgetItem(component.notes)
        notes_item.setFont(self.tables_font)
        self.components_table.setItem(current_row, ComponentsTableColumns.NOTES.value, notes_item)
        self.components_table_items[component].update({"notes": notes_item})

        self.components_table.blockSignals(False)
        self.update_components_table_height()

    def update_component_table_quantity(self):
        self.components_table.blockSignals(True)
        for component, table_data in self.components_table_items.items():
            table_data["quantity"].setText(str(component.quantity * self.assembly.meta_data.quantity))
        self.components_table.blockSignals(False)

    def update_components_table_prices(self):
        self.components_table.blockSignals(True)
        for component, table_data in self.components_table_items.items():
            table_data["price"].setText(f"${(self.price_calculator.get_component_cost(component) * component.quantity * self.assembly.meta_data.quantity):,.2f}")
        self.components_table.blockSignals(False)

    def components_table_changed(self, row: int):
        component = next(
            (component for component, table_data in self.components_table_items.items() if table_data["row"] == row),
            None,
        )
        if not component:
            return
        component.part_name = self.components_table_items[component]["part_name"].text()
        if self.components_inventory.get_component_by_name(component.name):
            component_inventory_status = f"{component.name} exists in inventory."
            self.set_table_row_color(
                self.components_table,
                self.components_table_items[component]["row"],
                f"{theme_var('background')}",
            )
        else:
            component_inventory_status = f"{component.name} does NOT exist in inventory."
            self.set_table_row_color(
                self.components_table,
                self.components_table_items[component]["row"],
                f"{theme_var('table-red-quantity')}",
            )
        self.components_table_items[component]["part_name"].setToolTip(component_inventory_status)
        self.components_table_items[component]["part_number"].setToolTip(component_inventory_status)
        component.part_number = self.components_table_items[component]["part_number"].text()
        with contextlib.suppress(ValueError):
            component.quantity = float(self.components_table_items[component]["unit_quantity"].text().replace(",", "").strip())
        with contextlib.suppress(ValueError):
            component.price = float(self.components_table_items[component]["unit_price"].text().replace(",", "").replace("$", "").strip())
        component.notes = self.components_table_items[component]["notes"].text()
        component.shelf_number = self.components_table_items[component]["shelf_number"].text()
        self.update_component_table_quantity()
        self.changes_made()

    def get_component_by_name(self, component_name: str) -> Component:
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

    def handle_components_table_context_menu(self, ACTION: str, selection: Union[str, float, int]):
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
        self.update_laser_cut_parts_table_height()

    def add_laser_cut_part_to_table(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts_table.blockSignals(True)

        def create_file_layout(file_types: list[str]) -> tuple[QWidget, QHBoxLayout]:
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

            scroll_area = QScrollArea(self.laser_cut_parts_table)
            scroll_area.setWidget(files_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFixedWidth(100)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            # scroll_area.setStyleSheet("QWidget#scrollAreaWidgetContents{background-color: rgba(20, 20, 20, 0.5);} QAbstractScrollArea{background-color: rgba(20, 20, 20, 0.5);}")

            main_layout.addWidget(scroll_area)

            for file_type in file_types:
                file_list = getattr(laser_cut_part, file_type)
                for file in file_list:
                    self.add_laser_cut_part_drag_file_widget(laser_cut_part, file_type, files_layout, file)
            return main_widget, files_layout

        does_exist_in_inventory = self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.name)
        current_row = self.laser_cut_parts_table.rowCount()
        self.laser_cut_part_table_items.update({laser_cut_part: {}})
        self.laser_cut_part_table_items[laser_cut_part].update({"row": current_row})
        self.laser_cut_parts_table.insertRow(current_row)
        self.laser_cut_parts_table.setRowHeight(current_row, self.laser_cut_parts_table.row_height)

        image_item = QTableWidgetItem()
        try:
            if "images" not in laser_cut_part.meta_data.image_index:
                laser_cut_part.meta_data.image_index = f"images/{laser_cut_part.meta_data.image_index}"
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
        if does_exist_in_inventory:
            laser_cut_part_inventory_status = f"{laser_cut_part.name} exists in inventory.\nProcess: {laser_cut_part.workspace_data.flowtag.get_flow_string()}"
        else:
            laser_cut_part_inventory_status = f"{laser_cut_part.name} does NOT exist in inventory.\nProcess: {laser_cut_part.workspace_data.flowtag.get_flow_string()}"

        part_name_item.setToolTip(laser_cut_part_inventory_status)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PART_NAME.value, part_name_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"part_name": part_name_item})

        # Files
        files_widget, files_layout = create_file_layout(["bending_files", "welding_files", "cnc_milling_files"])
        self.laser_cut_parts_table.setCellWidget(
            current_row,
            LaserCutTableColumns.FILES.value,
            files_widget,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"files": files_widget})

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

        part_dim_item = QTableWidgetItem(f"{laser_cut_part.meta_data.part_dim}\n{laser_cut_part.meta_data.surface_area:,.2f} in²")
        part_dim_item.setFont(self.tables_font)
        part_dim_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.laser_cut_parts_table.setItem(current_row, LaserCutTableColumns.PART_DIM.value, part_dim_item)

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

        # PAINT COST
        table_widget_item_paint_cost = QTableWidgetItem(f"${self.price_calculator.get_laser_cut_part_cost_for_painting(laser_cut_part):,.2f}")
        table_widget_item_paint_cost.setFont(self.tables_font)
        table_widget_item_paint_cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        table_widget_item_paint_cost.setToolTip(
            f"Cost for priming: ${laser_cut_part.cost_for_primer:,.2f}\nCost for painting: ${laser_cut_part.cost_for_paint:,.2f}\nCost for powder coating: ${laser_cut_part.cost_for_powder_coating:,.2f}"
        )
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.PAINT_COST.value,
            table_widget_item_paint_cost,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"paint_cost": table_widget_item_paint_cost})

        # COGS
        table_widget_item_cost_of_goods = QTableWidgetItem(f"${self.price_calculator.get_laser_cut_part_cost_of_goods(laser_cut_part):,.2f}")
        table_widget_item_cost_of_goods.setFont(self.tables_font)
        table_widget_item_cost_of_goods.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.COST_OF_GOODS.value,
            table_widget_item_cost_of_goods,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"cost_of_goods": table_widget_item_cost_of_goods})

        # Bend Cost
        table_widget_item_bend_cost = QTableWidgetItem(f"${laser_cut_part.prices.bend_cost:,.2f}")
        table_widget_item_bend_cost.setFont(self.tables_font)
        table_widget_item_bend_cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.BEND_COST.value,
            table_widget_item_bend_cost,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"bend_cost": table_widget_item_bend_cost})

        # Labor Cost
        table_widget_item_labor_cost = QTableWidgetItem(f"${laser_cut_part.prices.labor_cost:,.2f}")
        table_widget_item_labor_cost.setFont(self.tables_font)
        table_widget_item_labor_cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.LABOR_COST.value,
            table_widget_item_labor_cost,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"labor_cost": table_widget_item_labor_cost})

        # Unit Price
        unit_price = self.price_calculator.get_laser_cut_part_cost(laser_cut_part)
        table_widget_item_unit_price = QTableWidgetItem(f"${unit_price:,.2f}")
        table_widget_item_unit_price.setFont(self.tables_font)
        table_widget_item_unit_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.UNIT_PRICE.value,
            table_widget_item_unit_price,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"unit_price": table_widget_item_unit_price})

        # Price
        table_widget_item_price = QTableWidgetItem(f"${(unit_price * laser_cut_part.inventory_data.quantity * self.assembly.meta_data.quantity):.2f}")
        table_widget_item_price.setFont(self.tables_font)
        table_widget_item_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.PRICE.value,
            table_widget_item_price,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"price": table_widget_item_price})

        shelf_number_item = QTableWidgetItem(laser_cut_part.meta_data.shelf_number)
        shelf_number_item.setFont(self.tables_font)
        self.laser_cut_parts_table.setItem(
            current_row,
            LaserCutTableColumns.SHELF_NUMBER.value,
            shelf_number_item,
        )
        self.laser_cut_part_table_items[laser_cut_part].update({"shelf_number": shelf_number_item})

        if does_exist_in_inventory:
            self.set_table_row_color(self.laser_cut_parts_table, current_row, f"{theme_var('background')}")
        else:
            self.set_table_row_color(
                self.laser_cut_parts_table,
                current_row,
                f"{theme_var('table-red-quantity')}",
            )
        self.laser_cut_parts_table.blockSignals(False)
        self.update_laser_cut_parts_table_height()

    def update_laser_cut_parts_table_quantity(self):
        self.laser_cut_parts_table.blockSignals(True)
        for laser_cut_part, table_data in self.laser_cut_part_table_items.items():
            table_data["quantity"].setText(str(laser_cut_part.inventory_data.quantity * self.assembly.meta_data.quantity))
        self.laser_cut_parts_table.blockSignals(False)

    def update_laser_cut_parts_table_prices(self):
        self.laser_cut_parts_table.blockSignals(True)
        for laser_cut_part, table_data in self.laser_cut_part_table_items.items():
            unit_price = self.price_calculator.get_laser_cut_part_cost(laser_cut_part)
            cost_of_goods = self.price_calculator.get_laser_cut_part_cost_of_goods(laser_cut_part)
            paint_cost = self.price_calculator.get_laser_cut_part_cost_for_painting(laser_cut_part)
            table_data["paint_cost"].setText(f"${paint_cost:,.2f}")
            table_data["paint_cost"].setToolTip(
                f"Cost for priming: ${laser_cut_part.cost_for_primer:,.2f}\nCost for painting: ${laser_cut_part.cost_for_paint:,.2f}\nCost for powder coating: ${laser_cut_part.cost_for_powder_coating:,.2f}"
            )
            table_data["cost_of_goods"].setText(f"${cost_of_goods:,.2f}")
            table_data["labor_cost"].setText(f"${laser_cut_part.prices.labor_cost:,.2f}")
            table_data["bend_cost"].setText(f"${laser_cut_part.prices.bend_cost:,.2f}")
            table_data["unit_price"].setText(f"${unit_price:,.2f}")
            table_data["price"].setText(f"${(unit_price * laser_cut_part.inventory_data.quantity * self.assembly.meta_data.quantity):,.2f}")
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
        with contextlib.suppress(ValueError):
            changed_laser_cut_part.prices.bend_cost = float(self.laser_cut_part_table_items[changed_laser_cut_part]["bend_cost"].text())
        with contextlib.suppress(ValueError):
            changed_laser_cut_part.prices.labor_cost = float(self.laser_cut_part_table_items[changed_laser_cut_part]["labor_cost"].text())
        changed_laser_cut_part.meta_data.shelf_number = self.laser_cut_part_table_items[changed_laser_cut_part]["shelf_number"].text()
        self.update_laser_cut_parts_table_quantity()
        self.changes_made()

    def add_laser_cut_part_drag_file_widget(
        self,
        laser_cut_part: LaserCutPart,
        file_category: str,
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
        self.download_file_thread = WorkspaceDownloadWorker([file_path], True)
        self.download_file_thread.signals.success.connect(self.file_downloaded)
        QThreadPool.globalInstance().start(self.download_file_thread)
        # self.download_file_thread.start()
        # self.download_file_thread.wait()
        if file_path.lower().endswith(".pdf"):
            self.open_pdf(
                self.laser_cut_part_get_all_file_types(laser_cut_part, ".pdf"),
                file_path,
            )

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
        self.laser_cut_parts_table.setFixedHeight((len(self.assembly.laser_cut_parts) + 1) * self.laser_cut_parts_table.row_height)

    def add_laser_cut_part_to_inventory(self, laser_cut_part_to_add: LaserCutPart):
        if laser_cut_part_to_add.recut:
            new_recut_part = LaserCutPart(
                laser_cut_part_to_add.to_dict(),
                self.laser_cut_inventory,
            )
            new_recut_part.add_to_category(self.laser_cut_inventory.get_category("Recut"))
            if existing_recut_part := self.laser_cut_inventory.get_recut_part_by_name(laser_cut_part_to_add.name):
                existing_recut_part.recut_count += 1
                new_recut_part.recut_count = existing_recut_part.recut_count
                new_recut_part.name = f"{new_recut_part.name} - (Recut count: {new_recut_part.recut_count})"
            new_recut_part.meta_data.modified_date = f"{os.getlogin().title()} - Part added from {self.assembly.name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.laser_cut_inventory.add_recut_part(new_recut_part)
            self.laser_cut_inventory.save_laser_cut_part(existing_recut_part)
        elif existing_laser_cut_part := self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part_to_add.name):
            existing_laser_cut_part.inventory_data.quantity += laser_cut_part_to_add.inventory_data.quantity
            existing_laser_cut_part.meta_data.material = laser_cut_part_to_add.meta_data.material
            existing_laser_cut_part.meta_data.gauge = laser_cut_part_to_add.meta_data.gauge
            existing_laser_cut_part.primer_data.uses_primer = laser_cut_part_to_add.primer_data.uses_primer
            existing_laser_cut_part.primer_data.primer_name = laser_cut_part_to_add.primer_data.primer_name
            existing_laser_cut_part.paint_data.uses_paint = laser_cut_part_to_add.paint_data.uses_paint
            existing_laser_cut_part.paint_data.paint_name = laser_cut_part_to_add.paint_data.paint_name
            existing_laser_cut_part.powder_data.uses_powder = laser_cut_part_to_add.powder_data.uses_powder
            existing_laser_cut_part.powder_data.powder_name = laser_cut_part_to_add.powder_data.powder_name
            existing_laser_cut_part.primer_data.primer_overspray = laser_cut_part_to_add.primer_data.primer_overspray
            existing_laser_cut_part.paint_data.paint_overspray = laser_cut_part_to_add.paint_data.paint_overspray
            existing_laser_cut_part.meta_data.modified_date = f"{os.getlogin().title()} - Added {laser_cut_part_to_add.inventory_data.quantity} quantities from {self.assembly.name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.laser_cut_inventory.save_laser_cut_part(existing_laser_cut_part)
        else:
            if not (category := self.laser_cut_inventory.get_category("Uncategorized")):
                category = Category("Uncategorized")
                self.laser_cut_inventory.add_category(category)
            laser_cut_part_to_add.add_to_category(category)
            laser_cut_part_to_add.meta_data.modified_date = (
                f"{os.getlogin().title()} - Part added from {self.assembly.name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            )
            self.laser_cut_inventory.add_laser_cut_part(laser_cut_part_to_add)
        # self.laser_cut_inventory.save_local_copy()
        # self.sync_changes()

    def get_selected_laser_cut_part(self) -> LaserCutPart:
        if selected_laser_cut_parts := self.get_selected_laser_cut_parts():
            return selected_laser_cut_parts[0]
        else:
            return None

    def get_selected_laser_cut_parts(self) -> list[LaserCutPart]:
        selected_laser_cut_parts: list[LaserCutPart] = []
        selected_rows = self.get_selected_laser_cut_part_rows()
        selected_laser_cut_parts.extend(laser_cut_part for laser_cut_part, table_items in self.laser_cut_part_table_items.items() if table_items["row"] in selected_rows)
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
        menu.addMenu(add_to_menu)
        menu.addMenu(move_to_menu)
        menu.addAction(delete_action)

        self.laser_cut_parts_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    def handle_laser_cut_parts_table_context_menu(self, ACTION: str, selection: Union[str, int, float, "AssemblyQuotingWidget"]):
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
            elif ACTION == "ADD_PART_TO_ASSEMBLY":
                should_update_assembly_widget_tables = True
                assmebly_widget: AssemblyQuotingWidget = selection
                assembly: Assembly = assmebly_widget.assembly
                new_part = LaserCutPart(laser_cut_part.to_dict(), self.laser_cut_inventory)
                new_part.inventory_data.quantity = laser_cut_part.inventory_data.quantity
                assembly.add_laser_cut_part(new_part)
            elif ACTION == "MOVE_PART_TO_ASSEMBLY":
                should_update_assembly_widget_tables = True
                assmebly_widget: AssemblyQuotingWidget = selection
                assembly: Assembly = assmebly_widget.assembly
                self.assembly.remove_laser_cut_part(laser_cut_part)
                assembly.add_laser_cut_part(laser_cut_part)

        if should_update_assembly_widget_tables:
            selection.update_tables()

        self.load_laser_cut_parts_table()
        self.changes_made()

    # OTHER STUFF
    def get_all_sub_assembly_widgets(self) -> list["AssemblyQuotingWidget"]:
        widgets: list["AssemblyQuotingWidget"] = []
        widgets.extend(self.sub_assembly_widgets)
        for sub_assembly_widget in self.sub_assembly_widgets:
            widgets.extend(sub_assembly_widget.get_all_sub_assembly_widgets())
        return widgets

    def copy_file_with_overwrite(self, source: str, target: str, retry_interval=1, max_retries=10):
        source = source.replace("/", "\\")
        target = target.replace("/", "\\")
        if target in source:
            return
        retries = 0
        while retries < max_retries:
            try:
                if os.path.exists(target):
                    if os.path.samefile(source, target):
                        os.remove(target)
                shutil.copyfile(source, target)
                return
            except shutil.SameFileError:
                if os.path.samefile(source, target):
                    os.remove(target)
                    shutil.copyfile(source, target)
                    return
            except PermissionError as e:
                if e.winerror == 32:  # File in use error
                    retries += 1
                    time.sleep(retry_interval)
                else:
                    raise
        raise PermissionError(f"Failed to copy file {source} to {target} after {max_retries} retries.")

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
            # elif file_ext == "PDF":
            # self.open_pdf(laser_cut_part, local_path)

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
        file_category: str,
        file_paths: list[str],
    ):
        for file_path in file_paths:
            file_ext = file_path.split(".")[-1].upper()
            file_name = os.path.basename(file_path)

            target_dir = f"data\\workspace\\{file_ext}"
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
        # self.upload_files_thread.start()

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
            self.job_tab.get_active_job_widget().update_prices()

    def add_sub_assembly(self, new_sub_assembly: Optional[Assembly] = None) -> "AssemblyQuotingWidget":
        if not new_sub_assembly:
            sub_assembly = Assembly(
                {},
                self.assembly.job,
            )
            sub_assembly.name = f"Enter Sub Assembly Name{len(self.assembly.sub_assemblies)}"
            self.assembly.add_sub_assembly(sub_assembly)
        else:
            sub_assembly = new_sub_assembly
        sub_assembly.meta_data.color = self.assembly.meta_data.color

        sub_assembly_widget = AssemblyQuotingWidget(sub_assembly, self._parent_widget)
        self.sub_assemblies_toolbox.addItem(sub_assembly_widget, sub_assembly.name, self.assembly.meta_data.color)

        toggle_button = self.sub_assemblies_toolbox.getLastToggleButton()

        name_input: QLineEdit = self.sub_assemblies_toolbox.getLastInputBox()
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

    def delete_sub_assembly(self, sub_assembly_widget: "AssemblyQuotingWidget"):
        self.sub_assembly_widgets.remove(sub_assembly_widget)
        self.sub_assemblies_toolbox.removeItem(sub_assembly_widget)
        self.assembly.remove_sub_assembly(sub_assembly_widget.assembly)
        self.update_context_menu()
        self.changes_made()

    def sync_changes(self):
        self._parent_widget._parent_widget.sync_changes()

    def update_tables(self):
        self.load_components_table()
        self.load_laser_cut_parts_table()
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.update_tables()

    def reload_context_menu(self):
        self.load_laser_cut_parts_table_context_menu()
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.reload_context_menu()

    def update_prices(self):
        self.label_total_cost_for_assembly.setText(f"Total Cost for Assembly: ${self.price_calculator.get_assembly_cost(self.assembly):,.2f}")
        self.update_laser_cut_parts_table_prices()
        self.update_components_table_prices()
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.update_prices()
