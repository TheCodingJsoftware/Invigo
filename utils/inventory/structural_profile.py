import copy
from enum import Enum
from typing import TYPE_CHECKING, Union

from utils.inventory.inventory_item import InventoryItem
from utils.inventory.order import Order
from utils.workspace.flowtag import Flowtag
from utils.workspace.flowtag_data import FlowtagData
from utils.workspace.flowtag_timer import FlowtagTimer
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
        self.flowtag: Flowtag = None
        self.timer: FlowtagTimer = None
        self.flowtag_data: FlowtagData = None
        self.current_flow_tag_index: int = 0
        self.current_flow_tag_status_index: int = 0
        self.orders: list[Order] = []
        self.red_quantity_limit: int = 4
        self.yellow_quantity_limit: int = 10
        self.has_sent_warning: bool = False
        self.quantity: int = 0
        self.latest_change_quantity: str = ""
        self.length: float = 0.0
        self.cost: float = 0.0
        self.latest_change_cost: str = ""

        # NOTE Non serializable variables
        self.id = -1

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
        self.flowtag = Flowtag(data.get("flow_tag", []), self.workspace_settings)

        self.current_flow_tag_index = data.get("current_flow_tag_index", 0)
        self.current_flow_tag_status_index = data.get(
            "current_flow_tag_status_index", 0
        )
        # If deepcopy is not done, than a reference is kept in the original object it was copied from
        # and then it messes everything up, specifically it will mess up laser cut parts
        # when you add a job to workspace
        self.timer = FlowtagTimer(copy.deepcopy(data.get("timer", {})), self.flowtag)
        self.flowtag_data = FlowtagData(self.flowtag)
        self.flowtag_data.load_data(data.get("flow_tag_data", {}))
        # if tag := self.flowtag.get_tag_with_similar_name("laser"):
        #     self.flowtag_data.set_tag_data(
        #         tag, "expected_time_to_complete", int(self.machine_time * 60)
        #     )
        # elif tag := self.flowtag.get_tag_with_similar_name("picking"):
        #     self.flowtag_data.set_tag_data(
        #         tag, "expected_time_to_complete", self.weight
        #     )
        self.orders.clear()
        for order_data in data.get("orders", []):
            order = Order(order_data)
            self.add_order(order)

        self.name = data.get("name", "")
        self.part_number = data.get("part_number", "")
        self.red_quantity_limit: int = data.get("red_quantity_limit", 4)
        self.yellow_quantity_limit: int = data.get("yellow_quantity_limit", 10)
        self.has_sent_warning: bool = data.get("has_sent_warning", False)
        self.quantity: int = data.get("quantity", 0)
        self.latest_change_quantity: str = data.get("latest_change_quantity", "")
        self.length: float = data.get("length", 0.0)
        self.cost: float = data.get("cost", 0.0)
        self.latest_change_cost: str = data.get("latest_change_cost", "")

    def to_dict(self) -> dict[str, dict]:
        return {
            "name": self.name,
            "part_number": self.part_number,
            "material": self.material,
            "notes": self.notes,
            "quantity": self.quantity,
            "latest_change_quantity": self.latest_change_quantity,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
            "has_sent_warning": self.has_sent_warning,
            "orders": [order.to_dict() for order in self.orders],
            "length": self.length,
            "cost": self.cost,
            "latest_change_cost": self.latest_change_cost,
            "flow_tag": self.flowtag.to_dict(),
            "flow_tag_data": self.flowtag_data.to_dict(),
            "current_flow_tag_index": self.current_flow_tag_index,
            "current_flow_tag_status_index": self.current_flow_tag_status_index,
            "categories": [category.name for category in self.categories],
        }