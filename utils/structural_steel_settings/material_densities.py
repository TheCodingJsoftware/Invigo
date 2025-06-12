from typing import Dict, Iterator, Tuple, Union

from utils.structural_steel_settings.material import Material


class Density:
    def __init__(self, density: float, latest_change: str):
        self.density: float = density
        self.latest_change: str = latest_change

    def to_dict(self):
        return {
            "density": self.density,
            "latest_change": self.latest_change,
        }


class MaterialDensities:
    def __init__(self):
        self.data: Dict[Material, Density] = {}

    def remove_density(self, material: Material):
        del self.data[material]

    def add_density(self, material: Material) -> Density:
        if material not in self.data:
            self.data[material] = Density(0.0, "")
        return self.data[material]

    def get_density(self, material: Material) -> float:
        return self.data[material].density

    def set_density(
        self, material: Material, density: float
    ):
        if material in self.data in self.data[material]:
            self.data[material].density = density

    def clear(self):
        self.data.clear()

    def to_dict(self) -> Dict[str, Dict[str, Union[str, float]]]:
        data: Dict[str, Dict[str, Union[str, float]]] = {}
        for material, square_foot_object in self:
            data[material.name] = square_foot_object.to_dict()
        return data

    def __iter__(self) -> Iterator[Tuple[Material, Density]]:
        return iter(self.data.items())
