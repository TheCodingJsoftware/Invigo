import contextlib
import os
from datetime import datetime
from functools import partial

import sympy
from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCompleter,
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import (
    CustomTableWidget,
    CustomTabWidget,
    ExchangeRateComboBox,
    NotesPlainTextEdit,
    OrderStatusButton,
    POPushButton,
    PriorityComboBox,
)
from ui.dialogs.add_item_dialog import AddItemDialog
from ui.dialogs.edit_category_dialog import EditCategoryDialog
from ui.dialogs.items_change_quantity_dialog import ItemsChangeQuantityDialog
from ui.dialogs.select_item_dialog import SelectItemDialog
from ui.dialogs.set_component_order_pending_dialog import SetComponentOrderPendingDialog
from ui.dialogs.set_custom_limit_dialog import SetCustomLimitDialog
from ui.dialogs.update_component_order_pending_dialog import (
    UpdateComponentOrderPendingDialog,
)
from utils.dialog_buttons import DialogButtons
from utils.history_file import HistoryFile
from utils.inventory.category import Category
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.order import Order
from utils.po import get_all_po
from utils.po_template import POTemplate
from utils.settings import Settings
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class ComponentsTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setWordWrap(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.set_editable_column_index([0, 1, 2, 3, 4, 9])
        headers: list[str] = [
            "Part Name",
            "Part Number",
            "Quantity per Unit",
            "Quantity in Stock",
            "Item Price",
            "USD/CAD",
            "Total Cost in Stock",
            "Total Unit Cost",
            "Priority",
            "Shelf #",
            "Notes",
            "PO",
            "Orders",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)


class ComponentsTabWidget(CustomTabWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)


class OrderWidget(QWidget):
    def __init__(self, component: Component, parent: "ComponentsTab") -> None:
        super().__init__(parent)
        self.parent: "ComponentsTab" = parent
        self.component = component

        self.h_layout = QHBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_layout = QHBoxLayout()
        self.add_order_button = QPushButton("Add Order", self)
        self.add_order_button.clicked.connect(self.create_order)

        self.h_layout.addLayout(self.orders_layout)
        self.h_layout.addWidget(self.add_order_button)
        self.h_layout.addStretch()

        self.setLayout(self.h_layout)
        self.load_ui()

    def load_ui(self):
        self.clear_layout(self.orders_layout)

        for order in self.component.orders:
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
            arrival_date.wheelEvent = lambda event: None
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
            12, 400
        )  # Widgets don't like being resized with columns
        self.parent.update_component_row_color(
            self.parent.category_tables[self.parent.category], self.component
        )

    def create_order(self):
        select_date_dialog = SetComponentOrderPendingDialog(
            f'Set an expected arrival time for "{self.component.part_name}," the number of parts ordered, and notes.',
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
            self.component.add_order(new_order)
            self.parent.components_inventory.save()
            self.parent.sync_changes()
            self.load_ui()

    def order_button_pressed(
        self, order: Order, order_status_button: OrderStatusButton
    ):
        dialog = UpdateComponentOrderPendingDialog(
            order, f"Update order for {self.component.part_name}", self
        )
        if dialog.exec():
            if dialog.action == "CANCEL_ORDER":
                self.component.remove_order(order)
            elif dialog.action == "UPDATE_ORDER":
                order.notes = dialog.get_notes()
                order.quantity = dialog.get_order_quantity()
            elif dialog.action == "ADD_INCOMING_QUANTITY":
                quantity_to_add = dialog.get_order_quantity()
                remaining_quantity = order.quantity - quantity_to_add
                old_quantity = self.component.quantity
                new_quantity = old_quantity + quantity_to_add
                self.component.quantity = new_quantity
                self.component.latest_change_quantity = f"Used: Order pending - add quantity\nChanged from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                order.quantity = remaining_quantity
                if remaining_quantity <= 0:
                    msg = QMessageBox(
                        QMessageBox.Icon.Information,
                        "Order",
                        f"All the quantity from this order has been added, this order will now be removed from {self.component.part_name}",
                        QMessageBox.StandardButton.Ok,
                        self,
                    )
                    if msg.exec():
                        self.component.remove_order(order)
            else:  # You never know.
                order_status_button.setChecked(True)
                return
            self.parent.components_inventory.save()
            self.parent.sync_changes()
            self.parent.sort_components()
            self.parent.select_last_selected_item()
            self.load_ui()
        else:  # Close order pressed
            order_status_button.setChecked(True)

    def date_changed(self, order: Order, arrival_date: QDateEdit):
        order.expected_arrival_time = arrival_date.date().toString("yyyy-MM-dd")
        self.parent.components_inventory.save()
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


class ComponentsTab(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/components_tab.ui", self)
        from main import MainWindow

        self.parent: MainWindow = parent
        self.components_inventory: ComponentsInventory = (
            self.parent.components_inventory
        )

        self.settings_file = Settings()

        self.tab_widget = ComponentsTabWidget(self)

        self.category: Category = None
        self.finished_loading: bool = False
        self.category_tables: dict[Category, ComponentsTableWidget] = {}
        self.table_components_widgets: dict[
            Component,
            dict[
                str,
                QTableWidgetItem
                | PriorityComboBox
                | ExchangeRateComboBox
                | NotesPlainTextEdit,
            ],
        ] = {}
        self.po_buttons: list[POPushButton] = []
        self.margins = (15, 15, 5, 5)  # top, bottom, left, right
        self.margin_format = f"margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;"
        self.last_selected_component: str = ""
        self.last_selected_index: int = 0

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        self.load_ui()
        self.load_categories()
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

        self.label_exchange_price = self.findChild(QLabel, "label_exchange_price")
        self.label_total_unit_cost = self.findChild(QLabel, "label_total_unit_cost")
        self.gridLayout_category_stock_costs = self.findChild(
            QGridLayout, "gridLayout_category_stock_costs"
        )
        self.lineEdit_search_items = self.findChild(QLineEdit, "lineEdit_search_items")
        self.listWidget_itemnames = self.findChild(QListWidget, "listWidget_itemnames")
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
        self.pushButton_create_new = self.findChild(
            QPushButton, "pushButton_create_new"
        )
        self.verticalLayout = self.findChild(QVBoxLayout, "verticalLayout")
        self.verticalLayout.addWidget(self.tab_widget)

        self.lineEdit_search_items.textChanged.connect(
            self.update_edit_inventory_list_widget
        )

        self.pushButton_create_new.clicked.connect(self.add_item)
        self.pushButton_add_quantity.setIcon(QIcon("./icons/list_add.png"))
        self.pushButton_remove_quantity.setIcon(QIcon("./icons/list_remove.png"))

        self.listWidget_itemnames.itemSelectionChanged.connect(
            self.listWidget_item_changed
        )

    def add_category(self):
        new_category_name, ok = QInputDialog.getText(
            self, "New Category", "Enter a name for a category:"
        )
        if new_category_name and ok:
            new_category = Category(new_category_name)
            self.components_inventory.add_category(new_category)
            table = ComponentsTableWidget(self.tab_widget)
            self.category_tables.update({new_category: table})
            self.tab_widget.addTab(table, new_category.name)
            table.rowChanged.connect(self.table_changed)
            table.cellPressed.connect(self.table_selected_changed)
            self.components_inventory.save()
            self.sync_changes()
            self.update_category_total_stock_costs()
            self.load_categories()
            self.restore_last_selected_tab()

    def remove_category(self):
        category_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove Category",
            "Select a category to remove",
            [category.name for category in self.components_inventory.get_categories()],
            self.tab_widget.currentIndex(),
            False,
        )
        if category_to_remove and ok:
            category = self.components_inventory.delete_category(category_to_remove)
            tab_index_to_remove = self.tab_widget.get_tab_order().index(
                category_to_remove
            )
            self.tab_widget.removeTab(tab_index_to_remove)
            self.clear_layout(self.category_tables[category])
            del self.category_tables[category]
            self.components_inventory.save()
            self.sync_changes()
            self.update_category_total_stock_costs()
            self.load_categories()
            self.restore_last_selected_tab()

    def edit_category(self):
        edit_dialog = EditCategoryDialog(
            f"Edit {self.category.name}",
            f"Delete, duplicate, or rename: {self.category.name}.",
            self.category.name,
            self.category,
            self.components_inventory,
            self,
        )
        if edit_dialog.exec():
            action = edit_dialog.action
            input_text = edit_dialog.lineEditInput.text()
            if action == "DUPLICATE":
                new_name = input_text
                if new_name == self.category.name:
                    new_name += " - Copy"
                new_category = self.components_inventory.duplicate_category(
                    self.category, new_name
                )
                self.components_inventory.add_category(new_category)
                table = ComponentsTableWidget(self.tab_widget)
                self.category_tables.update({new_category: table})
                self.tab_widget.insertTab(
                    self.tab_widget.currentIndex() + 1, table, new_category.name
                )
                table.rowChanged.connect(self.table_changed)
                table.cellPressed.connect(self.table_selected_changed)
                self.components_inventory.save()
                self.sync_changes()
                self.update_category_total_stock_costs()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "RENAME":
                self.category.rename(input_text)
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), input_text)
                self.components_inventory.save()
                self.sync_changes()
                self.update_category_total_stock_costs()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "DELETE":
                self.clear_layout(self.category_tables[self.category])
                del self.category_tables[self.category]
                self.components_inventory.delete_category(self.category)
                self.tab_widget.removeTab(self.tab_widget.currentIndex())
                self.components_inventory.save()
                self.sync_changes()
                self.update_category_total_stock_costs()
                self.load_categories()
                self.restore_last_selected_tab()

    def load_categories(self):
        self.settings_file.load_data()
        self.tab_widget.clear()
        self.category_tables.clear()
        all_categories = [
            category.name for category in self.components_inventory.get_categories()
        ]
        tab_order: list[str] = self.settings_file.get_value("category_tabs_order")[
            "Components"
        ]

        # Updates the tab order to add categories that have not previously been added
        for category in all_categories:
            if category not in tab_order:
                tab_order.append(category)

        for tab in tab_order:
            if category := self.components_inventory.get_category(tab):
                table = ComponentsTableWidget(self.tab_widget)
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

    def load_table(self):
        self.category: Category = self.components_inventory.get_category(
            self.tab_widget.tabText(self.tab_widget.currentIndex())
        )
        self.po_buttons.clear()
        current_table = self.category_tables[self.category]
        current_table.blockSignals(True)
        current_table.clearContents()
        current_table.setRowCount(0)
        self.table_components_widgets.clear()
        po_menu = QMenu(self)
        for po in get_all_po():
            po_menu.addAction(po, partial(self.open_po, po))
        row_index = 0
        for component in self.components_inventory.components:
            if self.category not in component.categories:
                continue

            self.table_components_widgets.update({component: {}})
            self.table_components_widgets[component].update({"row": row_index})

            col_index: int = 0

            current_table.insertRow(row_index)
            current_table.setRowHeight(row_index, 60)

            # PART NAME
            table_item_part_name = QTableWidgetItem(component.part_name)
            table_item_part_name.setFont(self.tables_font)
            table_item_part_name.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            table_item_part_name.setToolTip(
                f"{component.part_name}\n\nComponent is present in:\n{component.print_categories()}"
            )
            current_table.setItem(row_index, col_index, table_item_part_name)
            self.table_components_widgets[component].update(
                {"part_name": table_item_part_name}
            )

            col_index += 1

            # PART NUMBER
            table_item_part_number = QTableWidgetItem(component.part_number)
            table_item_part_number.setFont(self.tables_font)
            table_item_part_number.setToolTip(
                f"{component.part_number}\n\nComponent is present in:\n{component.print_categories()}"
            )
            table_item_part_number.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            current_table.setItem(row_index, col_index, table_item_part_number)
            self.table_components_widgets[component].update(
                {"part_number": table_item_part_number}
            )

            col_index += 1

            # CATEGORY QUANTITY
            table_item_category_quantity = QTableWidgetItem(
                f"{component.get_category_quantity(self.category):,.2f}"
            )
            table_item_category_quantity.setFont(self.tables_font)
            table_item_category_quantity.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            table_item_category_quantity.setToolTip(
                f"Unit quantities:\n{component.print_category_quantities()}"
            )
            current_table.setItem(row_index, col_index, table_item_category_quantity)
            self.table_components_widgets[component].update(
                {"unit_quantity": table_item_category_quantity}
            )

            col_index += 1

            # ITEM QUANTITY
            table_item_quantity = QTableWidgetItem(f"{component.quantity:,.2f}")
            table_item_quantity.setFont(self.tables_font)
            if not component.latest_change_quantity:
                component.latest_change_quantity = "Nothing recorded"
            table_item_quantity.setToolTip(component.latest_change_quantity)
            table_item_quantity.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            current_table.setItem(row_index, col_index, table_item_quantity)
            self.table_components_widgets[component].update(
                {"quantity": table_item_quantity}
            )

            col_index += 1

            # PRICE
            converted_price: float = (
                component.price * self.get_exchange_rate()
                if component.use_exchange_rate
                else component.price / self.get_exchange_rate()
            )

            table_item_price = QTableWidgetItem(
                f'${component.price:,.2f} {"USD" if component.use_exchange_rate else "CAD"}'
            )
            table_item_price.setFont(self.tables_font)
            table_item_price.setToolTip(
                f'${converted_price:,.2f} {"CAD" if component.use_exchange_rate else "USD"}\n{component.latest_change_price}'
            )
            table_item_price.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            current_table.setItem(
                row_index,
                col_index,
                table_item_price,
            )
            self.table_components_widgets[component].update({"price": table_item_price})

            col_index += 1

            # EXCHANGE RATE
            combo_exchange_rate = ExchangeRateComboBox(
                parent=self,
                selected_item="USD" if component.use_exchange_rate else "CAD",
            )
            combo_exchange_rate.currentIndexChanged.connect(
                partial(self.table_changed, row_index)
            )
            combo_exchange_rate.setStyleSheet("border-radius: 0px;")
            # layout.addWidget(combo_exchange_rate)
            current_table.setCellWidget(row_index, col_index, combo_exchange_rate)
            self.table_components_widgets[component].update(
                {"use_exchange_rate": combo_exchange_rate}
            )

            col_index += 1

            # TOTAL COST
            table_item_total_cost_in_stock = QTableWidgetItem(
                f"${component.get_total_cost_in_stock():,.2f} {combo_exchange_rate.currentText()}"
            )
            table_item_total_cost_in_stock.setFont(self.tables_font)
            table_item_total_cost_in_stock.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            current_table.setItem(
                row_index,
                col_index,
                table_item_total_cost_in_stock,
            )
            self.table_components_widgets[component].update(
                {"total_cost_in_stock": table_item_total_cost_in_stock}
            )

            col_index += 1

            # TOTAL UNIT COST
            table_item_total_unit_cost = QTableWidgetItem(
                f"${component.get_total_unit_cost(self.category):,.2f} {combo_exchange_rate.currentText()}"
            )
            table_item_total_unit_cost.setFont(self.tables_font)
            table_item_total_unit_cost.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            current_table.setItem(
                row_index,
                col_index,
                table_item_total_unit_cost,
            )
            self.table_components_widgets[component].update(
                {"total_unit_cost": table_item_total_unit_cost}
            )

            col_index += 1

            # PRIORITY
            combo_priority = PriorityComboBox(self, component.priority)
            combo_priority.setStyleSheet("border-radius: 0px;")
            if combo_priority.currentText() == "Medium":
                combo_priority.setStyleSheet(
                    "QComboBox{background-color: #524b2f; border-radius: 0px;} QComboBox:hover{border-color: #e9bb3d;}"
                )
            elif combo_priority.currentText() == "High":
                combo_priority.setStyleSheet(
                    "QComboBox{background-color: #4d2323; border-radius: 0px;} QComboBox:hover{border-color: #e93d3d;}"
                )
            combo_priority.currentIndexChanged.connect(
                partial(self.table_changed, row_index)
            )
            current_table.setCellWidget(row_index, col_index, combo_priority)
            self.table_components_widgets[component].update(
                {"priority": combo_priority}
            )

            col_index += 1

            # SHELF NUMBER
            table_item_shelf_number = QTableWidgetItem(component.shelf_number)
            table_item_shelf_number.setFont(self.tables_font)
            table_item_shelf_number.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            current_table.setItem(row_index, col_index, table_item_shelf_number)
            self.table_components_widgets[component].update(
                {"shelf_number": table_item_shelf_number}
            )

            col_index += 1

            # NOTES
            text_notes = NotesPlainTextEdit(self, component.notes, "")
            text_notes.textChanged.connect(partial(self.table_changed, row_index))
            current_table.setCellWidget(row_index, col_index, text_notes)
            self.table_components_widgets[component].update({"notes": text_notes})

            col_index += 1

            # PURCHASE ORDER
            btn_po = POPushButton(self)
            btn_po.setMenu(po_menu)
            btn_po.setStyleSheet("border-radius: 0px;")
            current_table.setCellWidget(row_index, col_index, btn_po)
            self.po_buttons.append(btn_po)

            col_index += 1

            # ORDER WIDGET
            order_widget = OrderWidget(component, self)
            current_table.setCellWidget(row_index, col_index, order_widget)

            self.update_component_row_color(current_table, component)

            row_index += 1

        current_table.blockSignals(False)

        current_table.resizeColumnsToContents()
        current_table.setColumnWidth(0, 250)
        current_table.setColumnWidth(1, 150)

        self.load_context_menu()

        self.update_edit_inventory_list_widget()
        self.update_search_suggestions()
        self.update_category_total_stock_costs()
        self.update_components_costs()

        self.save_current_tab()
        self.save_category_tabs_order()
        self.restore_scroll_position()

    def table_selected_changed(self):
        if component := self.get_selected_component():
            self.last_selected_component = component.name
            self.last_selected_index = self.get_selected_row()

    def table_changed(self, row):
        if not (component := self.get_selected_component()):
            return
        component.part_name = self.table_components_widgets[component][
            "part_name"
        ].text()
        component.part_number = self.table_components_widgets[component][
            "part_number"
        ].text()
        try:
            new_unit_quantity = float(
                sympy.sympify(
                    self.table_components_widgets[component]["unit_quantity"]
                    .text()
                    .strip()
                    .replace(",", ""),
                    evaluate=True,
                )
            )
        except sympy.SympifyError:
            self.set_table_row_color(
                self.category_tables[self.category],
                self.table_components_widgets[component]["row"],
                "#e93d3d",
            )
            self.parent.status_button.setText(
                f"Invalid number for {component.name} unit quantity", "red"
            )
            return
        try:
            table_quantity = float(
                sympy.sympify(
                    self.table_components_widgets[component]["quantity"]
                    .text()
                    .strip()
                    .replace(",", ""),
                    evaluate=True,
                )
            )
        except sympy.SympifyError:
            self.set_table_row_color(
                self.category_tables[self.category],
                self.table_components_widgets[component]["row"],
                "#e93d3d",
            )
            self.parent.status_button.setText(
                f"Invalid number for {component.name} quantity", "red"
            )
            return

        try:
            new_price = float(
                sympy.sympify(
                    self.table_components_widgets[component]["price"]
                    .text()
                    .replace("USD", "")
                    .replace("CAD", "")
                    .strip()
                    .replace(",", "")
                    .replace("$", ""),
                    evaluate=True,
                )
            )
        except sympy.SympifyError:
            self.set_table_row_color(
                self.category_tables[self.category],
                self.table_components_widgets[component]["row"],
                "#e93d3d",
            )
            self.parent.status_button.setText(
                f"Invalid number for {component.name} price", "red"
            )
            return

        if component.quantity != table_quantity:
            component.latest_change_quantity = f"{os.getlogin().title()} manually set to {table_quantity} from {component.quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        component.price = new_price
        component.set_category_quantity(self.category, new_unit_quantity)
        component.quantity = table_quantity
        component.use_exchange_rate = (
            self.table_components_widgets[component]["use_exchange_rate"].currentText()
            == "USD"
        )
        component.priority = self.table_components_widgets[component][
            "priority"
        ].currentIndex()

        if (
            self.table_components_widgets[component]["priority"].currentText()
            == "Medium"
        ):
            self.table_components_widgets[component]["priority"].setStyleSheet(
                "QComboBox{background-color: #524b2f; border-radius: 0px;} QComboBox:hover{border-color: #e9bb3d;}"
            )
        elif (
            self.table_components_widgets[component]["priority"].currentText() == "High"
        ):
            self.table_components_widgets[component]["priority"].setStyleSheet(
                "QComboBox{background-color: #4d2323; border-radius: 0px;} QComboBox:hover{border-color: #e93d3d;}"
            )
        else:
            self.table_components_widgets[component]["priority"].setStyleSheet(
                "border-radius: 0px;"
            )

        component.shelf_number = self.table_components_widgets[component][
            "shelf_number"
        ].text()
        component.notes = self.table_components_widgets[component][
            "notes"
        ].toPlainText()
        self.components_inventory.save()
        self.sync_changes()
        self.category_tables[self.category].blockSignals(True)
        self.table_components_widgets[component]["unit_quantity"].setText(
            f"{component.get_category_quantity(self.category):,.2f}"
        )
        self.table_components_widgets[component]["unit_quantity"].setToolTip(
            f"Unit quantities:\n{component.print_category_quantities()}"
        )
        self.table_components_widgets[component]["quantity"].setText(
            f"{component.quantity:,.2f}"
        )
        self.table_components_widgets[component]["quantity"].setToolTip(
            component.latest_change_quantity
        )
        self.table_components_widgets[component]["price"].setText(
            f"${component.price:,.2f}"
        )
        self.category_tables[self.category].blockSignals(False)

        self.update_component_row_color(self.category_tables[self.category], component)

        self.update_components_costs()
        self.update_category_total_stock_costs()

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
        if current_table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            current_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

            menu = QMenu(self)
            action = QAction("Set Custom Quantity Limit", self)
            action.triggered.connect(self.set_custom_quantity_limit)
            menu.addAction(action)

            action = QAction("Print Selected Parts", self)
            action.triggered.connect(self.print_selected_items)
            menu.addAction(action)

            menu.addSeparator()

            def move_to_category(new_category: Category):
                if not (selected_components := self.get_selected_components()):
                    return
                existing_components: list[Component] = []
                for component in selected_components:
                    if new_category in component.categories:
                        existing_components.append(component)
                if existing_components:
                    message = f"The following components will be ignored since they already exist in {new_category.name}:\n"
                    for i, existing_part in enumerate(existing_components):
                        message += f"  {i+1}. {existing_part.name}\n"
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Exists")
                    msg.setText(message)
                    msg.setStandardButtons(
                        QMessageBox.StandardButton.Ok
                        | QMessageBox.StandardButton.Cancel
                    )
                    response = msg.exec()
                    if response == QMessageBox.StandardButton.Cancel:
                        return
                for component in selected_components:
                    if component in existing_components:
                        continue
                    component.move_to_category(self.category, new_category)
                self.components_inventory.save()
                self.sync_changes()
                self.sort_components()

            categories = QMenu(menu)
            categories.setTitle("Move to")
            for _, category in enumerate(self.components_inventory.get_categories()):
                action = QAction(category.name, self)
                if self.category == category:
                    action.setEnabled(False)
                    action.setText(f"{category.name} - (You are here)")
                action.triggered.connect(partial(move_to_category, category))
                categories.addAction(action)
            menu.addMenu(categories)

            def copy_to_category(new_category: Category):
                if not (selected_components := self.get_selected_components()):
                    return
                existing_components: list[Component] = []
                for component in selected_components:
                    if new_category in component.categories:
                        existing_components.append(component)
                if existing_components:
                    message = f"The following laser cut parts will be ignored since they already exist in {new_category.name}:\n"
                    for i, existing_part in enumerate(existing_components):
                        message += f"  {i+1}. {existing_part.name}\n"
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Exists")
                    msg.setText(message)
                    msg.setStandardButtons(
                        QMessageBox.StandardButton.Ok
                        | QMessageBox.StandardButton.Cancel
                    )
                    response = msg.exec()
                    if response == QMessageBox.StandardButton.Cancel:
                        return
                for component in selected_components:
                    if component in existing_components:
                        continue
                    component.add_to_category(new_category)
                self.category_tables[self.category].blockSignals(True)
                self.table_components_widgets[component]["unit_quantity"].setToolTip(
                    f"Unit quantities:\n{component.print_category_quantities()}"
                )
                self.table_components_widgets[component]["part_name"].setToolTip(
                    f"{component.part_name}\n\nComponent is present in:\n{component.print_categories()}"
                )
                self.table_components_widgets[component]["part_number"].setToolTip(
                    f"{component.part_number}\n\nComponent is present in:\n{component.print_categories()}"
                )
                self.category_tables[self.category].blockSignals(False)
                self.components_inventory.save()
                self.sync_changes()

            categories = QMenu(menu)
            categories.setTitle("Add to")
            for _, category in enumerate(self.components_inventory.get_categories()):
                action = QAction(category.name, self)
                if self.category == category:
                    action.setEnabled(False)
                    action.setText(f"{category.name} - (You are here)")
                action.triggered.connect(partial(copy_to_category, category))
                categories.addAction(action)
            menu.addMenu(categories)

            menu.addSeparator()

            def remove_parts_from_category():
                if not (selected_components := self.get_selected_components()):
                    return
                for component in selected_components:
                    if len(component.categories) <= 1:
                        self.components_inventory.remove_component(component)
                    else:
                        component.remove_from_category(self.category)
                self.components_inventory.save()
                self.sync_changes()
                self.load_table()

            action = QAction(f"Remove selected parts from {self.category.name}", self)
            action.triggered.connect(remove_parts_from_category)
            menu.addAction(action)

            def delete_selected_parts():
                if not (selected_components := self.get_selected_components()):
                    return
                for component in selected_components:
                    self.components_inventory.remove_component(component)
                self.components_inventory.save()
                self.sync_changes()
                self.load_table()

            action = QAction("Delete selected parts from inventory", self)
            action.triggered.connect(delete_selected_parts)
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

            current_table.customContextMenuRequested.connect(
                partial(self.open_group_menu, menu)
            )

    def add_to_assembly(self, job: Job, assembly: Assembly):
        if components := self.get_selected_components():
            for component in components:
                assembly.add_component(
                    Component(
                        component.name, component.to_dict(), self.components_inventory
                    )
                )
            job.changes_made()
            if len(components) == 1:
                self.parent.status_button.setText(
                    f"Added {len(components)} component to {job.name}", "lime"
                )
            else:
                self.parent.status_button.setText(
                    f"Added {len(components)} components to {job.name}", "lime"
                )

    def add_item(self) -> None:
        add_item_dialog = AddItemDialog(
            f'Add new item to "{self.category.name}"',
            f"Adding a new item to \"{self.category.name}\".\n\nPress 'Add' when finished.",
            self.components_inventory,
            self,
        )

        if add_item_dialog.exec():
            name: str = add_item_dialog.get_name()
            for component in self.components_inventory.components:
                if name == component.name:
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    msg_box.setWindowTitle("Invalid name?")
                    msg_box.setText(
                        f"'{name}'\nis an invalid item name.\n\nCan't be the same as other names."
                    )
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
                    response = msg_box.exec()
                    return

            new_component = Component(
                add_item_dialog.get_part_number(),
                {
                    "part_name": add_item_dialog.get_name(),
                    "unit_quantities": {
                        self.category: add_item_dialog.get_unit_quantity()
                    },
                    "current_quantity": add_item_dialog.get_current_quantity(),
                    "price": add_item_dialog.get_item_price(),
                    "use_exchange_rate": add_item_dialog.get_exchange_rate(),
                    "priority": add_item_dialog.get_priority(),
                    "notes": add_item_dialog.get_notes(),
                    "latest_change_quantity": f"Item added\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
                    "latest_change_price": f"Item added\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
                    "categories": [self.category.name],
                },
                self.components_inventory,
            )
            self.components_inventory.add_component(new_component)
            self.components_inventory.save()
            self.sync_changes()
            self.load_table()

    def update_components_costs(self):
        self.category_tables[self.category].blockSignals(True)
        total_cost_in_stock = 0.0
        total_unit_cost = 0.0
        for component, table_item in self.table_components_widgets.items():
            converted_price = (
                component.price * self.get_exchange_rate()
                if component.use_exchange_rate
                else component.price / self.get_exchange_rate()
            )
            table_item["price"].setText(
                f'${component.price:,.2f} {"USD" if component.use_exchange_rate else "CAD"}'
            )
            table_item["price"].setToolTip(
                f'${converted_price:,.2f} {"CAD" if component.use_exchange_rate else "USD"}\n{component.latest_change_price}'
            )
            table_item["total_cost_in_stock"].setText(
                f'${component.get_total_cost_in_stock():,.2f} {"USD" if component.use_exchange_rate else "CAD"}'
            )
            total_cost_in_stock += component.get_total_cost_in_stock()
            table_item["total_unit_cost"].setText(
                f'${component.get_total_unit_cost(self.category):,.2f} {"USD" if component.use_exchange_rate else "CAD"}'
            )
            total_unit_cost += component.get_total_unit_cost(self.category)
        self.category_tables[self.category].blockSignals(False)
        self.label_total_unit_cost.setText(f"Total Unit Cost: ${total_unit_cost:,.2f}")

    def update_category_total_stock_costs(self) -> None:
        total_stock_costs = {
            category.name: self.components_inventory.get_total_category_cost_in_stock(
                category
            )
            for category in self.components_inventory.get_categories()
        }
        total_stock_costs["Polar Total Stock Cost"] = (
            self.components_inventory.get_total_stock_cost_for_similar_categories(
                "Polar"
            )
        )
        total_stock_costs["BL Total Stock Cost"] = (
            self.components_inventory.get_total_stock_cost_for_similar_categories("BL")
        )

        total_stock_costs = dict(natsorted(total_stock_costs.items()))

        self.clear_layout(self.gridLayout_category_stock_costs)
        lbl = QLabel("Stock Costs:", self)
        self.gridLayout_category_stock_costs.addWidget(lbl, 0, 0)
        i: int = 0
        for i, stock_cost in enumerate(total_stock_costs, start=1):
            lbl = QLabel(stock_cost, self)
            if "Total" in stock_cost:
                lbl.setStyleSheet(
                    "border-top: 1px solid #8C8C8C; border-bottom: 1px solid #8C8C8C"
                )
            self.gridLayout_category_stock_costs.addWidget(lbl, i, 0)
            lbl = QLabel(f"${total_stock_costs[stock_cost]:,.2f}", self)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if "Total" in stock_cost:
                lbl.setStyleSheet(
                    "border-top: 1px solid #8C8C8C; border-bottom: 1px solid #8C8C8C"
                )
            self.gridLayout_category_stock_costs.addWidget(lbl, i, 1)
        lbl = QLabel("Total Cost in Stock:", self)
        lbl.setStyleSheet("border-top: 1px solid #8C8C8C")
        self.gridLayout_category_stock_costs.addWidget(lbl, i + 1, 0)
        lbl = QLabel(
            f"${self.components_inventory.get_total_stock_cost():,.2f}",
            self,
        )
        # lbl.setTextInteractionFlags(Qt.ItemFlag.TextSelectableByMouse)
        lbl.setStyleSheet("border-top: 1px solid #8C8C8C")
        self.gridLayout_category_stock_costs.addWidget(lbl, i + 1, 1)

    def set_custom_quantity_limit(self) -> None:
        current_table = self.category_tables[self.category]
        if components := self.get_selected_components():
            components_string = "".join(
                f"    {i + 1}. {component.part_name}\n"
                for i, component in enumerate(components)
            )
            set_custom_limit_dialog = SetCustomLimitDialog(
                self,
                f"Set a custom red and yellow quantity limit for each of the {len(components)} selected components:\n{components_string}",
                components[0].red_quantity_limit,
                components[0].yellow_quantity_limit,
            )
            if set_custom_limit_dialog.exec():
                for component in components:
                    component.red_quantity_limit = (
                        set_custom_limit_dialog.get_red_limit()
                    )
                    component.yellow_quantity_limit = (
                        set_custom_limit_dialog.get_yellow_limit()
                    )
                    self.update_component_row_color(current_table, component)
                self.components_inventory.save()
                self.sync_changes()

    def change_quantities(self, add_or_remove: str):
        selected_components = self.get_selected_components()
        dialog = ItemsChangeQuantityDialog(
            self.category.name, add_or_remove, selected_components, self
        )
        if dialog.exec():
            multiplier: int = dialog.get_multiplier()
            option = dialog.get_option()
            history_file = HistoryFile()
            if option == "Category":
                self.category_tables[self.category].blockSignals(True)
                for component, tables_item in self.table_components_widgets.items():
                    if add_or_remove == "ADD":
                        component.latest_change_quantity = f"{os.getlogin().title()} Used: All Items in Category - add quantity\nChanged from {component.quantity} to {component.quantity + (component.get_category_quantity(self.category) * multiplier)} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        component.quantity = component.quantity + (
                            multiplier * component.get_category_quantity(self.category)
                        )
                    elif add_or_remove == "REMOVE":
                        component.latest_change_quantity = f"{os.getlogin().title()} Used: All Items in Category - remove quantity\nChanged from {component.quantity} to {component.quantity - (component.get_category_quantity(self.category) * multiplier)} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        component.quantity = component.quantity - (
                            multiplier * component.get_category_quantity(self.category)
                        )
                    tables_item["quantity"].setText(str(component.quantity))
                    tables_item["quantity"].setToolTip(component.latest_change_quantity)
                self.category_tables[self.category].blockSignals(False)
                history_file.add_new_to_category(
                    date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
                    description=f'{"Added" if add_or_remove == "ADD" else "Removed"} a multiple of {multiplier} {"quantity" if multiplier == 1 else "quantities"} from each item in {self.category.name}',
                )
                self.components_inventory.save()
                self.sync_changes()
                self.update_components_costs()
                self.select_last_selected_item()
            elif option == "Item":
                self.category_tables[self.category].blockSignals(True)
                for component in selected_components:
                    if add_or_remove == "ADD":
                        component.latest_change_quantity = f"{os.getlogin().title()} Used: Selected Item - add quantity\nChanged from {component.quantity} to {component.quantity + multiplier} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        component.quantity += multiplier
                    elif add_or_remove == "REMOVE":
                        component.latest_change_quantity = f"{os.getlogin().title()} Used: Selected Item - remove quantity\nChanged from {component.quantity} to {component.quantity - multiplier} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                        component.quantity -= multiplier
                    history_file.add_new_to_single_item(
                        date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
                        description=f'{"Added" if add_or_remove == "ADD" else "Removed"} {multiplier} {"quantity" if multiplier == 1 else "quantities"} from "{component.part_name}"',
                    )
                    self.table_components_widgets[component]["quantity"].setText(
                        str(component.quantity)
                    )
                    self.table_components_widgets[component]["quantity"].setToolTip(
                        component.latest_change_quantity
                    )
                self.category_tables[self.category].blockSignals(False)
                self.components_inventory.save()
                self.sync_changes()
                self.sort_components()
                self.select_last_selected_item()

    def listWidget_item_changed(self):
        current_table = self.category_tables[self.category]
        selected_item = self.listWidget_itemnames.currentItem().text()
        for component, table_items in self.table_components_widgets.items():
            if (
                component.part_name == selected_item
                or component.part_number == selected_item
            ):
                current_table.selectRow(table_items["row"])
                current_table.scrollTo(
                    current_table.model().index(table_items["row"], 0)
                )

    def update_search_suggestions(self):
        current_tab_components = self.components_inventory.get_components_by_category(
            self.category
        )
        current_tab_components_sorted = natsorted(
            current_tab_components, key=lambda component: component.part_name
        )

        suggestions: list[str] = []
        for component in current_tab_components_sorted:
            suggestions.extend((component.part_name, component.part_number))

        completer = QCompleter(suggestions, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.lineEdit_search_items.setCompleter(completer)

    def update_edit_inventory_list_widget(self):
        current_tab_components = self.components_inventory.get_components_by_category(
            self.category
        )
        current_tab_components_sorted = natsorted(
            current_tab_components, key=lambda component: component.part_name
        )

        self.listWidget_itemnames.blockSignals(True)
        self.listWidget_itemnames.clear()

        for component in current_tab_components_sorted:
            if (
                self.lineEdit_search_items.text() in component.part_name
                or self.lineEdit_search_items.text() in component.part_number
            ):
                self.listWidget_itemnames.addItem(component.part_name)
                self.listWidget_itemnames.addItem(component.part_number)

        self.listWidget_itemnames.blockSignals(False)

        for row in range(self.listWidget_itemnames.count()):
            item = self.listWidget_itemnames.itemAt(0, row)
            with contextlib.suppress(AttributeError):  # For some unknown reason
                if self.lineEdit_search_items.text() == item.text():
                    self.listWidget_itemnames.setCurrentRow(row)
                    break

    def open_po(self, po_name: str = None) -> None:
        if po_name is None:
            input_dialog = SelectItemDialog(
                DialogButtons.open_cancel,
                "Open PO",
                "Select a PO to open",
                get_all_po(),
                self,
            )
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.open:
                    try:
                        po_template = POTemplate(
                            f"{os.path.abspath(os.getcwd())}/PO's/templates/{input_dialog.get_selected_item()}.xlsx"
                        )
                        po_template.generate()
                        os.startfile(po_template.get_output_path())
                    except AttributeError:
                        return
                elif response == DialogButtons.cancel:
                    return
        else:
            po_template = POTemplate(
                f"{os.path.abspath(os.getcwd())}/PO's/templates/{po_name}.xlsx"
            )
            po_template.generate()
            os.startfile(po_template.get_output_path())

    def select_last_selected_item(self):
        current_table = self.category_tables[self.category]
        for component, table_items in self.table_components_widgets.items():
            if component.name == self.last_selected_component:
                current_table.selectRow(table_items["row"])
                current_table.scrollTo(
                    current_table.model().index(table_items["row"], 0)
                )

    def get_exchange_rate(self) -> float:
        return self.settings_file.get_value(setting_name="exchange_rate")

    def get_selected_components(self) -> list[Component]:
        selected_components: list[Component] = []
        selected_rows = self.get_selected_rows()
        selected_components.extend(
            component
            for component, table_items in self.table_components_widgets.items()
            if table_items["row"] in selected_rows
        )
        return selected_components

    def get_selected_component(self) -> Component:
        selected_row = self.get_selected_row()
        for component, table_items in self.table_components_widgets.items():
            if table_items["row"] == selected_row:
                self.last_selected_index = selected_row
                self.last_selected_component = component.name
                return component

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
            "Part Number",
            "Unit Qty",
            "Qty in Stock",
            "Shelf #",
            "Notes",
            "Order Status",
        ]
        if components := self.get_selected_components():
            html = '<html><body><table style="width: 100%; border-collapse: collapse; text-align: left; vertical-align: middle; font-size: 12px; font-family: Verdana, Geneva, Tahoma, sans-serif;">'
            html += '<thead><tr style="border-bottom: 1px solid black;">'
            for header in headers:
                html += f"<th>{header}</th>"
            html += "</tr>"
            html += "</thead>"
            html += "<tbody>"
            for component in components:
                order_status = ""
                if component.orders:
                    for order in component.orders:
                        order_status += f"{order}<br>"
                else:
                    order_status = "No order is pending"
                html += f"""<tr style="border-bottom: 1px solid black;">
                <td>{component.part_name}</td>
                <td>{component.part_number}</td>
                <td>{component.get_category_quantity(self.category)}</td>
                <td>{component.quantity}</td>
                <td>{component.shelf_number}</td>
                <td>{component.notes.replace("\n", "<br>")}</td>
                <td>{order_status}</td>
                </tr>"""
            html += "</tbody></table><body><html>"
            with open("print_selected_parts.html", "w", encoding="utf-8") as f:
                f.write(html)
            self.parent.open_print_selected_parts()

    def update_component_row_color(self, table, component: Component):
        if component.orders:
            self.set_table_row_color(
                table, self.table_components_widgets[component]["row"], "#29422c"
            )
        elif component.quantity <= component.red_quantity_limit:
            self.set_table_row_color(
                table, self.table_components_widgets[component]["row"], "#3F1E25"
            )
        elif component.quantity <= component.yellow_quantity_limit:
            self.set_table_row_color(
                table, self.table_components_widgets[component]["row"], "#413C28"
            )
        else:
            self.set_table_row_color(
                table, self.table_components_widgets[component]["row"], "#141414"
            )

    def set_table_row_color(
        self, table: ComponentsTableWidget, row_index: int, color: str
    ):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def sort_components(self):
        self.settings_file.load_data()
        if self.settings_file.get_value(setting_name="sort_alphabatical"):
            self.components_inventory.sort_by_name(
                not self.settings_file.get_value(setting_name="sort_ascending")
            )
        elif self.settings_file.get_value(setting_name="sort_quantity_in_stock"):
            self.components_inventory.sort_by_quantity(
                not self.settings_file.get_value(setting_name="sort_ascending")
            )
        self.load_table()

    def save_current_tab(self):
        if self.finished_loading:
            self.parent.components_tab_widget_last_selected_tab_index = (
                self.tab_widget.currentIndex()
            )

    def restore_last_selected_tab(self):
        if (
            self.tab_widget.currentIndex()
            == self.parent.components_tab_widget_last_selected_tab_index
        ):
            self.sort_components()  # * This happens when the last selected tab is the first tab
        else:
            self.tab_widget.setCurrentIndex(
                self.parent.components_tab_widget_last_selected_tab_index
            )

    def save_category_tabs_order(self):
        self.settings_file.load_data()
        tab_order = self.settings_file.get_value("category_tabs_order")
        tab_order["Components"] = self.tab_widget.get_tab_order()
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

    def reload_po_menu(self) -> None:
        for po_button in self.po_buttons:
            po_menu = QMenu(self)
            for po in get_all_po():
                po_menu.addAction(po, partial(self.open_po, po))
            po_button.setMenu(po_menu)

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
