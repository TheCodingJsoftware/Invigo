from enum import Enum
from typing import TYPE_CHECKING

from utils.inventory.component import Component
from utils.inventory.inventory_item import InventoryItem

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class CoatingTypes(Enum):
    PAINT = "Paint"
    PRIMER = "Primer"
    POWDER = "Powder"


class CoatingItem(InventoryItem):
    def __init__(self, data, paint_inventory) -> None:
        super().__init__()
        self.paint_inventory: PaintInventory = paint_inventory
        self.id: int = -1
        self.component_id: int = -1
        self.part_name: str = ""
        self.part_number: str = ""
        self.component: Component | None = None
        self.color: str = "#ffffff"
        self.COATING_TYPE: CoatingTypes

        self.average_coverage: float = 300.0  # PAINT AND PRIMEr
        self.gravity: float = 2.0  # POWDER
        self.load_data(data)

    def get_component(self):
        self.component = self.paint_inventory.components_inventory.get_component_by_id(self.component_id)
        if self.component:
            self.part_number = self.component.part_number
            self.part_name = self.component.part_name

    def load_data(self, data):
        self.categories.clear()
        self.id = data.get("id", -1)
        self.component_id = data.get("component_id", -1)
        self.part_name = data.get("part_name", "")
        self.part_number = data.get("part_number", "")
        self.color = data.get("color", "#ffffff")
        self.average_coverage = data.get("average_coverage", 300)
        self.gravity = data.get("gravity", 2.0)
        self.COATING_TYPE = CoatingTypes(data.get("coating_type"))
        categories = data.get("categories", [])
        for category in self.paint_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)
        self.get_component()

    def to_dict(self):
        return {
            "id": self.id,
            "component_id": self.component_id,
            "name": self.part_number,
            "part_name": self.part_name,
            "part_number": self.part_number,
            "coating_type": self.COATING_TYPE.value,
            "color": self.color,
            "gravity": self.gravity,
            "average_coverage": self.average_coverage,
            "categories": [category.name for category in self.categories],
        }
