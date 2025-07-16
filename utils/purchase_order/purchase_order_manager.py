from typing import Callable

from natsort import natsorted
from PyQt6.QtCore import QThreadPool

from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.sheets_inventory import SheetsInventory
from utils.purchase_order.purchase_order import PurchaseOrder as PO
from utils.purchase_order.purchase_order import PurchaseOrderDict
from utils.purchase_order.shipping_address import ShippingAddress
from utils.purchase_order.vendor import Vendor, VendorDict
from utils.workers.components_inventory.update_components import UpdateComponentsWorker
from utils.workers.purchase_orders.delete_purchase_order import DeletePurchaseOrder
from utils.workers.purchase_orders.get_all_purchase_orders import GetAllPurchaseOrders
from utils.workers.purchase_orders.get_purchase_order import GetPurchaseOrderWorker
from utils.workers.purchase_orders.save_purchase_order import SavePurchaseOrderWorker
from utils.workers.runnable_chain import RunnableChain
from utils.workers.sheets_inventory.update_sheets import UpdateSheetsWorker
from utils.workers.shipping_addresses.delete_shipping_address import DeleteShippingAddressWorker
from utils.workers.shipping_addresses.get_all_shipping_addresses import GetAllShippingAddresses
from utils.workers.shipping_addresses.save_shipping_address import SaveShippingAddressWorker
from utils.workers.vendors.delete_vendor import DeleteVendorWorker
from utils.workers.vendors.get_all_vendors import GetAllVendors
from utils.workers.vendors.save_vendor import SaveVendorWorker


class PurchaseOrderManager:
    def __init__(
        self,
        components_inventory: ComponentsInventory,
        sheets_inventory: SheetsInventory,
    ):
        self.components_inventory = components_inventory
        self.sheets_inventory = sheets_inventory
        self.purchase_orders: list[PO] = []
        self.vendors: list[Vendor] = []
        self.shipping_addresses: list[ShippingAddress] = []

    def load_data(self, on_finished: Callable | None = None):
        self.chain = RunnableChain()

        get_vendors_worker = GetAllVendors()
        get_purchase_orders_worker = GetAllPurchaseOrders()
        get_shipping_addresses_worker = GetAllShippingAddresses()

        self.chain.add(get_vendors_worker, self.get_vendors_thread_response)
        self.chain.add(get_purchase_orders_worker, self.get_purchase_orders_thread_response)
        self.chain.add(get_shipping_addresses_worker, self.get_shipping_addresses_thread_response)

        if on_finished:
            self.chain.finished.connect(on_finished)

        self.chain.finished.connect(self.link_purchase_orders_with_orders)

        self.chain.start()

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
            po = PO(self.components_inventory, self.sheets_inventory)
            po.load_data(data["purchase_order_data"])
            po.id = data["id"]
            self.purchase_orders.append(po)

        self.purchase_orders.sort(key=lambda po: po.meta_data.purchase_order_number, reverse=True)

        next_step()

    def get_shipping_addresses_thread_response(self, response: list[dict], next_step: Callable):
        self.shipping_addresses.clear()
        for data in response:
            shipping_address = ShippingAddress(data)
            self.shipping_addresses.append(shipping_address)
        next_step()

    def get_purchase_order_data(self, purchase_order: PO, on_finished: Callable | None = None):
        worker = GetPurchaseOrderWorker(purchase_order.id)
        worker.signals.success.connect(self.handle_purchase_order_data)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def handle_purchase_order_data(self, response: tuple[dict, int]):
        data, purchase_order_id = response
        for purchase_order in self.purchase_orders:
            if purchase_order.id == purchase_order_id:
                purchase_order.load_data(data["purchase_order_data"])
                purchase_order.id = purchase_order_id
                break

    def get_latest_po_number(self, vendor: Vendor) -> int:
        return (
            next(
                (po.meta_data.purchase_order_number for po in self.purchase_orders if po.meta_data.vendor == vendor),
                0,
            )
            + 1
        )

    def link_purchase_orders_with_orders(self):
        purchase_order_lookup = {po.id: po for po in self.purchase_orders}

        for sheet in self.sheets_inventory.sheets:
            for order in sheet.orders:
                if po := purchase_order_lookup.get(order.purchase_order_id):
                    order.set_purchase_order(po)

        for component in self.components_inventory.components:
            for order in component.orders:
                if po := purchase_order_lookup.get(order.purchase_order_id):
                    order.set_purchase_order(po)

    def get_organized_purchase_orders(self) -> dict[str, list[PO]]:
        return {vendor.name: [po for po in self.purchase_orders if po.meta_data.vendor.name == vendor.name] for vendor in self.vendors}

    def get_vendor_by_name(self, vendor_name: str) -> Vendor | None:
        return next((vendor for vendor in self.vendors if vendor.name == vendor_name), None)

    def get_shipping_address_by_name(self, shipping_address_name: str) -> ShippingAddress | None:
        return next((address for address in self.shipping_addresses if address.name == shipping_address_name), None)

    def find_orders_by_vendor(self, vendor_name: str) -> list[PO]:
        return [po for po in self.purchase_orders if po.meta_data.vendor.name.lower() == vendor_name.lower()]

    def add_purchase_order(self, purchase_order: PO, on_finished: Callable | None = None):
        worker = SavePurchaseOrderWorker(purchase_order)
        worker.signals.success.connect(self.add_purchase_order_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_purchase_order_thread_response(self, response: tuple[dict, PO]):
        data, po = response
        po.id = data["id"]
        self.purchase_orders.append(po)

    def save_purchase_order(self, purchase_order: PO, on_finished: Callable | None = None):
        self.save_purchase_order_chain = RunnableChain()

        save_purchase_order_worker = SavePurchaseOrderWorker(purchase_order)
        save_components_worker = UpdateComponentsWorker(purchase_order.components)
        save_sheets_worker = UpdateSheetsWorker(purchase_order.sheets)

        self.save_purchase_order_chain.add(save_purchase_order_worker, self.save_purchase_order_thread_response)
        self.save_purchase_order_chain.add(save_components_worker, self.save_components_thread_response)
        self.save_purchase_order_chain.add(save_sheets_worker, self.save_sheets_thread_response)

        if on_finished:
            self.save_purchase_order_chain.finished.connect(on_finished)

        self.save_purchase_order_chain.start()

    def save_purchase_order_thread_response(self, response: tuple[dict, PO], next_step: Callable):
        data, po = response
        po.id = data["id"]
        next_step()

    def save_components_thread_response(self, response: tuple[dict, list[dict]], next_step: Callable):
        next_step()

    def save_sheets_thread_response(self, response: tuple[dict, list[dict]], next_step: Callable):
        next_step()

    def delete_purchase_order(self, purchase_order: PO, on_finished: Callable | None = None):
        worker = DeletePurchaseOrder(purchase_order.id)
        # worker.signals.success.connect(self.delete_purchase_order_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_vendor(self, vendor: Vendor, on_finished: Callable | None = None):
        worker = SaveVendorWorker(vendor)
        worker.signals.success.connect(self.add_vendor_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_vendor_thread_response(self, response: tuple[dict, Vendor]):
        data, vendor = response
        vendor.id = data["id"]
        self.vendors.append(vendor)

    def save_vendor(self, vendor: Vendor, on_finished: Callable | None = None):
        worker = SaveVendorWorker(vendor)
        worker.signals.success.connect(self.save_vendor_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def save_vendor_thread_response(self, response: tuple[dict, Vendor]):
        data, vendor = response
        vendor.id = data["id"]

    def delete_vendor(self, vendor: Vendor, on_finished: Callable | None = None):
        worker = DeleteVendorWorker(vendor.id)
        # worker.signals.success.connect(self.delete_vendor_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_shipping_address(self, shipping_address: ShippingAddress, on_finished: Callable | None = None):
        worker = SaveShippingAddressWorker(shipping_address)
        worker.signals.success.connect(self.add_shipping_address_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_shipping_address_thread_response(self, response: tuple[dict, ShippingAddress]):
        data, shipping_address = response
        shipping_address.id = data["id"]
        self.shipping_addresses.append(shipping_address)

    def save_shipping_address(self, shipping_address: ShippingAddress, on_finished: Callable | None = None):
        worker = SaveShippingAddressWorker(shipping_address)
        worker.signals.success.connect(self.save_shipping_address_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def save_shipping_address_thread_response(self, response: tuple[dict, ShippingAddress]):
        print("Saving shipping address response:", response)
        data, shipping_address = response
        shipping_address.id = data["id"]

    def delete_shipping_address(self, shipping_address: ShippingAddress, on_finished: Callable | None = None):
        worker = DeleteShippingAddressWorker(shipping_address.id)
        # worker.signals.success.connect(self.delete_shipping_address_thread_response)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)
