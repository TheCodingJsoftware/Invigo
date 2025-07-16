from typing import Dict, Iterator, Tuple, Union

from utils.sheet_settings.material import Material


class Price:
    def __init__(self, price_per_pound: float = 0.0, latest_change: str = ""):
        self.price_per_pound: float = price_per_pound
        self.latest_change: str = latest_change

    def to_dict(self) -> Dict[str, Union[float, str]]:
        return {
            "price_per_pound": self.price_per_pound,
            "latest_change": self.latest_change,
        }


class PricePerPound:
    def __init__(self):
        self.data: Dict[Material, Price] = {}

    def add_price_per_pound(self, material: Material) -> Price:
        if material not in self.data:
            self.data[material] = Price(0.0, "")
            return self.data[material]

    def remove_price_per_pound(self, material: Material) -> Price:
        del self.data[material]

    def get_price_per_pound(self, material: Material) -> float:
        return self.data[material].price_per_pound

    def set_price_per_pound(self, material: Material, price_per_pound: float):
        self.data[material].price_per_pound = price_per_pound

    def set_modified_date(self, material: Material, modified_date: str):
        self.data[material].latest_change = modified_date

    def clear(self):
        self.data.clear()

    def to_dict(self):
        return {material.name: price_per_pound_object.to_dict() for material, price_per_pound_object in self}

    def __iter__(self) -> Iterator[Tuple[Material, Price]]:
        return iter(self.data.items())
