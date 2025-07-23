import contextlib
import logging
import webbrowser
from datetime import datetime
from enum import Enum, auto
from functools import partial
from typing import TYPE_CHECKING, Callable

from natsort import natsorted
from numpy import add
from PyQt6.QtCore import QDate, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QCursor, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import CustomTableWidget, OrderStatusButton
from ui.dialogs.add_component_dialog import AddComponentDialog
from ui.dialogs.add_vendor_dialog import AddVendorDialog
from ui.dialogs.edit_shipping_address_dialog import EditShippingAddressDialog
from ui.dialogs.purchase_order_dialog_UI import Ui_Dialog
from ui.dialogs.update_component_order_pending_dialog import (
    UpdateComponentOrderPendingDialog,
)
from ui.dialogs.view_item_history_dialog import ViewItemHistoryDialog
from ui.icons import Icons
from ui.theme import theme_var
from utils.colors import lighten_color
from utils.inventory.component import Component
from utils.inventory.order import Order, OrderDict
from utils.inventory.sheet import Sheet
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.purchase_order.purchase_order import PurchaseOrder, PurchaseOrderDict, ShippingMethod, Status
from utils.purchase_order.purchase_order_manager import PurchaseOrderManager
from utils.purchase_order.shipping_address import ShippingAddress
from utils.purchase_order.vendor import Vendor, VendorDict
from utils.workers.purchase_orders.get_all_purchase_orders import GetAllPurchaseOrders
from utils.workers.runnable_chain import RunnableChain
from utils.workers.vendors.get_all_vendors import GetAllVendors

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class AutoNumber(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return count


class ComponentsTableColumns(AutoNumber):
    PART_NAME = auto()
    PART_NUMBER = auto()
    UNIT_PRICE = auto()
    QUANTITY_IN_STOCK = auto()
    QUANTITY_TO_ORDER = auto()
    ORDER_COST = auto()
    ORDER_WIDGET = auto()
    HISTORY = auto()


class ComponentsTable(CustomTableWidget):
    ROW_HEIGHT = 60

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        editable_columns = [
            ComponentsTableColumns.PART_NAME,
            ComponentsTableColumns.PART_NUMBER,
            ComponentsTableColumns.UNIT_PRICE,
            ComponentsTableColumns.QUANTITY_TO_ORDER,
        ]
        self.set_editable_column_index([col.value for col in editable_columns])

        headers = {
            "Part Name": ComponentsTableColumns.PART_NAME.value,
            "Part Number": ComponentsTableColumns.PART_NUMBER.value,
            "Unit Price": ComponentsTableColumns.UNIT_PRICE.value,
            "Quantity in Stock": ComponentsTableColumns.QUANTITY_IN_STOCK.value,
            "Quantity to Order": ComponentsTableColumns.QUANTITY_TO_ORDER.value,
            "Order Cost": ComponentsTableColumns.ORDER_COST.value,
            "Orders": ComponentsTableColumns.ORDER_WIDGET.value,
            "History": ComponentsTableColumns.HISTORY.value,
        }

        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))


class ComponentOrdersWidget(QWidget):
    orderOpened = pyqtSignal()
    orderClosed = pyqtSignal()

    def __init__(self, component: Component, parent: "PurchaseOrderDialog"):
        super().__init__(parent)
        self._parent_widget: "PurchaseOrderDialog" = parent
        self.component = component

        self.h_layout = QHBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_layout = QHBoxLayout()

        # self.add_order_button = QPushButton("Add Order", self)
        # self.add_order_button.clicked.connect(self.create_order)
        # self.add_order_button.setFlat(True)
        # self.add_order_button.setIcon(Icons.plus_icon)

        # self.view_order_history_button = QPushButton("View Order History", self)
        # self.view_order_history_button.clicked.connect(self.view_order_history)
        # self.view_order_history_button.setFlat(True)
        # self.view_order_history_button.setIcon(Icons.button_history_icon)

        self.h_layout.addLayout(self.orders_layout)
        # self.h_layout.addWidget(self.add_order_button)
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
            order_status_button.clicked.connect(partial(self.order_button_pressed, order, order_status_button))

            year, month, day = map(int, order.expected_arrival_time.split("-"))
            date = QDate(year, month, day)

            arrival_date = QDateEdit(self)
            arrival_date.setStyleSheet(
                f"QDateEdit{{border-top-left-radius: 0; border-top-right-radius: 0; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;}} QDateEdit:hover{{border-color: {theme_var('primary-green')}; }}"
            )
            arrival_date.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
            arrival_date.setDate(date)
            arrival_date.setCalendarPopup(True)
            arrival_date.setToolTip("Expected arrival time.")
            arrival_date.dateChanged.connect(partial(self.date_changed, order, arrival_date))

            v_layout.addWidget(order_status_button)
            v_layout.addWidget(arrival_date)
            self.orders_layout.addLayout(v_layout)

    # def create_order(self):
    #     select_date_dialog = SetComponentOrderPendingDialog(
    #         f'Set an expected arrival time for "{self.component.part_name}," the number of parts ordered, and notes.',
    #         self,
    #     )
    #     if select_date_dialog.exec():
    #         data: OrderDict = {
    #             "purchase_order_id": -1,
    #             "expected_arrival_time": select_date_dialog.get_selected_date(),
    #             "order_pending_quantity": select_date_dialog.get_order_quantity(),
    #             "order_pending_date": datetime.now().strftime("%Y-%m-%d"),
    #             "notes": select_date_dialog.get_notes(),
    #         }
    #         new_order = Order(data)
    #         self.component.add_order(new_order)
    #         self._parent_widget.components_inventory.save_component(self.component)
    #         # self.parent.components_inventory.save_local_copy()
    #         # self.parent.sync_changes()
    #         self.load_ui()

    # def view_order_history(self):
    #     view_item_history_dialog = ViewItemHistoryDialog(
    #         self, "component", self.component.id
    #     )
    #     view_item_history_dialog.show()

    def order_button_pressed(self, order: Order, order_status_button: OrderStatusButton):
        self.orderOpened.emit()
        dialog = UpdateComponentOrderPendingDialog(order, f"Update order for {self.component.part_name}", self)
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
                self.component.latest_change_quantity = (
                    f"Used: Order pending - add quantity\nChanged from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                )
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
            # self.parent.components_inventory.save_local_copy()
            self._parent_widget.purchase_order_manager.components_inventory.save_component(self.component)
            self._parent_widget.load_components_table()
            self._parent_widget.unsaved_changes = True
            # self.parent.sync_changes()
            # self._parent_widget.sort_components()
            # self._parent_widget.select_last_selected_item()
            self.load_ui()
        else:  # Close order pressed
            order_status_button.setChecked(True)
            self.orderClosed.emit()

    def date_changed(self, order: Order, arrival_date: QDateEdit):
        order.expected_arrival_time = arrival_date.date().toString("yyyy-MM-dd")
        # self.parent.components_inventory.save_local_copy()
        self._parent_widget.purchase_order_manager.components_inventory.save_component(self.component)
        # self.parent.sync_changes()

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


class SheetsTableColumns(AutoNumber):
    SHEET_NAME = auto()
    PRICE_PER_POUND = auto()
    QUANTITY_IN_STOCK = auto()
    QUANTITY_TO_ORDER = auto()
    WEIGHT = auto()
    ORDER_COST = auto()
    ORDER_WIDGET = auto()
    HISTORY = auto()


class SheetsTable(CustomTableWidget):
    ROW_HEIGHT = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        editable_columns = [SheetsTableColumns.QUANTITY_TO_ORDER, SheetsTableColumns.PRICE_PER_POUND]
        self.set_editable_column_index([col.value for col in editable_columns])

        headers = {
            "Sheet Name": SheetsTableColumns.SHEET_NAME.value,
            "Price per Pound": SheetsTableColumns.PRICE_PER_POUND.value,
            "Quantity in Stock": SheetsTableColumns.QUANTITY_IN_STOCK.value,
            "Quantity to\nOrder (sheets)": SheetsTableColumns.QUANTITY_TO_ORDER.value,
            "Weight (lbs)": SheetsTableColumns.WEIGHT.value,
            "Order Cost": SheetsTableColumns.ORDER_COST.value,
            "Orders": SheetsTableColumns.ORDER_WIDGET.value,
            "History": SheetsTableColumns.HISTORY.value,
        }

        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))


class SheetOrdersWidget(QWidget):
    orderOpened = pyqtSignal()
    orderClosed = pyqtSignal()

    def __init__(self, sheet: Sheet, parent: "PurchaseOrderDialog"):
        super().__init__(parent)
        self._parent_widget: "PurchaseOrderDialog" = parent
        self.sheet = sheet

        self.h_layout = QHBoxLayout()
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_layout = QHBoxLayout()

        # self.add_order_button = QPushButton("Add Order", self)
        # self.add_order_button.clicked.connect(self.create_order)
        # self.add_order_button.setFlat(True)
        # self.add_order_button.setIcon(Icons.plus_icon)

        # self.view_order_history_button = QPushButton("View Order History", self)
        # self.view_order_history_button.clicked.connect(self.view_order_history)
        # self.view_order_history_button.setFlat(True)
        # self.view_order_history_button.setIcon(Icons.button_history_icon)

        self.h_layout.addLayout(self.orders_layout)
        # self.h_layout.addWidget(self.add_order_button)
        # self.h_layout.addWidget(self.view_order_history_button)
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
            order_status_button.clicked.connect(partial(self.order_button_pressed, order, order_status_button))

            year, month, day = map(int, order.expected_arrival_time.split("-"))
            date = QDate(year, month, day)

            arrival_date = QDateEdit(self)
            arrival_date.setStyleSheet(
                "QDateEdit{border-top-left-radius: 0; border-top-right-radius: 0; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;} QDateEdit:hover{border-color: #3bba6d; }"
            )
            arrival_date.wheelEvent = lambda event: self._parent_widget.wheelEvent(event)
            arrival_date.setDate(date)
            arrival_date.setCalendarPopup(True)
            arrival_date.setToolTip("Expected arrival time.")
            arrival_date.dateChanged.connect(partial(self.date_changed, order, arrival_date))

            v_layout.addWidget(order_status_button)
            v_layout.addWidget(arrival_date)
            self.orders_layout.addLayout(v_layout)
        # self._parent_widget.category_tables[
        #     self._parent_widget.category
        # ].setColumnWidth(7, 400)  # Widgets don't like being resized with columns
        # self._parent_widget.update_sheet_row_color(
        #     self._parent_widget.category_tables[self._parent_widget.category],
        #     self.sheet,
        # )

    # def create_order(self):
    #     select_date_dialog = SetComponentOrderPendingDialog(
    #         f'Set an expected arrival time for "{self.sheet.get_name()}," the number of parts ordered, and notes.',
    #         self,
    #     )
    #     if select_date_dialog.exec():
    #         data: OrderDict = {
    #             "purchase_order_id": -1,
    #             "expected_arrival_time": select_date_dialog.get_selected_date(),
    #             "order_pending_quantity": select_date_dialog.get_order_quantity(),
    #             "order_pending_date": datetime.now().strftime("%Y-%m-%d"),
    #             "notes": select_date_dialog.get_notes(),
    #         }
    #         new_order = Order(data)
    #         self.sheet.add_order(new_order)
    #         self._parent_widget.sheets_inventory.save_sheet(self.sheet)
    #         # self._parent_widget.sheets_inventory.save_local_copy()
    #         # self._parent_widget.sync_changes()
    #         self.load_ui()

    # def view_order_history(self):
    #     item_history_dialog = ViewItemHistoryDialog(self, "sheet", self.sheet.id)
    #     item_history_dialog.tabWidget.setCurrentIndex(2)
    #     item_history_dialog.show()

    def order_button_pressed(self, order: Order, order_status_button: OrderStatusButton):
        self.orderOpened.emit()
        dialog = UpdateComponentOrderPendingDialog(order, f"Update order for {self.sheet.get_name()}", self)
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
                self.sheet.latest_change_quantity = (
                    f"Used: Order pending - add quantity\nChanged from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                )
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
            self._parent_widget.purchase_order_manager.sheets_inventory.save_sheet(self.sheet)
            self._parent_widget.load_sheets_table()
            self._parent_widget.unsaved_changes = True
            # self._parent_widget.sheets_inventory.save_local_copy()
            # self._parent_widget.sync_changes()
            # self._parent_widget.sort_sheets()
            # self._parent_widget.select_last_selected_item()
            self.load_ui()
        else:  # Close order pressed
            order_status_button.setChecked(True)
            self.orderClosed.emit()

    def date_changed(self, order: Order, arrival_date: QDateEdit):
        order.expected_arrival_time = arrival_date.date().toString("yyyy-MM-dd")
        self._parent_widget.purchase_order_manager.sheets_inventory.save_sheet(self.sheet)
        # self._parent_widget.sheets_inventory.save_local_copy()
        # self._parent_widget.sync_changes()

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


class PurchaseOrderDialog(QDialog, Ui_Dialog):
    closed = pyqtSignal()

    def __init__(
        self,
        parent: "MainWindow",
        purchase_order_manager: PurchaseOrderManager,
        purchase_order: PurchaseOrder,
    ):
        super().__init__(parent)
        self._parent_widget = parent

        self.setupUi(self)

        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.unsaved_changes = False

        self.purchase_order_manager = purchase_order_manager
        self.purchase_order = purchase_order
        self.vendors: list[Vendor] = []
        self.purchase_orders: list[PurchaseOrder] = []

        self.tree_widget_purchase_orders: dict[str, dict[str, QTreeWidgetItem | PurchaseOrder | Vendor]] = {}

        self.component_orders_widgets: list[ComponentOrdersWidget] = []
        self.sheets_orders_widgets: list[SheetOrdersWidget] = []

        self.components_table = ComponentsTable(self)
        self.components_table.rowChanged.connect(self.components_table_row_changed)
        self.components_dict: dict[int, Component] = {}

        self.sheets_table = SheetsTable(self)
        self.sheets_table.rowChanged.connect(self.sheets_table_row_changed)
        self.sheets_dict: dict[int, Sheet] = {}

        if self.purchase_order.meta_data.purchase_order_number:
            self.purchase_order_manager.get_purchase_order_data(self.purchase_order, on_finished=self.load_ui)
        else:
            self.load_ui()

    def load_ui(self):
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_components, self.widget_components)
        if not self.purchase_order.components:
            self.pushButton_components.click()
            self.pushButton_components.click()
        else:
            self.pushButton_components.setChecked(True)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_sheets, self.widget_sheets)
        if not self.purchase_order.sheets:
            self.pushButton_sheets.click()
            self.pushButton_sheets.click()
        else:
            self.pushButton_sheets.setChecked(True)

        self.pushButton_refresh_purchase_orders.setIcon(Icons.refresh_icon)
        self.pushButton_refresh_purchase_orders.clicked.connect(self.refresh_purchase_orders)
        self.pushButton_autofill.clicked.connect(self.autofill_purchase_order)
        self.pushButton_edit_vendor.setIcon(Icons.edit_icon)
        self.pushButton_edit_vendor.clicked.connect(self.edit_vendor)
        self.pushButton_edit_shipping_address.setIcon(Icons.edit_icon)
        self.pushButton_edit_shipping_address.clicked.connect(self.edit_shipping_address)
        self.pushButton_save.clicked.connect(self.save)
        self.pushButton_duplicate.clicked.connect(self.duplicate)
        self.pushButton_apply_orders.clicked.connect(self.apply_orders)
        self.pushButton_save_and_apply_orders.clicked.connect(self.save_and_apply_orders)
        self.pushButton_print.clicked.connect(self.open_printout)
        self.pushButton_delete.clicked.connect(self.delete)
        self.pushButton_close.clicked.connect(self.close)

        self.comboBox_vendor.addItems([vendor.name for vendor in self.purchase_order_manager.vendors])

        if self.purchase_order.meta_data.purchase_order_number <= 1:
            if selected_vendor := self.purchase_order_manager.get_vendor_by_name(self.comboBox_vendor.currentText()):
                self.purchase_order.meta_data.vendor = selected_vendor
            self.doubleSpinBox_po_number.setValue(self.purchase_order_manager.get_latest_po_number(self.purchase_order.meta_data.vendor))
            self.purchase_order.meta_data.purchase_order_number = int(self.doubleSpinBox_po_number.value())
        else:
            self.doubleSpinBox_po_number.setValue(self.purchase_order.meta_data.purchase_order_number)

        self.doubleSpinBox_po_number.valueChanged.connect(self.meta_data_changed)

        status_list = list(Status)
        self.comboBox_status.addItems([status.name.replace("_", " ").title() for status in status_list])
        try:
            status_index = status_list.index(self.purchase_order.meta_data.status)
        except ValueError:
            status_index = 0  # fallback to first if not found
        self.comboBox_status.setCurrentIndex(status_index)
        self.comboBox_status.currentIndexChanged.connect(self.meta_data_changed)

        self.comboBox_shipping_method.addItems([method.name.replace("_", " ").title() for method in ShippingMethod])
        self.comboBox_shipping_method.setCurrentIndex(self.purchase_order.meta_data.shipping_method.value)
        self.comboBox_shipping_method.currentIndexChanged.connect(self.meta_data_changed)
        self.comboBox_shipping_address.addItems([address.name for address in self.purchase_order_manager.shipping_addresses])
        self.comboBox_shipping_address.setCurrentText(self.purchase_order.meta_data.shipping_address.name)
        self.comboBox_shipping_address.setToolTip(self.purchase_order.meta_data.shipping_address.__str__())
        self.comboBox_shipping_address.currentIndexChanged.connect(self.meta_data_changed)

        self.comboBox_vendor.setCurrentText(self.purchase_order.meta_data.vendor.name)
        self.comboBox_vendor.setToolTip(self.purchase_order.meta_data.vendor.__str__())
        self.comboBox_vendor.currentIndexChanged.connect(self.vendor_changed)

        order_date_qdate = QDate.fromString(self.purchase_order.meta_data.order_date, "yyyy-MM-dd")
        if not order_date_qdate.isValid():
            order_date_qdate = QDate.currentDate()

        self.dateEdit_expected_arrival.setDate(order_date_qdate)
        self.dateEdit_expected_arrival.dateChanged.connect(self.meta_data_changed)

        self.textEdit_notes.setText(self.purchase_order.meta_data.notes)
        self.textEdit_notes.textChanged.connect(self.meta_data_changed)

        self.layout_components.addWidget(self.components_table)
        self.pushButto_add_component.clicked.connect(self.add_component)
        self.load_components_table()
        self.create_components_table_context_menu()

        self.layout_sheets.addWidget(self.sheets_table)
        self.pushButton_add_sheet.clicked.connect(self.add_sheet)
        self.load_sheets_table()
        self.create_sheets_table_context_menu()

        self.treeWidget_purchase_orders.setColumnCount(2)
        self.treeWidget_purchase_orders.setHeaderLabels(["Vendor/PO Number", "Status"])
        self.treeWidget_purchase_orders.itemDoubleClicked.connect(self.tree_widget_double_clicked)

        self.refresh_purchase_orders()

    def vendor_changed(self):
        if selected_vendor := self.purchase_order_manager.get_vendor_by_name(self.comboBox_vendor.currentText()):
            self.purchase_order.meta_data.vendor = selected_vendor
            self.comboBox_vendor.setToolTip(selected_vendor.__str__())
            self.doubleSpinBox_po_number.setValue(self.purchase_order_manager.get_latest_po_number(selected_vendor))
        self.unsaved_changes = True

    def meta_data_changed(self):
        self.purchase_order.meta_data.shipping_method = ShippingMethod(self.comboBox_shipping_method.currentIndex())
        self.purchase_order.meta_data.purchase_order_number = int(self.doubleSpinBox_po_number.value())
        if selected_shipping_address := self.purchase_order_manager.get_shipping_address_by_name(self.comboBox_shipping_address.currentText()):
            self.purchase_order.meta_data.shipping_address = selected_shipping_address
            self.comboBox_shipping_address.setToolTip(selected_shipping_address.__str__())
        self.purchase_order.meta_data.purchase_order_number = int(self.doubleSpinBox_po_number.value())
        self.purchase_order.meta_data.order_date = self.dateEdit_expected_arrival.date().toString("yyyy-MM-dd")
        self.purchase_order.meta_data.notes = self.textEdit_notes.toPlainText()
        self.unsaved_changes = True

    # * \/ COMPONENTS TABLE \/
    def get_selected_components(self) -> list[Component]:
        selected_components: list[Component] = []
        selected_rows = self.get_selected_rows(self.components_table)
        selected_components.extend(component for row, component in self.components_dict.items() if row in selected_rows)
        return selected_components

    def add_component(self):
        add_component_dialog = AddComponentDialog(self.purchase_order_manager.components_inventory, self)
        if add_component_dialog.exec():
            if selected_components := add_component_dialog.get_selected_components():
                for component in selected_components:
                    component.vendors.append(self.purchase_order.meta_data.vendor)
                    self.purchase_order.components.append(component)
                    self.purchase_order.set_component_order_quantity(component, 0)
                    self.add_component_to_table(component)
            else:
                new_component = Component(
                    {
                        "part_name": add_component_dialog.get_name(),
                        "part_number": add_component_dialog.get_name(),
                    },
                    self.purchase_order_manager.components_inventory,
                )

                def add_component_to_purchase_order():
                    self.purchase_order.components.append(new_component)
                    new_component.vendors.append(self.purchase_order.meta_data.vendor)
                    new_component.quantity = 0
                    self.purchase_order.set_component_order_quantity(new_component, add_component_dialog.get_current_quantity())
                    self.add_component_to_table(new_component)

                self.purchase_order_manager.components_inventory.add_component(new_component, on_finished=add_component_to_purchase_order)

            self.unsaved_changes = True

            QTimer.singleShot(100, self.components_table_loaded)

    def add_component_to_table(self, component: Component):
        self.components_table.blockSignals(True)
        row_count = self.components_table.rowCount()
        self.components_table.insertRow(row_count)
        self.components_table.setRowHeight(row_count, self.components_table.ROW_HEIGHT)
        self.components_dict[row_count] = component

        part_name = component.part_name
        part_number = component.part_number
        unit_price = component.price
        quantity_in_stock = component.quantity
        price_suffix = "CAD" if component.use_exchange_rate else "USD"
        quantity_to_order = self.purchase_order.get_component_quantity_to_order(component)
        order_cost = unit_price * quantity_to_order

        history_button = QPushButton("View History", self)
        history_button.clicked.connect(partial(self.open_component_history, component))
        history_button.setFlat(True)
        history_button.setIcon(Icons.button_history_icon)
        history_button.setToolTip("Open the component history.")

        part_name_widget = QTableWidgetItem(part_name)
        part_name_widget.setToolTip(f'<img src="{component.image_path}" width="150">')
        part_number_widget = QTableWidgetItem(part_number)
        part_number_widget.setToolTip(f'<img src="{component.image_path}" width="150">')
        price_widget = QTableWidgetItem(f"${unit_price:,.2f} {price_suffix}")
        quantity_in_stock_widget = QTableWidgetItem(str(quantity_in_stock))
        quantity_in_stock_widget.setToolTip(
            f"Category quantities:\n{component.print_category_quantities()}\nRed Quanatity Limit: {component.red_quantity_limit}\nYellow Quantity Limit: {component.yellow_quantity_limit}"
        )
        order_cost_widget = QTableWidgetItem(f"${order_cost:,.2f} {price_suffix}")
        order_cost_widget.setToolTip(f"Order cost: {order_cost}\nOrder quantity: {quantity_to_order}")

        self.components_table.setItem(row_count, ComponentsTableColumns.PART_NAME.value, part_name_widget)
        self.components_table.setItem(row_count, ComponentsTableColumns.PART_NUMBER.value, part_number_widget)
        self.components_table.setItem(row_count, ComponentsTableColumns.UNIT_PRICE.value, price_widget)
        self.components_table.setItem(
            row_count,
            ComponentsTableColumns.QUANTITY_IN_STOCK.value,
            quantity_in_stock_widget,
        )
        self.components_table.setItem(
            row_count,
            ComponentsTableColumns.QUANTITY_TO_ORDER.value,
            QTableWidgetItem(str(quantity_to_order)),
        )
        self.components_table.setCellWidget(row_count, ComponentsTableColumns.HISTORY.value, history_button)
        self.components_table.setItem(row_count, ComponentsTableColumns.ORDER_COST.value, order_cost_widget)
        order_widget = ComponentOrdersWidget(component, self)
        order_widget.orderOpened.connect(lambda: self.components_table.blockSignals(True))
        order_widget.orderClosed.connect(lambda: self.components_table.blockSignals(False))
        self.components_table.setCellWidget(row_count, ComponentsTableColumns.ORDER_WIDGET.value, order_widget)
        self.component_orders_widgets.append(order_widget)
        self.components_table.blockSignals(False)

    def components_table_row_changed(self, row: int):
        self.components_table.blockSignals(True)
        if component := self.components_dict.get(row):
            try:
                part_name = self.components_table.item(row, ComponentsTableColumns.PART_NAME.value).text()
                part_number = self.components_table.item(row, ComponentsTableColumns.PART_NUMBER.value).text()
                unit_price = float(
                    self.components_table.item(row, ComponentsTableColumns.UNIT_PRICE.value).text().replace("$", "").replace(",", "").replace("CAD", "").replace("USD", "").strip()
                )
                quantity_to_order = float(self.components_table.item(row, ComponentsTableColumns.QUANTITY_TO_ORDER.value).text().replace(",", "").strip())

                component.part_name = part_name
                component.part_number = part_number
                component.price = unit_price
                self.purchase_order.set_component_order_quantity(component, quantity_to_order)
                order_cost = unit_price * quantity_to_order
                price_suffix = "CAD" if component.use_exchange_rate else "USD"

                self.components_table.item(row, ComponentsTableColumns.UNIT_PRICE.value).setText(f"${unit_price:,.2f} {price_suffix}")
                self.components_table.item(row, ComponentsTableColumns.ORDER_COST.value).setText(f"${order_cost:,.2f} {price_suffix}")
                self.components_table.item(row, ComponentsTableColumns.QUANTITY_TO_ORDER.value).setText(f"{quantity_to_order:,}")

                self.unsaved_changes = True
            except Exception as e:
                print(e)
                logging.error(f"Error loading component: {e}")

        self.components_table.blockSignals(False)

    def load_components_table(self):
        self.components_dict.clear()
        self.components_table.setRowCount(0)
        self.component_orders_widgets.clear()
        for component in self.purchase_order.components:
            self.add_component_to_table(component)

        QTimer.singleShot(100, self.components_table_loaded)

    def components_table_loaded(self):
        self.components_table.resizeColumnsToContents()
        self.components_table.setFixedHeight(self.components_table.rowHeight(0) * self.components_table.rowCount() + 50)

    def create_components_table_context_menu(self):
        self.components_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu = QMenu(self)

        def remove_components():
            selected_components = self.get_selected_components()
            if not selected_components:
                return

            for component in selected_components:
                self.purchase_order.components.remove(component)
            self.load_components_table()

        delete_component_action = QAction("Remove Selected Components", self)
        delete_component_action.triggered.connect(remove_components)
        menu.addAction(delete_component_action)

        self.components_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    # * \/ SHEETS TABLE \/
    def get_selected_sheets(self) -> list[Sheet]:
        selected_sheets: list[Sheet] = []
        selected_rows = self.get_selected_rows(self.sheets_table)
        selected_sheets.extend(sheet for row, sheet in self.sheets_dict.items() if row in selected_rows)
        return selected_sheets

    def add_sheet(self):
        all_sheets = [sheet.get_name() for sheet in self.purchase_order_manager.sheets_inventory.sheets]

        sheet_name, ok = QInputDialog.getItem(self, "Add Sheet", "Select a sheet to add:", all_sheets, 0, False)
        if sheet_name and ok:
            if sheet := self.purchase_order_manager.sheets_inventory.get_sheet_by_name(sheet_name):
                self.purchase_order.set_sheet_order_quantity(sheet, 0)
                self.purchase_order.sheets.append(sheet)
                self.add_sheet_to_table(sheet)
                self.unsaved_changes = True

                QTimer.singleShot(100, self.sheets_table_loaded)

    def add_sheet_to_table(self, sheet: Sheet):
        self.sheets_table.blockSignals(True)
        row_count = self.sheets_table.rowCount()
        self.sheets_table.insertRow(row_count)
        self.sheets_table.setRowHeight(row_count, self.sheets_table.ROW_HEIGHT)
        self.sheets_dict[row_count] = sheet

        sheet_name = sheet.get_name()
        price_per_pound = self.purchase_order_manager.sheets_inventory.sheet_settings.get_price_per_pound(sheet.material)
        quantity_in_stock = sheet.quantity
        quantity_to_order = self.purchase_order.get_sheet_quantity_to_order(sheet)
        quantity_weight = quantity_to_order * ((sheet.length * sheet.width) / 144) * sheet.pounds_per_square_foot
        order_price = price_per_pound * quantity_to_order * ((sheet.length * sheet.width) / 144) * sheet.pounds_per_square_foot
        history_button = QPushButton("View History", self)
        history_button.clicked.connect(partial(self.open_sheet_history, sheet))
        history_button.setFlat(True)
        history_button.setIcon(Icons.button_history_icon)
        history_button.setToolTip("Open the sheet history.")

        self.sheets_table.setItem(row_count, SheetsTableColumns.SHEET_NAME.value, QTableWidgetItem(sheet_name))

        self.sheets_table.setItem(
            row_count,
            SheetsTableColumns.PRICE_PER_POUND.value,
            QTableWidgetItem(f"${price_per_pound:,.2f}"),
        )

        self.sheets_table.setItem(
            row_count,
            SheetsTableColumns.QUANTITY_IN_STOCK.value,
            QTableWidgetItem(f"{quantity_in_stock:,}"),
        )
        self.sheets_table.setItem(
            row_count,
            SheetsTableColumns.QUANTITY_TO_ORDER.value,
            QTableWidgetItem(f"{quantity_to_order:,}"),
        )
        self.sheets_table.setItem(
            row_count,
            SheetsTableColumns.WEIGHT.value,
            QTableWidgetItem(f"{quantity_weight:,.2f}"),
        )
        self.sheets_table.setCellWidget(row_count, SheetsTableColumns.HISTORY.value, history_button)
        self.sheets_table.setItem(
            row_count,
            SheetsTableColumns.ORDER_COST.value,
            QTableWidgetItem(f"${order_price:,.2f} CAD"),
        )
        order_widget = SheetOrdersWidget(sheet, self)
        order_widget.orderOpened.connect(lambda: self.sheets_table.blockSignals(True))
        order_widget.orderClosed.connect(lambda: self.sheets_table.blockSignals(False))
        self.sheets_table.setCellWidget(row_count, SheetsTableColumns.ORDER_WIDGET.value, order_widget)
        self.sheets_table.blockSignals(False)

    def sheets_table_row_changed(self, row: int):
        self.sheets_table.blockSignals(True)
        if sheet := self.sheets_dict.get(row):
            with contextlib.suppress(ValueError):
                price_per_pound = float(
                    self.sheets_table.item(row, SheetsTableColumns.PRICE_PER_POUND.value).text().replace("CAD", "").replace("USD", "").replace("$", "").replace(",", "").strip()
                )
                quantity_to_order = float(self.sheets_table.item(row, SheetsTableColumns.QUANTITY_TO_ORDER.value).text().replace(",", "").strip())

                sheet.price_per_pound = price_per_pound
                self.purchase_order.set_sheet_order_quantity(sheet, quantity_to_order)
                quantity_weight = quantity_to_order * ((sheet.length * sheet.width) / 144) * sheet.pounds_per_square_foot
                order_cost = price_per_pound * quantity_to_order * ((sheet.length * sheet.width) / 144) * sheet.pounds_per_square_foot

                self.sheets_table.item(row, SheetsTableColumns.ORDER_COST.value).setText(f"${order_cost:,.2f}")
                self.sheets_table.item(row, SheetsTableColumns.PRICE_PER_POUND.value).setText(f"${price_per_pound:,.2f}")
                self.sheets_table.item(row, SheetsTableColumns.QUANTITY_TO_ORDER.value).setText(f"{quantity_to_order:,}")
                self.sheets_table.item(row, SheetsTableColumns.WEIGHT.value).setText(f"{quantity_weight:,.2f}")

                self.unsaved_changes = True

        self.sheets_table.blockSignals(False)

    def sheets_table_loaded(self):
        self.sheets_table.resizeColumnsToContents()
        self.sheets_table.setFixedHeight(self.sheets_table.rowHeight(0) * self.sheets_table.rowCount() + 50)

    def load_sheets_table(self):
        self.sheets_dict.clear()
        self.sheets_table.setRowCount(0)
        self.sheets_orders_widgets.clear()
        for sheet in self.purchase_order.sheets:
            self.add_sheet_to_table(sheet)

        QTimer.singleShot(100, self.sheets_table_loaded)

    def create_sheets_table_context_menu(self):
        self.sheets_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu = QMenu(self)

        def remove_sheets():
            selected_sheets = self.get_selected_sheets()
            if not selected_sheets:
                return

            for sheet in selected_sheets:
                self.purchase_order.sheets.remove(sheet)
            self.load_sheets_table()

        delete_sheet_action = QAction("Remove Selected Sheets", self)
        delete_sheet_action.triggered.connect(remove_sheets)
        menu.addAction(delete_sheet_action)

        self.sheets_table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    # * \/ PURCHASE ORDERS \/
    def load_data_vendor_po_data(self, on_finished: Callable | None = None):
        self.chain = RunnableChain()

        get_vendors_worker = GetAllVendors()
        get_purchase_orders_worker = GetAllPurchaseOrders()

        self.chain.add(get_vendors_worker, self.get_vendors_thread_response)
        self.chain.add(get_purchase_orders_worker, self.get_purchase_orders_thread_response)

        if on_finished:
            self.chain.finished.connect(on_finished)

        self.chain.start()

    def refresh_purchase_orders(self):
        def data_loaded():
            self.tree_widget_purchase_orders.clear()
            self.treeWidget_purchase_orders.clear()
            for vendor_name, purchase_orders in self.get_organized_purchase_orders().items():
                if vendor := self.get_vendor_by_name(vendor_name):
                    vendor_item = QTreeWidgetItem(self.treeWidget_purchase_orders)
                    vendor_item.setText(0, vendor.name)
                    for purchase_order in purchase_orders:
                        po_item = QTreeWidgetItem(vendor_item)
                        po_item.setText(0, purchase_order.get_name())
                        po_item.setText(1, purchase_order.meta_data.status.name.replace("_", " ").title())

                        self.tree_widget_purchase_orders[f"{vendor.name}/{purchase_order.get_name()}"] = {
                            "purchase_order": purchase_order,
                            "vendor": vendor,
                            "tree_item": po_item,
                        }

                        vendor_item.addChild(po_item)
                    self.treeWidget_purchase_orders.addTopLevelItem(vendor_item)

            def resize_columns():
                self.treeWidget_purchase_orders.resizeColumnToContents(0)
                self.treeWidget_purchase_orders.resizeColumnToContents(1)

            QTimer.singleShot(100, resize_columns)

        self.load_data_vendor_po_data(on_finished=data_loaded)

    def get_vendor_by_name(self, vendor_name: str) -> Vendor | None:
        return next((vendor for vendor in self.vendors if vendor.name == vendor_name), None)

    def get_organized_purchase_orders(self) -> dict[str, list[PurchaseOrder]]:
        return {vendor.name: [po for po in self.purchase_orders if po.meta_data.vendor.name == vendor.name] for vendor in self.vendors}

    def get_vendors_thread_response(self, response: list[VendorDict], next_step: Callable):
        self.vendors.clear()
        for vendor_data in response:
            vendor = Vendor(vendor_data)
            self.vendors.append(vendor)

        self.vendors = natsorted(self.vendors, key=lambda v: v.name)

        next_step()

    def get_purchase_orders_thread_response(self, response: list[dict[str, PurchaseOrderDict]], next_step: Callable):
        if not response:
            next_step()
            return
        self.purchase_orders.clear()
        for data in response:
            po = PurchaseOrder(self.purchase_order_manager.components_inventory, self.purchase_order_manager.sheets_inventory)
            po.load_data(data["purchase_order_data"])
            po.id = data["id"]
            self.purchase_orders.append(po)

        self.purchase_orders.sort(key=lambda po: po.meta_data.purchase_order_number, reverse=True)

        next_step()

    def tree_widget_double_clicked(self, item: QTreeWidgetItem, column: int):
        selected_tree_item: QTreeWidgetItem | None = None
        selected_purchase_order: PurchaseOrder | None = None
        selected_vendor: Vendor | None = None
        for _, data in self.tree_widget_purchase_orders.items():
            if data["tree_item"] == item:
                selected_tree_item = data["tree_item"]
                selected_purchase_order = data["purchase_order"]
                selected_vendor = data["vendor"]
                break

        if not selected_tree_item:
            return

        if self.unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Unsaved changes",
                "You have unsaved changes. Are you sure you want to load this purchase order?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                self,
            )
            if msg.exec() != QMessageBox.StandardButton.Yes:
                return

        self.load_purchase_order_data(selected_purchase_order)

    def load_purchase_order_data(self, new_po: PurchaseOrder):
        self.purchase_order = new_po

        self.comboBox_vendor.blockSignals(True)
        self.comboBox_vendor.setCurrentText(new_po.meta_data.vendor.name)
        self.comboBox_vendor.blockSignals(False)

        self.comboBox_status.blockSignals(True)
        self.comboBox_status.setCurrentIndex(new_po.meta_data.status.value)
        self.comboBox_status.blockSignals(False)

        self.comboBox_shipping_method.blockSignals(True)
        self.comboBox_shipping_method.setCurrentIndex(new_po.meta_data.shipping_method.value)
        self.comboBox_shipping_method.blockSignals(False)

        self.doubleSpinBox_po_number.blockSignals(True)
        self.doubleSpinBox_po_number.setValue(new_po.meta_data.purchase_order_number)
        self.doubleSpinBox_po_number.blockSignals(False)

        self.dateEdit_expected_arrival.blockSignals(True)
        self.dateEdit_expected_arrival.setDate(QDate.fromString(new_po.meta_data.order_date, "yyyy-MM-dd"))
        self.dateEdit_expected_arrival.blockSignals(False)

        self.textEdit_notes.blockSignals(True)
        self.textEdit_notes.setText(new_po.meta_data.notes)
        self.textEdit_notes.blockSignals(False)

        self.load_components_table()
        self.load_sheets_table()
        self.meta_data_changed()

        self.unsaved_changes = False

        msg = QMessageBox(
            QMessageBox.Icon.Information,
            "Success",
            f"Successfully loaded {new_po.meta_data.vendor.name} {new_po.get_name()}",
            QMessageBox.StandardButton.Ok,
            self,
        )
        msg.exec()

    def autofill_purchase_order(self):
        are_you_sure = QMessageBox(
            QMessageBox.Icon.Question,
            "Autofill Purchase Order",
            "Are you sure you want to autofill this purchase order?\n\nThis is permanent and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            self,
        )
        if are_you_sure.exec() != QMessageBox.StandardButton.Yes:
            return

        self.purchase_order_manager.autofill_purchase_order(self.purchase_order)
        self.load_purchase_order_data(self.purchase_order)

    # * \/ OTHER \/
    def open_sheet_history(self, sheet: Sheet):
        item_history_dialog = ViewItemHistoryDialog(self, "sheet", sheet.id)
        item_history_dialog.show()

    def open_component_history(self, component: Component):
        item_history_dialog = ViewItemHistoryDialog(self, "component", component.id)
        item_history_dialog.show()

    def get_selected_vendor(self) -> Vendor | None:
        return self.purchase_order_manager.get_vendor_by_name(self.comboBox_vendor.currentText())

    def load_vendor_data(self):
        def load_vendor_data():
            self.comboBox_vendor.blockSignals(True)
            self.comboBox_vendor.clear()
            self.comboBox_vendor.addItems([vendor.name for vendor in self.purchase_order_manager.vendors])
            self.comboBox_vendor.setCurrentText(self.purchase_order.meta_data.vendor.name)
            self.comboBox_vendor.setToolTip(self.purchase_order.meta_data.vendor.__str__())

            self.comboBox_vendor.blockSignals(False)

        self.purchase_order_manager.load_data(on_finished=load_vendor_data)
        self._parent_widget.load_po_menus()

    def get_selected_shipping_address(self) -> ShippingAddress | None:
        return self.purchase_order_manager.get_shipping_address_by_name(self.comboBox_shipping_address.currentText())

    def load_shipping_address_data(self):
        def load_shipping_address_data():
            self.comboBox_shipping_address.blockSignals(True)

            self.comboBox_shipping_address.clear()
            self.comboBox_shipping_address.addItems([address.name for address in self.purchase_order_manager.shipping_addresses])
            self.comboBox_shipping_address.setCurrentText(self.purchase_order.meta_data.shipping_address.name)
            self.comboBox_shipping_address.setToolTip(self.purchase_order.meta_data.shipping_address.__str__())

            self.comboBox_shipping_address.blockSignals(False)

        self.purchase_order_manager.load_data(on_finished=load_shipping_address_data)
        self._parent_widget.load_po_menus()

    def duplicate(self):
        new_po = PurchaseOrder(self.purchase_order_manager.components_inventory, self.purchase_order_manager.sheets_inventory)
        new_po.load_data(self.purchase_order.to_dict())
        new_po.id = -1
        new_po.meta_data.purchase_order_number = self.purchase_order.meta_data.purchase_order_number + 1

        self.doubleSpinBox_po_number.blockSignals(True)
        self.doubleSpinBox_po_number.setValue(new_po.meta_data.purchase_order_number)
        self.doubleSpinBox_po_number.blockSignals(False)

        self.purchase_order = new_po

        self.load_components_table()
        self.load_sheets_table()
        self.meta_data_changed()

        msg = QMessageBox(
            QMessageBox.Icon.Information,
            "Success",
            "Successfully duplicated purchase order.",
            QMessageBox.StandardButton.Ok,
            self,
        )
        msg.exec()

    def delete(self):
        are_you_sure = QMessageBox(
            QMessageBox.Icon.Question,
            "Are you sure?",
            "Are you sure you want to delete this purchase order?\n\nThis is permanent and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            self,
        )
        if are_you_sure.exec() == QMessageBox.StandardButton.Yes:

            def on_finished():
                self._parent_widget.load_po_menus()
                self.close()

            self.purchase_order_manager.delete_purchase_order(self.purchase_order, on_finished=on_finished)

    def save(self):
        self.purchase_order.meta_data.purchase_order_number = int(self.doubleSpinBox_po_number.value())
        self.purchase_order.meta_data.status = Status(self.comboBox_status.currentIndex())
        self.purchase_order.meta_data.shipping_method = ShippingMethod(self.comboBox_shipping_method.currentIndex())

        if selected_vendor := self.purchase_order_manager.get_vendor_by_name(self.comboBox_vendor.currentText()):
            self.purchase_order.meta_data.vendor = selected_vendor

        self.purchase_order.meta_data.order_date = self.dateEdit_expected_arrival.date().toString("yyyy-MM-dd")
        self.purchase_order.meta_data.notes = self.textEdit_notes.toPlainText()

        self.purchase_order_manager.save_purchase_order(self.purchase_order, on_finished=self.saved_purchase_order)

        self._parent_widget.load_po_menus()
        QTimer.singleShot(1000, self.refresh_purchase_orders)

    def apply_orders(self):
        are_you_sure = QMessageBox(
            QMessageBox.Icon.Question,
            "Apply Orders",
            "Are you sure you want to add orders to the items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            self,
        )
        if are_you_sure.exec() != QMessageBox.StandardButton.Yes:
            return

        components_to_save: list[Component] = []
        for component in self.purchase_order.components:
            if component.quantity_to_order <= 0:
                continue
            components_to_save.append(component)
            expected_arrival_time = self.dateEdit_expected_arrival.date().toString("yyyy-MM-dd")
            order_data: OrderDict = {
                "purchase_order_id": self.purchase_order.id,
                "expected_arrival_time": expected_arrival_time,
                "order_pending_date": QDate().toString("yyyy-MM-dd"),
                "order_pending_quantity": self.purchase_order.get_component_quantity_to_order(component),
                "notes": "",
            }
            order = Order(order_data)
            order.set_purchase_order(self.purchase_order)
            component.add_order(order)

        self.purchase_order_manager.components_inventory.save_components(components_to_save)

        if self.purchase_order.components:
            self.load_components_table()

        sheets_to_save: list[Sheet] = []
        for sheet in self.purchase_order.sheets:
            if sheet.quantity_to_order <= 0:
                continue
            sheets_to_save.append(sheet)
            expected_arrival_time = self.dateEdit_expected_arrival.date().toString("yyyy-MM-dd")
            order_data: OrderDict = {
                "purchase_order_id": self.purchase_order.id,
                "expected_arrival_time": expected_arrival_time,
                "order_pending_date": QDate().toString("yyyy-MM-dd"),
                "order_pending_quantity": self.purchase_order.get_sheet_quantity_to_order(sheet),
                "notes": "",
            }
            order = Order(order_data)
            order.set_purchase_order(self.purchase_order)
            sheet.add_order(order)

        self.purchase_order_manager.sheets_inventory.save_sheets(sheets_to_save)

        if self.purchase_order.sheets:
            self.load_sheets_table()

        self.unsaved_changes = True

        done = QMessageBox(
            QMessageBox.Icon.Information,
            "Orders Applied",
            "Orders applied successfully.",
            QMessageBox.StandardButton.Ok,
            self,
        )
        done.exec()

    def save_and_apply_orders(self):
        self.apply_orders()
        self.save()

    def edit_vendor(self):
        edit_vendor_dialog = AddVendorDialog(self, self.get_selected_vendor())
        if edit_vendor_dialog.exec():
            new_vendor = edit_vendor_dialog.get_vendor()
            self.purchase_order_manager.save_vendor(new_vendor, on_finished=self.load_vendor_data)
            self.purchase_order.meta_data.vendor = new_vendor
            self.unsaved_changes = True

    def edit_shipping_address(self):
        edit_shipping_address_dialog = EditShippingAddressDialog(self, self.get_selected_shipping_address())
        if edit_shipping_address_dialog.exec():
            new_shipping_address = edit_shipping_address_dialog.get_shipping_address()
            self.purchase_order_manager.save_shipping_address(new_shipping_address, on_finished=self.load_shipping_address_data)
            self.purchase_order.meta_data.shipping_address = new_shipping_address
            self.unsaved_changes = True

    def open_printout(self):
        webbrowser.open(
            f"http://{get_server_ip_address()}:{get_server_port()}/purchase_orders/view?id={self.purchase_order.id}",
            new=0,
        )

    def saved_purchase_order(self):
        self.unsaved_changes = False
        msg = QMessageBox(
            QMessageBox.Icon.Information,
            "Success",
            "Successfully saved purchase order.",
            QMessageBox.StandardButton.Ok,
            self,
        )
        msg.exec()

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = theme_var("primary")
        hover_color: str = lighten_color(base_color)
        inverted_color = theme_var("on-primary")
        button.setObjectName("tool_box_button")
        button.setStyleSheet(
            f"""
            QPushButton#tool_box_button {{
                border: 1px solid {theme_var("surface")};
                background-color: {theme_var("surface")};
                border-radius: {theme_var("border-radius")};
                color: {theme_var("on-surface")};
                text-align: left;
            }}

            /* CLOSED */
            QPushButton:!checked#tool_box_button {{
                color: {theme_var("on-surface")};
                border: 1px solid {theme_var("outline")};
            }}

            QPushButton:!checked:hover#tool_box_button {{
                background-color: {theme_var("outline-variant")};
            }}
            QPushButton:!checked:pressed#tool_box_button {{
                background-color: {theme_var("surface")};
            }}
            /* OPENED */
            QPushButton:checked#tool_box_button {{
                color: %(inverted_color)s;
                border-color: %(base_color)s;
                background-color: %(base_color)s;
                border-top-left-radius: {theme_var("border-radius")};
                border-top-right-radius: {theme_var("border-radius")};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}

            QPushButton:checked:hover#tool_box_button {{
                background-color: %(hover_color)s;
            }}

            QPushButton:checked:pressed#tool_box_button {{
                background-color: %(pressed_color)s;
            }}"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": base_color,
                "inverted_color": inverted_color,
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

    def get_selected_rows(self, table: QTableWidget) -> list[int]:
        rows: set[int] = {item.row() for item in table.selectedItems()}
        return list(rows)

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Unsaved changes",
                "Are you sure you want to close this purchase order without saving?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                self,
            )
            result = msg.exec()
            if result == QMessageBox.StandardButton.Yes:
                self.closed.emit()
                event.accept()
            else:
                event.ignore()
        else:
            self.closed.emit()
            event.accept()
