import os

import msgspec

from utils.sheet_settings.collection import Collection
from utils.sheet_settings.material import Material
from utils.sheet_settings.pounds_per_square_foot import PoundsPerSquareFoot
from utils.sheet_settings.price_per_pound import PricePerPound
from utils.sheet_settings.thickness import Thickness


class SheetSettings:
    def __init__(self):
        self.filename: str = "sheet_settings"
        self.materials = Collection[Material]()
        self.thicknesses = Collection[Thickness]()
        self.material_id: dict[str, dict[str, str]] = {}

        self.pounds_per_square_foot: PoundsPerSquareFoot = PoundsPerSquareFoot()
        self.price_per_pound: PricePerPound = PricePerPound()
        self.cost_for_laser: dict[str, float] = {}
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.load_data()

    def get_materials(self) -> list[str]:
        return [material.name for material in self.materials]

    def get_thicknesses(self) -> list[str]:
        return [thickness.name for thickness in self.thicknesses]

    def add_material(self, material_name: str):
        new_material = Material(material_name)
        self.price_per_pound.add_price_per_pound(new_material)
        self.materials.add_item(new_material)
        for thickness in self.thicknesses:
            self.pounds_per_square_foot.add_square_foot_object(new_material, thickness)

    def remove_material(self, material_name: str):
        material_to_remove = self.materials.get(material_name)
        self.price_per_pound.remove_price_per_pound(material_to_remove)
        self.pounds_per_square_foot.remove_material(material_to_remove)
        self.materials.remove_item(material_to_remove)

    def add_thickness(self, thickness_name: str):
        new_thickness = Thickness(thickness_name)
        self.thicknesses.add_item(new_thickness)
        for material in self.materials:
            self.pounds_per_square_foot.add_square_foot_object(material, new_thickness)

    def remove_thickness(self, thickness_name: str):
        thickness_to_remove = self.thicknesses.get(thickness_name)
        self.thicknesses.remove_item(thickness_to_remove)
        for material in self.materials:
            self.pounds_per_square_foot.remove_square_foot_object(
                material, thickness_to_remove
            )

    def set_price_per_pound(self, material_name: str, new_price: float):
        if material := self.materials.get(material_name):
            self.price_per_pound.set_price_per_pound(material, new_price)

    def set_price_per_pound_modified_date(self, material_name: str, modified_date: str):
        if material := self.materials.get(material_name):
            self.price_per_pound.set_modified_date(material, modified_date)

    def get_price_per_pound(self, material_name: str) -> float:
        if material := self.materials.get(material_name):
            if price_per_pound := self.price_per_pound.get_price_per_pound(material):
                return price_per_pound
        return 0.0

    def get_cost_for_laser(self, material: str) -> float:
        return (
            self.cost_for_laser["Nitrogen"]
            if material in {"304 SS", "409 SS", "Aluminium"}
            else self.cost_for_laser["CO2"]
        )

    def get_laser_cost(self, cutting_method: str) -> float:
        return self.cost_for_laser[cutting_method]

    def get_pounds_per_square_foot(
        self, material_name: str, thickness_name: str
    ) -> float:
        if material := self.materials.get(material_name):
            if thickness := self.thicknesses.get(thickness_name):
                if (
                    pounds_per_square_foot
                    := self.pounds_per_square_foot.get_pounds_per_square_foot(
                        material, thickness
                    )
                ):
                    return pounds_per_square_foot
        return 0.0

    def save_data(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
            data = msgspec.json.decode(file.read())

        self.cost_for_laser.clear()
        for cutting_method in data["cost_for_laser"]:
            self.cost_for_laser.update(
                {cutting_method: data["cost_for_laser"][cutting_method]}
            )

        self.materials.clear()
        for material in data["materials"]:
            self.materials.add_item(Material(material))

        self.thicknesses.clear()
        for thickness in data["thicknesses"]:
            self.thicknesses.add_item(Thickness(thickness))

        self.pounds_per_square_foot.clear()
        for material in self.materials:
            for thickness in self.thicknesses:
                square_foot_object = self.pounds_per_square_foot.add_square_foot_object(
                    material, thickness
                )
                square_foot_object.pounds_per_square_foot = data[
                    "pounds_per_square_foot"
                ][material.name][thickness.name]["pounds_per_square_foot"]
                square_foot_object.latest_change = data["pounds_per_square_foot"][
                    material.name
                ][thickness.name]["latest_change"]

        self.price_per_pound.clear()
        for material in self.materials:
            price_per_pound_object = self.price_per_pound.add_price_per_pound(material)
            price_per_pound_object.price_per_pound = data["price_per_pound"][
                material.name
            ]["price_per_pound"]
            price_per_pound_object.latest_change = data["price_per_pound"][
                material.name
            ]["latest_change"]

        self.material_id.clear()
        self.material_id.update({"cutting_methods": {}, "thickness_ids": {}})
        for material_id, cutting_methods in data["cutting_methods"].items():
            self.material_id["cutting_methods"].update(
                {
                    material_id: {
                        "name": cutting_methods["name"],
                        "cut": cutting_methods["cut"],
                    }
                }
            )
        for thickness_id, thickness in data["thickness_ids"].items():
            self.material_id["thickness_ids"].update({thickness_id: thickness})

    def to_dict(self):
        return {
            "cost_for_laser": self.cost_for_laser,
            "materials": self.materials.to_dict(),
            "thicknesses": self.thicknesses.to_dict(),
            "pounds_per_square_foot": self.pounds_per_square_foot.to_dict(),
            "price_per_pound": self.price_per_pound.to_dict(),
            "cutting_methods": {
                "SS": {
                    "name": self.material_id["cutting_methods"]["SS"]["name"],
                    "cut": self.material_id["cutting_methods"]["SS"]["cut"],
                },
                "ST": {
                    "name": self.material_id["cutting_methods"]["ST"]["name"],
                    "cut": self.material_id["cutting_methods"]["ST"]["cut"],
                },
                "AL": {
                    "name": self.material_id["cutting_methods"]["AL"]["name"],
                    "cut": self.material_id["cutting_methods"]["AL"]["cut"],
                },
                "GALV": {
                    "name": self.material_id["cutting_methods"]["GALV"]["name"],
                    "cut": self.material_id["cutting_methods"]["GALV"]["cut"],
                },
                "GALN": {
                    "name": self.material_id["cutting_methods"]["GALN"]["name"],
                    "cut": self.material_id["cutting_methods"]["GALN"]["cut"],
                },
            },
            "thickness_ids": dict(self.material_id["thickness_ids"].items()),
        }
