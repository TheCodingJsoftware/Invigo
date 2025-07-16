import contextlib
import os
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

import sympy
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QInputDialog,
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
    HumbleDoubleSpinBox,
    NotesPlainTextEdit,
    OrderStatusButton,
)
from ui.dialogs.add_new_structural_steel_item_dialog import AddStructuralSteelItemDialog
from ui.dialogs.edit_category_dialog import EditCategoryDialog
from ui.dialogs.edit_structural_steel_item_dialog import EditStructuralSteelItemDialog
from ui.dialogs.set_component_order_pending_dialog import SetComponentOrderPendingDialog
from ui.dialogs.set_custom_limit_dialog import SetCustomLimitDialog
from ui.dialogs.update_component_order_pending_dialog import (
    UpdateComponentOrderPendingDialog,
)
from ui.icons import Icons
from ui.theme import theme_var
from ui.widgets.structural_steel_tab_UI import Ui_Form
from utils.inventory.angle_bar import AngleBar
from utils.inventory.category import Category
from utils.inventory.dom_round_tube import DOMRoundTube
from utils.inventory.flat_bar import FlatBar
from utils.inventory.order import Order, OrderDict
from utils.inventory.pipe import Pipe
from utils.inventory.rectangular_bar import RectangularBar
from utils.inventory.rectangular_tube import RectangularTube
from utils.inventory.round_bar import RoundBar
from utils.inventory.round_tube import RoundTube
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile
from utils.inventory.structural_steel_inventory import StructuralSteelInventory
from utils.settings import Settings
from utils.structural_steel_settings.structural_steel_settings import (
    StructuralSteelSettings,
)
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class StructuralSteelTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.set_editable_column_index([1, 2, 3, 6])
        headers: list[str] = [
            "Name",
            "Part #",
            "Length",
            "Quantity",
            "Total Cost in Stock",
            "Orders",
            "Notes",
            "Modified Date",
            "Edit",
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)


class StructuralSteelTabWidget(CustomTabWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)


class OrderWidget(QWidget):
    orderOpened = pyqtSignal()
    orderClosed = pyqtSignal()

    def __init__(
        self,
        item: RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar,
        parent: "StructuralSteelInventoryTab",
    ):
        super().__init__(parent)
        self.parent: "StructuralSteelInventoryTab" = parent
        self.item = item

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

        for order in self.item.orders:
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
            order_status_button.clicked.connect(partial(self.order_button_pressed, order, order_status_button))

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
            arrival_date.dateChanged.connect(partial(self.date_changed, order, arrival_date))

            v_layout.addWidget(order_status_button)
            v_layout.addWidget(arrival_date)
            self.orders_layout.addLayout(v_layout)
        self.parent.category_tables[self.parent.category].setColumnWidth(7, 400)  # Widgets don't like being resized with columns
        self.parent.update_item_row_color(self.parent.category_tables[self.parent.category], self.item)

    def create_order(self):
        select_date_dialog = SetComponentOrderPendingDialog(
            f'Set an expected arrival time for "{self.item.get_name()}," the number of parts ordered, and notes.',
            self,
        )
        if select_date_dialog.exec():
            data: OrderDict = {
                "purchase_order_id": -1,
                "expected_arrival_time": select_date_dialog.get_selected_date(),
                "order_pending_quantity": select_date_dialog.get_order_quantity(),
                "order_pending_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": select_date_dialog.get_notes(),
            }
            new_order = Order(data)
            self.item.add_order(new_order)
            self.parent.structural_steel_inventory.save()
            self.parent.sync_changes()
            self.parent.load_table()
            self.load_ui()

    def order_button_pressed(self, order: Order, order_status_button: OrderStatusButton):
        self.orderOpened.emit()
        dialog = UpdateComponentOrderPendingDialog(order, f"Update order for {self.item.get_name()}", self)
        if dialog.exec():
            if dialog.action == "CANCEL_ORDER":
                self.item.remove_order(order)
            elif dialog.action == "UPDATE_ORDER":
                order.notes = dialog.get_notes()
                order.quantity = dialog.get_order_quantity()
            elif dialog.action == "ADD_INCOMING_QUANTITY":
                quantity_to_add = dialog.get_order_quantity()
                remaining_quantity = order.quantity - quantity_to_add
                old_quantity = self.item.quantity
                new_quantity = old_quantity + quantity_to_add
                self.item.quantity = new_quantity
                self.item.has_sent_warning = False
                self.item.latest_change_quantity = (
                    f"Used: Order pending - add quantity\nChanged from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                )
                order.quantity = remaining_quantity
                if remaining_quantity <= 0:
                    msg = QMessageBox(
                        QMessageBox.Icon.Information,
                        "Order",
                        f"All the quantity from this order has been added, this order will now be removed from {self.item.get_name()}",
                        QMessageBox.StandardButton.Ok,
                        self,
                    )
                    if msg.exec():
                        self.item.remove_order(order)
            else:  # You never know.
                order_status_button.setChecked(True)
                self.orderClosed.emit()
                return
            self.parent.structural_steel_inventory.save()
            self.parent.sync_changes()
            self.parent.sort_items()
            self.parent.select_last_selected_item()
            self.load_ui()
        else:  # Close order pressed
            order_status_button.setChecked(True)
            self.orderClosed.emit()

    def date_changed(self, order: Order, arrival_date: QDateEdit):
        order.expected_arrival_time = arrival_date.date().toString("yyyy-MM-dd")
        self.parent.structural_steel_inventory.save()
        self.parent.sync_changes()

    def clear_layout(self, layout: QVBoxLayout | QHBoxLayout | QWidget):
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
        self.original_layout_parent: "StructuralSteelInventoryTab" = self.original_layout.parentWidget()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Sheets In Inventory Tab")
        self.setLayout(self.original_layout)
        self.setObjectName("popout_widget")

    def closeEvent(self, event):
        if self.original_layout_parent:
            self.original_layout_parent.setLayout(self.original_layout)
            self.original_layout_parent.pushButton_popout.setIcon(Icons.dock_icon)
            self.original_layout_parent.pushButton_popout.clicked.disconnect()
            self.original_layout_parent.pushButton_popout.clicked.connect(self.original_layout_parent.popout)
        super().closeEvent(event)


class StructuralSteelInventoryTab(QWidget, Ui_Form):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)
        self.parent: MainWindow = parent
        self.structural_steel_inventory: StructuralSteelInventory = self.parent.structural_steel_inventory
        self.structural_steel_settings: StructuralSteelSettings = self.parent.structural_steel_settings
        self.workspace_settings: WorkspaceSettings = self.parent.workspace_settings

        self.settings_file = Settings()

        self.tab_widget = StructuralSteelTabWidget(self)

        self.category: Category = None
        self.finished_loading: bool = False
        self.category_tables: dict[Category, StructuralSteelTableWidget] = {}
        self.table_structural_steel_item_widgets: dict[
            RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar,
            dict[
                str,
                QTableWidgetItem | HumbleDoubleSpinBox | QComboBox | NotesPlainTextEdit,
            ],
        ] = {}
        self.margins = (15, 15, 5, 5)  # top, bottom, left, right
        self.margin_format = f"margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;"
        self.last_selected_sheet: str = ""
        self.last_selected_index: int = 0
        self.load_ui()
        self.load_categories()
        self.restore_last_selected_tab()
        self.finished_loading = True

    def load_ui(self):
        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.pushButton_add_new_structural_item.clicked.connect(self.add_structural_steel_item)
        self.pushButton_add_new_structural_item.setIcon(Icons.plus_circle_icon)

        self.verticalLayout_10.addWidget(self.tab_widget)

        self.pushButton_popout.setStyleSheet("background-color: transparent; border: none;")
        self.pushButton_popout.clicked.connect(self.popout)
        self.pushButton_popout.setIcon(Icons.dock_icon)

    def add_category(self):
        new_category_name, ok = QInputDialog.getText(self, "New Category", "Enter a name for a category:")
        if new_category_name and ok:
            new_category = Category(new_category_name)
            self.structural_steel_inventory.add_category(new_category)
            table = StructuralSteelTableWidget(self.tab_widget)
            self.category_tables.update({new_category: table})
            self.tab_widget.addTab(table, new_category.name)
            table.rowChanged.connect(self.table_changed)
            table.cellPressed.connect(self.table_selected_changed)
            self.structural_steel_inventory.save()
            self.sync_changes()

    def remove_category(self):
        category_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove Category",
            "Select a category to remove",
            [category.name for category in self.structural_steel_inventory.get_categories()],
            editable=False,
        )
        if category_to_remove and ok:
            category = self.structural_steel_inventory.delete_category(category_to_remove)
            tab_index_to_remove = self.tab_widget.get_tab_order().index(category_to_remove)
            self.tab_widget.removeTab(tab_index_to_remove)
            self.clear_layout(self.category_tables[category])
            del self.category_tables[category]
            self.structural_steel_inventory.save()
            self.sync_changes()

    def edit_category(self):
        edit_dialog = EditCategoryDialog(
            f"Edit {self.category.name}",
            f"Delete, duplicate, or rename: {self.category.name}.",
            self.category.name,
            self.category,
            self.structural_steel_inventory,
            self,
        )
        if edit_dialog.exec():
            action = edit_dialog.action
            input_text = edit_dialog.lineEditInput.text()
            if action == "DUPLICATE":
                new_name = input_text
                if new_name == self.category.name:
                    new_name += " - Copy"
                new_category = self.structural_steel_inventory.duplicate_category(self.category, new_name)
                # self.sheets_inventory.add_category(new_category)
                table = StructuralSteelTableWidget(self.tab_widget)
                self.category_tables.update({new_category: table})
                self.tab_widget.insertTab(self.tab_widget.currentIndex() + 1, table, new_category.name)
                table.rowChanged.connect(self.table_changed)
                table.cellPressed.connect(self.table_selected_changed)
                self.structural_steel_inventory.save()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "RENAME":
                self.category.rename(input_text)
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), input_text)
                self.structural_steel_inventory.save()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()
            elif action == "DELETE":
                self.clear_layout(self.category_tables[self.category])
                del self.category_tables[self.category]
                self.structural_steel_inventory.delete_category(self.category)
                self.tab_widget.removeTab(self.tab_widget.currentIndex())
                self.structural_steel_inventory.save()
                self.sync_changes()
                self.load_categories()
                self.restore_last_selected_tab()

    def load_categories(self):
        self.settings_file.load_data()
        self.tab_widget.clear()
        self.category_tables.clear()
        all_categories = [category.name for category in self.structural_steel_inventory.get_categories()]
        try:
            tab_order: list[str] = self.settings_file.get_value("category_tabs_order")["Structural Steel Inventory"]
        except KeyError:
            tab_order = []

        # Updates the tab order to add categories that have not previously been added
        for category in all_categories:
            if category not in tab_order:
                tab_order.append(category)

        for tab in tab_order:
            if category := self.structural_steel_inventory.get_category(tab):
                table = StructuralSteelTableWidget(self.tab_widget)
                self.category_tables.update({category: table})
                self.tab_widget.addTab(table, category.name)
                table.rowChanged.connect(self.table_changed)
                table.cellPressed.connect(self.table_selected_changed)
                table.verticalScrollBar().valueChanged.connect(self.save_scroll_position)
        self.tab_widget.currentChanged.connect(self.load_table)
        self.tab_widget.tabOrderChanged.connect(self.save_category_tabs_order)
        self.tab_widget.tabOrderChanged.connect(self.save_current_tab)
        self.tab_widget.tabBarDoubleClicked.connect(self.edit_category)
        self.tab_widget.addCategory.connect(self.add_category)
        self.tab_widget.removeCategory.connect(self.remove_category)

    def load_table(self):
        self.category = self.structural_steel_inventory.get_category(self.tab_widget.tabText(self.tab_widget.currentIndex()))
        if not self.category:
            return
        current_table = self.category_tables[self.category]
        current_table.blockSignals(True)
        current_table.clearContents()
        current_table.setRowCount(0)
        self.table_structural_steel_item_widgets.clear()
        row_index = 0
        for group in self.structural_steel_inventory.get_items_by_profile_type(self.structural_steel_inventory.get_items_by_category(self.category)):
            current_table.insertRow(row_index)
            group_table_item = QTableWidgetItem(group.value)
            group_table_item.setTextAlignment(4)  # Align text center

            font = QFont()
            font.setPointSize(15)
            group_table_item.setFont(font)
            current_table.setItem(row_index, 0, group_table_item)
            current_table.setSpan(row_index, 0, 1, current_table.columnCount())
            self.set_table_row_color(current_table, row_index, f"{theme_var('background')}")
            row_index += 1

            for structural_steel_item in self.structural_steel_inventory.get_items_by_category(self.category):
                if group != structural_steel_item.PROFILE_TYPE:
                    continue
                self.table_structural_steel_item_widgets.update({structural_steel_item: {}})
                self.table_structural_steel_item_widgets[structural_steel_item].update({"row": row_index})
                col_index: int = 0
                current_table.insertRow(row_index)
                current_table.setRowHeight(row_index, 60)

                # NAME
                table_item_name = QTableWidgetItem(structural_steel_item.get_name())
                table_item_name.setToolTip(structural_steel_item.tooltip())
                current_table.setItem(row_index, col_index, table_item_name)
                current_table.item(row_index, col_index).setFont(self.tables_font)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"name": table_item_name})
                col_index += 1

                # PART NUMBER
                table_item_part_number = QTableWidgetItem(structural_steel_item.part_number)
                table_item_part_number.setToolTip(structural_steel_item.tooltip())
                current_table.setItem(row_index, col_index, table_item_part_number)
                current_table.item(row_index, col_index).setFont(self.tables_font)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"part_number": table_item_part_number})
                col_index += 1

                # LENGTH
                table_item_length = QTableWidgetItem(f"{structural_steel_item.length:,.3f} in")
                tooltip_conversion = f"{(structural_steel_item.length / 12):,.3f} ft\n{(structural_steel_item.length * 0.0254):,.3f} m"
                table_item_length.setToolTip(tooltip_conversion)
                current_table.setItem(row_index, col_index, table_item_length)
                current_table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                current_table.item(row_index, col_index).setFont(self.tables_font)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"length": table_item_length})
                col_index += 1

                # CURRENT QUANTITY
                table_item_quantity = QTableWidgetItem(f"{structural_steel_item.quantity:,.0f}")
                current_table.setItem(row_index, col_index, table_item_quantity)
                current_table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                current_table.item(row_index, col_index).setFont(self.tables_font)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"quantity": table_item_quantity})
                col_index += 1

                # COST IN STOCK
                total_cost_in_stock = structural_steel_item.get_cost() * structural_steel_item.quantity
                table_item_cost_in_stock = QTableWidgetItem(f"${total_cost_in_stock:,.2f}")
                current_table.setItem(row_index, col_index, table_item_cost_in_stock)
                current_table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                current_table.item(row_index, col_index).setFont(self.tables_font)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"total_cost_in_stock": table_item_cost_in_stock})
                col_index += 1

                # ORDERS
                order_widget = OrderWidget(structural_steel_item, self)
                order_widget.orderOpened.connect(self.block_table_signals)
                order_widget.orderClosed.connect(self.unblock_table_signals)
                current_table.setCellWidget(row_index, col_index, order_widget)
                col_index += 1

                # NOTES
                notes_widget = NotesPlainTextEdit(self, structural_steel_item.notes, structural_steel_item.tooltip())
                notes_widget.textChanged.connect(partial(self.table_changed, row_index))
                current_table.setCellWidget(row_index, col_index, notes_widget)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"notes": notes_widget})
                col_index += 1

                # MODIFIED DATE
                table_item_modified_date = QTableWidgetItem(structural_steel_item.latest_change_quantity)
                table_item_modified_date.setToolTip(structural_steel_item.latest_change_quantity)
                current_table.setItem(row_index, col_index, table_item_modified_date)
                current_table.item(row_index, col_index).setFont(self.tables_font)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"modified_date": table_item_modified_date})
                col_index += 1

                # EDIT BUTTON
                edit_button = QPushButton("", self)
                edit_button.setFlat(True)
                edit_button.setIcon(Icons.edit_icon)
                edit_button.clicked.connect(partial(self.edit_structural_steel_item, structural_steel_item))
                current_table.setCellWidget(row_index, col_index, edit_button)
                self.table_structural_steel_item_widgets[structural_steel_item].update({"edit_button": edit_button})

                col_index += 1

                self.update_item_row_color(current_table, structural_steel_item)

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

            def delete_selected_items():
                if not (selected_items := self.get_selected_structural_steel_items()):
                    return
                for item in selected_items:
                    self.structural_steel_inventory.remove_item(item)
                self.structural_steel_inventory.save()
                self.sync_changes()
                self.load_table()

            action = QAction("Delete", self)
            action.triggered.connect(delete_selected_items)
            menu.addAction(action)

            current_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        current_table.setColumnWidth(7, 400)  # Widgets don't like being resized with columns
        self.save_current_tab()
        self.save_category_tabs_order()
        self.restore_scroll_position()

    def edit_structural_steel_item(
        self,
        item_to_edit: RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar,
    ):
        edit_dialog = EditStructuralSteelItemDialog(
            self.category,
            self.structural_steel_inventory,
            self.structural_steel_settings,
            self.workspace_settings,
            item_to_edit,
            self,
        )
        if edit_dialog.exec():
            new_item = edit_dialog.get_item()
            item_to_edit.load_data(new_item.to_dict())
            self.structural_steel_inventory.save()
            self.sync_changes()
            self.sort_items()

    def block_table_signals(self):
        self.category_tables[self.category].blockSignals(True)

    def unblock_table_signals(self):
        self.category_tables[self.category].blockSignals(False)

    def table_selected_changed(self):
        if item := self.get_selected_item():
            self.last_selected_sheet = item.name
            self.last_selected_index = self.get_selected_row()

    def table_changed(self, row: int):
        item = next(
            (sheet for sheet, table_data in self.table_structural_steel_item_widgets.items() if table_data["row"] == row),
            None,
        )
        if not item:
            return
        old_quantity = item.quantity
        item.quantity = float(
            sympy.sympify(
                self.table_structural_steel_item_widgets[item]["quantity"].text().strip().replace(",", ""),
                evaluate=True,
            )
        )
        if old_quantity != item.quantity:
            item.has_sent_warning = False
            item.latest_change_quantity = (
                f"{os.getlogin().title()} - Manually set to {item.quantity} from {old_quantity} quantity at {str(datetime.now().strftime('%B %d %A %Y %I:%M:%S %p'))}"
            )
        item.notes = self.table_structural_steel_item_widgets[item]["notes"].toPlainText()
        item.part_number = self.table_structural_steel_item_widgets[item]["part_number"].text()
        item.length = float(
            sympy.sympify(
                self.table_structural_steel_item_widgets[item]["length"].text().replace("in", "").strip().replace(",", ""),
                evaluate=True,
            )
        )
        self.structural_steel_inventory.save()
        self.sync_changes()
        self.category_tables[self.category].blockSignals(True)
        self.table_structural_steel_item_widgets[item]["total_cost_in_stock"].setText(f"${(item.get_cost() * item.quantity):,.2f}")
        self.table_structural_steel_item_widgets[item]["length"].setText(f"{item.length:,.3f} in")
        tooltip_conversion = f"{(item.length / 12):,.3f} ft\n{(item.length * 0.0254):,.3f} m"
        self.table_structural_steel_item_widgets[item]["length"].setToolTip(tooltip_conversion)
        self.table_structural_steel_item_widgets[item]["quantity"].setText(f"{item.quantity:,.0f}")
        self.table_structural_steel_item_widgets[item]["modified_date"].setText(item.latest_change_quantity)
        self.category_tables[self.category].blockSignals(False)
        self.update_item_row_color(self.category_tables[self.category], item)

    def add_structural_steel_item(self):
        add_item_dialog = AddStructuralSteelItemDialog(
            self.category,
            self.structural_steel_inventory,
            self.structural_steel_settings,
            self.workspace_settings,
            None,
            self,
        )

        if add_item_dialog.exec():
            new_item = add_item_dialog.get_item()
            if new_item.PROFILE_TYPE == ProfilesTypes.RECTANGULAR_BAR:
                self.structural_steel_inventory.add_rectangular_bar(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.ROUND_BAR:
                self.structural_steel_inventory.add_round_bar(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.FLAT_BAR:
                self.structural_steel_inventory.add_flat_bar(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.ANGLE_BAR:
                self.structural_steel_inventory.add_angle_bar(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.RECTANGULAR_TUBE:
                self.structural_steel_inventory.add_rectangular_tube(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.ROUND_TUBE:
                self.structural_steel_inventory.add_round_tube(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.DOM_ROUND_TUBE:
                self.structural_steel_inventory.add_DOM_round_tube(new_item)
            elif new_item.PROFILE_TYPE == ProfilesTypes.PIPE:
                self.structural_steel_inventory.add_pipe(new_item)
            self.structural_steel_inventory.save()
            self.sync_changes()
            self.load_categories()
            self.restore_last_selected_tab()

    def set_custom_quantity_limit(self):
        current_table = self.category_tables[self.category]
        if sheets := self.get_selected_structural_steel_items():
            sheets_string = "".join(f"    {i + 1}. {sheet.get_name()}\n" for i, sheet in enumerate(sheets))
            set_custom_limit_dialog = SetCustomLimitDialog(
                self,
                f"Set a custom red and yellow quantity limit for each of the {len(sheets)} selected sheets:\n{sheets_string}",
                sheets[0].red_quantity_limit,
                sheets[0].yellow_quantity_limit,
            )
            if set_custom_limit_dialog.exec():
                for sheet in sheets:
                    sheet.red_quantity_limit = set_custom_limit_dialog.get_red_limit()
                    sheet.yellow_quantity_limit = set_custom_limit_dialog.get_yellow_limit()
                    self.update_item_row_color(current_table, sheet)
                self.structural_steel_inventory.save()
                self.sync_changes()

    def select_last_selected_item(self):
        current_table = self.category_tables[self.category]
        for sheet, table_items in self.table_structural_steel_item_widgets.items():
            if sheet.name == self.last_selected_sheet:
                current_table.selectRow(table_items["row"])
                current_table.scrollTo(current_table.model().index(table_items["row"], 0))

    def get_selected_structural_steel_items(
        self,
    ) -> list[RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar]:
        selected_sheets: list[RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar] = []
        selected_rows = self.get_selected_rows()
        selected_sheets.extend(sheet for sheet, table_items in self.table_structural_steel_item_widgets.items() if table_items["row"] in selected_rows)
        return selected_sheets

    def get_selected_item(
        self,
    ) -> RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar:
        selected_row = self.get_selected_row()
        for (
            structural_steel_item,
            table_items,
        ) in self.table_structural_steel_item_widgets.items():
            if table_items["row"] == selected_row:
                self.last_selected_index = selected_row
                self.last_selected_sheet = structural_steel_item.name
                return structural_steel_item

    def get_selected_rows(self) -> list[int]:
        rows: set[int] = {item.row() for item in self.category_tables[self.category].selectedItems()}
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
        if sheets := self.get_selected_structural_steel_items():
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

    def update_item_row_color(
        self,
        table,
        item: RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar,
    ):
        if item.orders:
            self.set_table_row_color(
                table,
                self.table_structural_steel_item_widgets[item]["row"],
                f"{theme_var('table-order-pending')}",
            )
        elif item.quantity <= item.red_quantity_limit:
            self.set_table_row_color(
                table,
                self.table_structural_steel_item_widgets[item]["row"],
                f"{theme_var('table-red-quantity')}",
            )
        elif item.quantity <= item.yellow_quantity_limit:
            self.set_table_row_color(
                table,
                self.table_structural_steel_item_widgets[item]["row"],
                f"{theme_var('table-yellow-quantity')}",
            )
        else:
            self.set_table_row_color(
                table,
                self.table_structural_steel_item_widgets[item]["row"],
                f"{theme_var('background')}",
            )

    def set_table_row_color(self, table: StructuralSteelTableWidget, row_index: int, color: str):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def sort_items(self):
        self.structural_steel_inventory.sort_by_quantity()
        self.load_table()

    def save_current_tab(self):
        if self.finished_loading:
            self.parent.structural_steel_inventory_tab_widget_last_selected_tab_index = self.tab_widget.currentIndex()

    def restore_last_selected_tab(self):
        if self.tab_widget.currentIndex() == self.parent.structural_steel_inventory_tab_widget_last_selected_tab_index:
            self.sort_items()  # * This happens when the last selected tab is the first tab
        else:
            self.tab_widget.setCurrentIndex(self.parent.structural_steel_inventory_tab_widget_last_selected_tab_index)

    def save_category_tabs_order(self):
        self.settings_file.load_data()
        tab_order = self.settings_file.get_value("category_tabs_order")
        tab_order["Sheets In Inventory"] = self.tab_widget.get_tab_order()
        self.settings_file.set_value("category_tabs_order", tab_order)

    def save_scroll_position(self):
        if self.finished_loading:
            self.parent.save_scroll_position(self.category, self.category_tables[self.category])

    def restore_scroll_position(self):
        if scroll_position := self.parent.get_scroll_position(self.category):
            self.category_tables[self.category].verticalScrollBar().setValue(scroll_position)

    def popout(self):
        self.popout_widget = PopoutWidget(self.layout(), self.parent)
        self.popout_widget.show()
        self.pushButton_popout.setIcon(Icons.redock_icon)
        self.pushButton_popout.clicked.disconnect()
        self.pushButton_popout.clicked.connect(self.popout_widget.close)

    def sync_changes(self):
        self.parent.sync_changes("structural_steel_inventory_tab")

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def clear_layout(self, layout: QVBoxLayout | QHBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
