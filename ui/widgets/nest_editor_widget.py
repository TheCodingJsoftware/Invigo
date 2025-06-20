import contextlib
import os
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ui.custom.nest_editor_table_widget import (
    NestEditorPartsTableColumns,
    NestEditorPartsTableWidget,
)
from ui.custom_widgets import ClickableRichTextLabel, MachineCutTimeSpinBox, RecutButton
from ui.dialogs.add_laser_cut_part_dialog import AddLaserCutPartDialog
from ui.dialogs.add_sheet_dialog import AddSheetDialog
from ui.dialogs.recut_dialog import RecutDialog
from ui.theme import theme_var
from ui.widgets.nest_editor_widget_UI import Ui_Form
from utils.colors import get_contrast_text_color, lighten_color
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.inventory.sheet import Sheet
from utils.settings import Settings

if TYPE_CHECKING:
    from ui.dialogs.nest_editor_dialog import NestEditorDialog


class NestEditorWidget(QWidget, Ui_Form):
    sheetSettingsChanged = pyqtSignal()

    def __init__(
        self,
        nest: Nest,
        parent=None,
    ):
        super().__init__(parent)
        self.parent: NestEditorDialog = parent
        self.setupUi(self)

        self.nest = nest
        self.parts_table_items: dict[
            LaserCutPart, dict[str, int | QTableWidgetItem | QComboBox | RecutButton]
        ] = {}
        self.pushButton_nest_name.setText(self.nest.get_name())
        self.sheet_settings = self.parent.parent.sheet_settings
        self.sheets_inventory = self.parent.parent.sheets_inventory
        self.laser_cut_inventory = self.parent.parent.laser_cut_parts_inventory

        self.settings_file = Settings()
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
        self.parts_table = NestEditorPartsTableWidget(self)
        self.parts_table.rowChanged.connect(self.parts_table_row_changed)
        self.parts_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.parts_table.customContextMenuRequested.connect(
            partial(self.open_group_menu, self.load_context_menu())
        )
        self.verticalLayout_nest_table_layout.addWidget(self.parts_table)

        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_nest_name, self.widget_nest
        )
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_laser_cut_parts_toggle_view, self.widget_nest_table
        )

        self.label_sheet_status = ClickableRichTextLabel(self)
        self.horizontalLayout_sheet_status.addWidget(self.label_sheet_status)

        self.sheet_cut_time = MachineCutTimeSpinBox(self)
        self.sheet_cut_time.setValue(self.nest.sheet_cut_time)
        self.sheet_cut_time.valueChanged.connect(self.sheet_cut_time_changed)
        self.sheet_cut_time.setToolTip(
            f"Original: {self.get_sheet_cut_time(self.nest)}"
        )
        self.verticalLayout_sheet_cut_time.addWidget(self.sheet_cut_time)

        self.comboBox_sheet_material.addItems(self.sheet_settings.get_materials())
        self.comboBox_sheet_material.wheelEvent = lambda event: self.parent.wheelEvent(
            event
        )

        self.comboBox_sheet_thickness.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_sheet_thickness.wheelEvent = lambda event: self.parent.wheelEvent(
            event
        )

        self.comboBox_cutting_method.setCurrentText(self.nest.cutting_method)
        self.comboBox_cutting_method.wheelEvent = lambda event: self.parent.wheelEvent(
            event
        )

        self.comboBox_sheet_thickness.setCurrentText(self.nest.sheet.thickness)

        self.comboBox_sheet_material.setCurrentText(self.nest.sheet.material)

        self.doubleSpinBox_sheet_length.setValue(self.nest.sheet.length)
        self.doubleSpinBox_sheet_length.wheelEvent = (
            lambda event: self.parent.wheelEvent(event)
        )

        self.doubleSpinBox_sheet_width.setValue(self.nest.sheet.width)
        self.doubleSpinBox_sheet_width.wheelEvent = (
            lambda event: self.parent.wheelEvent(event)
        )

        self.doubleSpinBox_sheet_count.setValue(self.nest.sheet_count)
        self.doubleSpinBox_sheet_count.wheelEvent = (
            lambda event: self.parent.wheelEvent(event)
        )

        self.plainTextEdit_notes.setPlainText(self.nest.notes)

        self.comboBox_cutting_method.currentTextChanged.connect(
            self.cutting_method_changed
        )
        self.comboBox_sheet_thickness.currentTextChanged.connect(
            self.sheet_thickness_changed
        )
        self.comboBox_sheet_thickness.currentTextChanged.connect(
            self.sheetSettingsChanged.emit
        )
        self.comboBox_sheet_material.currentTextChanged.connect(
            self.sheet_material_changed
        )
        self.comboBox_sheet_material.currentTextChanged.connect(
            self.sheetSettingsChanged.emit
        )
        self.doubleSpinBox_sheet_length.valueChanged.connect(self.sheet_length_changed)
        self.doubleSpinBox_sheet_length.valueChanged.connect(
            self.sheetSettingsChanged.emit
        )
        self.doubleSpinBox_sheet_width.valueChanged.connect(self.sheet_width_changed)
        self.doubleSpinBox_sheet_width.valueChanged.connect(
            self.sheetSettingsChanged.emit
        )
        self.doubleSpinBox_sheet_count.valueChanged.connect(self.sheet_count_changed)
        self.plainTextEdit_notes.textChanged.connect(self.notes_changed)

        self.pushButton_add_laser_cut_part.clicked.connect(
            self.add_new_laser_cut_part_to_nest
        )

        if "404" not in self.nest.image_path:
            self.label_nest_image.setFixedSize(485, 345)
            pixmap = QPixmap(self.nest.image_path)
            if pixmap.isNull():
                pixmap = QPixmap("images/404.jpeg")
            scaled_pixmap = pixmap.scaled(
                self.label_nest_image.size(),
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            )
            self.label_nest_image.setPixmap(scaled_pixmap)

        self.load_parts_table()

    def update_name(self):
        self.pushButton_nest_name.setText(self.nest.get_name())

    def load_parts_table(self):
        self.parts_table_items.clear()
        self.parts_table.setRowCount(0)
        self.parts_table.blockSignals(True)
        sorted_parts = sorted(
            self.nest.laser_cut_parts, key=lambda part: part.part_number
        )

        for laser_cut_part in sorted_parts:
            self.add_laser_cut_part(laser_cut_part)
        self.parts_table.blockSignals(False)
        self.update_laser_cut_parts_table_height()
        self.parts_table.resizeColumnsToContents()
        self.parts_table.setColumnWidth(NestEditorPartsTableColumns.PICTURE.value, 74)
        self.update_sheet_scrap_percentage()
        self.update_sheet_status()
        self.update_total_nest_cut_time()

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        current_row = self.parts_table.rowCount()
        self.parts_table_items.update({laser_cut_part: {}})
        self.parts_table_items[laser_cut_part].update({"row": current_row})
        self.parts_table.insertRow(current_row)
        self.parts_table.setRowHeight(current_row, self.parts_table.row_height)

        image_item = QTableWidgetItem("")
        if laser_cut_part.image_index:
            image = QPixmap(laser_cut_part.image_index)
            if image.isNull():
                image = QPixmap("images/404.jpeg")

            original_width = image.width()
            original_height = image.height()
            new_height = self.parts_table.row_height
            new_width = int(original_width * (new_height / original_height))
            pixmap = image.scaled(
                new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio
            )
            image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.parts_table.setRowHeight(current_row, new_height)

        self.parts_table.setItem(
            current_row, NestEditorPartsTableColumns.PICTURE.value, image_item
        )

        part_name_item = QTableWidgetItem(laser_cut_part.name)
        part_name_item.setFont(self.tables_font)
        self.parts_table.setItem(
            current_row, NestEditorPartsTableColumns.PART_NAME.value, part_name_item
        )
        self.parts_table_items[laser_cut_part].update({"part_name": part_name_item})

        combobox_material = QComboBox(self)
        combobox_material.setStyleSheet("border-radius: 0px;")
        combobox_material.wheelEvent = lambda event: self.parent.wheelEvent(event)
        combobox_material.addItems(self.sheet_settings.get_materials())
        combobox_material.setCurrentText(laser_cut_part.material)
        combobox_material.currentTextChanged.connect(
            partial(self.part_material_changed, current_row)
        )
        self.parts_table.setCellWidget(
            current_row, NestEditorPartsTableColumns.MATERIAL.value, combobox_material
        )
        self.parts_table_items[laser_cut_part].update({"material": combobox_material})

        combobox_thickness = QComboBox(self)
        combobox_thickness.setStyleSheet("border-radius: 0px;")
        combobox_thickness.wheelEvent = lambda event: self.parent.wheelEvent(event)
        combobox_thickness.addItems(self.sheet_settings.get_thicknesses())
        combobox_thickness.setCurrentText(laser_cut_part.gauge)
        combobox_thickness.currentTextChanged.connect(
            partial(self.part_thickness_changed, current_row)
        )
        self.parts_table.setCellWidget(
            current_row, NestEditorPartsTableColumns.THICKNESS.value, combobox_thickness
        )
        self.parts_table_items[laser_cut_part].update({"thickness": combobox_thickness})

        sheet_quantity_item = QTableWidgetItem(
            f"{laser_cut_part.quantity_on_sheet:,.0f}"
        )
        sheet_quantity_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        sheet_quantity_item.setFont(self.tables_font)
        self.parts_table.setItem(
            current_row,
            NestEditorPartsTableColumns.QUANTITY_ON_SHEET.value,
            sheet_quantity_item,
        )
        self.parts_table_items[laser_cut_part].update(
            {"sheet_quantity": sheet_quantity_item}
        )

        total_quantity_item = QTableWidgetItem(
            f"{(laser_cut_part.quantity_on_sheet * self.nest.sheet_count):,.0f}"
        )
        total_quantity_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        total_quantity_item.setFont(self.tables_font)
        self.parts_table.setItem(
            current_row,
            NestEditorPartsTableColumns.TOTAL_QUANTITY.value,
            total_quantity_item,
        )
        self.parts_table_items[laser_cut_part].update(
            {"total_quantity": total_quantity_item}
        )

        part_dim_item = QTableWidgetItem(
            f"{laser_cut_part.part_dim}\n\n{laser_cut_part.surface_area:,.2f} in²"
        )
        part_dim_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        part_dim_item.setFont(self.tables_font)
        self.parts_table.setItem(
            current_row, NestEditorPartsTableColumns.PART_DIMENSION.value, part_dim_item
        )
        self.parts_table_items[laser_cut_part].update({"part_dimension": part_dim_item})

        recut_button = RecutButton(self)
        recut_button.clicked.connect(
            partial(self.recut_pressed, laser_cut_part, recut_button)
        )
        recut_button.setStyleSheet("margin: 5%;")
        self.parts_table.setCellWidget(
            current_row, NestEditorPartsTableColumns.RECUT.value, recut_button
        )
        self.parts_table_items[laser_cut_part].update({"recut_button": recut_button})

    def recut_pressed(self, recut_part: LaserCutPart, button: RecutButton):
        if button.isChecked():
            recut_dialog = RecutDialog("How many are Recut?", recut_part.quantity, self)
            if recut_dialog.exec() and recut_dialog.get_quantity() >= 1:
                recut_part.recut = button.isChecked()
                recut_count = recut_dialog.get_quantity()
                recut_part.recut_count_notes = recut_count
                button.setText(f"Recut ({recut_count})")
                self.plainTextEdit_notes.setPlainText(
                    self.generate_recut_part_summary()
                )
            else:
                button.blockSignals(True)
                button.set_to_no_recut()
                button.blockSignals(False)
        else:
            button.setText("No Recut")
            recut_part.recut = False
            recut_part.recut_count_notes = 0
            self.plainTextEdit_notes.setPlainText(self.generate_recut_part_summary())

    def generate_recut_part_summary(self) -> str:
        summary = ""
        for part in self.nest.laser_cut_parts:
            if part.recut:
                if part.recut_count_notes == 1:
                    summary += f"{part.name} has {part.recut_count_notes} recut\n"
                else:
                    summary += f"{part.name} has {part.recut_count_notes} recuts\n"
        return summary

    def add_new_laser_cut_part_to_nest(self):
        add_item_dialog = AddLaserCutPartDialog(self.laser_cut_inventory, self)
        if add_item_dialog.exec():
            if (
                selected_laser_cut_parts
                := add_item_dialog.get_selected_laser_cut_parts()
            ):
                for laser_cut_part in selected_laser_cut_parts:
                    new_laser_cut_part = LaserCutPart(
                        laser_cut_part.to_dict(), self.laser_cut_inventory
                    )
                    new_laser_cut_part.quantity_on_sheet = 1
                    new_laser_cut_part.quantity = (
                        laser_cut_part.quantity_on_sheet * self.nest.sheet_count
                    )
                    self.nest.add_laser_cut_part(new_laser_cut_part)
            self.load_parts_table()
            self.update_sheet_scrap_percentage()

    def parts_table_row_changed(self, row: int):
        current_laser_cut_part = next(
            (
                laser_cut_part
                for laser_cut_part, table_data in self.parts_table_items.items()
                if table_data["row"] == row
            ),
            None,
        )
        if not current_laser_cut_part:
            return

        self.parts_table.blockSignals(True)

        sheet_quantity = int(
            self.parts_table_items[current_laser_cut_part]["sheet_quantity"]
            .text()
            .strip()
            .replace(",", "")
        )

        current_laser_cut_part.quantity_on_sheet = sheet_quantity
        current_laser_cut_part.quantity = sheet_quantity * self.nest.sheet_count

        self.parts_table_items[current_laser_cut_part]["sheet_quantity"].setText(
            f"{sheet_quantity:,.0f}"
        )
        self.parts_table_items[current_laser_cut_part]["total_quantity"].setText(
            f"{(self.nest.sheet_count * sheet_quantity):,.0f}"
        )
        self.update_sheet_scrap_percentage()

        self.parts_table.blockSignals(False)

    def part_material_changed(self, row: int, new_material: str):
        current_laser_cut_part = next(
            (
                laser_cut_part
                for laser_cut_part, table_data in self.parts_table_items.items()
                if table_data["row"] == row
            ),
            None,
        )
        if not current_laser_cut_part:
            return
        current_laser_cut_part.material = new_material

    def part_thickness_changed(self, row: int, new_thickness: str):
        current_laser_cut_part = next(
            (
                laser_cut_part
                for laser_cut_part, table_data in self.parts_table_items.items()
                if table_data["row"] == row
            ),
            None,
        )
        if not current_laser_cut_part:
            return
        current_laser_cut_part.gauge = new_thickness
        self.parts_table.blockSignals(True)
        self.parts_table_items[current_laser_cut_part]["thickness"].setCurrentText(
            new_thickness
        )
        self.parts_table.blockSignals(False)

    def update_laser_cut_parts_table_height(self):
        total_height = 0
        for row in range(self.parts_table.rowCount()):
            total_height += self.parts_table.rowHeight(row)
        self.parts_table.setFixedHeight(total_height + 70)

    def update_sheet_scrap_percentage(self):
        self.label_sheet_scrap_percentage.setText(
            f"{self.nest.calculate_scrap_percentage():.2f}%"
        )

    def sheet_cut_time_changed(self, new_cut_time: int):
        self.nest.sheet_cut_time = new_cut_time
        self.update_total_nest_cut_time()

    def update_total_nest_cut_time(self):
        self.label_nest_cut_time.setText(f"{self.get_total_cutting_time()}")

    def cutting_method_changed(self, new_cutting_method: str):
        self.nest.cutting_method = new_cutting_method

    def sheet_material_changed(self, new_material: str):
        self.nest.sheet.material = new_material
        for laser_cut_part in self.nest.laser_cut_parts:
            laser_cut_part.material = new_material
            self.parts_table.blockSignals(True)
            self.parts_table_items[laser_cut_part]["material"].setCurrentText(
                new_material
            )
            self.parts_table.blockSignals(False)
        self.update_name()
        self.update_sheet_status()

    def sheet_thickness_changed(self, new_thickness: str):
        self.nest.sheet.thickness = new_thickness
        for laser_cut_part in self.nest.laser_cut_parts:
            laser_cut_part.gauge = new_thickness
            self.parts_table.blockSignals(True)
            self.parts_table_items[laser_cut_part]["thickness"].setCurrentText(
                new_thickness
            )
            self.parts_table.blockSignals(False)
        self.update_name()
        self.update_sheet_status()

    def sheet_length_changed(self, new_length: float):
        self.nest.sheet.length = new_length
        self.update_name()
        self.update_sheet_status()
        self.update_sheet_scrap_percentage()

    def sheet_width_changed(self, new_width: float):
        self.nest.sheet.width = new_width
        self.update_name()
        self.update_sheet_status()
        self.update_sheet_scrap_percentage()

    def sheet_count_changed(self, new_sheet_count: int):
        self.nest.sheet_count = new_sheet_count
        self.parts_table.blockSignals(True)
        for laser_cut_part, table_data in self.parts_table_items.items():
            sheet_quantity = int(
                table_data["sheet_quantity"].text().strip().replace(",", "")
            )
            table_data["total_quantity"].setText(
                f"{(new_sheet_count * sheet_quantity):,.0f}"
            )
            laser_cut_part.quantity = sheet_quantity * new_sheet_count
        self.parts_table.blockSignals(False)
        self.update_total_nest_cut_time()

    def notes_changed(self):
        self.nest.notes = self.plainTextEdit_notes.toPlainText()

    def delete_selected_laser_cut_parts(self):
        selected_rows: set[int] = {
            selection.row() for selection in self.parts_table.selectedItems()
        }
        for laser_cut_part, table_item_data in self.parts_table_items.items():
            if table_item_data["row"] in selected_rows:
                laser_cut_part.nest.remove_laser_cut_part(laser_cut_part)
        else:
            self.load_parts_table()

    def update_selected_laser_cut_parts_settings(
        self, setting_name: str, new_value: str
    ):
        selected_rows: set[int] = {
            selection.row() for selection in self.parts_table.selectedItems()
        }
        for laser_cut_part, table_item_data in self.parts_table_items.items():
            if table_item_data["row"] in selected_rows:
                if setting_name == "material":
                    laser_cut_part.material = new_value
                elif setting_name == "thickness":
                    laser_cut_part.gauge = new_value
                table_item_data[setting_name].blockSignals(True)
                table_item_data[setting_name].setCurrentText(new_value)
                table_item_data[setting_name].blockSignals(False)

    def add_selected_parts_to_inventory(self):
        selected_rows: set[int] = {
            selection.row() for selection in self.parts_table.selectedItems()
        }
        laser_cut_parts_to_update = []
        for laser_cut_part, table_item_data in self.parts_table_items.items():
            if table_item_data["row"] in selected_rows:
                self.parent.parent.add_laser_cut_part_to_inventory(
                    laser_cut_part, self.nest.get_name()
                )
                laser_cut_parts_to_update.append(laser_cut_part)
        self.laser_cut_inventory.save_laser_cut_parts(laser_cut_parts_to_update)

    def update_sheet_status(self):
        if self.sheets_inventory.exists(self.nest.sheet):
            if sheet := self.sheets_inventory.get_sheet_by_name(
                self.nest.sheet.get_name()
            ):
                self.label_sheet_status.setText(
                    f"This sheet exists in sheets inventory with {sheet.quantity:,.0f} in stock."
                )
                with contextlib.suppress(
                    TypeError
                ):  # Disconnect the signal if it wasn't connected
                    self.label_sheet_status.disconnect()
        else:
            self.label_sheet_status.setText(
                f"This sheet does not exist in sheets inventory. Would you like to <a style='color:{theme_var('inverse-primary')};' href='#'>add it to the inventory</a>?"
            )
            self.label_sheet_status.clicked.connect(self.add_new_sheet_to_inventory)

    def add_new_sheet_to_inventory(self):
        add_sheet_dialog = AddSheetDialog(
            self.nest.sheet, None, self.sheets_inventory, self.sheet_settings, self
        )

        if add_sheet_dialog.exec():
            new_sheet = Sheet(
                {
                    "quantity": add_sheet_dialog.get_quantity(),
                    "length": add_sheet_dialog.get_length(),
                    "width": add_sheet_dialog.get_width(),
                    "thickness": add_sheet_dialog.get_thickness(),
                    "material": add_sheet_dialog.get_material(),
                    "latest_change_quantity": f"{os.getlogin().title()} - Sheet was added via nest editor at {str(datetime.now().strftime('%B %d %A %Y %I:%M:%S %p'))}",
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
            self.comboBox_sheet_thickness.setCurrentText(new_sheet.thickness)
            self.comboBox_sheet_material.setCurrentText(new_sheet.material)
            self.doubleSpinBox_sheet_length.setValue(new_sheet.length)
            self.doubleSpinBox_sheet_width.setValue(new_sheet.width)
            for laser_cut_part in self.nest.laser_cut_parts:
                laser_cut_part.gauge = new_sheet.thickness
                laser_cut_part.material = new_sheet.material
            self.sheets_inventory.add_sheet(
                new_sheet, on_finished=self.update_sheet_status
            )
            # self.sheets_inventory.save_local_copy()
            # self.sync_changes()
            # self.update_sheet_status()

    def load_context_menu(self) -> QMenu:
        menu = QMenu("Options", self)

        delete_selected_parts_action = QAction("Delete selected items", self)
        delete_selected_parts_action.triggered.connect(
            self.delete_selected_laser_cut_parts
        )

        add_selected_parts_to_inventory_action = QAction("Add to inventory", self)
        add_selected_parts_to_inventory_action.triggered.connect(
            self.add_selected_parts_to_inventory
        )

        material_menu = QMenu("Set Material", menu)
        for material in self.sheet_settings.get_materials():
            material_action = QAction(material, material_menu)
            material_action.triggered.connect(
                partial(
                    self.update_selected_laser_cut_parts_settings, "material", material
                )
            )
            material_menu.addAction(material_action)

        thickness_menu = QMenu("Set Thickness", menu)
        for thickness in self.sheet_settings.get_thicknesses():
            thickness_action = QAction(thickness, material_menu)
            thickness_action.triggered.connect(
                partial(
                    self.update_selected_laser_cut_parts_settings,
                    "thickness",
                    thickness,
                )
            )
            thickness_menu.addAction(thickness_action)

        menu.addAction(add_selected_parts_to_inventory_action)
        menu.addSeparator()
        menu.addMenu(material_menu)
        menu.addMenu(thickness_menu)
        menu.addSeparator()
        menu.addAction(delete_selected_parts_action)

        return menu

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def sync_changes(self):
        self.parent.sync_changes()

    def get_total_cutting_time(self) -> str:
        total_seconds = self.nest.sheet_cut_time * self.nest.sheet_count
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def get_sheet_cut_time(self, nest: Nest) -> str:
        total_seconds = nest.sheet_cut_time
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = theme_var("primary")
        hover_color = lighten_color(base_color)
        inverted_color = get_contrast_text_color(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            f"""
QPushButton#assembly_button_drop_menu {{
    border: 1px solid {theme_var("surface")};
    background-color: {theme_var("surface")};
    border-radius: {theme_var("border-radius")};
    color: {theme_var("on-surface")};
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
QPushButton:!checked:pressed#assembly_button_drop_menu {{
    background-color: {theme_var("surface")};
}}
/* OPENED */
QPushButton:checked#assembly_button_drop_menu {{
    color: %(inverted_color)s;
    border-color: %(base_color)s;
    background-color: %(base_color)s;
    border-top-left-radius: {theme_var("border-radius")};
    border-top-right-radius: {theme_var("border-radius")};
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}}

QPushButton:checked:hover#assembly_button_drop_menu {{
    background-color: %(hover_color)s;
}}

QPushButton:checked:pressed#assembly_button_drop_menu {{
    background-color: %(pressed_color)s;
}}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": base_color,
                "inverted_color": inverted_color,
            }
        )
        widget.setObjectName("assembly_widget_drop_menu")
        widget.setStyleSheet(
            f"""QWidget#assembly_widget_drop_menu{{
            border: 1px solid %(base_color)s;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            background-color: {theme_var("background")};
            }}"""
            % {"base_color": base_color}
        )

    def set_table_row_color(self, table: QTableWidget, row_index: int, color: str):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))
