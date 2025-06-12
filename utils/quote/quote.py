from natsort import natsorted

from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.sheet_settings.sheet_settings import SheetSettings


class Quote:
    def __init__(
        self,
        name: str,
        data: dict,
        component_inventory: ComponentsInventory,
        laser_cut_inventory: LaserCutInventory,
        sheet_settings: SheetSettings,
    ):
        self.name = name

        if data is None:
            data = {
                "settings": {},
                "components": {},
                "laser_cut_parts": {},
                "nests": {},
            }

        self.component_inventory = component_inventory
        self.laser_cut_inventory = laser_cut_inventory
        self.sheet_settings = sheet_settings

        self.grouped_laser_cut_parts: list[LaserCutPart] = []
        self.components: list[Component] = []
        self.nests: list[Nest] = []
        self.custom_nest = Nest(
            {"name": "Custom"}, self.sheet_settings, self.laser_cut_inventory
        )
        self.custom_nest.is_custom = True

        # * Nest, Sheet, Item Quoting Settings
        self.laser_cutting_method: str = "CO2"
        self.laser_cutting_cost: float = self.sheet_settings.cost_for_laser[
            self.laser_cutting_method
        ]

        self.item_overhead: float = 18.0
        self.item_profit_margin: float = 30.0
        self.match_item_to_sheet_cost: bool = False

        self.sheet_overhead: float = 18.0
        self.sheet_profit_margin: float = 30.0
        self.match_sheet_cost_to_item: bool = False

        self.component_use_overhead: bool = False
        self.component_use_profit_margin: bool = False

        # * Paint Settings
        self.primer_overspray: float = 66.67

        self.paint_overspray: float = 66.67

        self.transfer_efficiency: float = 66.67
        self.mil_thickness: float = 2.0

        # * Quote Settings
        self.order_number: float = 0.0
        self.status: str = "In progress"
        self.date_shipped: str = ""
        self.date_expected: str = ""
        self.ship_to: str = ""

        # NOTE Non serialized variables
        self.unsaved_changes = False
        self.downloaded_from_server = False

        self.load_data(data)

    def changes_made(self):
        self.unsaved_changes = True

    def add_component(self, component: Component):
        self.components.append(component)

    def remove_component(self, component: Component):
        self.components.remove(component)

    def group_laser_cut_parts(self):
        laser_cut_part_dict: dict[str, LaserCutPart] = {}
        for nest in [self.custom_nest] + self.nests:
            if not nest.laser_cut_parts:
                continue
            for laser_cut_part in nest.laser_cut_parts:
                if laser_cut_part.name in laser_cut_part_dict:
                    laser_cut_part_dict[
                        laser_cut_part.name
                    ].quantity += laser_cut_part.quantity
                else:
                    new_laser_cut_part = LaserCutPart(
                        laser_cut_part.to_dict(),
                        self.laser_cut_inventory,
                    )
                    # This is because we group the data, so all nest reference is lost.
                    new_laser_cut_part.quantity_on_sheet = None
                    laser_cut_part_dict[laser_cut_part.name] = new_laser_cut_part

        self.grouped_laser_cut_parts = laser_cut_part_dict.values()
        self.sort_laser_cut_parts()

    def add_laser_cut_part_to_custom_nest(self, laser_cut_part: LaserCutPart):
        laser_cut_part.nest = self.custom_nest
        self.custom_nest.add_laser_cut_part(laser_cut_part)

    def remove_laser_cut_part_to_custom_nest(self, laser_cut_part: LaserCutPart):
        self.custom_nest.remove_laser_cut_part(laser_cut_part)

    def add_nest(self, nest: Nest):
        self.nests.append(nest)

    def remove_nest(self, nest: Nest):
        self.nests.remove(nest)

    def sort_nests(self):
        self.nests = natsorted(self.nests, key=lambda nest: nest.name)

    def sort_laser_cut_parts(self):
        self.grouped_laser_cut_parts = natsorted(
            self.grouped_laser_cut_parts, key=lambda laser_cut_part: laser_cut_part.name
        )

    def load_settings(self, data: dict[str, dict[str, str | bool | float]]):
        # * Nest, Sheet, Item Quoting Settings
        self.laser_cutting_method = data["settings"].get("laser_cutting_method", "CO2")
        self.laser_cutting_cost = data["settings"].get("laser_cutting_cost", 150.0)
        self.item_overhead = data["settings"].get("item_overhead", 18.0)
        self.item_profit_margin = data["settings"].get("item_profit_margin", 30.0)
        self.match_item_to_sheet_cost = data["settings"].get(
            "match_item_to_sheet_cost", False
        )
        self.sheet_overhead = data["settings"].get("sheet_overhead", 18.0)
        self.sheet_profit_margin = data["settings"].get("sheet_profit_margin", 30.0)
        self.match_sheet_cost_to_item = data["settings"].get(
            "match_sheet_cost_to_item", False
        )
        self.component_use_overhead = data["settings"].get(
            "component_use_overhead", False
        )
        self.component_use_profit_margin = data["settings"].get(
            "component_use_profit_margin", False
        )

        # * Paint Settings
        self.primer_overspray = data["settings"].get("primer_overspray", 66.67)
        self.paint_overspray = data["settings"].get("paint_overspray", 66.67)
        self.transfer_efficiency = data["settings"].get("transfer_efficiency", 66.67)
        self.mil_thickness = data["settings"].get("mil_thickness", 2.0)

        # * Quote Settings
        self.order_number = data["settings"].get("order_number", 0.0)
        self.status = data["settings"].get("status", "In progress")
        self.date_shipped = data["settings"].get("date_shipped", "")
        self.date_expected = data["settings"].get("date_expected", "")
        self.ship_to = data["settings"].get("ship_to", "")

    def load_data(self, data: dict[str, dict[str, str | bool | float]]):
        self.load_settings(data)
        self.components.clear()
        for component_data in data["components"]:
            try:
                component = Component(component_data, self.component_inventory)
            except AttributeError:  # Old inventory format
                component = Component(
                    data["components"][component_data], self.component_inventory
                )
                component.name = component_data
            self.components.append(component)

        self.nests.clear()

        custom_nest_data = data.get("custom_nest", {})
        self.custom_nest = Nest(
            custom_nest_data, self.sheet_settings, self.laser_cut_inventory
        )
        self.custom_nest.name = "Custom"
        self.custom_nest.is_custom = True

        for nest_data in data["nests"]:
            try:
                nest = Nest(nest_data, self.sheet_settings, self.laser_cut_inventory)
            except AttributeError:  # Old inventory format
                nest = Nest(
                    data["nests"][nest_data],
                    self.sheet_settings,
                    self.laser_cut_inventory,
                )
            self.nests.append(nest)

        self.group_laser_cut_parts()

    def to_dict(self) -> dict[str, dict[str, dict]]:
        self.unsaved_changes = False
        return {
            "settings": {
                "laser_cutting_method": self.laser_cutting_method,
                "laser_cutting_cost": self.laser_cutting_cost,
                "item_overhead": self.item_overhead,
                "item_profit_margin": self.item_profit_margin,
                "match_item_to_sheet_cost": self.match_item_to_sheet_cost,
                "sheet_overhead": self.sheet_overhead,
                "sheet_profit_margin": self.sheet_profit_margin,
                "match_sheet_cost_to_item": self.match_sheet_cost_to_item,
                "component_use_overhead": self.component_use_overhead,
                "component_use_profit_margin": self.component_use_profit_margin,
                "primer_overspray": self.primer_overspray,
                "paint_overspray": self.paint_overspray,
                "transfer_efficiency": self.transfer_efficiency,
                "mil_thickness": self.mil_thickness,
                "order_number": self.order_number,
                "status": self.status,
                "date_shipped": self.date_shipped,
                "ship_to": self.ship_to,
                "date_expected": self.date_expected,
            },
            "components": [component.to_dict() for component in self.components],
            "nests": [nest.to_dict() for nest in self.nests],
            "custom_nest": self.custom_nest.to_dict(),
        }
