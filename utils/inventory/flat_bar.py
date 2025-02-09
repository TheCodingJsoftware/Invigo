from typing import Union

from utils.inventory.category import Category
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile


class FlatBar(StructuralProfile):
    def __init__(self, data: dict, structural_steel_inventory):
        super().__init__(structural_steel_inventory)
        self.PROFILE_TYPE = ProfilesTypes.FLAT_BAR
        self.width: float = 0.0
        self.wall_thickness: float = 0.0
        self.load_data(data)

    def get_name(self) -> str:
        return f"{self.material} {self.PROFILE_TYPE.value} {self.width:,.3f} x {self.length:,.3f} x {self.wall_thickness:,.3f}"

    def tooltip(self) -> str:
        return f'Length: {self.length:,.3f} in\nWidth: {self.width:,.3f} in\nWall Thickness: {self.wall_thickness:,.3f} in'

    def get_volume(self) -> float:
        return self.width * self.wall_thickness * self.length

    def get_weight(self) -> float:
        return self.get_volume() * self.get_density()

    def get_cost(self) -> float:
        return self.get_weight() * self.structural_steel_settings.get_price_per_pound(self.material)

    def load_data(self, data: dict[str, Union[float, str]]):
        super().load_data(data)
        self.width = data.get("width", 0.0)
        self.wall_thickness = data.get("wall_thickness", 0.0)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.structural_steel_inventory.remove_flat_bar(self)

    def to_dict(self) -> dict[str, Union[float, str]]:
        return {
            "profile_type": self.PROFILE_TYPE.value,
            "name": self.get_name(),
            "part_number": self.part_number,
            "length": self.length,
            "wall_thickness": self.wall_thickness,
            "width": self.width,
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
