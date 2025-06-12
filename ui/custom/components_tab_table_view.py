import contextlib
from datetime import datetime
from enum import Enum, auto
from functools import partial
from typing import TYPE_CHECKING

import sympy
from PyQt6.QtCore import QAbstractTableModel, QDate, QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import OrderStatusButton
from ui.dialogs.set_component_order_pending_dialog import SetComponentOrderPendingDialog
from ui.dialogs.update_component_order_pending_dialog import (
    UpdateComponentOrderPendingDialog,
)
from ui.icons import Icons
from ui.theme import theme_var
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.order import Order
from utils.settings import Settings

if TYPE_CHECKING:
    from ui.widgets.components_tab import ComponentsTab


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class ComponentsTableColumns(AutoNumber):
    PART_NAME = auto()
    PART_NUMBER = auto()
    QUANTITY_PER_UNIT = auto()
    QUANTITY_IN_STOCK = auto()
    ITEM_PRICE = auto()
    USD_CAD = auto()
    TOTAL_COST_IN_STOCK = auto()
    TOTAL_UNIT_COST = auto()
    PRIORITY = auto()
    SHELF_NUMBER = auto()
    NOTES = auto()
    PO = auto()
    ORDERS = auto()


class OrderWidget(QWidget):
    orderOpened = pyqtSignal()
    orderClosed = pyqtSignal()

    def __init__(
        self, component: Component, components_tab: "ComponentsTab", parent=None
    ):
        super().__init__(parent)
        self.components_tab: "ComponentsTab" = components_tab
        self.component = component

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
                f"QDateEdit{{border-top-left-radius: 0; border-top-right-radius: 0; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;}} QDateEdit:hover{{border-color: {theme_var('primary-green')}; }}"
            )
            arrival_date.wheelEvent = lambda event: self.parent().wheelEvent(event)
            arrival_date.setDate(date)
            arrival_date.setCalendarPopup(True)
            arrival_date.setToolTip("Expected arrival time.")
            arrival_date.dateChanged.connect(
                partial(self.date_changed, order, arrival_date)
            )

            v_layout.addWidget(order_status_button)
            v_layout.addWidget(arrival_date)
            self.orders_layout.addLayout(v_layout)
        # self.parent.category_tables[self.parent.category].setColumnWidth(12, 400)  # Widgets don't like being resized with columns
        # self.parent.update_component_row_color(self.parent.category_tables[self.parent.category], self.component)

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
            self.components_tab.components_inventory.save()
            self.components_tab.sync_changes()
            self.load_ui()

    def order_button_pressed(
        self, order: Order, order_status_button: OrderStatusButton
    ):
        self.orderOpened.emit()
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
                self.orderClosed.emit()
                return
            self.components_tab.components_inventory.save()
            self.components_tab.sync_changes()
            self.components_tab.sort_components()
            self.components_tab.select_last_selected_item()
            self.load_ui()
        else:  # Close order pressed
            order_status_button.setChecked(True)
            self.orderClosed.emit()

    def date_changed(self, order: Order, arrival_date: QDateEdit):
        order.expected_arrival_time = arrival_date.date().toString("yyyy-MM-dd")
        self.components_tab.components_inventory.save()
        self.components_tab.sync_changes()

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


class OrderWidgetDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._widgets: dict[QModelIndex, OrderWidget] = {}

    def paint(self, painter, option: OrderWidget, index: QModelIndex):
        if index not in self._widgets:
            self.createOrderWidget(option, index)

    def createOrderWidget(self, option: OrderWidget, index: QModelIndex):
        component = index.model().data(index, Qt.ItemDataRole.UserRole)
        if component:
            order_widget = OrderWidget(component, self.parent, option.widget)
            order_widget.setGeometry(option.rect)
            order_widget.setParent(option.widget.viewport())
            order_widget.show()
            self._widgets[index] = order_widget

    def sizeHint(self, option, index):
        return QSize(500, 60)

    def clear_widgets(self):
        for widget in self._widgets.values():
            widget.deleteLater()
        self._widgets.clear()


class CurrencyComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)
        combo_box.addItems(["USD", "CAD"])
        return combo_box

    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        current_value = index.data(Qt.ItemDataRole.EditRole)
        if current_value:
            idx = editor.findText(current_value)
            if idx >= 0:
                editor.setCurrentIndex(idx)

    def setModelData(
        self, editor: QComboBox, model: "ComponentsTableModel", index: QModelIndex
    ):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class PriorityComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)
        combo_box.addItems(["Default", "Low", "Medium", "High"])
        return combo_box

    def setEditorData(self, editor: QComboBox, index: QModelIndex):
        current_index = index.data(Qt.ItemDataRole.EditRole)
        if current_index is not None:
            editor.setCurrentIndex(int(current_index))

    def setModelData(
        self, editor: QComboBox, model: "ComponentsTableModel", index: QModelIndex
    ):
        model.setData(index, editor.currentIndex(), Qt.ItemDataRole.EditRole)

    def displayText(self, value, locale):
        mapping = {0: "Default", 1: "Low", 2: "Medium", 3: "High"}
        return mapping.get(int(value), "Default")


class NotesPlainTextEdit(QPlainTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("notes")
        self.setStyleSheet("QPlainTextEdit#notes{border-radius: 0px;}")
        self.setFixedHeight(60)


class NotesPlainTextDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = NotesPlainTextEdit(parent)
        return editor

    def setEditorData(self, editor: NotesPlainTextEdit, index):
        text = index.data(Qt.ItemDataRole.EditRole)
        if text:
            editor.setPlainText(text)

    def setModelData(
        self, editor: NotesPlainTextEdit, model: "ComponentsTableModel", index
    ):
        text = editor.toPlainText()
        model.setData(index, text, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor: NotesPlainTextEdit, option, index):
        editor.setGeometry(option.rect)


class ComponentsTableModel(QAbstractTableModel):
    def __init__(
        self, components_inventory: ComponentsInventory, category, parent=None
    ):
        super().__init__(parent)
        self.parent: "ComponentsTab" = parent
        self.components_inventory = components_inventory
        self.category = category

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

        self.headers = {
            "Part Name": ComponentsTableColumns.PART_NAME.value,
            "Part Number": ComponentsTableColumns.PART_NUMBER.value,
            "Quantity per Unit": ComponentsTableColumns.QUANTITY_PER_UNIT.value,
            "Quantity in Stock": ComponentsTableColumns.QUANTITY_IN_STOCK.value,
            "Item Price": ComponentsTableColumns.ITEM_PRICE.value,
            "USD/CAD": ComponentsTableColumns.USD_CAD.value,
            "Total Cost in Stock": ComponentsTableColumns.TOTAL_COST_IN_STOCK.value,
            "Total Unit Cost": ComponentsTableColumns.TOTAL_UNIT_COST.value,
            "Priority": ComponentsTableColumns.PRIORITY.value,
            "Shelf #": ComponentsTableColumns.SHELF_NUMBER.value,
            "Notes": ComponentsTableColumns.NOTES.value,
            "PO": ComponentsTableColumns.PO.value,
            "Orders": ComponentsTableColumns.ORDERS.value,
        }

    def rowCount(self, parent=QModelIndex()):
        return len(
            [
                comp
                for comp in self.components_inventory.components
                if self.category in comp.categories
            ]
        )

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        components_in_category = [
            comp
            for comp in self.components_inventory.components
            if self.category in comp.categories
        ]

        if index.row() >= len(components_in_category):
            return None
        component = components_in_category[index.row()]

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            column = list(self.headers.values())[index.column()]
            if column == ComponentsTableColumns.PART_NAME.value:
                return component.part_name
            elif column == ComponentsTableColumns.PART_NUMBER.value:
                return component.part_number
            elif column == ComponentsTableColumns.QUANTITY_PER_UNIT.value:
                return f"{component.get_category_quantity(self.category):,.2f}"
            elif column == ComponentsTableColumns.QUANTITY_IN_STOCK.value:
                return f"{component.quantity:,.2f}"
            elif column == ComponentsTableColumns.ITEM_PRICE.value:
                return f'${component.price:,.2f} {"USD" if component.use_exchange_rate else "CAD"}'
            elif column == ComponentsTableColumns.USD_CAD.value:
                return "USD" if component.use_exchange_rate else "CAD"
            elif column == ComponentsTableColumns.TOTAL_COST_IN_STOCK.value:
                return f"${component.get_total_cost_in_stock():,.2f}"
            elif column == ComponentsTableColumns.TOTAL_UNIT_COST.value:
                return f"${component.get_total_unit_cost(self.category):,.2f}"
            elif column == ComponentsTableColumns.PRIORITY.value:
                return component.priority
            elif column == ComponentsTableColumns.SHELF_NUMBER.value:
                return component.shelf_number
            elif column == ComponentsTableColumns.NOTES.value:
                return component.notes
            elif column == ComponentsTableColumns.PO.value:
                return "PO Button Placeholder"
            elif column == ComponentsTableColumns.ORDERS.value:
                return ""  # Handle with custom widgets or a delegate
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            column = list(self.headers.values())[index.column()]
            if column in (
                ComponentsTableColumns.PART_NAME.value,
                ComponentsTableColumns.NOTES.value,
            ):
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            else:
                return Qt.AlignmentFlag.AlignCenter
        elif role == Qt.ItemDataRole.FontRole:
            return self.tables_font

        elif role == Qt.ItemDataRole.ToolTipRole:
            if index.column() == ComponentsTableColumns.ITEM_PRICE.value:
                converted_price = (
                    component.price * self.get_exchange_rate()
                    if component.use_exchange_rate
                    else component.price / self.get_exchange_rate()
                )
                return f'${converted_price:,.2f} {"CAD" if component.use_exchange_rate else "USD"}\n{component.latest_change_price}'
            elif index.column() == ComponentsTableColumns.QUANTITY_PER_UNIT.value:
                return f"Unit quantities:\n{component.print_category_quantities()}"

        elif (
            role == Qt.ItemDataRole.UserRole
            and index.column() == ComponentsTableColumns.ORDERS.value
        ):
            return component

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return list(self.headers.keys())[section]
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False

        components_in_category = [
            comp
            for comp in self.components_inventory.components
            if self.category in comp.categories
        ]

        if index.row() >= len(components_in_category):
            return None

        component = components_in_category[index.row()]

        column = list(self.headers.values())[index.column()]

        if role == Qt.ItemDataRole.EditRole:
            if column == ComponentsTableColumns.PART_NAME.value:
                component.part_name = value
            elif column == ComponentsTableColumns.PART_NUMBER.value:
                component.part_number = value
            elif column == ComponentsTableColumns.QUANTITY_PER_UNIT.value:
                try:
                    quantity = float(
                        sympy.sympify(
                            value.strip().replace(",", ""),
                            evaluate=True,
                        )
                    )
                    component.set_category_quantity(self.category, quantity)
                except sympy.SympifyError:
                    return False
            elif column == ComponentsTableColumns.QUANTITY_IN_STOCK.value:
                try:
                    quantity = float(
                        sympy.sympify(
                            value.strip().replace(",", ""),
                            evaluate=True,
                        )
                    )
                    component.quantity = quantity
                except sympy.SympifyError:
                    return False
            elif column == ComponentsTableColumns.ITEM_PRICE.value:
                try:
                    new_price = float(
                        sympy.sympify(
                            value.replace("USD", "")
                            .replace("CAD", "")
                            .strip()
                            .replace(",", "")
                            .replace("$", ""),
                            evaluate=True,
                        )
                    )
                    component.price = new_price
                except sympy.SympifyError:
                    return False
            elif column == ComponentsTableColumns.USD_CAD.value:
                component.use_exchange_rate = value == "USD"
                self.update_price_based_on_exchange_rate(component)
            elif column == ComponentsTableColumns.PRIORITY.value:
                component.priority = value
            elif column == ComponentsTableColumns.SHELF_NUMBER.value:
                component.shelf_number = value
            elif column == ComponentsTableColumns.NOTES.value:
                component.notes = value
            print(f"{component.name}")
            self.components_inventory.save()
            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
        )

    def update_price_based_on_exchange_rate(self, component: Component):
        if component.use_exchange_rate:
            converted_price = component.price * self.get_exchange_rate()
        else:
            converted_price = component.price / self.get_exchange_rate()
        tooltip_text = f'${converted_price:,.2f} {"CAD" if component.use_exchange_rate else "USD"}\n{component.latest_change_price}'
        row = self.components_inventory.components.index(component)
        index = self.index(row, ComponentsTableColumns.ITEM_PRICE.value)
        self.setData(index, tooltip_text, Qt.ItemDataRole.ToolTipRole)
        self.setData(
            index,
            f'${component.price:,.2f} {"USD" if component.use_exchange_rate else "CAD"}',
            Qt.ItemDataRole.DisplayRole,
        )

    def get_exchange_rate(self) -> float:
        return self.settings_file.get_value(setting_name="exchange_rate")

    def get_selected_components(
        self, selected_indexes: list[QModelIndex]
    ) -> list[Component]:
        selected_components: list[Component] = []

        components_in_category = [
            comp
            for comp in self.components_inventory.components
            if self.category in comp.categories
        ]

        for index in selected_indexes:
            if index.isValid():
                component = components_in_category[index.row()]
                selected_components.append(component)
        return selected_components


class ComponentsTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setSortingEnabled(False)
        self.setWordWrap(True)
        self.setShowGrid(True)

    def selectedItems(self) -> list[Component]:
        selected_indexes = self.selectionModel().selectedRows()
        model: ComponentsTableModel = self.model()
        return model.get_selected_components(selected_indexes)
