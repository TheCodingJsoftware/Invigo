from enum import Enum
from typing import TYPE_CHECKING, Union

from utils.inventory.inventory_item import InventoryItem
from utils.inventory.order import Order
from utils.workspace.flowtag import Flowtag
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from utils.inventory.structural_steel_inventory import StructuralSteelInventory
    from utils.structural_steel_settings.structural_steel_settings import StructuralSteelSettings


class ProfilesTypes(Enum):
    RECTANGULAR_BAR = "Rectangular Bar"
    ROUND_BAR = "Round Bar"
    FLAT_BAR = "Flat Bar"
    ANGLE_BAR = "Angle Bar"
    RECTANGULAR_TUBE = "Rectangular Tube"
    ROUND_TUBE = "Round Tube"
    DOM_ROUND_TUBE = "DOM Round Tube"
    PIPE = "Pipe"


class StructuralProfile(InventoryItem):
    def __init__(self, structural_steel_inventory):
        super().__init__()
        self.structural_steel_inventory: StructuralSteelInventory = structural_steel_inventory
        self.structural_steel_settings: StructuralSteelSettings = (
            self.structural_steel_inventory.structural_steel_settings
        )
        self.workspace_settings: WorkspaceSettings = self.structural_steel_inventory.workspace_settings

        self.part_number: str = ""
        self.notes: str = ""
        self.material: str = ""
        self.flow_tag: Flowtag = None
        self.orders: list[Order] = []
        self.red_quantity_limit: int = 4
        self.yellow_quantity_limit: int = 10
        self.has_sent_warning: bool = False
        self.quantity: int = 0
        self.latest_change_quantity: str = ""
        self.length: float = 0.0
        self.cost: float = 0.0
        self.latest_change_cost: str = ""

    def get_density(self) -> float:
        return self.structural_steel_settings.get_density(self.material) / 1728 # Convert from lb/ft^3 to lb/in^3

    def get_categories(self) -> list[str]:
        return [category.name for category in self.categories]

    def add_order(self, order: Order):
        self.orders.append(order)

    def remove_order(self, order: Order):
        self.orders.remove(order)

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        self.categories.clear()
        categories = data.get("categories", [])
        for category in self.structural_steel_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)
        self.material = data.get("material", "")
        self.notes = data.get("notes", "")
        self.flow_tag = Flowtag(data.get("flow_tag", []), self.workspace_settings)

        self.orders.clear()
        for order_data in data.get("orders", []):
            order = Order(order_data)
            self.add_order(order)

        self.name = data.get("name", "")
        self.red_quantity_limit: int = data.get("red_quantity_limit", 4)
        self.yellow_quantity_limit: int = data.get("yellow_quantity_limit", 10)
        self.has_sent_warning: bool = data.get("has_sent_warning", False)
        self.quantity: int = data.get("quantity", 0)
        self.latest_change_quantity: str = data.get("latest_change_quantity", "")
        self.length: float = data.get("length", 0.0)
        self.cost: float = data.get("cost", 0.0)
        self.latest_change_cost: str = data.get("latest_change_cost", "")