from dataclasses import dataclass
from enum import Enum, auto
from typing import TypedDict

from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.sheet import Sheet
from utils.inventory.sheets_inventory import SheetsInventory
from utils.purchase_order.business_info import BusinessInfo, BusinessInfoDict
from utils.purchase_order.contact_info import ContactInfo, ContactInfoDict
from utils.purchase_order.shipping_address import ShippingAddress, ShippingAddressDict
from utils.purchase_order.vendor import Vendor, VendorDict


class MetaDataDict(TypedDict):
    purchase_order_number: int
    status: int
    order_date: str
    notes: str
    shipping_method: int
    shipping_address: ShippingAddressDict
    contact_info: ContactInfoDict
    business_info: BusinessInfoDict
    vendor: VendorDict


class POItemDict(TypedDict):
    id: int
    order_quantity: float


class PurchaseOrderDict(TypedDict):
    id: int
    meta_data: "MetaDataDict"
    components: list[POItemDict]
    sheets: list[POItemDict]


class AutoNumber(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return count


class Status(AutoNumber):
    PURCHASE_ORDER = auto()
    QUOTE = auto()


class ShippingMethod(AutoNumber):
    HOLD_FOR_PICKUP = auto()
    PICK_UP = auto()
    BRUDER_DELIVERY = auto()
    FED_EX = auto()
    MAIL = auto()
    SEND_BY_COURIER = auto()
    GARDWINE_COLLECT = auto()
    PRE_PAID = auto()
    MOTOPAK_COLLECT = auto()
    MOTOPACK_PRE_PAID = auto()
    GREHOUND_COLLECT = auto()
    ROSENORTH_COLLECT = auto()
    COLLECT = auto()
    WILL_CALL = auto()


@dataclass
class MetaData:
    vendor: Vendor
    shipping_address: ShippingAddress
    purchase_order_number: int = 0
    status: Status = Status.PURCHASE_ORDER
    shipping_method: ShippingMethod = ShippingMethod.HOLD_FOR_PICKUP
    order_date: str = ""
    notes: str = ""

    def __init__(self, data: MetaDataDict | None = None):
        if data:
            self.load_data(data)
        else:
            self.vendor = Vendor()
            self.purchase_order_number = 0
            self.status = Status.PURCHASE_ORDER
            self.shipping_method = ShippingMethod.HOLD_FOR_PICKUP
            self.shipping_address = ShippingAddress()
            self.order_date = ""
            self.notes = ""
        self.contact_info = ContactInfo()
        self.business_info = BusinessInfo()

    def load_data(self, data: MetaDataDict):
        self.vendor.load_data(data["vendor"])
        self.shipping_address.load_data(data.get("shipping_address", {}))
        self.status = Status(int(data.get("status", Status.PURCHASE_ORDER.value)))
        self.shipping_method = ShippingMethod(int(data.get("shipping_method", ShippingMethod.HOLD_FOR_PICKUP.value)))
        self.purchase_order_number = int(data.get("purchase_order_number", 0))
        self.order_date = data.get("order_date", "")
        self.notes = data.get("notes", "")

    def to_dict(self) -> MetaDataDict:
        return {
            "purchase_order_number": self.purchase_order_number,
            "status": self.status.value,
            "shipping_method": self.shipping_method.value,
            "shipping_address": self.shipping_address.to_dict(),
            "order_date": self.order_date,
            "notes": self.notes,
            "contact_info": self.contact_info.to_dict(),
            "business_info": self.business_info.to_dict(),
            "vendor": self.vendor.to_dict(),
        }


@dataclass
class PurchaseOrder:
    id: int = -1

    def __init__(
        self,
        components_inventory: ComponentsInventory,
        sheets_inventory: SheetsInventory,
    ) -> None:
        self.meta_data = MetaData()

        self.sheets_order_data: list[POItemDict] = []
        self.sheets: list[Sheet] = []
        self.sheets_inventory = sheets_inventory

        self.components_order_data: list[POItemDict] = []
        self.components: list[Component] = []
        self.components_inventory = components_inventory

    def get_name(self):
        return f"#{self.meta_data.purchase_order_number}"

    def load_data(self, data: PurchaseOrderDict):
        self.id = data.get("id", -1)
        self.meta_data.load_data(data["meta_data"])
        self.components.clear()
        self.components_order_data.clear()
        for component_data in data.get("components", []):
            if component := self.components_inventory.get_component_by_id(component_data["id"]):
                component.quantity_to_order = component_data.get("order_quantity", 0)
                self.components.append(component)
                self.components_order_data.append(component_data)

        self.sheets.clear()
        self.sheets_order_data.clear()
        for sheet_data in data.get("sheets", []):
            if sheet := self.sheets_inventory.get_sheet_by_id(sheet_data["id"]):
                sheet.quantity_to_order = sheet_data.get("order_quantity", 0)
                self.sheets.append(sheet)
                self.sheets_order_data.append(sheet_data)

    def set_component_order_quantity(self, component: Component, quantity_to_order: float):
        for item in self.components_order_data:
            if item["id"] == component.id:
                item["order_quantity"] = quantity_to_order
                return
        self.components_order_data.append({"id": component.id, "order_quantity": quantity_to_order})

    def set_sheet_order_quantity(self, sheet: Sheet, quantity_to_order: int):
        for item in self.sheets_order_data:
            if item["id"] == sheet.id:
                item["order_quantity"] = quantity_to_order
                return
        self.sheets_order_data.append({"id": sheet.id, "order_quantity": quantity_to_order})

    def get_component_quantity_to_order(self, component: Component) -> int:
        return next((item["order_quantity"] for item in self.components_order_data if item["id"] == component.id), 0)

    def get_sheet_quantity_to_order(self, sheet: Sheet) -> int:
        return next((item["order_quantity"] for item in self.sheets_order_data if item["id"] == sheet.id), 0)

    def to_dict(self) -> PurchaseOrderDict:
        return {
            "id": self.id,
            "meta_data": self.meta_data.to_dict(),
            "components": self.components_order_data,
            "sheets": self.sheets_order_data,
        }
