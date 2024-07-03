import contextlib
import os
from datetime import datetime
from functools import partial

import sympy
from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import CustomTableWidget, CustomTabWidget, FilterButton
from ui.dialogs.edit_category_dialog import EditCategoryDialog
from ui.dialogs.items_change_quantity_dialog import ItemsChangeQuantityDialog
from ui.dialogs.set_custom_limit_dialog import SetCustomLimitDialog
from utils.inventory.category import Category
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class EditLaserCutPart(QDialog):
    def __init__(self, laser_cut_part: LaserCutPart, parent=None):
        super().__init__(parent)
        self.laser_cut_part = laser_cut_part
        self.laser_cut_part_data = {}

        self.setWindowTitle(self.laser_cut_part.name)

        main_layout = QVBoxLayout(self)
        widget = QWidget()
        layout = QVBoxLayout(widget)  # Set the layout for the scrollable widget

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(widget)

        label = QLabel("Laser Cut Part Name:", widget)
        main_layout.addWidget(label)
        self.lineEdit_name = QLineEdit(widget)
        self.lineEdit_name.setText(self.laser_cut_part.name)
        main_layout.addWidget(self.lineEdit_name)

        label = QLabel("Laser Cut Part Data:", widget)
        main_layout.addWidget(label)
        main_layout.addWidget(scroll_area)  # Add the scroll area to the main layout

        grid_layout = QGridLayout()
        layout.addLayout(
            grid_layout
        )  # Add the grid layout to the scrollable widget's layout

        for row, (key, value) in enumerate(self.laser_cut_part.to_dict().items()):
            if key == "categories":
                continue
            label = QLabel(key, widget)
            if isinstance(value, str):
                edit = QLineEdit(widget)
                edit.setText(value)
            elif isinstance(value, float):
                edit = QDoubleSpinBox(widget)
                edit.wheelEvent = lambda event: None
                edit.setValue(value)
            elif isinstance(value, bool):
                edit = QCheckBox(widget)
                edit.setChecked(value)
            elif isinstance(value, int):
                edit = QDoubleSpinBox(widget)
                edit.wheelEvent = lambda event: None
                edit.setDecimals(0)
                edit.setValue(value)
            else:
                edit = QLabel(str(value), widget)

            self.laser_cut_part_data[key] = edit
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(edit, row, 1)

        btn_apply = QPushButton("Apply Changes", widget)
        btn_apply.clicked.connect(self.accept)
        main_layout.addWidget(btn_apply)

        btn_cancel = QPushButton("Cancel", widget)
        btn_cancel.clicked.connect(self.reject)
        main_layout.addWidget(btn_cancel)

        self.setMinimumWidth(600)
        self.setMinimumHeight(600)

    def get_data(self) -> dict[str, QCheckBox | QDoubleSpinBox | QLineEdit]:
        return self.laser_cut_part_data


class LaserCutPartsTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent: "LaserCutPartsTabWidget" = parent
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.part_name_column = 0
        self.price_column = 1
        self.unit_quantity_column = 2
        self.quantity_column = 3
        self.total_cost_in_stock_column = 4
        self.paint_column = 5
        self.paint_settings_column = 6
        self.shelf_number_column = 7
        self.modified_date_column = 8

        self.set_editable_column_index(
            [
                self.part_name_column,
                self.unit_quantity_column,
                self.quantity_column,
                self.shelf_number_column,
                self.modified_date_column,
            ]
        )
        headers: dict[str, int] = {
            "Part Name": self.part_name_column,
            "Price": self.price_column,
            "Quantity per Unit": self.unit_quantity_column,
            "Quantity in Stock": self.quantity_column,
            "Total Cost in Stock": self.total_cost_in_stock_column,
            "Paint": self.paint_column,
            "Paint Settings": self.paint_settings_column,
            "Shelf #": self.shelf_number_column,
            "Modified Date": self.modified_date_column,
        }
        self.setColumnCount(len(list(headers.keys())))
        self.setHorizontalHeaderLabels(headers)


class LaserCutPartsTabWidget(CustomTabWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.parent: "LaserCutTab" = parent


class PaintSettingsWidget(QWidget):
    def __init__(
        self, laser_cut_part: LaserCutPart, parent: LaserCutPartsTableWidget
    ) -> None:
        super().__init__(parent)
        self.parent: LaserCutPartsTableWidget = parent
        self.laser_cut_part = laser_cut_part
        self.paint_inventory = self.laser_cut_part.paint_inventory

        self.paint_settings_layout = QHBoxLayout(self)

        self.paint_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.paint_settings_layout.setSpacing(0)
        self.not_painted_label = QLabel("Not painted", self)
        self.paint_settings_layout.addWidget(self.not_painted_label)

        self.widget_primer = QWidget(self)
        self.widget_primer.setObjectName("widget_primer")
        self.widget_primer.setStyleSheet(
            "QWidget#widget_primer{border: 1px solid rgba(120, 120, 120, 70);}"
        )
        self.primer_layout = QGridLayout(self.widget_primer)
        self.primer_layout.setContentsMargins(3, 3, 3, 3)
        self.primer_layout.setSpacing(0)
        self.combobox_primer = QComboBox(self.widget_primer)
        self.combobox_primer.wheelEvent = lambda event: None
        self.combobox_primer.addItems(["None"] + self.paint_inventory.get_all_primers())
        if self.laser_cut_part.primer_name:
            self.combobox_primer.setCurrentText(self.laser_cut_part.primer_name)
        self.combobox_primer.currentTextChanged.connect(self.update_paint_settings)
        self.primer_layout.addWidget(QLabel("Primer:", self.widget_primer), 0, 0)
        self.primer_layout.addWidget(self.combobox_primer, 1, 0)
        self.widget_primer.setVisible(self.laser_cut_part.uses_primer)
        self.paint_settings_layout.addWidget(self.widget_primer)

        # PAINT COLOR
        self.widget_paint_color = QWidget(self)
        self.widget_paint_color.setObjectName("widget_paint_color")
        self.widget_paint_color.setStyleSheet(
            "QWidget#widget_paint_color{border: 1px solid rgba(120, 120, 120, 70);}"
        )
        self.paint_color_layout = QGridLayout(self.widget_paint_color)
        self.paint_color_layout.setContentsMargins(3, 3, 3, 3)
        self.paint_color_layout.setSpacing(0)
        self.combobox_paint_color = QComboBox(self.widget_paint_color)
        self.combobox_paint_color.wheelEvent = lambda event: None
        self.combobox_paint_color.addItems(
            ["None"] + self.paint_inventory.get_all_paints()
        )
        if self.laser_cut_part.paint_name:
            self.combobox_paint_color.setCurrentText(self.laser_cut_part.paint_name)
        self.combobox_paint_color.currentTextChanged.connect(self.update_paint_settings)
        self.paint_color_layout.addWidget(
            QLabel("Paint color:", self.widget_paint_color), 0, 0
        )
        self.paint_color_layout.addWidget(self.combobox_paint_color, 1, 0)
        self.widget_paint_color.setVisible(self.laser_cut_part.uses_paint)
        self.paint_settings_layout.addWidget(self.widget_paint_color)

        # POWDER COATING COLOR
        self.widget_powder_coating = QWidget(self)
        self.widget_powder_coating.setObjectName("widget_powder_coating")
        self.widget_powder_coating.setStyleSheet(
            "QWidget#widget_powder_coating{border: 1px solid rgba(120, 120, 120, 70);}"
        )
        self.powder_coating_layout = QGridLayout(self.widget_powder_coating)
        self.powder_coating_layout.setContentsMargins(3, 3, 3, 3)
        self.powder_coating_layout.setSpacing(0)
        self.combobox_powder_coating_color = QComboBox(self.widget_powder_coating)
        self.combobox_powder_coating_color.wheelEvent = lambda event: None
        self.combobox_powder_coating_color.addItems(
            ["None"] + self.paint_inventory.get_all_powders()
        )
        if self.laser_cut_part.powder_name:
            self.combobox_powder_coating_color.setCurrentText(
                self.laser_cut_part.powder_name
            )
        self.combobox_powder_coating_color.currentTextChanged.connect(
            self.update_paint_settings
        )
        self.powder_coating_layout.addWidget(
            QLabel("Powder color:", self.widget_powder_coating), 0, 0
        )
        self.powder_coating_layout.addWidget(self.combobox_powder_coating_color, 1, 0)
        self.widget_powder_coating.setVisible(self.laser_cut_part.uses_powder)
        self.paint_settings_layout.addWidget(self.widget_powder_coating)

        self.setLayout(self.paint_settings_layout)

    def update_paint_settings(self):
        self.laser_cut_part.paint_name = self.combobox_paint_color.currentText()
        self.laser_cut_part.primer_name = self.combobox_primer.currentText()
        self.laser_cut_part.powder_name = (
            self.combobox_powder_coating_color.currentText()
        )

        self.parent.resizeColumnsToContents()
        self.laser_cut_part.laser_cut_inventory.save()
        self.parent.parent.parent.sync_changes()


class PaintWidget(QWidget):
    def __init__(
        self,
        laser_cut_part: LaserCutPart,
        paint_settings_widget: PaintSettingsWidget,
        parent: LaserCutPartsTableWidget,
    ) -> None:
        super().__init__(parent)
        self.parent: LaserCutPartsTableWidget = parent

        self.laser_cut_part = laser_cut_part
        self.paint_settings_widget = paint_settings_widget

        layout = QVBoxLayout(self)

        self.checkbox_primer = QCheckBox("Primer", self)
        self.checkbox_primer.setChecked(self.laser_cut_part.uses_primer)
        self.checkbox_primer.checkStateChanged.connect(self.update_paint)
        self.checkbox_paint = QCheckBox("Paint", self)
        self.checkbox_paint.setChecked(self.laser_cut_part.uses_paint)
        self.checkbox_paint.checkStateChanged.connect(self.update_paint)
        self.checkbox_powder = QCheckBox("Powder", self)
        self.checkbox_powder.setChecked(self.laser_cut_part.uses_powder)
        self.checkbox_powder.checkStateChanged.connect(self.update_paint)

        layout.addWidget(self.checkbox_primer)
        layout.addWidget(self.checkbox_paint)
        layout.addWidget(self.checkbox_powder)

        self.setLayout(layout)

        self.paint_settings_widget.widget_primer.setVisible(
            self.laser_cut_part.uses_primer
        )
        self.paint_settings_widget.widget_paint_color.setVisible(
            self.laser_cut_part.uses_paint
        )
        self.paint_settings_widget.widget_powder_coating.setVisible(
            self.laser_cut_part.uses_powder
        )
        self.paint_settings_widget.not_painted_label.setVisible(
            not (
                self.laser_cut_part.uses_primer
                or self.laser_cut_part.uses_paint
                or self.laser_cut_part.uses_powder
            )
        )

        self.parent.resizeColumnsToContents()

    def update_paint(self):
        self.laser_cut_part.uses_primer = self.checkbox_primer.isChecked()
        self.laser_cut_part.uses_paint = self.checkbox_paint.isChecked()
        self.laser_cut_part.uses_powder = self.checkbox_powder.isChecked()

        self.paint_settings_widget.widget_primer.setVisible(
            self.laser_cut_part.uses_primer
        )
        self.paint_settings_widget.widget_paint_color.setVisible(
            self.laser_cut_part.uses_paint
        )
        self.paint_settings_widget.widget_powder_coating.setVisible(
            self.laser_cut_part.uses_powder
        )
        self.paint_settings_widget.not_painted_label.setVisible(
            not (
                self.laser_cut_part.uses_primer
                or self.laser_cut_part.uses_paint
                or self.laser_cut_part.uses_powder
            )
        )

        self.parent.resizeColumnsToContents()
        self.laser_cut_part.laser_cut_inventory.save()
        self.parent.parent.parent.sync_changes()


class LaserCutTab(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/laser_cut_tab.ui", self)
        from main import MainWindow

        self.parent: MainWindow = parent
        self.laser_cut_inventory: LaserCutInventory = self.parent.laser_cut_inventory
        self.paint_inventory = self.laser_cut_inventory.paint_inventory
        self.sheet_settings: SheetSettings = self.parent.sheet_settings

        self.settings_file = Settings()

        self.tab_widget = LaserCutPartsTabWidget(self)

        self.category: Category = None
        self.finished_loading: bool = False
        self.category_tables: dict[Category, LaserCutPartsTableWidget] = {}
        self.table_laser_cut_parts_widgets: dict[
            LaserCutPart, dict[str, QTableWidgetItem]
        ] = {}
        self.laser_cut_parts_filter: dict[str, list[FilterButton]] = {}

        self.last_selected_laser_cut_part: str = ""
        self.last_selected_index: int = 0

        self.splitter_2.setStretchFactor(0, 1)
        self.splitter_2.setStretchFactor(1, 0)

        self.load_ui()
        self.load_categories()
        self.update_all_laser_cut_parts_costs()
        self.restore_last_selected_tab()
        self.finished_loading = True

    def load_ui(self):
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

        self.gridLayout_laser_cut_parts_summary = self.findChild(
            QGridLayout, "gridLayout_laser_cut_parts_summary"
        )
        self.gridLayout_materials = self.findChild(QGridLayout, "gridLayout_materials")
        self.gridLayout_materials.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        self.gridLayout_thicknesses = self.findChild(
            QGridLayout, "gridLayout_thicknesses"
        )
        self.gridLayout_thicknesses.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )

        self.lineEdit_search_laser_cut_parts = self.findChild(
            QLineEdit, "lineEdit_search_parts_in_inventory"
        )
        self.pushButton_add_quantity = self.findChild(
            QPushButton, "pushButton_add_quantity"
        )
        self.pushButton_add_quantity.clicked.connect(
            partial(self.change_quantities, "ADD")
        )
        self.pushButton_remove_quantity = self.findChild(
            QPushButton, "pushButton_remove_quantity"
        )
        self.pushButton_remove_quantity.clicked.connect(
            partial(self.change_quantities, "REMOVE")
        )

        self.verticalLayout_11 = self.findChild(QVBoxLayout, "verticalLayout_11")
        self.clear_layout(self.verticalLayout_11)
        self.verticalLayout_11.addWidget(self.tab_widget)

        self.laser_cut_parts_filter.update({"materials": []})
        col = 0
        row = 0
        for material in self.sheet_settings.get_materials():
            button = FilterButton(material, self)
            button.clicked.connect(self.load_table)
            if col == 2:
                col = 0
                row += 1
            self.gridLayout_materials.addWidget(button, row, col)
            col += 1
            self.laser_cut_parts_filter["materials"].append(button)

        self.laser_cut_parts_filter.update({"thicknesses": []})
        col = 0
        row = 0
        for thickness in self.sheet_settings.get_thicknesses():
            button = FilterButton(thickness, self)
            button.clicked.connect(self.load_table)
            if col == 2:
                col = 0
                row += 1
            self.gridLayout_thicknesses.addWidget(button, row, col)
            col += 1
            self.laser_cut_parts_filter["thicknesses"].append(button)

        self.lineEdit_search_laser_cut_parts.textChanged.connect(self.load_table)
        autofill_search_options = natsorted(
            self.laser_cut_inventory.get_all_part_names()
        )
        completer = QCompleter(autofill_search_options, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.lineEdit_search_laser_cut_parts.setCompleter(completer)

        self.pushButton_add_quantity.setIcon(QIcon("icons/list_add.png"))
        self.pushButton_remove_quantity.setIcon(QIcon("icons/list_remove.png"))

    def add_category(self):
        new_category_name, ok = QInputDialog.getText(
            self, "New Category", "Enter a name for a category:"
        )
        if new_category_name in ["Recut", "Custom"]:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Aborting")
            msg.setText("Can't use that name.")
            msg.exec()
            return
        if new_category_name and ok:
            new_category = Category(new_category_name)
            self.laser_cut_inventory.add_category(new_category)
            table = LaserCutPartsTableWidget(self.tab_widget)
            self.category_tables.update({new_category: table})
            self.tab_widget.addTab(table, new_category.name)
            table.rowChanged.connect(self.table_changed)
            table.cellPressed.connect(self.table_selected_changed)
            self.laser_cut_inventory.save()
            self.sync_changes()
            self.load_categories()
            self.restore_last_selected_tab()

    def remove_category(self):
        category_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove Category",
            "Select a category to remove",
            [category.name for category in self.laser_cut_inventory.get_categories()],
            self.tab_widget.currentIndex(),
            False,
        )
        if category_to_remove in ["Recut", "Custom"]:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Aborting")
            msg.setText("Can't delete that category.")
            msg.exec()
            return
        if category_to_remove and ok:
            category = self.laser_cut_inventory.delete_category(category_to_remove)
            tab_index_to_remove = self.tab_widget.get_tab_order().index(
                category_to_remove
            )
            self.tab_widget.removeTab(tab_index_to_remove)
            self.clear_layout(self.category_tables[category])
            del self.category_tables[category]
            self.laser_cut_inventory.save()
            self.sync_changes()
            self.load_categories()
            self.restore_last_selected_tab()

    def edit_category(self):
        if self.category.name in ["Recut", "Custom"]:
            return
        edit_dialog = EditCategoryDialog(
            f"Edit {self.category.name}",
            f"Delete, duplicate, or rename: {self.category.name}.",
            self.category.name,
            self.category,
            self.laser_cut_inventory,
            self,
        )
        if edit_dialog.exec():
            action = edit_dialog.action
            input_text = edit_dialog.lineEditInput.text()
            if action == "DUPLICATE":
                new_name = input_text
                if new_name == self.category.name:
                    new_name += " - Copy"
                new_category = self.laser_cut_inventory.duplicate_category(
                    self.category, new_name
                )
                self.laser_cut_inventory.add_category(new_category)
                table = LaserCutPartsTableWidget(self.tab_widget)
                self.category_tables.update({new_category: table})
                self.tab_widget.insertTab(
                    self.tab_widget.currentIndex() + 1, table, new_category.name
                )
                table.rowChanged.connect(self.table_changed)
                table.cellPressed.connect(self.table_selected_changed)
                self.laser_cut_inventory.save()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "RENAME":
                self.category.rename(input_text)
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), input_text)
                self.laser_cut_inventory.save()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "DELETE":
                self.clear_layout(self.category_tables[self.category])
                del self.category_tables[self.category]
                self.laser_cut_inventory.delete_category(self.category)
                self.tab_widget.removeTab(self.tab_widget.currentIndex())
                self.laser_cut_inventory.save()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()

    def load_categories(self):
        self.settings_file.load_data()
        self.tab_widget.clear()
        self.category_tables.clear()
        all_categories = [
            category.name for category in self.laser_cut_inventory.get_categories()
        ]
        tab_order: list[str] = self.settings_file.get_value("category_tabs_order")[
            "Laser Cut Inventory"
        ]

        # Updates the tab order to add categories that have not previously been added
        for category in all_categories:
            if category not in tab_order:
                tab_order.append(category)

        for tab in tab_order:
            if category := self.laser_cut_inventory.get_category(tab):
                table = LaserCutPartsTableWidget(self.tab_widget)
                self.category_tables.update({category: table})
                self.tab_widget.addTab(table, category.name)
                table.rowChanged.connect(self.table_changed)
                table.cellPressed.connect(self.table_selected_changed)
                table.verticalScrollBar().valueChanged.connect(
                    self.save_scroll_position
                )
        self.tab_widget.currentChanged.connect(self.load_table)
        self.tab_widget.tabOrderChanged.connect(self.save_category_tabs_order)
        self.tab_widget.tabOrderChanged.connect(self.save_current_tab)
        self.tab_widget.tabBarDoubleClicked.connect(self.edit_category)
        self.tab_widget.addCategory.connect(self.add_category)
        self.tab_widget.removeCategory.connect(self.remove_category)
        # NOTE I know, just testing
        # self.update_category_total_stock_costs()

    def load_table(self):
        self.category: Category = self.laser_cut_inventory.get_category(
            self.tab_widget.tabText(self.tab_widget.currentIndex())
        )
        current_table = self.category_tables[self.category]
        current_table.blockSignals(True)
        current_table.clearContents()
        current_table.setRowCount(0)
        self.table_laser_cut_parts_widgets.clear()
        row_index = 0
        grouped_laser_cut_parts = self.laser_cut_inventory.get_group_categories(
            self.laser_cut_inventory.get_laser_cut_parts_by_category(self.category)
        )
        for group, laser_cut_parts in grouped_laser_cut_parts.items():
            group_material = group.split(";")[0]
            group_thickness = group.split(";")[1]
            group_name = group.replace(";", " ")

            if selected_materials := [
                button.text()
                for button in self.laser_cut_parts_filter["materials"]
                if button.isChecked()
            ]:
                if group_material not in selected_materials:
                    continue

            if selected_thicknesses := [
                button.text()
                for button in self.laser_cut_parts_filter["thicknesses"]
                if button.isChecked()
            ]:
                if group_thickness not in selected_thicknesses:
                    continue

            # We check to see if there are any items to show, if not, we dont loop through the group data
            for laser_cut_part in laser_cut_parts:
                if self.lineEdit_search_laser_cut_parts.text() in laser_cut_part.name:
                    break
            else:
                continue

            current_table.insertRow(row_index)
            item = QTableWidgetItem(group_name)
            item.setTextAlignment(4)  # Align text center
            font = QFont()
            font.setPointSize(15)
            item.setFont(font)
            current_table.setItem(row_index, 0, item)
            current_table.setSpan(row_index, 0, 1, current_table.columnCount())
            self.set_table_row_color(current_table, row_index, "#141414")
            row_index += 1
            for laser_cut_part in laser_cut_parts:
                if (
                    self.lineEdit_search_laser_cut_parts.text()
                    not in laser_cut_part.name
                ):
                    continue
                if selected_materials := [
                    button.text()
                    for button in self.laser_cut_parts_filter["materials"]
                    if button.isChecked()
                ]:
                    if laser_cut_part.material not in selected_materials:
                        continue

                if selected_thicknesses := [
                    button.text()
                    for button in self.laser_cut_parts_filter["thicknesses"]
                    if button.isChecked()
                ]:
                    if laser_cut_part.gauge not in selected_thicknesses:
                        continue

                current_table.insertRow(row_index)
                current_table.setRowHeight(row_index, 70)

                self.table_laser_cut_parts_widgets.update({laser_cut_part: {}})
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"row": row_index}
                )

                table_item_name = QTableWidgetItem(laser_cut_part.name)
                table_item_name.setFont(self.tables_font)
                table_item_name.setToolTip(
                    f"{laser_cut_part.geofile_name}\n\n Laser cut part is present in:\n{laser_cut_part.print_categories()}"
                )
                current_table.setItem(
                    row_index, current_table.part_name_column, table_item_name
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"name": table_item_name}
                )

                # PRICE
                table_item_price = QTableWidgetItem(f"${laser_cut_part.price:,.2f}")
                table_item_price.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                table_item_price.setFont(self.tables_font)
                current_table.setItem(
                    row_index, current_table.price_column, table_item_price
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"price": table_item_price}
                )

                # CATEGORY QUANTITY
                table_item_category_quantity = QTableWidgetItem(
                    f"{laser_cut_part.get_category_quantity(self.category):,.2f}"
                )
                table_item_category_quantity.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                table_item_category_quantity.setFont(self.tables_font)
                table_item_category_quantity.setToolTip(
                    f"Unit quantities:\n{laser_cut_part.print_category_quantities()}"
                )
                current_table.setItem(
                    row_index,
                    current_table.unit_quantity_column,
                    table_item_category_quantity,
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"unit_quantity": table_item_category_quantity}
                )

                # QUANTITY
                table_item_quantity = QTableWidgetItem(
                    f"{laser_cut_part.quantity:,.2f}"
                )
                table_item_quantity.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                table_item_quantity.setFont(self.tables_font)
                current_table.setItem(
                    row_index, current_table.quantity_column, table_item_quantity
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"quantity": table_item_quantity}
                )

                # TOTAL COST
                table_item_total_cost = QTableWidgetItem(
                    f"${(laser_cut_part.price*laser_cut_part.quantity):,.2f}"
                )
                table_item_total_cost.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                table_item_total_cost.setFont(self.tables_font)
                current_table.setItem(
                    row_index,
                    current_table.total_cost_in_stock_column,
                    table_item_total_cost,
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"total_cost": table_item_total_cost}
                )

                # PAINT SETTINGS
                paint_settings_widget = PaintSettingsWidget(
                    laser_cut_part, current_table
                )
                current_table.setCellWidget(
                    row_index,
                    current_table.paint_settings_column,
                    paint_settings_widget,
                )
                # PAINT
                paint_widget = PaintWidget(
                    laser_cut_part, paint_settings_widget, current_table
                )
                current_table.setCellWidget(
                    row_index,
                    current_table.paint_column,
                    paint_widget,
                )

                # SHELF NUMBER
                table_item_shelf_number = QTableWidgetItem(laser_cut_part.shelf_number)
                table_item_shelf_number.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                table_item_shelf_number.setFont(self.tables_font)
                current_table.setItem(
                    row_index,
                    current_table.shelf_number_column,
                    table_item_shelf_number,
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"shelf_number": table_item_shelf_number}
                )

                # MODFIED DATE
                table_item_modified_date = QTableWidgetItem(
                    laser_cut_part.modified_date
                )
                table_item_modified_date.setFont(self.tables_font)
                current_table.setItem(
                    row_index,
                    current_table.modified_date_column,
                    table_item_modified_date,
                )
                self.table_laser_cut_parts_widgets[laser_cut_part].update(
                    {"modified_date": table_item_modified_date}
                )

                if self.category.name != "Recut":
                    if laser_cut_part.quantity <= laser_cut_part.red_quantity_limit:
                        self.set_table_row_color(current_table, row_index, "#3F1E25")
                    elif (
                        laser_cut_part.quantity <= laser_cut_part.yellow_quantity_limit
                    ):
                        self.set_table_row_color(current_table, row_index, "#413C28")
                row_index += 1

        current_table.blockSignals(False)

        current_table.resizeColumnsToContents()

        if current_table.rowCount() == 0:
            current_table.insertRow(0)
            current_table.setItem(0, 0, QTableWidgetItem("Nothing to show"))
            current_table.item(0, 0).setFont(self.tables_font)
            current_table.resizeColumnsToContents()
            return

        self.save_current_tab()
        self.save_category_tabs_order()
        self.restore_scroll_position()

        self.load_context_menu()

    def load_assembly_menu(
        self, menu: QMenu, job: Job, assemblies: list[Assembly], level=0, prefix=""
    ):
        for i, assembly in enumerate(assemblies):
            is_last = i == len(assemblies) - 1
            next_assembly = None if is_last else assemblies[i + 1]
            has_next_assembly = next_assembly is not None

            action_text = prefix + ("├ " if has_next_assembly else "└ ") + assembly.name

            action = QAction(action_text, menu)
            action.triggered.connect(partial(self.add_to_assembly, job, assembly))
            menu.addAction(action)
            if assembly.sub_assemblies:
                sub_prefix = prefix + ("│   " if has_next_assembly else "    ")
                self.load_assembly_menu(
                    menu, job, assembly.sub_assemblies, level + 1, sub_prefix
                )

    def load_context_menu(self):
        current_table = self.category_tables[self.category]
        if current_table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
            return
        current_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu = QMenu(self)
        action = QAction("View Parts Data", self)
        action.triggered.connect(self.edit_laser_cut_part)
        menu.addAction(action)

        action = QAction(self)
        action.triggered.connect(self.print_selected_items)
        action.setText("Print Selected Parts")
        menu.addAction(action)

        action = QAction("Set Custom Quantity Limit", self)
        if self.category.name != "Recut":
            action.triggered.connect(self.set_custom_quantity_limit)
            menu.addAction(action)

        menu.addSeparator()

        def move_to_category(new_category: Category):
            if not (selected_laser_cut_parts := self.get_selected_laser_cut_parts()):
                return
            existing_laser_cut_parts: list[LaserCutPart] = []
            for laser_cut_part in selected_laser_cut_parts:
                if new_category in laser_cut_part.categories:
                    existing_laser_cut_parts.append(laser_cut_part)
            if existing_laser_cut_parts:
                message = f"The following laser cut parts will be ignored since they already exist in {new_category.name}:\n"
                for i, existing_part in enumerate(existing_laser_cut_parts):
                    message += f"  {i+1}. {existing_part.name}\n"
                msg = QMessageBox(self)
                msg.setWindowTitle("Exists")
                msg.setText(message)
                msg.setStandardButtons(
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                response = msg.exec()
                if response == QMessageBox.StandardButton.Cancel:
                    return
            for laser_cut_part in selected_laser_cut_parts:
                if laser_cut_part in existing_laser_cut_parts:
                    continue
                laser_cut_part.move_to_category(self.category, new_category)
                self.category_tables[self.category].blockSignals(True)
                self.table_laser_cut_parts_widgets[laser_cut_part][
                    "unit_quantity"
                ].setToolTip(
                    f"Unit quantities:\n{laser_cut_part.print_category_quantities()}"
                )
                self.table_laser_cut_parts_widgets[laser_cut_part]["name"].setToolTip(
                    f"{laser_cut_part.geofile_name}\n\n Laser cut part is present in:\n{laser_cut_part.print_categories()}"
                )
                self.category_tables[self.category].blockSignals(False)
            self.laser_cut_inventory.save()
            self.sync_changes()
            self.sort_laser_cut_parts()

        categories = QMenu(menu)
        categories.setTitle("Move selected parts to category")
        for _, category in enumerate(self.laser_cut_inventory.get_categories()):
            if category.name == "Recut":
                continue
            action = QAction(category.name, self)
            if self.category == category:
                action.setEnabled(False)
                action.setText(f"{category.name} - (You are here)")
            action.triggered.connect(partial(move_to_category, category))
            categories.addAction(action)
        menu.addMenu(categories)

        def copy_to_category(new_category: Category):
            if not (selected_laser_cut_parts := self.get_selected_laser_cut_parts()):
                return
            existing_laser_cut_parts: list[LaserCutPart] = []
            for laser_cut_part in selected_laser_cut_parts:
                if new_category in laser_cut_part.categories:
                    existing_laser_cut_parts.append(laser_cut_part)
            if existing_laser_cut_parts:
                message = f"The following laser cut parts will be ignored since they already exist in {new_category.name}:\n"
                for i, existing_part in enumerate(existing_laser_cut_parts):
                    message += f"  {i+1}. {existing_part.name}\n"
                msg = QMessageBox(self)
                msg.setWindowTitle("Exists")
                msg.setText(message)
                msg.setStandardButtons(
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                response = msg.exec()
                if response == QMessageBox.StandardButton.Cancel:
                    return
            for laser_cut_part in selected_laser_cut_parts:
                if laser_cut_part in existing_laser_cut_parts:
                    continue
                laser_cut_part.add_to_category(new_category)
                self.category_tables[self.category].blockSignals(True)
                self.table_laser_cut_parts_widgets[laser_cut_part][
                    "unit_quantity"
                ].setToolTip(
                    f"Unit quantities:\n{laser_cut_part.print_category_quantities()}"
                )
                self.table_laser_cut_parts_widgets[laser_cut_part]["name"].setToolTip(
                    f"{laser_cut_part.geofile_name}\n\n Laser cut part is present in:\n{laser_cut_part.print_categories()}"
                )
                self.category_tables[self.category].blockSignals(False)
            self.laser_cut_inventory.save()
            self.sync_changes()

        categories = QMenu(menu)
        categories.setTitle("Copy selected parts to category")
        for _, category in enumerate(self.laser_cut_inventory.get_categories()):
            if category.name == "Recut":
                continue
            action = QAction(category.name, self)
            if self.category == category:
                action.setEnabled(False)
                action.setText(f"{category.name} - (You are here)")
            action.triggered.connect(partial(copy_to_category, category))
            categories.addAction(action)
        menu.addMenu(categories)

        menu.addSeparator()

        def remove_parts_from_category():
            if not (selected_laser_cut_parts := self.get_selected_laser_cut_parts()):
                return
            for laser_cut_part in selected_laser_cut_parts:
                laser_cut_part.remove_from_category(self.category)
                if len(laser_cut_part.categories) == 0:
                    if self.category.name == "Recut":
                        self.laser_cut_inventory.remove_recut_part(laser_cut_part)
                    else:
                        self.laser_cut_inventory.remove_laser_cut_part(laser_cut_part)
            self.laser_cut_inventory.save()
            self.sync_changes()
            self.load_table()

        action = QAction(f"Remove selected parts from {self.category.name}", self)
        action.triggered.connect(remove_parts_from_category)
        menu.addAction(action)

        def delete_selected_parts():
            if not (selected_laser_cut_parts := self.get_selected_laser_cut_parts()):
                return
            if self.category.name == "Recut":
                for laser_cut_part in selected_laser_cut_parts:
                    self.laser_cut_inventory.remove_recut_part(laser_cut_part)
            else:
                for laser_cut_part in selected_laser_cut_parts:
                    self.laser_cut_inventory.remove_laser_cut_part(laser_cut_part)
            self.laser_cut_inventory.save()
            self.sync_changes()
            self.sort_laser_cut_parts()

        action = QAction("Delete selected parts from inventory", self)
        action.triggered.connect(delete_selected_parts)
        menu.addAction(action)

        def reset_selected_parts_quantity():
            if selected_laser_cut_parts := self.get_selected_laser_cut_parts():
                for laser_cut_part in selected_laser_cut_parts:
                    laser_cut_part.quantity = 0
                self.laser_cut_inventory.save()
                self.sync_changes()
                self.sort_laser_cut_parts()

        action = QAction("Set selected parts to zero quantity", self)
        action.triggered.connect(reset_selected_parts_quantity)
        menu.addAction(action)

        menu.addSeparator()

        job_planner_menu = QMenu("Add to Job", self)
        for job_widget in self.parent.job_planner_widget.job_widgets:
            job = job_widget.job
            job_menu = QMenu(job.name, job_planner_menu)
            for group in job.groups:
                group_menu = QMenu(group.name, job_menu)
                for assembly in group.assemblies:
                    self.load_assembly_menu(group_menu, job, [assembly])
                job_menu.addMenu(group_menu)
            job_planner_menu.addMenu(job_menu)

        menu.addMenu(job_planner_menu)

        # if self.category.name != "Recut":
        #     action1 = QAction("Generate Quote with Selected Parts", self)
        #     action1.triggered.connect(partial(self.generate_quote_with_selected_parts, current_table))
        #     menu.addAction(action1)
        #     action2 = QAction("Add Selected Parts to Quote", self)
        #     action2.triggered.connect(partial(self.add_selected_parts_to_quote, current_table))
        #     menu.addAction(action2)
        current_table.customContextMenuRequested.connect(
            partial(self.open_group_menu, menu)
        )

    def add_to_assembly(self, job: Job, assembly: Assembly):
        if laser_cut_parts := self.get_selected_laser_cut_parts():
            for laser_cut_part in laser_cut_parts:
                assembly.add_laser_cut_part(
                    LaserCutPart(
                        laser_cut_part.name,
                        laser_cut_part.to_dict(),
                        self.laser_cut_inventory,
                    )
                )
            job.changes_made()
            if len(laser_cut_parts) == 1:
                self.parent.status_button.setText(
                    f"Added {len(laser_cut_parts)} laser cut part to {job.name}", "lime"
                )
            else:
                self.parent.status_button.setText(
                    f"Added {len(laser_cut_parts)} laser cut parts to {job.name}",
                    "lime",
                )

    def table_selected_changed(self):
        if laser_cut_part := self.get_selected_laser_cut_part():
            self.last_selected_laser_cut_part = laser_cut_part.name
            self.last_selected_index = self.get_selected_row()

    def table_changed(self):
        if not (laser_cut_part := self.get_selected_laser_cut_part()):
            return
        old_quantity = laser_cut_part.quantity
        laser_cut_part.name = self.table_laser_cut_parts_widgets[laser_cut_part][
            "name"
        ].text()
        laser_cut_part.set_category_quantity(
            self.category,
            float(
                sympy.sympify(
                    self.table_laser_cut_parts_widgets[laser_cut_part]["unit_quantity"]
                    .text()
                    .strip()
                    .replace(",", ""),
                    evaluate=True,
                )
            ),
        )
        laser_cut_part.quantity = float(
            sympy.sympify(
                self.table_laser_cut_parts_widgets[laser_cut_part]["quantity"]
                .text()
                .strip()
                .replace(",", ""),
                evaluate=True,
            )
        )
        laser_cut_part.shelf_number = self.table_laser_cut_parts_widgets[
            laser_cut_part
        ]["shelf_number"].text()
        if old_quantity != laser_cut_part.quantity:
            laser_cut_part.modified_date = f"{os.getlogin().title()} - Manually set to {laser_cut_part.quantity} from {old_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        self.laser_cut_inventory.save()
        self.sync_changes()
        self.category_tables[self.category].blockSignals(True)
        self.table_laser_cut_parts_widgets[laser_cut_part]["unit_quantity"].setText(
            f"{laser_cut_part.get_category_quantity(self.category):,.2f}"
        )
        self.table_laser_cut_parts_widgets[laser_cut_part]["unit_quantity"].setToolTip(
            f"Unit quantities:\n{laser_cut_part.print_category_quantities()}"
        )
        self.table_laser_cut_parts_widgets[laser_cut_part]["quantity"].setText(
            f"{laser_cut_part.quantity:,.2f}"
        )
        self.table_laser_cut_parts_widgets[laser_cut_part]["modified_date"].setText(
            laser_cut_part.modified_date
        )
        self.category_tables[self.category].blockSignals(False)
        self.update_category_total_stock_costs()
        self.update_laser_cut_prices()

    def update_all_laser_cut_parts_costs(self):
        for laser_cut_part in self.laser_cut_inventory.laser_cut_parts:
            price_per_pound: float = self.sheet_settings.get_price_per_pound(
                laser_cut_part.material
            )
            cost_for_laser: float = self.sheet_settings.get_cost_for_laser(
                laser_cut_part.material
            )
            laser_cut_part.price = float(
                (laser_cut_part.machine_time * (cost_for_laser / 60))
                + (laser_cut_part.weight * price_per_pound)
            )
        self.laser_cut_inventory.save()
        self.sync_changes()

    def update_laser_cut_prices(self):
        self.category_tables[self.category].blockSignals(True)
        for laser_cut_part, table_items in self.table_laser_cut_parts_widgets.items():
            table_items["price"].setText(f"${laser_cut_part.price:,.2f}")
            table_items["total_cost"].setText(
                f"${laser_cut_part.price*laser_cut_part.quantity:,.2f}"
            )
        self.category_tables[self.category].blockSignals(False)

    def update_category_total_stock_costs(self) -> None:
        summary: dict[str, float] = {
            category.name: self.laser_cut_inventory.get_category_parts_total_stock_cost(
                category
            )
            for category in self.laser_cut_inventory.get_categories()
        } | {"Recut": self.laser_cut_inventory.get_recut_parts_total_stock_cost()}
        summary = dict(natsorted(summary.items()))

        self.clear_layout(self.gridLayout_laser_cut_parts_summary)
        row_index = 0
        for row_index, (category, category_total) in enumerate(summary.items()):
            lbl = QLabel(f"{category}:", self)
            self.gridLayout_laser_cut_parts_summary.addWidget(lbl, row_index, 0)
            lbl = QLabel(f"${category_total:,.2f}", self)
            self.gridLayout_laser_cut_parts_summary.addWidget(lbl, row_index, 1)

    def set_custom_quantity_limit(self) -> None:
        current_table = self.category_tables[self.category]
        if laser_cut_parts := self.get_selected_laser_cut_parts():
            laser_cut_parts_string = "".join(
                f"    {i + 1}. {laser_cut_part.name}\n"
                for i, laser_cut_part in enumerate(laser_cut_parts)
            )
            set_custom_limit_dialog = SetCustomLimitDialog(
                self,
                f"Set a custom red and yellow quantity limit for each of the {len(laser_cut_parts)} selected laser parts:\n{laser_cut_parts_string}",
                laser_cut_parts[0].red_quantity_limit,
                laser_cut_parts[0].yellow_quantity_limit,
            )
            if set_custom_limit_dialog.exec():
                for laser_cut_part in laser_cut_parts:
                    laser_cut_part.red_quantity_limit = (
                        set_custom_limit_dialog.get_red_limit()
                    )
                    laser_cut_part.yellow_quantity_limit = (
                        set_custom_limit_dialog.get_yellow_limit()
                    )
                    if laser_cut_part.quantity <= laser_cut_part.red_quantity_limit:
                        self.set_table_row_color(
                            current_table,
                            self.table_laser_cut_parts_widgets[laser_cut_part]["row"],
                            "#3F1E25",
                        )
                    elif (
                        laser_cut_part.quantity <= laser_cut_part.yellow_quantity_limit
                    ):
                        self.set_table_row_color(
                            current_table,
                            self.table_laser_cut_parts_widgets[laser_cut_part]["row"],
                            "#413C28",
                        )
                    else:
                        self.set_table_row_color(
                            current_table,
                            self.table_laser_cut_parts_widgets[laser_cut_part]["row"],
                            "#2c2c2c",
                        )
                self.laser_cut_inventory.save()
                self.sync_changes()

    def change_quantities(self, add_or_remove: str):
        selected_laser_cut_parts = self.get_selected_laser_cut_parts()
        dialog = ItemsChangeQuantityDialog(
            self.category.name, add_or_remove, selected_laser_cut_parts, self
        )
        if dialog.exec():
            multiplier: int = dialog.get_multiplier()
            option = dialog.get_option()
            if option == "Category":
                self.category_tables[self.category].blockSignals(True)
                for (
                    laser_cut_part,
                    tables_item,
                ) in self.table_laser_cut_parts_widgets.items():
                    if add_or_remove == "ADD":
                        laser_cut_part.modified_date = f"{os.getlogin().title()} Used: All Items in Category - add quantity. Changed from {laser_cut_part.quantity} to {laser_cut_part.quantity + (laser_cut_part.get_category_quantity(self.category) * multiplier)} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        laser_cut_part.quantity = laser_cut_part.quantity + (
                            multiplier
                            * laser_cut_part.get_category_quantity(self.category)
                        )
                    elif add_or_remove == "REMOVE":
                        laser_cut_part.modified_date = f"{os.getlogin().title()} Used: All Items in Category - remove quantity. Changed from {laser_cut_part.quantity} to {laser_cut_part.quantity - (laser_cut_part.get_category_quantity(self.category) * multiplier)} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        laser_cut_part.quantity = laser_cut_part.quantity - (
                            multiplier
                            * laser_cut_part.get_category_quantity(self.category)
                        )
                    tables_item["quantity"].setText(str(laser_cut_part.quantity))
                    tables_item["quantity"].setToolTip(laser_cut_part.modified_date)
                self.category_tables[self.category].blockSignals(False)
                self.laser_cut_inventory.save()
                self.sync_changes()
                self.update_all_laser_cut_parts_costs()
                self.select_last_selected_item()
            elif option == "Item":
                for laser_cut_part in selected_laser_cut_parts:
                    if add_or_remove == "ADD":
                        laser_cut_part.modified_date = f"{os.getlogin().title()} Used: Selected Item - add quantity. Changed from {laser_cut_part.quantity} to {laser_cut_part.quantity + multiplier} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        laser_cut_part.quantity += multiplier
                    elif add_or_remove == "REMOVE":
                        laser_cut_part.modified_date = f"{os.getlogin().title()} Used: Selected Item - remove quantity. Changed from {laser_cut_part.quantity} to {laser_cut_part.quantity - multiplier} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        laser_cut_part.quantity -= multiplier
                self.laser_cut_inventory.save()
                self.sync_changes()
                self.sort_laser_cut_parts()
                self.select_last_selected_item()

    def edit_laser_cut_part(self) -> None:
        if not (laser_cut_part := self.get_selected_laser_cut_part()):
            return
        item_dialog = EditLaserCutPart(laser_cut_part, self)
        if item_dialog.exec():
            self.update_laser_cut_part(item_dialog, laser_cut_part)

    def update_laser_cut_part(
        self, item_dialog: EditLaserCutPart, laser_cut_part: LaserCutPart
    ):
        new_name = item_dialog.lineEdit_name.text()
        item_data = item_dialog.get_data()
        categories: list[str] = [
            category.name for category in laser_cut_part.categories
        ]
        new_laser_cut_part_data = {}
        for key, value in item_data.items():
            if key == "categories":  # * to preserve the pointers
                continue
            if isinstance(value, QLineEdit):
                new_laser_cut_part_data[key] = value.text()
            elif isinstance(value, QDoubleSpinBox):
                new_laser_cut_part_data[key] = value.value()
            elif isinstance(value, QCheckBox):
                new_laser_cut_part_data[key] = value.isChecked()
        new_laser_cut_part_data["categories"] = categories  # * to preserve the pointers
        laser_cut_part.name = new_name
        laser_cut_part.load_data(new_laser_cut_part_data)
        self.laser_cut_inventory.save()
        self.sync_changes()
        self.sort_laser_cut_parts()

    def select_last_selected_item(self):
        current_table = self.category_tables[self.category]
        for laser_cut_part, table_items in self.table_laser_cut_parts_widgets.items():
            if laser_cut_part.name == self.last_selected_laser_cut_part:
                current_table.selectRow(table_items["row"])
                current_table.scrollTo(
                    current_table.model().index(table_items["row"], 0)
                )

    def get_selected_laser_cut_parts(self) -> list[LaserCutPart]:
        selected_laser_cut_parts: list[LaserCutPart] = []
        selected_rows = self.get_selected_rows()
        selected_laser_cut_parts.extend(
            laser_cut_part
            for laser_cut_part, table_items in self.table_laser_cut_parts_widgets.items()
            if table_items["row"] in selected_rows
        )
        return selected_laser_cut_parts

    def get_selected_laser_cut_part(self) -> LaserCutPart:
        selected_row = self.get_selected_row()
        for laser_cut_part, table_items in self.table_laser_cut_parts_widgets.items():
            if table_items["row"] == selected_row:
                self.last_selected_index = selected_row
                self.last_selected_laser_cut_part = laser_cut_part.name
                return laser_cut_part

    def get_selected_rows(self) -> list[int]:
        rows: set[int] = {
            item.row() for item in self.category_tables[self.category].selectedItems()
        }
        return list(rows)

    def get_selected_row(self) -> int:
        with contextlib.suppress(IndexError):
            return self.category_tables[self.category].selectedItems()[0].row()

    def print_selected_items(self):
        headers = [
            "Part Name",
            "Unit Qty",
            "Qty in Stock",
            "Painting",
            "Shelf #",
            "Modified Date",
        ]
        if laser_cut_parts := self.get_selected_laser_cut_parts():
            html = '<html><body><table style="width: 100%; border-collapse: collapse; text-align: left; vertical-align: middle; font-size: 12px; font-family: Verdana, Geneva, Tahoma, sans-serif;">'
            html += '<thead><tr style="border-bottom: 1px solid black;">'
            for header in headers:
                html += f"<th>{header}</th>"
            html += "</tr>"
            html += "</thead>"
            html += "<tbody>"
            for laser_cut_part in laser_cut_parts:
                paint_message = ""
                if laser_cut_part.uses_primer:
                    paint_message += f"Primer: {laser_cut_part.primer_name}\n"
                if laser_cut_part.uses_paint:
                    paint_message += f"Paint: {laser_cut_part.paint_name}\n"
                if laser_cut_part.uses_powder:
                    paint_message += f"Powder: {laser_cut_part.powder_name}\n"
                if not (
                    laser_cut_part.uses_primer
                    or laser_cut_part.uses_paint
                    or laser_cut_part.uses_powder
                ):
                    paint_message = "Not painted"
                html += f'''<tr style="border-bottom: 1px solid black;">
                <td>{laser_cut_part.name}</td>
                <td>{laser_cut_part.get_category_quantity(self.category)}</td>
                <td>{laser_cut_part.quantity}</td>
                <td>{paint_message.replace("\n", "<br>")}</td>
                <td>{laser_cut_part.shelf_number}</td>
                <td>{laser_cut_part.modified_date.replace("\n", "<br>")}</td></tr>'''
            html += "</tbody></table><body><html>"
        with open("print_selected_parts.html", "w", encoding="utf-8") as f:
            f.write(html)
        self.parent.open_print_selected_parts()

    def set_table_row_color(
        self, table: LaserCutPartsTableWidget, row_index: int, color: str
    ):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def sort_laser_cut_parts(self):
        self.laser_cut_inventory.sort_by_quantity()
        self.load_table()

    def save_current_tab(self):
        if self.finished_loading:
            self.parent.laser_cut_tab_widget_last_selected_tab_index = (
                self.tab_widget.currentIndex()
            )

    def restore_last_selected_tab(self):
        if (
            self.tab_widget.currentIndex()
            == self.parent.laser_cut_tab_widget_last_selected_tab_index
        ):
            self.sort_laser_cut_parts()  # * This happens when the last selected tab is the first tab
        else:
            self.tab_widget.setCurrentIndex(
                self.parent.laser_cut_tab_widget_last_selected_tab_index
            )

    def save_category_tabs_order(self):
        self.settings_file.load_data()
        tab_order = self.settings_file.get_value("category_tabs_order")
        tab_order["Laser Cut Inventory"] = self.tab_widget.get_tab_order()
        self.settings_file.set_value("category_tabs_order", tab_order)

    def save_scroll_position(self):
        if self.finished_loading:
            self.parent.save_scroll_position(
                self.category, self.category_tables[self.category]
            )

    def restore_scroll_position(self):
        if scroll_position := self.parent.get_scroll_position(self.category):
            self.category_tables[self.category].verticalScrollBar().setValue(
                scroll_position
            )

    def sync_changes(self):
        self.parent.sync_changes()

    def open_group_menu(self, menu: QMenu) -> None:
        menu.exec(QCursor.pos())

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
