import os
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import (QComboBox, QMenu, QMessageBox, QPushButton,
                             QTreeWidgetItem, QWidget)

from ui.custom.machine_cut_time_double_spin_box import \
    MachineCutTimeDoubleSpinBox
from ui.dialogs.add_sheet_dialog import AddSheetDialog
from ui.widgets.nest_widget_UI import Ui_Form
from utils.inventory.category import Category
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.inventory.sheets_inventory import Sheet
from utils.workspace.assembly import Assembly

if TYPE_CHECKING:
    from ui.widgets.job_widget import JobWidget


class NestWidget(QWidget, Ui_Form):
    updateLaserCutPartSettings = pyqtSignal(Nest)

    def __init__(self, nest: Nest, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.parent: JobWidget = parent
        self.toolbox_button: QPushButton = None
        self.nest = nest
        self.sheet = self.nest.sheet
        self.sheets_inventory = self.parent.parent.job_manager.sheets_inventory
        self.sheet_settings = self.parent.parent.job_manager.sheet_settings
        self.price_calculator = self.parent.price_calculator
        self.job_preferences = self.parent.job_preferences
        self.laser_cut_inventory = self.parent.parent.job_manager.laser_cut_inventory

        self.part_to_assembly: dict[str, Assembly] = {}
        self.assembly_dict: dict[str, Assembly] = {}
        self.part_assembly_comboboxes: list[QComboBox] = []
        self.preprocess_assemblies()
        self.load_ui()

    def load_ui(self):
        self.pushButton_settings.setChecked(
            self.job_preferences.is_nest_setting_closed(self.nest)
        )
        self.parent.apply_stylesheet_to_toggle_buttons(
            self.pushButton_settings, self.settings_widget
        )
        self.settings_widget.setHidden(
            not self.job_preferences.is_nest_setting_closed(self.nest)
        )

        self.pushButton_laser_cut_parts.setChecked(
            self.job_preferences.is_nest_laser_cut_closed(self.nest)
        )
        self.parent.apply_stylesheet_to_toggle_buttons(
            self.pushButton_laser_cut_parts, self.laser_cut_parts_widget
        )
        self.laser_cut_parts_widget.setHidden(
            not self.job_preferences.is_nest_laser_cut_closed(self.nest)
        )

        self.pushButton_image.setChecked(
            self.job_preferences.is_nest_image_closed(self.nest)
        )
        self.parent.apply_stylesheet_to_toggle_buttons(
            self.pushButton_image, self.image_widget_2
        )
        self.image_widget_2.setHidden(
            not self.job_preferences.is_nest_image_closed(self.nest)
        )

        self.pushButton_settings.clicked.connect(
            partial(
                self.job_preferences.nest_widget_toolbox_toggled,
                self.nest,
                self.pushButton_settings,
                self.pushButton_laser_cut_parts,
                self.pushButton_image,
            )
        )
        self.pushButton_laser_cut_parts.clicked.connect(
            partial(
                self.job_preferences.nest_widget_toolbox_toggled,
                self.nest,
                self.pushButton_settings,
                self.pushButton_laser_cut_parts,
                self.pushButton_image,
            )
        )
        self.pushButton_image.clicked.connect(
            partial(
                self.job_preferences.nest_widget_toolbox_toggled,
                self.nest,
                self.pushButton_settings,
                self.pushButton_laser_cut_parts,
                self.pushButton_image,
            )
        )

        self.pushButton_add_sheet.clicked.connect(self.add_new_sheet_to_inventory)
        self.label_scrap_percentage.setText(f"{self.nest.scrap_percentage:,.2f}%")

        self.doubleSpinBox_sheet_cut_time = MachineCutTimeDoubleSpinBox(self)
        self.doubleSpinBox_sheet_cut_time.wheelEvent = (
            lambda event: self.parent.wheelEvent(event)
        )
        self.doubleSpinBox_sheet_cut_time.setValue(self.nest.sheet_cut_time)
        self.doubleSpinBox_sheet_cut_time.setToolTip(
            f"Original: {self.get_sheet_cut_time()}"
        )
        self.doubleSpinBox_sheet_cut_time.valueChanged.connect(self.nest_changed)
        self.verticalLayout_sheet_cut_time.addWidget(self.doubleSpinBox_sheet_cut_time)

        self.doubleSpinBox_sheet_count.wheelEvent = (
            lambda event: self.parent.wheelEvent(event)
        )
        self.doubleSpinBox_sheet_count.setValue(self.nest.sheet_count)
        self.doubleSpinBox_sheet_count.valueChanged.connect(self.nest_changed)

        self.comboBox_material.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.comboBox_material.addItems(self.sheet_settings.get_materials())
        self.comboBox_material.setCurrentText(self.sheet.material)
        self.comboBox_material.currentTextChanged.connect(self.sheet_changed)

        self.comboBox_thickness.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.comboBox_thickness.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_thickness.setCurrentText(self.sheet.thickness)
        self.comboBox_thickness.currentTextChanged.connect(self.sheet_changed)

        self.doubleSpinBox_length.wheelEvent = lambda event: self.parent.wheelEvent(
            event
        )
        self.doubleSpinBox_length.setValue(self.sheet.length)
        self.doubleSpinBox_length.valueChanged.connect(self.sheet_changed)

        self.doubleSpinBox_width.wheelEvent = lambda event: self.parent.wheelEvent(
            event
        )
        self.doubleSpinBox_width.setValue(self.sheet.width)
        self.doubleSpinBox_width.valueChanged.connect(self.sheet_changed)

        self.treeWidget_parts.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.treeWidget_parts.customContextMenuRequested.connect(self.show_context_menu)

        self.load_nest_parts()

        self.image_widget.setHidden(True)

        if "404" not in self.nest.image_path:
            self.image_widget.setHidden(False)
            self.label_image.setFixedSize(485, 345)
            pixmap = QPixmap(self.nest.image_path)
            scaled_pixmap = pixmap.scaled(
                self.label_image.size(),
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            )
            self.label_image.setPixmap(scaled_pixmap)

        self.update_nest_cost()
        self.update_sheet_status()

    def show_context_menu(self, position):
        context_menu = QMenu(self)

        assembly_menu = QMenu("Assmebly", context_menu)

        for assembly in ["None"] + [
            assembly.name for assembly in self.parent.job.get_all_assemblies()
        ]:
            assembly_action = QAction(assembly, assembly_menu)
            assembly_action.triggered.connect(
                partial(self.parts_assembly_changed, assembly)
            )
            assembly_menu.addAction(assembly_action)

        add_to_inventory_action = QAction("Add to Inventory", assembly_menu)
        add_to_inventory_action.triggered.connect(self.add_parts_to_inventory)

        context_menu.addMenu(assembly_menu)
        context_menu.addAction(add_to_inventory_action)
        context_menu.exec(self.treeWidget_parts.viewport().mapToGlobal(position))

    def update_ui_values(self):
        self.block_ui_signals(True)
        self.doubleSpinBox_length.setValue(self.sheet.length)
        self.doubleSpinBox_width.setValue(self.sheet.width)
        self.comboBox_thickness.setCurrentText(self.sheet.thickness)
        self.comboBox_material.setCurrentText(self.sheet.material)
        self.block_ui_signals(False)

    def block_ui_signals(self, block: bool):
        self.doubleSpinBox_length.blockSignals(block)
        self.doubleSpinBox_width.blockSignals(block)
        self.comboBox_thickness.blockSignals(block)
        self.comboBox_material.blockSignals(block)

    def sheet_changed(self):
        self.sheet.length = self.doubleSpinBox_length.value()
        self.sheet.width = self.doubleSpinBox_width.value()
        self.sheet.material = self.comboBox_material.currentText()
        self.sheet.thickness = self.comboBox_thickness.currentText()
        if self.toolbox_button:
            self.toolbox_button.setText(self.nest.get_name())
            self.job_preferences.nest_toggled(self.nest.get_name(), self.toolbox_button)
        for nest_laser_cut_part in self.nest.laser_cut_parts:
            for assembly_name, assembly in self.assembly_dict.items():
                if self.is_part_in_assembly(assembly_name, nest_laser_cut_part.name):
                    for laser_cut_part in assembly.laser_cut_parts:
                        if laser_cut_part.name == nest_laser_cut_part.name:
                            laser_cut_part.material = self.sheet.material
                            laser_cut_part.gauge = self.sheet.thickness
        self.parent.parent.update_tables()
        self.parent.changes_made()
        self.update_nest_cost()

    def nest_changed(self):
        self.nest.sheet_count = self.doubleSpinBox_sheet_count.value()
        self.nest.sheet_cut_time = self.doubleSpinBox_sheet_cut_time.value()
        self.update_nest_cut_time()
        self.load_nest_parts()
        self.update_nest_cost()
        self.parent.changes_made()

    def set_cost_for_sheets(self, cost: float):
        self.label_cost_for_sheets.setText(f"${cost:,.2f}")

    def set_cutting_cost(self, cost: float):
        self.label_cutting_cost.setText(f"${cost:,.2f}")

    def update_nest_cut_time(self):
        self.label_nest_cut_time.setText(self.get_total_cutting_time())

    def update_nest_cost(self):
        self.label_total_cost_for_nested_parts.setText(
            f"Total Cost for Parts: ${self.price_calculator.get_nest_laser_cut_parts_cost(self.nest):,.2f}"
        )
        self.label_cost_for_sheets.setText(
            f"${self.price_calculator.get_sheet_cost(self.nest.sheet) * self.nest.sheet_count:,.2f}"
        )
        self.label_cutting_cost.setText(
            f"${self.price_calculator.get_cutting_cost(self.nest):,.2f}"
        )

    def get_sheet_cut_time(self) -> str:
        total_seconds = self.nest.sheet_cut_time
        return self.get_formatted_time(total_seconds)

    def get_total_cutting_time(self) -> str:
        total_seconds = self.nest.sheet_cut_time * self.nest.sheet_count
        return self.get_formatted_time(total_seconds)

    def get_formatted_time(self, total_seconds) -> str:
        hours = int(total_seconds // 3600)
        minutes = int(total_seconds % 3600 // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def add_new_sheet_to_inventory(self):
        add_sheet_dialog = AddSheetDialog(
            self.sheet, None, self.sheets_inventory, self.sheet_settings, self
        )

        if add_sheet_dialog.exec():
            new_sheet = Sheet(
                {
                    "quantity": add_sheet_dialog.get_quantity(),
                    "length": add_sheet_dialog.get_length(),
                    "width": add_sheet_dialog.get_width(),
                    "thickness": add_sheet_dialog.get_thickness(),
                    "material": add_sheet_dialog.get_material(),
                    "latest_change_quantity": f'{os.getlogin().title()} - Sheet was added via quote generator at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}',
                },
                self.sheets_inventory,
            )
            new_sheet.add_to_category(
                self.sheets_inventory.get_category(add_sheet_dialog.get_category())
            )
            for sheet in self.sheets_inventory.sheets:
                if new_sheet.get_name() == sheet.get_name():
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setWindowTitle("Exists")
                    msg.setText(f"'{new_sheet.get_name()}'\nAlready exists.")
                    msg.exec()
                    return
            self.sheet = new_sheet
            self.comboBox_thickness.setCurrentText(new_sheet.thickness)
            self.comboBox_material.setCurrentText(new_sheet.material)
            self.doubleSpinBox_length.setValue(new_sheet.length)
            self.doubleSpinBox_width.setValue(new_sheet.width)
            for laser_cut_part in self.nest.laser_cut_parts:
                laser_cut_part.gauge = new_sheet.thickness
                laser_cut_part.material = new_sheet.material
            self.updateLaserCutPartSettings.emit(self)
            self.sheets_inventory.add_sheet(new_sheet)
            self.sheets_inventory.save_local_copy()
            self.sync_changes()
            self.changes_made()
            # self.nests_tool_box.setItemText(self.nest_items[nest]["tab_index"], nest.get_name())
            # self.update_laser_cut_parts_price()
            # self.update_scrap_percentage()
            # self.update_sheet_price()
            # self.load_nest_summary()
            self.update_sheet_status()

    def update_cutting_time(self):
        self.label_nest_cut_time.setText(self.nest.get_total_cutting_time())

    def update_sheet_status(self):
        if self.sheets_inventory.exists(self.nest.sheet):
            self.pushButton_add_sheet.setHidden(True)
            if sheet := self.sheets_inventory.get_sheet_by_name(
                self.nest.sheet.get_name()
            ):
                self.label_sheet_status.setText(
                    f"This sheet exists in sheets inventory with {sheet.quantity} in stock."
                )
        else:
            self.pushButton_add_sheet.setHidden(False)
            self.label_sheet_status.setText(
                "This sheet does not exist in sheets inventory."
            )

    def update_nest_summary(self):
        self.parent.update_nest_summary()

    def load_nest_parts(self):
        self.part_assembly_comboboxes.clear()
        self.treeWidget_parts.clear()
        self.treeWidget_parts.setHeaderLabels(
            ["Part Name", "Qty", "Nest Qty", "Assembly"]
        )

        for laser_cut_part in self.nest.laser_cut_parts:
            tree_item = QTreeWidgetItem(
                self.treeWidget_parts,
                [
                    laser_cut_part.name,
                    str(int(laser_cut_part.quantity_on_sheet)),
                    str(int(laser_cut_part.quantity_on_sheet * self.nest.sheet_count)),
                    "",
                ],
            )  # Placeholder for the QComboBox
            assembly_combobox = QComboBox(self.treeWidget_parts)
            self.part_assembly_comboboxes.append(assembly_combobox)
            assembly_combobox.wheelEvent = lambda event: self.parent.wheelEvent(event)
            assembly_combobox.addItems(
                ["None"]
                + [assembly.name for assembly in self.parent.job.get_all_assemblies()]
            )
            if assembly := self.find_parts_assembly(laser_cut_part.name):
                assembly_combobox.setCurrentText(assembly.name)
            assembly_combobox.currentTextChanged.connect(
                partial(self.part_assembly_changed, assembly_combobox, laser_cut_part)
            )
            self.treeWidget_parts.addTopLevelItem(tree_item)
            self.treeWidget_parts.setItemWidget(tree_item, 3, assembly_combobox)
        self.treeWidget_parts.resizeColumnToContents(1)
        self.treeWidget_parts.resizeColumnToContents(2)
        self.treeWidget_parts.resizeColumnToContents(3)

    def update_parts_assembly(self):
        self.preprocess_assemblies()
        for assembly_combobox in self.part_assembly_comboboxes:
            selection = (
                assembly_combobox.currentIndex()
            )  # Because the user might have renamed the assembly
            assembly_combobox.blockSignals(True)
            assembly_combobox.clear()
            assembly_combobox.addItems(
                ["None"]
                + [assembly.name for assembly in self.parent.job.get_all_assemblies()]
            )
            assembly_combobox.setCurrentIndex(selection)
            assembly_combobox.blockSignals(False)

    def preprocess_assemblies(self):
        self.part_to_assembly.clear()
        self.assembly_dict.clear()

        for assembly in self.parent.job.get_all_assemblies():
            self.assembly_dict[assembly.name] = assembly
            for laser_cut_part in assembly.laser_cut_parts:
                self.part_to_assembly[laser_cut_part.name] = assembly

    def find_parts_assembly(self, part_name: str) -> Optional[Assembly]:
        return self.part_to_assembly.get(part_name, None)

    def is_part_in_assembly(self, assembly_name: str, part_name: str) -> bool:
        if assembly := self.assembly_dict.get(assembly_name):
            return any(part_name == part.name for part in assembly.laser_cut_parts)
        return False

    def get_selected_tree_items(self) -> list[str]:
        selected_items: list[str] = [
            item.text(0) for item in self.treeWidget_parts.selectedItems()
        ]
        return selected_items

    def get_nested_laser_cut_part(self, name: str) -> LaserCutPart:
        return next(
            (
                nested_laser_cut_part
                for nested_laser_cut_part in self.nest.laser_cut_parts
                if nested_laser_cut_part.name == name
            ),
            None,
        )

    def get_selected_tree_parts(self) -> list[LaserCutPart]:
        selected_parts: list[LaserCutPart] = []
        if selected_items := self.get_selected_tree_items():
            for item in selected_items:
                selected_parts.append(self.get_nested_laser_cut_part(item))
        return selected_parts

    def add_parts_to_inventory(self):
        if selected_parts := self.get_selected_tree_parts():
            for selected_nest_laser_cut_part in selected_parts:
                if (
                    existing_laser_cut_part
                    := self.laser_cut_inventory.get_laser_cut_part_by_name(
                        selected_nest_laser_cut_part.name
                    )
                ):
                    existing_laser_cut_part.quantity += (
                        selected_nest_laser_cut_part.quantity
                    )
                    existing_laser_cut_part.material = (
                        selected_nest_laser_cut_part.material
                    )
                    existing_laser_cut_part.gauge = selected_nest_laser_cut_part.gauge
                    existing_laser_cut_part.modified_date = f"{os.getlogin().title()} - Added {selected_nest_laser_cut_part.quantity} quantities from {self.nest.name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                else:
                    if not (
                        category := self.laser_cut_inventory.get_category(
                            "Uncategorized"
                        )
                    ):
                        category = Category("Uncategorized")
                        self.laser_cut_inventory.add_category(category)
                    selected_nest_laser_cut_part.add_to_category(category)
                    selected_nest_laser_cut_part.modified_date = f"{os.getlogin().title()} - Part added from {self.assembly.name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                    self.laser_cut_inventory.add_laser_cut_part(
                        selected_nest_laser_cut_part
                    )
            self.laser_cut_inventory.save()
            self.sync_changes()

    def parts_assembly_changed(self, assembly_name: str):
        if assembly_name == "None":
            return
        updated_parts = ""
        parts_that_do_not_exist: list[LaserCutPart] = []
        if selected_parts := self.get_selected_tree_parts():
            for selected_nest_laser_cut_part in selected_parts:
                if self.is_part_in_assembly(
                    assembly_name, selected_nest_laser_cut_part.name
                ):
                    if assembly := self.assembly_dict.get(assembly_name):
                        for laser_cut_part in assembly.laser_cut_parts:
                            if laser_cut_part.name == selected_nest_laser_cut_part.name:
                                laser_cut_part.load_part_data(
                                    selected_nest_laser_cut_part.to_dict()
                                )
                                updated_parts += f"{laser_cut_part.name}\n"
                else:
                    parts_that_do_not_exist.append(selected_nest_laser_cut_part)
            self.parent.update_tables()
            if updated_parts:
                msg = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Updated",
                    f"Updated the following parts:\n{updated_parts}",
                    QMessageBox.StandardButton.Ok,
                    self,
                )
                msg.exec()
            if parts_that_do_not_exist:
                parts_that_do_not_exist_text = ""
                for part in parts_that_do_not_exist:
                    parts_that_do_not_exist_text += f"{part.name}\n"
                msg = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Items not found",
                    f"The following items could not be found in {assembly_name}:\n{parts_that_do_not_exist_text}\nDo you want to add them to {assembly_name}?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    self,
                )
                if msg.exec() != QMessageBox.StandardButton.Yes:
                    return
                if assembly := self.assembly_dict.get(assembly_name):
                    for nest_laser_cut_part in parts_that_do_not_exist:
                        new_laser_cut_part = LaserCutPart(
                            nest_laser_cut_part.to_dict(),
                            nest_laser_cut_part.laser_cut_inventory,
                        )
                        assembly.add_laser_cut_part(new_laser_cut_part)
                        self.part_to_assembly[nest_laser_cut_part] = assembly
                    self.parent.update_tables()
                    self.parent.changes_made()
                self.load_nest_parts()

    def part_assembly_changed(
        self, assembly_combobox: QComboBox, nest_laser_cut_part: LaserCutPart
    ):
        if assembly_combobox.currentText() == "None":
            return

        if self.is_part_in_assembly(
            assembly_combobox.currentText(), nest_laser_cut_part.name
        ):
            if assembly := self.assembly_dict.get(assembly_combobox.currentText()):
                for laser_cut_part in assembly.laser_cut_parts:
                    if laser_cut_part.name == nest_laser_cut_part.name:
                        laser_cut_part.load_part_data(nest_laser_cut_part.to_dict())
                        self.parent.update_tables()
                        msg = QMessageBox(
                            QMessageBox.Icon.Information,
                            "Updated",
                            f"Updated {nest_laser_cut_part.name}'s data in job.",
                            QMessageBox.StandardButton.Ok,
                            self,
                        )
                        msg.exec()
                        return
        else:
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Item not found",
                f"{nest_laser_cut_part.name} does not exist in {assembly_combobox.currentText()}.\n\nWould you like to add it?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                self,
            )
            if msg.exec() != QMessageBox.StandardButton.Yes:
                self.load_nest_parts()
                return
            if assembly := self.assembly_dict.get(assembly_combobox.currentText()):
                new_laser_cut_part = LaserCutPart(
                    nest_laser_cut_part.to_dict(),
                    nest_laser_cut_part.laser_cut_inventory,
                )
                assembly.add_laser_cut_part(new_laser_cut_part)
                self.part_to_assembly[nest_laser_cut_part] = assembly
                self.parent.update_tables()
                self.parent.changes_made()

    def sync_changes(self):
        self.parent.parent.sync_changes()

    def changes_made(self):
        self.parent.changes_made()
