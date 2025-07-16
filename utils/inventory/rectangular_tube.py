from typing import Union

from utils.inventory.category import Category
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile


class RectangularTube(StructuralProfile):
    def __init__(self, data: dict, structural_steel_inventory):
        super().__init__(structural_steel_inventory)
        self.PROFILE_TYPE = ProfilesTypes.RECTANGULAR_TUBE
        self.outer_width: float = 0.0
        self.outer_height: float = 0.0
        self.wall_thickness: float = 0.0
        self.load_data(data)

    def get_name(self) -> str:
        return f"{self.material} {self.PROFILE_TYPE.value} {self.outer_width:,.3f} x {self.outer_height:,.3f} x {self.wall_thickness:,.3f}"

    def tooltip(self) -> str:
        return f"Length: {self.length:,.3f} in\nOuter Width: {self.outer_width:,.3f} in\nOuter Height: {self.outer_height:,.3f} in\nWall Thickness: {self.wall_thickness:,.3f} in"

    def get_volume(self) -> float:
        return ((self.outer_width * self.outer_height) - ((self.outer_width - (2 * self.wall_thickness)) * (self.outer_height - (2 * self.wall_thickness)))) * self.length

    def get_weight(self) -> float:
        print(self.get_volume())
        print(self.get_density())
        print(self.get_volume() * self.get_density())
        return self.get_volume() * self.get_density()

    def get_cost(self) -> float:
        return self.get_weight() * self.structural_steel_settings.get_price_per_pound(self.material)

    def load_data(self, data: dict[str, Union[float, str]]):
        super().load_data(data)
        self.outer_width = data.get("outer_width", 0.0)
        self.outer_height = data.get("outer_height", 0.0)
        self.wall_thickness = data.get("wall_thickness", 0.0)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.structural_steel_inventory.remove_rectangular_tube(self)

    def to_dict(self) -> dict[str, Union[float, str]]:
        data = super().to_dict()
        data.update(
            {
                "profile_type": self.PROFILE_TYPE.value,
                "outer_width": self.outer_width,
                "outer_height": self.outer_height,
                "wall_thickness": self.wall_thickness,
            }
        )
        return data
