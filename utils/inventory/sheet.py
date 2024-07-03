import copy
from typing import TYPE_CHECKING, Union

from utils.inventory.category import Category
from utils.inventory.inventory_item import InventoryItem
from utils.inventory.order import Order

if TYPE_CHECKING:
    from utils.inventory.sheets_inventory import SheetsInventory


class Sheet(InventoryItem):
    def __init__(self, name: str, data: dict, sheets_inventory):
        super().__init__(name)
        self.sheets_inventory: SheetsInventory = sheets_inventory
        self.quantity: int = 0
        self.length: float = 0.0
        self.width: float = 0.0
        self.thickness: str = ""
        self.material: str = ""
        self.latest_change_quantity: str = ""
        self.red_quantity_limit: int = 4
        self.yellow_quantity_limit: int = 10
        self.has_sent_warning: bool = False
        self.notes: str = ""
        self.orders: list[Order] = []
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

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        self.quantity: int = data.get("quantity", 0)
        self.latest_change_quantity: str = data.get("latest_change_quantity", "")
        self.length: str = data.get("length", 120.0)
        self.width: str = data.get("width", 60.0)
        self.thickness: str = data.get("thickness", "")
        self.material: str = data.get("material", "")
        self.red_quantity_limit: int = data.get("red_quantity_limit", 4)
        self.yellow_quantity_limit: int = data.get("yellow_quantity_limit", 10)

        self.orders.clear()
        for order_data in data.get("orders", []):
            order = Order(order_data)
            self.add_order(order)

        self.has_sent_warning: bool = data.get("has_sent_warning", False)
        self.notes: str = data.get("notes", "")
        self.categories.clear()
        try:
            categories = data.get("categories", [])
            for category in self.sheets_inventory.get_categories():
                if category.name in categories:
                    self.categories.append(category)
        except (
            AttributeError
        ):  # Because these sheets come from utils.threads.load_nests.py
            self.categories = []

    def to_dict(self) -> dict[str, dict]:
        return {
            "quantity": self.quantity,
            "latest_change_quantity": self.latest_change_quantity,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
            "thickness": self.thickness,
            "material": self.material,
            "width": round(self.width, 3),
            "length": round(self.length, 3),
            "has_sent_warning": self.has_sent_warning,
            "notes": self.notes,
            "orders": [order.to_dict() for order in self.orders],
            "categories": [category.name for category in self.categories],
        }
