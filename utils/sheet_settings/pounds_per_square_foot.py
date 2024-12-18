from typing import Dict, Iterator, Tuple, Union

from utils.sheet_settings.material import Material
from utils.sheet_settings.thickness import Thickness


class Pound:
    def __init__(self, pounds_per_square_foot: float, latest_change: str):
        self.pounds_per_square_foot: float = pounds_per_square_foot
        self.latest_change: str = latest_change

    def to_dict(self):
        return {
            "pounds_per_square_foot": self.pounds_per_square_foot,
            "latest_change": self.latest_change,
        }


class PoundsPerSquareFoot:
    def __init__(self):
        self.data: Dict[Material, Dict[Thickness, Pound]] = {}

    def add_square_foot_object(self, material: Material, thickness: Thickness) -> Pound:
        if material not in self.data:
            self.data[material] = {}
        if thickness not in self.data[material]:
            self.data[material][thickness] = Pound(0.0, "")
        return self.data[material][thickness]

    def remove_square_foot_object(
        self, material: Material, thickness: Thickness
    ) -> Pound:
        del self.data[material][thickness]

    def get_pounds_per_square_foot(
        self, material: Material, thickness: Thickness
    ) -> float:
        return self.data[material][thickness].pounds_per_square_foot

    def remove_material(self, material: Material):
        del self.data[material]

    def set_pound_per_square_foot(
        self, material: Material, thickness: Thickness, pounds_per_square_foot: float
    ):
        if material in self.data and thickness in self.data[material]:
            self.data[material][
                thickness
            ].pounds_per_square_foot = pounds_per_square_foot

    def set_modified_date(
        self, material: Material, thickness: Thickness, modified_date: str
    ):
        if material in self.data and thickness in self.data[material]:
            self.data[material][thickness].latest_change = modified_date

    def clear(self):
        self.data.clear()

    def to_dict(self) -> Dict[str, Dict[str, Dict[str, Union[str, float]]]]:
        data: Dict[str, Dict[str, Dict[str, Union[str, float]]]] = {}
        for material, thickness_data in self:
            data |= {material.name: {}}
            for thickness, square_foot_object in thickness_data.items():
                data[material.name].update(
                    {thickness.name: square_foot_object.to_dict()}
                )
        return data

    def __iter__(self) -> Iterator[Tuple[Material, Dict[Thickness, Pound]]]:
        return iter(self.data.items())
