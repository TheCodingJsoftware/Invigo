from typing import TYPE_CHECKING, Union

from utils.inventory.component import Component
from utils.inventory.inventory_item import InventoryItem

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class Powder(InventoryItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__()
        self.paint_inventory: PaintInventory = paint_inventory
        self.component: Component = None
        self.color: str = "#ffffff"
        self.gravity: float = 2.0
        self.load_data(data)

    def get_component(self):
        self.component = self.paint_inventory.components_inventory.get_component_by_part_name(self.name)

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        self.categories.clear()
        self.name = data.get("name", "")
        self.color = data.get("color", "#ffffff")
        self.gravity = data.get("gravity", 2.0)
        categories = data.get("categories", [])
        for category in self.paint_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)
        self.get_component()

    def to_dict(self) -> dict[str, dict]:
        return {
            "name": self.name,
            "color": self.color,
            "gravity": self.gravity,
            "categories": [category.name for category in self.categories],
        }
