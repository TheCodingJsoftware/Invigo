import math
from typing import Union

from utils.inventory.category import Category
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile


class RoundBar(StructuralProfile):
    def __init__(self, data: dict, structural_steel_inventory):
        super().__init__(structural_steel_inventory)
        self.PROFILE_TYPE = ProfilesTypes.ROUND_BAR
        self.outside_diameter: float = 0.0
        self.load_data(data)

    def get_name(self) -> str:
        return f"{self.material} {self.PROFILE_TYPE.value} {self.outside_diameter:,.3f}"

    def tooltip(self) -> str:
        return f'Length: {self.length:,.3f}\nOutside diameter: {self.outside_diameter:,.3f}'

    def get_volume(self) -> float:
        return (math.pi * math.pow(self.outside_diameter, 2) / 4) * self.length

    def get_weight(self) -> float:
        return self.get_volume() * self.get_density()

    def get_cost(self) -> float:
        return self.get_weight() * self.structural_steel_settings.get_price_per_pound(self.material)

    def load_data(self, data: dict[str, Union[float, str]]):
        super().load_data(data)
        self.outside_diameter = data.get("outside_diameter", 0.0)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.structural_steel_inventory.remove_round_bar(self)

    def to_dict(self) -> dict[str, Union[float, str]]:
        data = super().to_dict()
        data.update(
            {
                "profile_type": self.PROFILE_TYPE.value,
                "outside_diameter": self.outside_diameter,
            }
        )
        return data
