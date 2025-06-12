import contextlib
import os
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

import sympy
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QFont
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QDateEdit,
                             QHBoxLayout, QInputDialog, QLabel, QMenu,
                             QMessageBox, QPushButton, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from ui.custom_widgets import (CustomTableWidget, CustomTabWidget,
                               HumbleDoubleSpinBox, OrderStatusButton)
from ui.dialogs.add_sheet_dialog import AddSheetDialog
from ui.dialogs.edit_category_dialog import EditCategoryDialog
from ui.dialogs.set_component_order_pending_dialog import \
    SetComponentOrderPendingDialog
from ui.dialogs.set_custom_limit_dialog import SetCustomLimitDialog
from ui.dialogs.update_component_order_pending_dialog import \
    UpdateComponentOrderPendingDialog
from ui.icons import Icons
from ui.theme import theme_var
from ui.widgets.sheets_in_inventory_tab_UI import Ui_Form
from utils.inventory.category import Category
from utils.inventory.order import Order
from utils.inventory.sheet import Sheet
from utils.inventory.sheets_inventory import SheetsInventory
from utils.settings import Settings
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.threads.sheets_inventory.add_sheet import AddSheetThread

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class SheetsTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.set_editable_column_index([5, 8])
        headers: list[str] = [
            "Thickness",
            "Material",
            "Length",
            "Width",
            "Cost per Sheet",
            "Quantity in Stock",
            "Total Cost in Stock",
            "Orders",
            "Notes",
            "Modified Date",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)


class SheetsTabWidget(CustomTabWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)


class OrderWidget(QWidget):
    orderOpened = pyqtSignal()
    orderClosed = pyqtSignal()

    def __init__(self, sheet: Sheet, parent: "SheetsInInventoryTab"):
        super().__init__(parent)
        self.parent: "SheetsInInventoryTab" = parent
        self.sheet = sheet

        self.h_layout = QHBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_layout = QHBoxLayout()
        self.add_order_button = QPushButton("Add Order", self)
        self.add_order_button.clicked.connect(self.create_order)
        self.add_order_button.setFlat(True)
        self.add_order_button.setIcon(Icons.plus_icon)

        self.h_layout.addLayout(self.orders_layout)
        self.h_layout.addWidget(self.add_order_button)
        self.h_layout.addStretch()

        self.setLayout(self.h_layout)
        self.load_ui()

    def load_ui(self):
        self.clear_layout(self.orders_layout)

        for order in self.sheet.orders:
            v_layout = QVBoxLayout()
            v_layout.setContentsMargins(1, 1, 1, 1)
            v_layout.setSpacing(0)
            order_status_button = OrderStatusButton(self)
            order_status_button.setStyleSheet(
                "QPushButton#order_status{border-top-left-radius: 5px; border-top-right-radius: 5px; border-bottom-left-radius: 0; border-bottom-right-radius: 0;}"
            )
            order_status_button.setText(f"Order Pending ({int(order.quantity)})")
            order_status_button.setToolTip(str(order))
            order_status_button.setChecked(True)
            order_status_button.clicked.connect(
                partial(self.order_button_pressed, order, order_status_button)
            )

            year, month, day = map(int, order.expected_arrival_time.split("-"))
            date = QDate(year, month, day)

            arrival_date = QDateEdit(self)
            arrival_date.setStyleSheet(
                "QDateEdit{border-top-left-radius: 0; border-top-right-radius: 0; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;} QDateEdit:hover{border-color: #3bba6d; }"
            )
            arrival_date.wheelEvent = lambda event: self.parent.wheelEvent(event)
            arrival_date.setDate(date)
            arrival_date.setCalendarPopup(True)
            arrival_date.setToolTip("Expected arrival time.")
            arrival_date.dateChanged.connect(
                partial(self.date_changed, order, arrival_date)
            )

            v_layout.addWidget(order_status_button)
            v_layout.addWidget(arrival_date)
            self.orders_layout.addLayout(v_layout)
        self.parent.category_tables[self.parent.category].setColumnWidth(
            7, 400
        )  # Widgets don't like being resized with columns
        self.parent.update_sheet_row_color(
            self.parent.category_tables[self.parent.category], self.sheet
        )

    def create_order(self):
        select_date_dialog = SetComponentOrderPendingDialog(
            f'Set an expected arrival time for "{self.sheet.get_name()}," the number of parts ordered, and notes.',
            self,
        )
        if select_date_dialog.exec():
            new_order = Order(
                {
                    "expected_arrival_time": select_date_dialog.get_selected_date(),
                    "order_pending_quantity": select_date_dialog.get_order_quantity(),
                    "order_pending_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": select_date_dialog.get_notes(),
                }
            )
            self.sheet.add_order(new_order)
            self.parent.sheets_inventory.save_local_copy()
            self.parent.sync_changes()
            self.load_ui()

    def order_button_pressed(
        self, order: Order, order_status_button: OrderStatusButton
    ):
        self.orderOpened.emit()
        dialog = UpdateComponentOrderPendingDialog(
            order, f"Update order for {self.sheet.get_name()}", self
        )
        if dialog.exec():
            if dialog.action == "CANCEL_ORDER":
                self.sheet.remove_order(order)
            elif dialog.action == "UPDATE_ORDER":
                order.notes = dialog.get_notes()
                order.quantity = dialog.get_order_quantity()
            elif dialog.action == "ADD_INCOMING_QUANTITY":
                quantity_to_add = dialog.get_order_quantity()
                remaining_quantity = order.quantity - quantity_to_add
                old_quantity = self.sheet.quantity
                new_quantity = old_quantity + quantity_to_add
                self.sheet.quantity = new_quantity
                self.sheet.has_sent_warning = False
                self.sheet.latest_change_quantity = f"Used: Order pending - add quantity\nChanged from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                order.quantity = remaining_quantity
                if remaining_quantity <= 0:
                    msg = QMessageBox(
                        QMessageBox.Icon.Information,
                        "Order",
                        f"All the quantity from this order has been added, this order will now be removed from {self.sheet.get_name()}",
                        QMessageBox.StandardButton.Ok,
                        self,
                    )
                    if msg.exec():
                        self.sheet.remove_order(order)
            else:  # You never know.
                order_status_button.setChecked(True)
                self.orderClosed.emit()
                return
            self.parent.sheets_inventory.save_local_copy()
            self.parent.sync_changes()
            self.parent.sort_sheets()
            self.parent.select_last_selected_item()
            self.load_ui()
        else:  # Close order pressed
            order_status_button.setChecked(True)
            self.orderClosed.emit()

    def date_changed(self, order: Order, arrival_date: QDateEdit):
        order.expected_arrival_time = arrival_date.date().toString("yyyy-MM-dd")
        self.parent.sheets_inventory.save_local_copy()
        self.parent.sync_changes()

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())


class PopoutWidget(QWidget):
    def __init__(self, layout_to_popout: QVBoxLayout, parent=None):
        super().__init__(parent)
        self.parent: MainWindow = parent
        self.original_layout = layout_to_popout
        self.original_layout_parent: "SheetsInInventoryTab" = (
            self.original_layout.parentWidget()
        )
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Sheets In Inventory Tab")
        self.setLayout(self.original_layout)
        self.setObjectName("popout_widget")

    def closeEvent(self, event):
        if self.original_layout_parent:
            self.original_layout_parent.setLayout(self.original_layout)
            self.original_layout_parent.pushButton_popout.setIcon(Icons.dock_icon)
            self.original_layout_parent.pushButton_popout.clicked.disconnect()
            self.original_layout_parent.pushButton_popout.clicked.connect(
                self.original_layout_parent.popout
            )
        super().closeEvent(event)


class SheetsInInventoryTab(QWidget, Ui_Form):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent: MainWindow = parent
        self.sheets_inventory: SheetsInventory = self.parent.sheets_inventory
        self.sheet_settings: SheetSettings = self.parent.sheet_settings

        self.settings_file = Settings()

        self.tab_widget = SheetsTabWidget(self)

        self.category: Category = None
        self.finished_loading: bool = False
        self.category_tables: dict[Category, SheetsTableWidget] = {}
        self.table_sheets_widgets: dict[
            Sheet, dict[str, QTableWidgetItem | HumbleDoubleSpinBox | QComboBox | OrderWidget]
        ] = {}
        self.margins = (15, 15, 5, 5)  # top, bottom, left, right
        self.margin_format = f"margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;"
        self.last_selected_sheet: str = ""
        self.last_selected_index: int = 0
        self.load_ui()
        self.load_categories()
        self.restore_last_selected_tab()
        self.update_stock_costs()
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

        self.pushButton_add_new_sheet.clicked.connect(self.add_new_sheet)
        self.pushButton_add_new_sheet.setIcon(Icons.plus_circle_icon)

        self.verticalLayout_10.addWidget(self.tab_widget)
        self.checkBox_edit_sheets.toggled.connect(self.toggle_edit_mode)

        self.pushButton_popout.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.pushButton_popout.clicked.connect(self.popout)
        self.pushButton_popout.setIcon(Icons.dock_icon)

    def add_category(self):
        new_category_name, ok = QInputDialog.getText(
            self, "New Category", "Enter a name for a category:"
        )
        if new_category_name and ok:
            new_category = Category(new_category_name)
            self.sheets_inventory.add_category(new_category)
            table = SheetsTableWidget(self.tab_widget)
            self.category_tables.update({new_category: table})
            self.tab_widget.addTab(table, new_category.name)
            table.rowChanged.connect(self.table_changed)
            table.cellPressed.connect(self.table_selected_changed)
            self.sheets_inventory.save_local_copy()
            self.sync_changes()
            self.update_stock_costs()

    def remove_category(self):
        category_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove Category",
            "Select a category to remove",
            [category.name for category in self.sheets_inventory.get_categories()],
            editable=False,
        )
        if category_to_remove and ok:
            category = self.sheets_inventory.delete_category(category_to_remove)
            tab_index_to_remove = self.tab_widget.get_tab_order().index(
                category_to_remove
            )
            self.tab_widget.removeTab(tab_index_to_remove)
            self.clear_layout(self.category_tables[category])
            del self.category_tables[category]
            self.sheets_inventory.save_local_copy()
            self.sync_changes()
            self.update_stock_costs()

    def edit_category(self):
        edit_dialog = EditCategoryDialog(
            f"Edit {self.category.name}",
            f"Delete, duplicate, or rename: {self.category.name}.",
            self.category.name,
            self.category,
            self.sheets_inventory,
            self,
        )
        if edit_dialog.exec():
            action = edit_dialog.action
            input_text = edit_dialog.lineEditInput.text()
            if action == "DUPLICATE":
                new_name = input_text
                if new_name == self.category.name:
                    new_name += " - Copy"
                new_category = self.sheets_inventory.duplicate_category(
                    self.category, new_name
                )
                # self.sheets_inventory.add_category(new_category)
                table = SheetsTableWidget(self.tab_widget)
                self.category_tables.update({new_category: table})
                self.tab_widget.insertTab(
                    self.tab_widget.currentIndex() + 1, table, new_category.name
                )
                table.rowChanged.connect(self.table_changed)
                table.cellPressed.connect(self.table_selected_changed)
                self.sheets_inventory.save_local_copy()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "RENAME":
                self.category.rename(input_text)
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), input_text)
                self.sheets_inventory.save_local_copy()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "DELETE":
                self.clear_layout(self.category_tables[self.category])
                del self.category_tables[self.category]
                self.sheets_inventory.delete_category(self.category)
                self.tab_widget.removeTab(self.tab_widget.currentIndex())
                self.sheets_inventory.save_local_copy()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()

    def load_categories(self):
        self.settings_file.load_data()
        self.tab_widget.clear()
        self.category_tables.clear()
        all_categories = [
            category.name for category in self.sheets_inventory.get_categories()
        ]
        try:
            tab_order: list[str] = self.settings_file.get_value("category_tabs_order")[
                "Sheets In Inventory"
            ]
        except KeyError:
            tab_order = []

        # Updates the tab order to add categories that have not previously been added
        for category in all_categories:
            if category not in tab_order:
                tab_order.append(category)

        for tab in tab_order:
            if category := self.sheets_inventory.get_category(tab):
                table = SheetsTableWidget(self.tab_widget)
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

    def update_sheet(self, sheet_data: dict):
            if updated_sheet := self.sheets_inventory.update_sheet_data(sheet_data["id"], sheet_data): # Meaning the sheet already existed, but just got updated
                with contextlib.suppress(KeyError): # This happens when the updated sheet is not currently loaded. The UI will be updated when they switch tabs as the data for the sheet is updated.
                    self.update_sheet_table(self.category_tables[self.category], updated_sheet)
            else: # Meaning the sheet just got added
                # I don't think this will ever run.
                sheet = Sheet(sheet_data, self.sheets_inventory)
                self.sheets_inventory.sheets.append(sheet)
                self.add_sheet_to_table(self.category_tables[self.category], self.category_tables[self.category].rowCount(), sheet)

    def update_sheet_table(self, current_table: CustomTableWidget, sheet: Sheet):
        self.table_sheets_widgets[sheet]["thickness"].setCurrentText(sheet.thickness)
        self.table_sheets_widgets[sheet]["material"].setCurrentText(sheet.material)
        self.table_sheets_widgets[sheet]["length"].setValue(sheet.length)
        self.table_sheets_widgets[sheet]["width"].setValue(sheet.width)
        self.table_sheets_widgets[sheet]["cost"].setText(f"${self.sheets_inventory.get_sheet_cost(sheet):,.2f}")
        self.table_sheets_widgets[sheet]["quantity"].setText(f"{sheet.quantity:,.0f}")
        self.table_sheets_widgets[sheet]["total_cost_in_stock"].setText(f"${self.sheets_inventory.get_sheet_cost(sheet) * sheet.quantity:,.2f}")
        self.table_sheets_widgets[sheet]["order_widget"].load_ui()
        self.table_sheets_widgets[sheet]["notes"].setText(sheet.notes)
        self.table_sheets_widgets[sheet]["modified_date"].setText(sheet.latest_change_quantity)
        self.update_sheet_row_color(current_table, sheet)

    def add_sheet_to_table(
        self, current_table: CustomTableWidget, row_index: int, sheet: Sheet
    ):
        self.table_sheets_widgets.update({sheet: {}})
        self.table_sheets_widgets[sheet].update({"row": row_index})
        col_index: int = 0
        current_table.insertRow(row_index)
        current_table.setRowHeight(row_index, 60)

        # THICKNESS
        comboBox_thickness = QComboBox(self)
        comboBox_thickness.setEnabled(self.checkBox_edit_sheets.isChecked())
        comboBox_thickness.setStyleSheet("border-radius: none;")
        comboBox_thickness.wheelEvent = lambda event: event.ignore()
        comboBox_thickness.addItems(self.sheet_settings.get_thicknesses())
        comboBox_thickness.setCurrentText(sheet.thickness)
        comboBox_thickness.currentTextChanged.connect(
            partial(self.table_changed, row_index)
        )
        current_table.setCellWidget(row_index, col_index, comboBox_thickness)
        self.table_sheets_widgets[sheet].update({"thickness": comboBox_thickness})
        col_index += 1

        # MATERIAL
        comboBox_material = QComboBox(self)
        comboBox_material.setEnabled(self.checkBox_edit_sheets.isChecked())
        comboBox_material.setStyleSheet("border-radius: none;")
        comboBox_material.wheelEvent = lambda event: event.ignore()
        comboBox_material.addItems(self.sheet_settings.get_materials())
        comboBox_material.setCurrentText(sheet.material)
        comboBox_material.currentTextChanged.connect(
            partial(self.table_changed, row_index)
        )
        current_table.setCellWidget(row_index, col_index, comboBox_material)
        self.table_sheets_widgets[sheet].update({"material": comboBox_material})
        col_index += 1

        # LENGTH
        spinbox_length = HumbleDoubleSpinBox(self)
        spinbox_length.setEnabled(self.checkBox_edit_sheets.isChecked())
        spinbox_length.setDecimals(3)
        spinbox_length.setStyleSheet("border-radius: none;")
        spinbox_length.setValue(sheet.length)
        spinbox_length.valueChanged.connect(partial(self.table_changed, row_index))
        current_table.setCellWidget(row_index, col_index, spinbox_length)
        self.table_sheets_widgets[sheet].update({"length": spinbox_length})
        col_index += 1

        # WIDTH
        spinbox_width = HumbleDoubleSpinBox(self)
        spinbox_width.setEnabled(self.checkBox_edit_sheets.isChecked())
        spinbox_width.setDecimals(3)
        spinbox_width.setStyleSheet("border-radius: none;")
        spinbox_width.setValue(sheet.width)
        spinbox_width.valueChanged.connect(partial(self.table_changed, row_index))
        current_table.setCellWidget(row_index, col_index, spinbox_width)
        self.table_sheets_widgets[sheet].update({"width": spinbox_width})
        col_index += 1

        # COST
        cost_per_sheet = self.sheets_inventory.get_sheet_cost(sheet)
        table_item_cost = QTableWidgetItem(f"${cost_per_sheet:,.2f}")
        current_table.setItem(
            row_index,
            col_index,
            table_item_cost,
        )
        current_table.item(row_index, col_index).setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        current_table.item(row_index, col_index).setFont(self.tables_font)
        self.table_sheets_widgets[sheet].update({"cost": table_item_cost})
        col_index += 1

        # CURRENT QUANTITY
        table_item_quantity = QTableWidgetItem(f"{sheet.quantity:,.2f}")
        current_table.setItem(row_index, col_index, table_item_quantity)
        current_table.item(row_index, col_index).setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        current_table.item(row_index, col_index).setFont(self.tables_font)
        self.table_sheets_widgets[sheet].update({"quantity": table_item_quantity})
        col_index += 1

        # COST IN STOCK
        total_cost_in_stock = cost_per_sheet * sheet.quantity
        table_item_cost_in_stock = QTableWidgetItem(f"${total_cost_in_stock:,.2f}")
        current_table.setItem(row_index, col_index, table_item_cost_in_stock)
        current_table.item(row_index, col_index).setTextAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )
        current_table.item(row_index, col_index).setFont(self.tables_font)
        self.table_sheets_widgets[sheet].update(
            {"total_cost_in_stock": table_item_cost_in_stock}
        )
        col_index += 1

        # ORDERS
        order_widget = OrderWidget(sheet, self)
        order_widget.orderOpened.connect(self.block_table_signals)
        order_widget.orderClosed.connect(self.unblock_table_signals)
        current_table.setCellWidget(row_index, col_index, order_widget)
        self.table_sheets_widgets[sheet].update({"order_widget": order_widget})
        col_index += 1

        # NOTES
        table_item_notes = QTableWidgetItem(sheet.notes)
        current_table.setItem(row_index, col_index, table_item_notes)
        current_table.item(row_index, col_index).setFont(self.tables_font)
        self.table_sheets_widgets[sheet].update({"notes": table_item_notes})
        col_index += 1

        # MODIFIED DATE
        table_item_modified_date = QTableWidgetItem(sheet.latest_change_quantity)
        table_item_modified_date.setToolTip(sheet.latest_change_quantity)
        current_table.setItem(row_index, col_index, table_item_modified_date)
        current_table.item(row_index, col_index).setFont(self.tables_font)
        self.table_sheets_widgets[sheet].update(
            {"modified_date": table_item_modified_date}
        )

        self.update_sheet_row_color(current_table, sheet)


    def load_table(self):
        self.category = self.sheets_inventory.get_category(
            self.tab_widget.tabText(self.tab_widget.currentIndex())
        )
        current_table = self.category_tables[self.category]
        current_table.blockSignals(True)
        current_table.clearContents()
        current_table.setRowCount(0)
        self.table_sheets_widgets.clear()
        row_index = 0
        for group in self.sheets_inventory.get_all_sheets_material(
            self.sheets_inventory.get_sheets_by_category(self.category)
        ):
            current_table.insertRow(row_index)
            group_table_item = QTableWidgetItem(group)
            group_table_item.setTextAlignment(4)  # Align text center

            font = QFont()
            font.setPointSize(15)
            group_table_item.setFont(font)
            current_table.setItem(row_index, 0, group_table_item)
            current_table.setSpan(row_index, 0, 1, current_table.columnCount())
            self.set_table_row_color(
                current_table, row_index, f"{theme_var('background')}"
            )
            row_index += 1

            for sheet in self.sheets_inventory.get_sheets_by_category(self.category):
                if group != sheet.material:
                    continue
                self.add_sheet_to_table(current_table, row_index, sheet)
                row_index += 1

        current_table.blockSignals(False)

        current_table.resizeColumnsToContents()

        if current_table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            current_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(self)
            action = QAction(self)
            action.triggered.connect(self.set_custom_quantity_limit)
            action.setText("Set Custom Quantity Limit")
            menu.addAction(action)

            action = QAction(self)
            action.triggered.connect(self.print_selected_items)
            action.setText("Print Selected Sheets")
            menu.addAction(action)

            def delete_selected_sheets():
                selected_sheets = self.get_selected_sheets()
                if not selected_sheets:
                    return

                self.sheets_inventory.remove_sheets(selected_sheets, on_finished=self.load_table)

            action = QAction("Delete", self)
            action.triggered.connect(delete_selected_sheets)
            menu.addAction(action)

            current_table.customContextMenuRequested.connect(
                partial(self.open_group_menu, menu)
            )

        current_table.setColumnWidth(
            7, 400
        )  # Widgets don't like being resized with columns
        self.save_current_tab()
        self.save_category_tabs_order()
        self.restore_scroll_position()

    def block_table_signals(self):
        self.category_tables[self.category].blockSignals(True)

    def unblock_table_signals(self):
        self.category_tables[self.category].blockSignals(False)

    def table_selected_changed(self):
        if sheet := self.get_selected_sheet():
            self.last_selected_sheet = sheet.name
            self.last_selected_index = self.get_selected_row()

    def table_changed(self, row: int):
        sheet = next(
            (
                sheet
                for sheet, table_data in self.table_sheets_widgets.items()
                if table_data["row"] == row
            ),
            None,
        )
        if not sheet:
            return
        old_quantity = sheet.quantity
        sheet.quantity = float(
            sympy.sympify(
                self.table_sheets_widgets[sheet]["quantity"]
                .text()
                .strip()
                .replace(",", ""),
                evaluate=True,
            )
        )
        if old_quantity != sheet.quantity:
            sheet.has_sent_warning = False
            sheet.latest_change_quantity = f'{os.getlogin().title()} - Manually set to {sheet.quantity} from {old_quantity} quantity at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}'
        sheet.notes = self.table_sheets_widgets[sheet]["notes"].text()
        sheet.material = self.table_sheets_widgets[sheet]["material"].currentText()
        sheet.thickness = self.table_sheets_widgets[sheet]["thickness"].currentText()
        sheet.length = self.table_sheets_widgets[sheet]["length"].value()
        sheet.width = self.table_sheets_widgets[sheet]["width"].value()
        self.sheets_inventory.save_local_copy()
        self.sync_changes()
        self.category_tables[self.category].blockSignals(True)
        self.table_sheets_widgets[sheet]["quantity"].setText(f"{sheet.quantity:,.2f}")
        self.table_sheets_widgets[sheet]["modified_date"].setText(
            sheet.latest_change_quantity
        )
        self.category_tables[self.category].blockSignals(False)
        self.update_sheet_row_color(self.category_tables[self.category], sheet)
        self.update_sheet_costs()
        self.update_stock_costs()

    def toggle_edit_mode(self):
        for table_data in self.table_sheets_widgets.values():
            table_data["material"].setEnabled(self.checkBox_edit_sheets.isChecked())
            table_data["thickness"].setEnabled(self.checkBox_edit_sheets.isChecked())
            table_data["length"].setEnabled(self.checkBox_edit_sheets.isChecked())
            table_data["width"].setEnabled(self.checkBox_edit_sheets.isChecked())

    def add_new_sheet(self):
        add_sheet_dialog = AddSheetDialog(
            None, self.category, self.sheets_inventory, self.sheet_settings, self
        )

        if add_sheet_dialog.exec():
            new_sheet = Sheet(
                {
                    "quantity": add_sheet_dialog.get_quantity(),
                    "length": add_sheet_dialog.get_length(),
                    "width": add_sheet_dialog.get_width(),
                    "thickness": add_sheet_dialog.get_thickness(),
                    "material": add_sheet_dialog.get_material(),
                    "latest_change_quantity": f"Sheet added at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
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

            self.sheets_inventory.add_sheet(new_sheet)
            self.sheets_inventory.save_local_copy()
            self.sync_changes()
            self.sort_sheets()
            self.update_stock_costs()

    def update_sheet_costs(self):
        self.category_tables[self.category].blockSignals(True)
        for sheet, table_items in self.table_sheets_widgets.items():
            cost_per_sheet = self.sheets_inventory.get_sheet_cost(sheet)
            table_item_cost_in_stock = cost_per_sheet * sheet.quantity
            table_items["cost"].setText(f"${cost_per_sheet:,.2f}")
            table_items["total_cost_in_stock"].setText(
                f"${table_item_cost_in_stock:,.2f}"
            )
        self.category_tables[self.category].blockSignals(False)

    def set_custom_quantity_limit(self):
        current_table = self.category_tables[self.category]
        if sheets := self.get_selected_sheets():
            sheets_string = "".join(
                f"    {i + 1}. {sheet.get_name()}\n" for i, sheet in enumerate(sheets)
            )
            set_custom_limit_dialog = SetCustomLimitDialog(
                self,
                f"Set a custom red and yellow quantity limit for each of the {len(sheets)} selected sheets:\n{sheets_string}",
                sheets[0].red_quantity_limit,
                sheets[0].yellow_quantity_limit,
            )
            if set_custom_limit_dialog.exec():
                for sheet in sheets:
                    sheet.red_quantity_limit = set_custom_limit_dialog.get_red_limit()
                    sheet.yellow_quantity_limit = (
                        set_custom_limit_dialog.get_yellow_limit()
                    )
                    self.update_sheet_row_color(current_table, sheet)
                self.sheets_inventory.save_local_copy()
                self.sync_changes()

    def update_stock_costs(self):
        self.clear_layout(self.gridLayout_sheet_prices)
        grand_total: float = 0.0
        i: int = 0
        for i, category in enumerate(self.sheets_inventory.get_categories()):
            category_total = self.sheets_inventory.get_category_stock_cost(category)
            lbl = QLabel(f"{category.name}:", self)
            self.gridLayout_sheet_prices.addWidget(lbl, i, 0)
            lbl = QLabel(f"${category_total:,.2f}", self)
            # lbl.setTextInteractionFlags(Qt.ItemFlag.TextSelectableByMouse)
            self.gridLayout_sheet_prices.addWidget(lbl, i, 1)
            grand_total += category_total
            i += 1
        lbl = QLabel("Total:", self)
        lbl.setStyleSheet(
            f"border-top: 1px solid {theme_var('outline')}; border-bottom: 1px solid {theme_var('outline')}"
        )
        self.gridLayout_sheet_prices.addWidget(lbl, i + 1, 0)
        lbl = QLabel(f"${grand_total:,.2f}", self)
        lbl.setStyleSheet(
            f"border-top: 1px solid {theme_var('outline')}; border-bottom: 1px solid {theme_var('outline')}"
        )
        self.gridLayout_sheet_prices.addWidget(lbl, i + 1, 1)

    def select_last_selected_item(self):
        current_table = self.category_tables[self.category]
        for sheet, table_items in self.table_sheets_widgets.items():
            if sheet.name == self.last_selected_sheet:
                current_table.selectRow(table_items["row"])
                current_table.scrollTo(
                    current_table.model().index(table_items["row"], 0)
                )

    def get_selected_sheets(self) -> list[Sheet]:
        selected_sheets: list[Sheet] = []
        selected_rows = self.get_selected_rows()
        selected_sheets.extend(
            sheet
            for sheet, table_items in self.table_sheets_widgets.items()
            if table_items["row"] in selected_rows
        )
        return selected_sheets

    def get_selected_sheet(self) -> Sheet:
        selected_row = self.get_selected_row()
        for sheet, table_items in self.table_sheets_widgets.items():
            if table_items["row"] == selected_row:
                self.last_selected_index = selected_row
                self.last_selected_sheet = sheet.name
                return sheet

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
            "Sheet Name",
            "Qty in Stock",
            "Notes",
            "Order Status",
            "Modified Date",
        ]
        if sheets := self.get_selected_sheets():
            html = '<html><body><table style="width: 100%; border-collapse: collapse; text-align: left; vertical-align: middle; font-size: 12px; font-family: Verdana, Geneva, Tahoma, sans-serif;">'
            html += '<thead><tr style="border-bottom: 1px solid black;">'
            for header in headers:
                html += f"<th>{header}</th>"
            html += "</tr>"
            html += "</thead>"
            html += "<tbody>"
            for sheet in sheets:
                order_status = ""
                if sheet.orders:
                    for order in sheet.orders:
                        order_status += f"{order}<br>"
                else:
                    order_status = "No order is pending"
                html += f"""<tr style="border-bottom: 1px solid black;">
                <td>{sheet.get_name()}</td>
                <td>{sheet.quantity}</td>
                <td>{sheet.notes.replace("\n", "<br>")}</td>
                <td>{order_status}</td>
                <td>{sheet.latest_change_quantity.replace("\n", "<br>")}</td>
                </tr>"""
            html += "</tbody></table><body><html>"
            with open("print_selected_parts.html", "w", encoding="utf-8") as f:
                f.write(html)
            self.parent.open_print_selected_parts()

    def update_sheet_row_color(self, table, sheet: Sheet):
        if sheet.orders:
            self.set_table_row_color(
                table,
                self.table_sheets_widgets[sheet]["row"],
                f"{theme_var('table-order-pending')}",
            )
        elif sheet.quantity <= sheet.red_quantity_limit:
            self.set_table_row_color(
                table,
                self.table_sheets_widgets[sheet]["row"],
                f"{theme_var('table-red-quantity')}",
            )
        elif sheet.quantity <= sheet.yellow_quantity_limit:
            self.set_table_row_color(
                table,
                self.table_sheets_widgets[sheet]["row"],
                f"{theme_var('table-yellow-quantity')}",
            )
        else:
            self.set_table_row_color(
                table,
                self.table_sheets_widgets[sheet]["row"],
                f"{theme_var('background')}",
            )

    def set_table_row_color(self, table: SheetsTableWidget, row_index: int, color: str):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def sort_sheets(self):
        self.sheets_inventory.sort_by_thickness()
        self.load_table()

    def save_current_tab(self):
        if self.finished_loading:
            self.parent.sheets_inventory_tab_widget_last_selected_tab_index = (
                self.tab_widget.currentIndex()
            )

    def restore_last_selected_tab(self):
        if (
            self.tab_widget.currentIndex()
            == self.parent.sheets_inventory_tab_widget_last_selected_tab_index
        ):
            self.sort_sheets()  # * This happens when the last selected tab is the first tab
        else:
            self.tab_widget.setCurrentIndex(
                self.parent.sheets_inventory_tab_widget_last_selected_tab_index
            )

    def save_category_tabs_order(self):
        self.settings_file.load_data()
        tab_order = self.settings_file.get_value("category_tabs_order")
        tab_order["Sheets In Inventory"] = self.tab_widget.get_tab_order()
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

    def popout(self):
        self.popout_widget = PopoutWidget(self.layout(), self.parent)
        self.popout_widget.show()
        self.pushButton_popout.setIcon(Icons.redock_icon)
        self.pushButton_popout.clicked.disconnect()
        self.pushButton_popout.clicked.connect(self.popout_widget.close)

    def sync_changes(self):
        self.parent.sync_changes("sheets_in_inventory_tab")

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
