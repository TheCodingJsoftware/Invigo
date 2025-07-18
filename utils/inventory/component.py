import copy
from typing import TYPE_CHECKING, TypedDict

from utils.inventory.category import Category
from utils.inventory.inventory_item import InventoryItem
from utils.inventory.order import Order, OrderDict
from utils.purchase_order.vendor import Vendor

if TYPE_CHECKING:
    from utils.inventory.components_inventory import ComponentsInventory


class ComponentDict(TypedDict):
    id: int
    name: str
    part_number: str
    part_name: str
    category: str
    quantity: float
    price: float
    use_exchange_rate: bool
    priority: int
    shelf_number: str
    notes: str
    image_path: str
    latest_change_quantity: str
    latest_change_price: str
    red_quantity_limit: float
    yellow_quantity_limit: float
    quantity_to_order: int
    vendor_ids: list[int]
    orders: list[OrderDict]
    categories: list[str]
    category_quantities: dict[str, float]


class Component(InventoryItem):
    def __init__(self, data: ComponentDict, components_inventory):
        super().__init__()
        self.components_inventory: ComponentsInventory = components_inventory
        self.id: int = -1
        self.quantity: float = 0.0
        self.category_quantities: dict[Category, float] = {}
        self.part_number: str = ""
        self.part_name: str = ""
        self.price: float = 0.0
        self.use_exchange_rate: bool = False
        self.priority: int = 0
        self.shelf_number: str = ""
        self.notes: str = ""
        self.image_path: str = ""
        self.latest_change_quantity: str = "Nothing recorded"
        self.latest_change_price: str = "Nothing recorded"
        self.red_quantity_limit: float = 0.0
        self.yellow_quantity_limit: float = 0.0
        self.orders: list[Order] = []
        self.quantity_to_order: int = 0  # Purchase Order Quantity
        self.vendors: list[Vendor] = []
        self._vendor_ids: list[int] = []

        self.load_data(data)

    def get_exchange_rate(self) -> float:
        return 1.3

    def get_total_unit_cost(self, category: str | Category) -> float:
        if isinstance(category, str):
            category = self.components_inventory.get_category(category)
        exchange_rate = self.get_exchange_rate() if self.use_exchange_rate else 1
        return self.price * self.get_category_quantity(category) * exchange_rate

    def get_total_cost_in_stock(self) -> float:
        exchange_rate = self.get_exchange_rate() if self.use_exchange_rate else 1
        return max(self.price * self.quantity * exchange_rate, 0)

    def move_to_category(self, from_category: Category, to_category: Category):
        super().remove_from_category(from_category)
        self.add_to_category(to_category)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.components_inventory.remove_component(self)

    def add_order(self, order: Order):
        self.orders.append(order)

    def remove_order(self, order: Order):
        self.orders.remove(order)

    def get_category_quantity(self, category: str | Category) -> float:
        if isinstance(category, str):
            category = self.components_inventory.get_category(category)
        try:
            return self.category_quantities[category]
        except KeyError:
            return 1.0

    def set_category_quantity(self, category: str | Category, quantity: float) -> float:
        if isinstance(category, str):
            category = self.components_inventory.get_category(category)
        self.category_quantities[category] = quantity
        return quantity

    def print_category_quantities(self) -> str:
        return "".join(f"{i + 1}. {category.name}: {self.get_category_quantity(category)}\n" for i, category in enumerate(self.categories))

    def load_data(self, data: ComponentDict):
        self.id = data.get("id", -1)
        self.part_number = data.get("part_number", "")
        self.name = self.part_number
        self.quantity = data.get("quantity", 0.0)
        self.category_quantities.clear()
        for category_name, unit_quantity in data.get("category_quantities", {}).items():
            category = self.components_inventory.get_category(category_name)
            self.category_quantities.update({category: unit_quantity})
        self.part_name = data.get("part_name", "")
        self.price = data.get("price", 0.0)
        self.use_exchange_rate = data.get("use_exchange_rate", False)
        self.priority = data.get("priority", 0)
        self.shelf_number = data.get("shelf_number", "")
        self.notes = data.get("notes", "")
        self.image_path = data.get("image_path", "")
        self.latest_change_quantity = data.get("latest_change_quantity", "Nothing recorded")
        self.latest_change_price = data.get("latest_change_price", "Nothing recorded")
        self.red_quantity_limit = data.get("red_quantity_limit", 10.0)
        self.yellow_quantity_limit = data.get("yellow_quantity_limit", 20.0)

        self.quantity_to_order = data.get("quantity_to_order", 0)

        self._vendor_ids = data.get("vendor_ids", [])

        self.orders.clear()
        for order_data in data.get("orders", []):
            order = Order(order_data)
            self.add_order(order)

        self.categories.clear()
        categories = data.get("categories", [])
        for category in self.components_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)

    def get_copy(self) -> "Component":
        return copy.deepcopy(self)

    def to_dict(self) -> ComponentDict:
        return {
            "id": self.id,
            "name": self.name,
            "part_number": self.part_number,
            "part_name": self.part_name,
            "quantity": round(self.quantity, 2),
            "latest_change_quantity": self.latest_change_quantity,
            "price": round(self.price, 2),
            "latest_change_price": self.latest_change_price,
            "use_exchange_rate": self.use_exchange_rate,
            "priority": self.priority,
            "shelf_number": self.shelf_number,
            "notes": self.notes,
            "image_path": self.image_path,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
            "quantity_to_order": self.quantity_to_order,
            "vendor_ids": list({vendor.id for vendor in self.vendors}),
            "orders": [order.to_dict() for order in self.orders],
            "categories": [category.name for category in self.categories],
            "category_quantities": {category.name: self.category_quantities.get(category, 1.0) for category in self.categories},
        }
