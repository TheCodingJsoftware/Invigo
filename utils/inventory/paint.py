from typing import TYPE_CHECKING, Union

from utils.inventory.component import Component
from utils.inventory.inventory_item import InventoryItem

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class Paint(InventoryItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__()
        self.paint_inventory: PaintInventory = paint_inventory
        self.component: Component = None
        self.color: str = "#ffffff"
        self.average_coverage: float = 300.0
        self.load_data(data)

    def get_component(self):
        self.component = (
            self.paint_inventory.components_inventory.get_component_by_part_name(
                self.name
            )
        )

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        self.categories.clear()
        self.name = data.get("name", "")
        self.color = data.get("color", "#ffffff")
        self.average_coverage = data.get("average_coverage", 300)
        categories = data.get("categories", [])
        for category in self.paint_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)
        self.get_component()

    def to_dict(self) -> dict[str, dict]:
        return {
            "name": self.name,
            "color": self.color,
            "average_coverage": self.average_coverage,
            "categories": [category.name for category in self.categories],
        }
