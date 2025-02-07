import math
from typing import Union

from utils.inventory.category import Category
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile


class AngleBar(StructuralProfile):
    def __init__(self, data: dict, structural_steel_inventory):
        super().__init__(structural_steel_inventory)
        self.PROFILE_TYPE = ProfilesTypes.ANGLE_BAR
        self.leg_a: float = 0.0
        self.leg_b: float = 0.0
        self.wall_thickness: float = 0.0
        self.load_data(data)

    def get_name(self) -> str:
        return f"{self.material} {self.PROFILE_TYPE.value} {self.leg_a:,.3f} x {self.leg_b:,.3f} x {self.wall_thickness:,.3f}"

    def tooltip(self) -> str:
        return f'Length: {self.length:,.3f} in\nLeg A: {self.leg_a:,.3f} in\nLeg B: {self.leg_b:,.3f} in\nWall Thickness: {self.wall_thickness:,.3f} in'

    def get_volume(self) -> float:
        return (
            (self.leg_a * self.wall_thickness)
            + (self.leg_b * self.wall_thickness)
            - math.pow(self.wall_thickness, 2) * self.length
        )

    def get_weight(self) -> float:
        return self.get_volume() * self.get_density()

    def get_cost(self) -> float:
        return self.get_weight() * self.structural_steel_settings.get_price_per_pound(self.material)

    def load_data(self, data: dict[str, Union[float, str]]):
        super().load_data(data)
        self.leg_a = data.get("leg_a", 0.0)
        self.leg_b = data.get("leg_b", 0.0)
        self.wall_thickness = data.get("wall_thickness", 0.0)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.structural_steel_inventory.remove_angle_bar(self)

    def to_dict(self) -> dict[str, Union[float, str]]:
        return {
            "name": self.get_name(),
            "part_number": self.part_number,
            "leg_a": self.leg_a,
            "leg_b": self.leg_b,
            "length": self.length,
            "wall_thickness": self.wall_thickness,
            "material": self.material,
            "notes": self.notes,
            "cost": self.get_cost(),
            "quantity": self.quantity,
            "latest_change_quantity": self.latest_change_quantity,
            "latest_change_cost": self.latest_change_cost,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
            "has_sent_warning": self.has_sent_warning,
            "orders": [order.to_dict() for order in self.orders],
            "flow_tag": self.flow_tag.to_dict(),
            "categories": [category.name for category in self.categories],
        }
