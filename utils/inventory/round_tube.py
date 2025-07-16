import math
from typing import Union

from utils.inventory.category import Category
from utils.inventory.structural_profile import StructuralProfile, ProfilesTypes


class RoundTube(StructuralProfile):
    def __init__(self, data: dict, structural_steel_inventory):
        super().__init__(structural_steel_inventory)
        self.PROFILE_TYPE = ProfilesTypes.ROUND_TUBE
        self.outside_diameter: float = 0.0
        self.inside_diameter: float = 0.0
        self.wall_thickness: float = 0.0
        self.load_data(data)

    def get_name(self) -> str:
        return f"{self.material} {self.PROFILE_TYPE.value} {self.outside_diameter:,.3f} x {self.inside_diameter:,.3f}"

    def tooltip(self) -> str:
        return f"Length: {self.length:,.3f} in\nOutside Diameter: {self.outside_diameter:,.3f} in\nInside Diameter: {self.inside_diameter:,.3f} in\nWall Thickness: {self.wall_thickness:,.3f} in"

    def get_cross_section_area(self) -> float:
        return (math.pi / 4) * (math.pow(self.outside_diameter, 2) - math.pow(self.inside_diameter, 2))

    def get_volume(self) -> float:
        return self.get_cross_section_area() * self.length

    def get_weight(self) -> float:
        return self.get_volume() * self.get_density()

    def get_cost(self) -> float:
        return self.get_weight() * self.structural_steel_settings.get_price_per_pound(self.material)

    def load_data(self, data: dict[str, Union[float, str]]):
        super().load_data(data)
        self.outside_diameter = data.get("outside_diameter", 0.0)
        self.inside_diameter = data.get("inside_diameter", 0.0)
        self.wall_thickness = data.get("wall_thickness", 0.0)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.structural_steel_inventory.remove_round_tube(self)

    def to_dict(self) -> dict[str, Union[float, str]]:
        data = super().to_dict()
        data.update(
            {
                "profile_type": self.PROFILE_TYPE.value,
                "outside_diameter": self.outside_diameter,
                "inside_diameter": self.inside_diameter,
                "wall_thickness": self.wall_thickness,
            }
        )
        return data
