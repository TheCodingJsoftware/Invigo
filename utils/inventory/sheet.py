import copy
from typing import TYPE_CHECKING

from utils.inventory.category import Category
from utils.inventory.inventory_item import InventoryItem
from utils.inventory.order import Order
from utils.purchase_order.vendor import Vendor

if TYPE_CHECKING:
    from utils.inventory.sheets_inventory import SheetsInventory


class Sheet(InventoryItem):
    def __init__(self, data: dict, sheets_inventory):
        super().__init__()
        self.sheets_inventory: SheetsInventory = sheets_inventory
        self.id: int = -1
        self.quantity: int = 0
        self.price: float = 0.0
        self.price_per_pound: float = 0.0
        self.length: float = 0.0
        self.width: float = 0.0
        self.pounds_per_square_foot: float = 0.0
        self.thickness: str = ""
        self.material: str = ""
        self.latest_change_quantity: str = ""
        self.red_quantity_limit: int = 4
        self.yellow_quantity_limit: int = 10
        self.has_sent_warning: bool = False
        self.notes: str = ""
        self.orders: list[Order] = []
        self._vendor_ids: list[int] = []
        self.vendors: list[Vendor] = []
        self.quantity_to_order: int = 0  # Purchase Order Quantity
        self.load_data(data)

    def get_sheet_dimension(self) -> str:
        return f"{self.length:.3f}x{self.width:.3f}"

    def get_name(self) -> str:
        return f"{self.thickness} {self.material} {self.get_sheet_dimension()}"

    def get_copy(self) -> "Sheet":
        return copy.deepcopy(self)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.sheets_inventory.remove_sheet(self)

    def add_order(self, order: Order):
        self.orders.append(order)

    def remove_order(self, order: Order):
        self.orders.remove(order)

    def get_categories(self) -> list[str]:
        return [category.name for category in self.categories]

    def load_data(self, data: dict):
        self.id = data.get("id", -1)
        self.quantity = data.get("quantity", 0)
        self.price = data.get("price", 0.0)
        self.price_per_pound = data.get("price_per_pound", 0.0)
        self.latest_change_quantity = data.get("latest_change_quantity", "")
        self.length = data.get("length", 120.0)
        self.width = data.get("width", 60.0)
        self.pounds_per_square_foot = data.get("pounds_per_square_foot", 0.0)
        self.thickness = data.get("thickness", "")
        self.material = data.get("material", "")
        self.red_quantity_limit = data.get("red_quantity_limit", 4)
        self.yellow_quantity_limit = data.get("yellow_quantity_limit", 10)

        self.quantity_to_order = data.get("quantity_to_order", 0)

        self._vendor_ids = data.get("vendor_ids", [])

        self.orders.clear()
        for order_data in data.get("orders", []):
            order = Order(order_data)
            self.add_order(order)

        self.has_sent_warning = data.get("has_sent_warning", False)
        self.notes = data.get("notes", "")
        self.categories.clear()
        try:
            categories = data.get("categories", [])
            for category in self.sheets_inventory.get_categories():
                if category.name in categories:
                    self.categories.append(category)
        except AttributeError:  # Because these sheets come from utils.threads.load_nests.py
            self.categories = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.get_name(),
            "thickness": self.thickness,
            "material": self.material,
            "width": round(self.width, 3),
            "length": round(self.length, 3),
            "pounds_per_square_foot": self.pounds_per_square_foot,
            "has_sent_warning": self.has_sent_warning,
            "notes": self.notes,
            "quantity_to_order": self.quantity_to_order,
            "vendor_ids": list({vendor.id for vendor in self.vendors}),
            "orders": [order.to_dict() for order in self.orders],
            "categories": [category.name for category in self.categories],
            "quantity": self.quantity,
            "price": self.price,
            "price_per_pound": self.price_per_pound,
            "latest_change_quantity": self.latest_change_quantity,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
        }
