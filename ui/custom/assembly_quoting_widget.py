import contextlib
import os
import shutil
from functools import partial
from typing import TYPE_CHECKING

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QCursor, QPixmap
from PyQt6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox,
                             QHBoxLayout, QLineEdit, QMenu, QMessageBox,
                             QPushButton, QScrollArea, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from ui.add_component_dialog import AddComponentDialog
from ui.add_laser_cut_part_dialog import AddLaserCutPartDialog
from ui.custom.assembly_file_drop_widget import AssemblyFileDropWidget
from ui.custom.assembly_image import AssemblyImage
from ui.custom.assembly_paint_settings_widget import \
    AssemblyPaintSettingsWidget
from ui.custom.assembly_paint_widget import AssemblyPaintWidget
from ui.custom.assembly_widget import AssemblyWidget
from ui.custom.components_quoting_table_widget import \
    ComponentsQuotingTableWidget
from ui.custom.file_button import FileButton
from ui.custom.laser_cut_part_file_drop_widget import \
    LaserCutPartFileDropWidget
from ui.custom.laser_cut_part_paint_settings_widget import \
    LasserCutPartPaintSettingsWidget
from ui.custom.laser_cut_part_paint_widget import LaserCutPartPaintWidget
from ui.custom.laser_cut_parts_quoting_table_widget import \
    LaserCutPartsQuotingTableWidget
from ui.custom_widgets import AssemblyMultiToolBox
from ui.image_viewer import QImageViewer
from ui.pdf_viewer import PDFViewer
from utils.colors import darken_color, lighten_color
from utils.components_inventory.component import Component
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.threads.upload_thread import UploadThread
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.threads.workspace_upload_file_thread import WorkspaceUploadThread
from utils.workspace.assembly import Assembly
from utils.workspace.job_preferences import JobPreferences

if TYPE_CHECKING:
    from ui.custom.job_tab import JobTab


class AssemblyPlanningWidget(AssemblyWidget):
    def __init__(self, assembly: Assembly, parent) -> None:
        super(AssemblyPlanningWidget, self).__init__(assembly, parent)
        self.parent: JobTab = parent
        self.assembly = assembly
        self.job_preferences: JobPreferences = self.parent.job_preferences

        self.sheet_settings = self.assembly.group.job.sheet_settings
        self.workspace_settings = self.assembly.group.job.workspace_settings
        self.components_inventory = self.assembly.group.job.components_inventory
        self.laser_cut_inventory = self.assembly.group.job.laser_cut_inventory

        self.sub_assembly_widgets: list[AssemblyPlanningWidget] = []
        self.laser_cut_part_table_items: dict[LaserCutPart, dict[str, QTableWidgetItem | QComboBox | QWidget | int]] = {}
        self.components_table_items: dict[Component, dict[str, QTableWidgetItem | int]] = {}

        self.upload_images_thread: UploadThread = None
        self.upload_files_thread: WorkspaceUploadThread = None
        self.download_file_thread: WorkspaceDownloadFile = None

        self.load_ui()
        self.load_laser_cut_parts_table()
        self.load_components_table()

    def load_ui(self):
        self.assembly_widget = self.findChild(QWidget, "assembly_widget")
        self.assembly_widget.setStyleSheet(
            """
QWidget#assembly_widget {
border: 1px solid %(base_color)s;
border-bottom-left-radius: 10px;
border-bottom-right-radius: 10px;
border-top-right-radius: 0px;
border-top-left-radius: 0px;
}"""
            % {"base_color": self.assembly.group.color}
        )
        self.verticalLayout_14.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_3.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_10.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pushButton_laser_cut_parts = self.findChild(QPushButton, "pushButton_laser_cut_parts")
        self.pushButton_laser_cut_parts.setCursor(Qt.CursorShape.PointingHandCursor)
        self.laser_cut_widget = self.findChild(QWidget, "laser_cut_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_laser_cut_parts, self.laser_cut_widget)

        self.pushButton_components = self.findChild(QPushButton, "pushButton_components")
        self.pushButton_components.setCursor(Qt.CursorShape.PointingHandCursor)
        self.component_widget = self.findChild(QWidget, "component_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_components, self.component_widget)

        self.pushButton_sub_assemblies = self.findChild(QPushButton, "pushButton_sub_assemblies")
        self.pushButton_sub_assemblies.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sub_assemblies_widget = self.findChild(QWidget, "sub_assemblies_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_sub_assemblies, self.sub_assemblies_widget)

        self.image_layout = self.findChild(QVBoxLayout, "image_layout")

        self.assembly_files_layout = self.findChild(QHBoxLayout, "assembly_files_layout")
        assembly_files_widget, assembly_files_layout = self.create_assembly_file_layout()
        self.assembly_files_layout.addWidget(assembly_files_widget)

        self.assembly_image = AssemblyImage(self)

        if self.assembly.assembly_image:
            self.assembly_image.set_new_image(self.assembly.assembly_image)

        self.assembly_image.clicked.connect(self.open_assembly_image)

        self.assembly_image.imagePathDropped.connect(self.upload_assembly_image)
        self.assembly_image.customContextMenuRequested.connect(self.assembly_image_show_context_menu)

        self.paint_widget = self.findChild(QWidget, "paint_widget")
        self.paint_widget.setVisible(self.assembly.flow_tag.has_tag("Painting"))

        self.assembly_setting_paint_widget = AssemblyPaintSettingsWidget(self.assembly, self)
        self.assembly_setting_paint_widget.settingsChanged.connect(self.changes_made)
        self.assembly_paint_widget = AssemblyPaintWidget(self.assembly, self.assembly_setting_paint_widget, self)
        self.assembly_paint_widget.settingsChanged.connect(self.changes_made)
        self.paint_layout = self.findChild(QHBoxLayout, "paint_layout")
        self.paint_layout.addWidget(self.assembly_paint_widget)
        self.paint_layout.addWidget(self.assembly_setting_paint_widget)

        self.image_layout.addWidget(self.assembly_image)

        self.comboBox_assembly_flow_tag = self.findChild(QComboBox, "comboBox_assembly_flow_tag")
        if str(self.assembly.flow_tag.name):
            self.comboBox_assembly_flow_tag.addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_assembly_flow_tags().values())])
        else:
            self.comboBox_assembly_flow_tag.addItems(["Select flow tag"] + [f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_assembly_flow_tags().values())])
        self.comboBox_assembly_flow_tag.setCurrentText(str(self.assembly.flow_tag))
        self.comboBox_assembly_flow_tag.wheelEvent = lambda event: None
        self.comboBox_assembly_flow_tag.currentTextChanged.connect(self.assembly_flow_tag_changed)

        self.laser_cut_parts_layout = self.findChild(QVBoxLayout, "laser_cut_parts_layout")
        self.laser_cut_parts_table = LaserCutPartsQuotingTableWidget(self)
        self.laser_cut_parts_table.rowChanged.connect(self.laser_cut_parts_table_changed)
        self.laser_cut_parts_layout.addWidget(self.laser_cut_parts_table)
        self.add_laser_cut_part_button = self.findChild(QPushButton, "add_laser_cut_part_button")
        self.add_laser_cut_part_button.clicked.connect(self.add_laser_cut_part)
        self.load_laser_cut_parts_table_context_menu()

        self.components_layout = self.findChild(QVBoxLayout, "components_layout")
        self.components_table = ComponentsQuotingTableWidget(self)
        self.components_table.rowChanged.connect(self.components_table_changed)
        self.components_table.imagePasted.connect(self.component_image_pasted)
        self.load_components_table_context_menu()

        self.components_layout.addWidget(self.components_table)

        self.add_component_button = self.findChild(QPushButton, "add_component_button")
        self.add_component_button.clicked.connect(self.add_component)

        self.sub_assembly_layout = self.findChild(QVBoxLayout, "sub_assembly_layout")
        self.sub_assembly_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.add_sub_assembly_button = self.findChild(QPushButton, "add_sub_assembly_button")
        self.add_sub_assembly_button.clicked.connect(self.add_sub_assembly)

        self.sub_assemblies_toolbox = AssemblyMultiToolBox(self)
        self.sub_assembly_layout.addWidget(self.sub_assemblies_toolbox)

        # ! JUST FOR TESTING REMOVE IN PRODUCTION
        # self.splitter.setSizes([0, 0, 0, 0])
        # self.splitter.setSizes([0, 1, 0, 0])
        # self.splitter.setSizes([0, 1, 1, 0])
        # self.splitter.setStretchFactor(0, 1)
        # self.splitter.setStretchFactor(1, 0)

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = self.assembly.group.color
        hover_color: str = lighten_color(base_color)
        pressed_color: str = darken_color(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            """
QPushButton#assembly_button_drop_menu {
    border: 1px solid rgba(71, 71, 71, 110);
    background-color: rgba(71, 71, 71, 110);
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
    color: #EAE9FC;
    text-align: left;
}

QPushButton:hover#assembly_button_drop_menu {
    background-color: rgba(76, 76, 76, 110);
    border: 1px solid %(base_color)s;
}

QPushButton:pressed#assembly_button_drop_menu {
    background-color: %(base_color)s;
    color: #EAE9FC;
}

QPushButton:!checked#assembly_button_drop_menu {
    color: #8C8C8C;
}

QPushButton:!checked:pressed#assembly_button_drop_menu {
    color: #EAE9FC;
}

QPushButton:checked#assembly_button_drop_menu {
    color: #EAE9FC;
    border-color: %(base_color)s;
    background-color: %(base_color)s;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}

QPushButton:checked:hover#assembly_button_drop_menu {
    background-color: %(hover_color)s;
}

QPushButton:checked:pressed#assembly_button_drop_menu {
    color: #EAE9FC;
    background-color: %(pressed_color)s;
}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": pressed_color,
            }
        )
        widget.setObjectName("assembly_widget_drop_menu")
        widget.setStyleSheet(
            """QWidget#assembly_widget_drop_menu{
            border: 1px solid %(base_color)s;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            };
            """
            % {"base_color": base_color}
        )

    def workspace_settings_changed(self):
        assembly_selected_flow_tag = self.comboBox_assembly_flow_tag.currentText()
        self.comboBox_assembly_flow_tag.blockSignals(True)
        self.comboBox_assembly_flow_tag.clear()
        self.comboBox_assembly_flow_tag.addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_assembly_flow_tags().values())])
        self.comboBox_assembly_flow_tag.setCurrentText(assembly_selected_flow_tag)
        self.comboBox_assembly_flow_tag.blockSignals(False)
        for _, table_items in self.laser_cut_part_table_items.items():
            selected_flow_tag = table_items["flow_tag"].currentText()
            table_items["flow_tag"].blockSignals(True)
            table_items["flow_tag"].clear()
            table_items["flow_tag"].addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())])
            table_items["flow_tag"].setCurrentText(selected_flow_tag)
            table_items["flow_tag"].blockSignals(False)
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.workspace_settings_changed()
        self.changes_made()

    # ASSEMBLY STUFF
    def upload_assembly_image(self, path_to_image: str):
        file_name = os.path.basename(path_to_image)

        target_path = os.path.join("images", file_name)

        shutil.copyfile(path_to_image, target_path)

        self.assembly_image.set_new_image(target_path)
        self.assembly.assembly_image = target_path
        self.upload_images([target_path])
        self.changes_made()

    def assembly_image_show_context_menu(self):
        contextMenu = QMenu(self)
        delete_action = contextMenu.addAction("Clear image")
        paste_action = contextMenu.addAction("Paste image from clipboard")

        action = contextMenu.exec(QCursor.pos())

        if action == delete_action:
            self.assembly.assembly_image = None
            self.assembly_image.clear_image()
            self.changes_made()
        elif action == paste_action:
            clipboard = QApplication.clipboard()
            image = clipboard.image()
            if not image.isNull():
                temp_path = f"images/{self.assembly.name}.png"
                image.save(temp_path)
                self.upload_assembly_image(temp_path)

    def assembly_flow_tag_changed(self):
        self.assembly.flow_tag = self.workspace_settings.get_flow_tag_by_name(self.comboBox_assembly_flow_tag.currentText())
        self.paint_widget.setVisible(self.assembly.flow_tag.has_tag("Painting"))
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

        for file in self.assembly.assembly_files:
            self.add_assembly_drag_file_widget(files_layout, file)

        return main_widget, files_layout

    def assembly_file_clicked(self, file_path: str):
        self.download_file_thread = WorkspaceDownloadFile([file_path], True)
        self.download_file_thread.signal.connect(self.file_downloaded)
        self.download_file_thread.start()
        self.download_file_thread.wait()
        if file_path.lower().endswith(".pdf"):
            self.open_pdf(self.assembly_get_all_file_types(".pdf"), file_path)

    def assembly_delete_file(self, file_path: str, file_button: FileButton):
        self.assembly.assembly_files.remove(file_path)
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
                shutil.copyfile(file_path, target_path)
                self.assembly.assembly_files.append(target_path)
                self.add_assembly_drag_file_widget(files_layout, target_path)
        self.upload_files(file_paths)
        self.changes_made()

    def assembly_get_all_file_types(self, file_ext: str) -> list[str]:
        files: set[str] = {file for file in self.assembly.assembly_files if file.lower().endswith(file_ext)}
        return list(files)

    def open_assembly_image(self):
        self.open_image(self.assembly.assembly_image, self.assembly.name)

    def open_image(self, path: str, title: str) -> None:
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def open_pdf(self, files, file_path: str):
        pdf_viewer = PDFViewer(files, file_path, self)
        pdf_viewer.show()

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

    def component_image_pasted(self, image_file_name: str, row: int) -> None:
        component_name = self.components_table.item(row, self.components_table.part_number_column).text()
        component = self.get_component_by_name(component_name)

        target_path = os.path.join("images", f"{component.name}.png")

        shutil.copyfile(image_file_name, target_path)

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
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.components_table.setRowHeight(current_row, new_height)

        self.components_table.setItem(current_row, self.components_table.image_column, image_item)

        part_name_item = QTableWidgetItem(component.part_name)
        if self.components_inventory.get_component_by_name(component.name):
            component_inventory_status = f"{component.name} exists in inventory."
            self.set_table_row_color(self.components_table, current_row, "#141414")
        else:
            component_inventory_status = f"{component.name} does NOT exist in inventory."
            self.set_table_row_color(self.components_table, current_row, "#3F1E25")
        part_name_item.setToolTip(component_inventory_status)
        self.components_table.setItem(current_row, self.components_table.part_name_column, part_name_item)
        self.components_table_items[component].update({"part_name": part_name_item})

        part_number_item = QTableWidgetItem(component.part_number)
        part_number_item.setToolTip(component_inventory_status)
        self.components_table.setItem(current_row, self.components_table.part_number_column, part_number_item)
        self.components_table_items[component].update({"part_number": part_number_item})

        quantity_item = QTableWidgetItem(str(component.quantity))
        self.components_table.setItem(current_row, self.components_table.quantity_column, quantity_item)
        self.components_table_items[component].update({"quantity": quantity_item})

        notes_item = QTableWidgetItem(component.notes)
        notes_item.setToolTip(component.notes)
        self.components_table.setItem(current_row, self.components_table.notes_column, notes_item)
        self.components_table_items[component].update({"notes": notes_item})

        shelf_number_item = QTableWidgetItem(component.shelf_number)
        self.components_table.setItem(current_row, self.components_table.shelf_number_column, shelf_number_item)
        self.components_table_items[component].update({"shelf_number": shelf_number_item})
        self.components_table.blockSignals(False)
        self.update_components_table_height()

    def components_table_changed(self):
        if not (component := self.get_selected_component()):
            return
        component.part_name = self.components_table_items[component]["part_name"].text()
        if self.components_inventory.get_component_by_name(component.name):
            component_inventory_status = f"{component.name} exists in inventory."
            self.set_table_row_color(self.components_table, self.components_table_items[component]["row"], "#141414")
        else:
            component_inventory_status = f"{component.name} does NOT exist in inventory."
            self.set_table_row_color(self.components_table, self.components_table_items[component]["row"], "#3F1E25")
        self.components_table_items[component]["part_name"].setToolTip(component_inventory_status)
        self.components_table_items[component]["part_number"].setToolTip(component_inventory_status)
        component.part_number = self.components_table_items[component]["part_number"].text()
        with contextlib.suppress(ValueError):
            component.quantity = float(self.components_table_items[component]["quantity"].text())
        component.notes = self.components_table_items[component]["notes"].text()
        component.shelf_number = self.components_table_items[component]["shelf_number"].text()
        self.changes_made()

    def get_component_by_name(self, component_name: str) -> Component:
        return next(
            (component for component in self.assembly.components if component.name == component_name),
            None,
        )

    def add_component(self):
        add_item_dialog = AddComponentDialog(self)
        if add_item_dialog.exec():
            if component := add_item_dialog.get_selected_component():
                new_component = Component(component.name, component.to_dict(), self.components_inventory)
            else:
                new_component = Component(add_item_dialog.get_part_number(), {"part_name": add_item_dialog.get_name()}, self.components_inventory)
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
                action.triggered.connect(partial(self.handle_components_table_context_menu, "SET_QUANTITY", number))
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
            if not "images" in laser_cut_part.image_index:
                laser_cut_part.image_index = "images/" + laser_cut_part.image_index
            if not laser_cut_part.image_index.endswith(".jpeg"):
                laser_cut_part.image_index += ".jpeg"
            image = QPixmap(laser_cut_part.image_index)
            if image.isNull():
                image = QPixmap("images/404.jpeg")
            original_width = image.width()
            original_height = image.height()
            new_height = self.laser_cut_parts_table.row_height
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
        except Exception as e:
            image_item.setText(f"Error: {e}")

        self.laser_cut_parts_table.setRowHeight(current_row, new_height)
        self.laser_cut_parts_table.setItem(current_row, self.laser_cut_parts_table.image_column, image_item)

        part_name_item = QTableWidgetItem(laser_cut_part.name)
        if self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.name):
            laser_cut_part_inventory_status = f"{laser_cut_part.name} exists in inventory."
            self.set_table_row_color(self.laser_cut_parts_table, current_row, "#141414")
        else:
            laser_cut_part_inventory_status = f"{laser_cut_part.name} does NOT exist in inventory."
            self.set_table_row_color(self.laser_cut_parts_table, current_row, "#3F1E25")

        part_name_item.setToolTip(laser_cut_part_inventory_status)
        self.laser_cut_parts_table.setItem(current_row, self.laser_cut_parts_table.part_name_column, part_name_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"part_name": part_name_item})

        # Bending files
        bending_files_widget, bending_files_layout = create_file_layout("bending_files")
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.bending_files_column, bending_files_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"bending_files": bending_files_widget})

        # Welding files
        welding_files_widget, welding_files_layout = create_file_layout("welding_files")
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.welding_files_column, welding_files_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"welding_files": welding_files_widget})

        # CNC milling files
        cnc_milling_files_widget, cnc_milling_files_layout = create_file_layout("cnc_milling_files")
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.cnc_milling_files_column, cnc_milling_files_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"cnc_milling_files": cnc_milling_files_widget})

        materials_combobox = QComboBox(self)
        materials_combobox.setStyleSheet("border-radius: 0px;")
        materials_combobox.wheelEvent = lambda event: None
        materials_combobox.addItems(self.sheet_settings.get_materials())
        materials_combobox.setCurrentText(laser_cut_part.material)
        materials_combobox.currentTextChanged.connect(self.laser_cut_parts_table_changed)
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.material_column, materials_combobox)
        self.laser_cut_part_table_items[laser_cut_part].update({"material": materials_combobox})

        thicknesses_combobox = QComboBox(self)
        thicknesses_combobox.setStyleSheet("border-radius: 0px;")
        thicknesses_combobox.wheelEvent = lambda event: None
        thicknesses_combobox.addItems(self.sheet_settings.get_thicknesses())
        thicknesses_combobox.setCurrentText(laser_cut_part.gauge)
        thicknesses_combobox.currentTextChanged.connect(self.laser_cut_parts_table_changed)
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.thickness_column, thicknesses_combobox)
        self.laser_cut_part_table_items[laser_cut_part].update({"thickness": thicknesses_combobox})

        quantity_item = QTableWidgetItem(str(laser_cut_part.quantity))
        quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.laser_cut_parts_table.setItem(current_row, self.laser_cut_parts_table.quantity_column, quantity_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"quantity": quantity_item})

        painting_settings_widget = LasserCutPartPaintSettingsWidget(laser_cut_part, self.laser_cut_parts_table)
        painting_settings_widget.settingsChanged.connect(self.changes_made)
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.paint_settings_column, painting_settings_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"painting_settings_widget": painting_settings_widget})

        painting_widget = LaserCutPartPaintWidget(laser_cut_part, painting_settings_widget, self.laser_cut_parts_table)
        painting_widget.settingsChanged.connect(self.changes_made)
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.painting_column, painting_widget)
        self.laser_cut_part_table_items[laser_cut_part].update({"painting_widget": painting_widget})

        flow_tag_combobox = QComboBox(self)
        flow_tag_combobox.setStyleSheet("border-radius: 0px;")
        flow_tag_combobox.wheelEvent = lambda event: None
        if str(laser_cut_part.flow_tag.name):
            flow_tag_combobox.addItems([f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())])
        else:
            flow_tag_combobox.addItems(["Select flow tag"] + [f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())])
        flow_tag_combobox.setCurrentText(str(laser_cut_part.flow_tag))
        flow_tag_combobox.currentTextChanged.connect(partial(self.laser_cut_part_flow_tag_changed, laser_cut_part, flow_tag_combobox))
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.flow_tag_column, flow_tag_combobox)
        self.laser_cut_part_table_items[laser_cut_part].update({"flow_tag": flow_tag_combobox})

        expected_time_to_complete = QDoubleSpinBox(self)
        self.laser_cut_parts_table.setCellWidget(current_row, self.laser_cut_parts_table.expected_time_to_complete_column, expected_time_to_complete)
        self.laser_cut_part_table_items[laser_cut_part].update({"expected_time_to_complete": expected_time_to_complete})

        notes_item = QTableWidgetItem(laser_cut_part.notes)
        self.laser_cut_parts_table.setItem(current_row, self.laser_cut_parts_table.notes_column, notes_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"notes": notes_item})

        shelf_number_item = QTableWidgetItem(laser_cut_part.shelf_number)
        self.laser_cut_parts_table.setItem(current_row, self.laser_cut_parts_table.shelf_number_column, shelf_number_item)
        self.laser_cut_part_table_items[laser_cut_part].update({"shelf_number": shelf_number_item})
        self.laser_cut_parts_table.blockSignals(False)
        self.update_laser_cut_parts_table_height()

    def laser_cut_parts_table_changed(self):
        if not (laser_cut_part := self.get_selected_laser_cut_part()):
            return
        laser_cut_part.name = self.laser_cut_part_table_items[laser_cut_part]["part_name"].text()
        if self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.name):
            laser_cut_part_inventory_status = f"{laser_cut_part.name} exists in inventory."
            self.set_table_row_color(self.laser_cut_parts_table, self.laser_cut_part_table_items[laser_cut_part]["row"], "#141414")
        else:
            laser_cut_part_inventory_status = f"{laser_cut_part.name} does NOT exist in inventory."
            self.set_table_row_color(self.laser_cut_parts_table, self.laser_cut_part_table_items[laser_cut_part]["row"], "#3F1E25")
        self.laser_cut_part_table_items[laser_cut_part]["part_name"].setToolTip(laser_cut_part_inventory_status)
        laser_cut_part.material = self.laser_cut_part_table_items[laser_cut_part]["material"].currentText()
        laser_cut_part.gauge = self.laser_cut_part_table_items[laser_cut_part]["thickness"].currentText()
        with contextlib.suppress(ValueError):
            laser_cut_part.quantity = float(self.laser_cut_part_table_items[laser_cut_part]["quantity"].text())
        laser_cut_part.notes = self.laser_cut_part_table_items[laser_cut_part]["notes"].text()
        laser_cut_part.shelf_number = self.laser_cut_part_table_items[laser_cut_part]["shelf_number"].text()
        self.changes_made()

    def laser_cut_part_flow_tag_changed(self, laser_cut_part: LaserCutPart, flow_tag_combobox: QComboBox):
        laser_cut_part.flow_tag = self.workspace_settings.get_flow_tag_by_name(flow_tag_combobox.currentText())
        self.changes_made()

    def add_laser_cut_part_drag_file_widget(self, laser_cut_part: LaserCutPart, file_category: str, files_layout: QHBoxLayout, file_path: str):
        file_button = FileButton(f"{os.getcwd()}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.laser_cut_part_file_clicked, laser_cut_part, file_path))
        file_button.deleteFileClicked.connect(partial(self.laser_cut_part_delete_file, laser_cut_part, file_category, file_path, file_button))
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)
        self.laser_cut_parts_table.resizeColumnsToContents()

    def update_laser_cut_parts_table_height(self):
        self.laser_cut_parts_table.setFixedHeight((len(self.assembly.laser_cut_parts) + 1) * self.laser_cut_parts_table.row_height)

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
            self.open_pdf(self.laser_cut_part_get_all_file_types(laser_cut_part, ".pdf"), file_path)

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
        if self.laser_cut_parts_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
            return
        self.laser_cut_parts_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        menu = QMenu(self)

        material_menu = QMenu("Set Material", menu)
        for material in self.sheet_settings.get_materials():
            action = QAction(material, material_menu)
            action.triggered.connect(partial(self.handle_laser_cut_parts_table_context_menu, "SET_MATERIAL", material))
            material_menu.addAction(action)

        thickness_menu = QMenu("Set Thickness", menu)
        for thickness in self.sheet_settings.get_thicknesses():
            action = QAction(thickness, thickness_menu)
            action.triggered.connect(partial(self.handle_laser_cut_parts_table_context_menu, "SET_THICKNESS", thickness))
            thickness_menu.addAction(action)

        set_quantity_menu = QMenu("Set Quantity", menu)
        for number in range(10):
            action = QAction(str(number), set_quantity_menu)
            action.triggered.connect(partial(self.handle_laser_cut_parts_table_context_menu, "SET_QUANTITY", number))
            set_quantity_menu.addAction(action)

        flow_tag_menu = QMenu("Set Flow Tag", menu)
        for flow_tag in [f"{flow_tag}" for flow_tag in list(self.workspace_settings.get_all_laser_cut_part_flow_tags().values())]:
            action = QAction(flow_tag, flow_tag_menu)
            action.triggered.connect(partial(self.handle_laser_cut_parts_table_context_menu, "SET_FLOW_TAG", flow_tag))
            flow_tag_menu.addAction(action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_selected_laser_cut_parts)

        menu.addMenu(material_menu)
        menu.addMenu(thickness_menu)
        menu.addMenu(set_quantity_menu)
        menu.addMenu(flow_tag_menu)
        menu.addAction(delete_action)

        self.laser_cut_parts_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    def handle_laser_cut_parts_table_context_menu(self, ACTION: str, selection: str | int | float):
        if not (selected_laser_cut_parts := self.get_selected_laser_cut_parts()):
            return
        for laser_cut_part in selected_laser_cut_parts:
            if ACTION == "SET_MATERIAL":
                laser_cut_part.material = selection
            elif ACTION == "SET_THICKNESS":
                laser_cut_part.gauge = selection
            elif ACTION == "SET_QUANTITY":
                laser_cut_part.quantity = float(selection)
            elif ACTION == "SET_FLOW_TAG":
                laser_cut_part.flow_tag = self.workspace_settings.get_flow_tag_by_name(selection)
        self.load_laser_cut_parts_table()
        self.changes_made()

    # OTHER STUFF
    def file_downloaded(self, file_ext: str, file_name: str, open_when_done: bool):
        if file_ext is None:
            msg = QMessageBox(QMessageBox.Icon.Critical, "Error", f"Failed to download file: {file_name}", QMessageBox.StandardButton.Ok, self)
            msg.show()
            return
        if open_when_done:
            if file_ext in {"PNG", "JPG", "JPEG"}:
                local_path = f"data/workspace/{file_ext}/{file_name}"
                self.open_image(local_path, file_name)
            # elif file_ext == "PDF":
            # self.open_pdf(laser_cut_part, local_path)

    def laser_cut_part_delete_file(self, laser_cut_part: LaserCutPart, file_category: str, file_path: str, file_button: FileButton):
        if file_category == "bending_files":
            laser_cut_part.bending_files.remove(file_path)
        elif file_category == "welding_files":
            laser_cut_part.welding_files.remove(file_path)
        elif file_category == "cnc_milling_files":
            laser_cut_part.cnc_milling_files.remove(file_path)
        file_button.deleteLater()
        self.changes_made()

    def laser_cut_part_file_dropped(self, files_layout: QHBoxLayout, laser_cut_part: LaserCutPart, file_category: str, file_paths: list[str]):
        for file_path in file_paths:
            file_ext = file_path.split(".")[-1].upper()
            file_name = os.path.basename(file_path)

            target_dir = f"data\\workspace\\{file_ext}"
            target_path = os.path.join(target_dir, file_name)

            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            shutil.copyfile(file_path, target_path)
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
        self.upload_files_thread = WorkspaceUploadThread(files)
        self.upload_files_thread.start()

    def upload_images(self, files: list[str]):
        self.upload_images_thread = UploadThread(files)
        self.upload_images_thread.start()

    def get_laser_cut_part_by_name(self, laser_cut_part_name: str) -> LaserCutPart:
        return next(
            (laser_cut_part_name for laser_cut_part_name in self.assembly.laser_cut_parts if laser_cut_part_name.name == laser_cut_part_name),
            None,
        )

    def add_laser_cut_part(self):
        add_item_dialog = AddLaserCutPartDialog(self)
        if add_item_dialog.exec():
            if laser_cut_part := add_item_dialog.get_selected_laser_cut_part():
                new_laser_cut_part = LaserCutPart(laser_cut_part.name, laser_cut_part.to_dict(), self.laser_cut_inventory)
            else:
                new_laser_cut_part = LaserCutPart(add_item_dialog.get_name(), {}, self.laser_cut_inventory)
            new_laser_cut_part.quantity = add_item_dialog.get_current_quantity()
            self.assembly.add_laser_cut_part(new_laser_cut_part)
            self.add_laser_cut_part_to_table(new_laser_cut_part)

    def add_sub_assembly(self, new_sub_assembly: Assembly = None) -> "AssemblyPlanningWidget":
        if not new_sub_assembly:
            sub_assembly = Assembly(f"Enter Sub Assembly Name{len(self.assembly.sub_assemblies)}", {}, self.assembly.group)
            self.assembly.add_sub_assembly(sub_assembly)
        else:
            sub_assembly = new_sub_assembly

        sub_assembly_widget = AssemblyPlanningWidget(sub_assembly, self.parent)
        self.sub_assemblies_toolbox.addItem(sub_assembly_widget, sub_assembly.name, sub_assembly.group.color)

        toggle_button = self.sub_assemblies_toolbox.getLastToggleButton()

        name_input: QLineEdit = self.sub_assemblies_toolbox.getLastInputBox()
        name_input.textChanged.connect(partial(self.sub_assembly_name_renamed, sub_assembly, name_input))

        name_input.textChanged.connect(partial(self.job_preferences.assembly_toolbox_toggled, name_input, toggle_button, sub_assembly_widget.pushButton_laser_cut_parts, sub_assembly_widget.pushButton_components, sub_assembly_widget.pushButton_sub_assemblies))
        toggle_button.clicked.connect(partial(self.job_preferences.assembly_toolbox_toggled, name_input, toggle_button, sub_assembly_widget.pushButton_laser_cut_parts, sub_assembly_widget.pushButton_components, sub_assembly_widget.pushButton_sub_assemblies))

        duplicate_button = self.sub_assemblies_toolbox.getLastDuplicateButton()
        duplicate_button.clicked.connect(partial(self.duplicate_sub_assembly, sub_assembly))

        delete_button = self.sub_assemblies_toolbox.getLastDeleteButton()
        delete_button.clicked.connect(partial(self.delete_sub_assembly, sub_assembly_widget))

        sub_assembly_widget.pushButton_laser_cut_parts.clicked.connect(partial(self.job_preferences.assembly_toolbox_toggled, name_input, toggle_button, sub_assembly_widget.pushButton_laser_cut_parts, sub_assembly_widget.pushButton_components, sub_assembly_widget.pushButton_sub_assemblies))
        sub_assembly_widget.pushButton_components.clicked.connect(partial(self.job_preferences.assembly_toolbox_toggled, name_input, toggle_button, sub_assembly_widget.pushButton_laser_cut_parts, sub_assembly_widget.pushButton_components, sub_assembly_widget.pushButton_sub_assemblies))
        sub_assembly_widget.pushButton_sub_assemblies.clicked.connect(partial(self.job_preferences.assembly_toolbox_toggled, name_input, toggle_button, sub_assembly_widget.pushButton_laser_cut_parts, sub_assembly_widget.pushButton_components, sub_assembly_widget.pushButton_sub_assemblies))

        self.sub_assembly_widgets.append(sub_assembly_widget)

        if self.job_preferences.is_assembly_closed(sub_assembly.name):
            self.sub_assemblies_toolbox.closeLastToolBox()

        sub_assembly_widget.pushButton_laser_cut_parts.setChecked(self.job_preferences.is_assembly_laser_cut_closed(sub_assembly.name))
        sub_assembly_widget.laser_cut_widget.setHidden(not self.job_preferences.is_assembly_laser_cut_closed(sub_assembly.name))
        sub_assembly_widget.pushButton_components.setChecked(self.job_preferences.is_assembly_component_closed(sub_assembly.name))
        sub_assembly_widget.component_widget.setHidden(not self.job_preferences.is_assembly_component_closed(sub_assembly.name))
        sub_assembly_widget.pushButton_sub_assemblies.setChecked(self.job_preferences.is_assembly_sub_assembly_closed(sub_assembly.name))
        sub_assembly_widget.sub_assemblies_widget.setHidden(not self.job_preferences.is_assembly_sub_assembly_closed(sub_assembly.name))

        return sub_assembly_widget

    def load_sub_assemblies(self):
        for sub_assembly in self.assembly.sub_assemblies:
            sub_assembly.group = self.assembly.group
            self.load_sub_assembly(sub_assembly)

    def load_sub_assembly(self, assembly: Assembly):
        sub_assembly_widget = self.add_sub_assembly(assembly)
        sub_assembly_widget.load_sub_assemblies()

    def sub_assembly_name_renamed(self, sub_assembly: Assembly, new_sub_assembly_name: QLineEdit):
        sub_assembly.name = new_sub_assembly_name.text()
        self.changes_made()

    def duplicate_sub_assembly(self, sub_assembly: Assembly):
        new_sub_assembly = Assembly(f"{sub_assembly.name} - (Copy)", sub_assembly.to_dict(), self.assembly.group)
        self.load_sub_assembly(new_sub_assembly)
        self.assembly.add_sub_assembly(new_sub_assembly)
        self.changes_made()

    def delete_sub_assembly(self, sub_assembly_widget: "AssemblyPlanningWidget"):
        self.sub_assembly_widgets.remove(sub_assembly_widget)
        self.sub_assemblies_toolbox.removeItem(sub_assembly_widget)
        self.assembly.remove_sub_assembly(sub_assembly_widget.assembly)
        self.changes_made()

    def update_tables(self):
        self.load_components_table()
        self.load_laser_cut_parts_table()
        for sub_assembly_widget in self.sub_assembly_widgets:
            sub_assembly_widget.update_tables()

    def set_table_row_color(self, table: LaserCutPartsQuotingTableWidget | ComponentsQuotingTableWidget, row_index: int, color: str):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def open_group_menu(self, menu: QMenu) -> None:
        menu.exec(QCursor.pos())

    def changes_made(self):
        self.parent.changes_made()

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
