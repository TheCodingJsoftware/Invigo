import os
from typing import Union

import msgspec

from utils.structural_steel_settings.collection import Collection
from utils.structural_steel_settings.material import Material
from utils.structural_steel_settings.material_densities import MaterialDensities
from utils.structural_steel_settings.material_price_per_pounds import MaterialPricePerPounds


class StructuralSteelSettings:
    def __init__(self):
        self.filename: str = "structural_steel_settings"

        self.materials = Collection[Material]()
        self.material_densities: MaterialDensities = MaterialDensities()
        self.material_price_per_pounds: MaterialPricePerPounds = MaterialPricePerPounds()

        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.load_data()

    def get_materials(self) -> list[str]:
        return [material.name for material in self.materials]

    def get_material(self, material_name: str) -> Union[Material, None]:
        if material := self.materials.get(material_name):
            return material
        return None

    def add_material(self, material_name: str):
        new_material = Material(material_name)
        self.material_price_per_pounds.add_price_per_pound(new_material)
        self.material_densities.add_density(new_material)
        self.materials.add_item(new_material)

    def remove_material(self, material_name: str):
        material_to_remove = self.materials.get(material_name)
        self.material_price_per_pounds.remove_price_per_pound(material_to_remove)
        self.material_densities.remove_density(material_to_remove)
        self.materials.remove_item(material_to_remove)

    def get_price_per_pound(self, material_name: str) -> float:
        if material := self.materials.get(material_name):
            return self.material_price_per_pounds.get_price_per_pound(material)
        return 0.0

    def get_density(self, material_name: str) -> float:
        if material := self.materials.get(material_name):
            return self.material_densities.get_density(material)
        return 0.0

    def set_price_per_pound(self, material_name: str, new_price: float):
        if material := self.materials.get(material_name):
            self.material_price_per_pounds.set_price_per_pound(material, new_price)

    def set_price_per_pound_modified_date(self, material_name: str, modified_date: str):
        if material := self.materials.get(material_name):
            self.material_price_per_pounds.set_modified_date(material, modified_date)

    def save_data(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def __create_file(self):
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.filename}.json"):
            self._reset_file()

    def _reset_file(self):
        with open(
            f"{self.FOLDER_LOCATION}/{self.filename}.json", "w", encoding="utf-8"
        ) as file:
            file.write("{}")

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: dict[str, Union[list[str], dict[str, dict]]] = msgspec.json.decode(file.read())
            self.materials.clear()
            for material in data.get("materials", []):
                self.materials.add_item(Material(material))

            self.material_densities.clear()
            self.material_price_per_pounds.clear()

            for material, (_, material_data) in zip(self.materials, data.get("material_price_per_pounds", {}).items()):
                material_price_per_pound_object = self.material_price_per_pounds.add_price_per_pound(material)
                material_price_per_pound_object.price_per_pound = material_data["price_per_pound"]
                material_price_per_pound_object.latest_change = material_data["latest_change"]

            for material, (_, material_data) in zip(self.materials, data.get("material_densities", {}).items()):
                material_density_object = self.material_densities.add_density(material)
                material_density_object.density = material_data["density"]
                material_density_object.latest_change = material_data["latest_change"]
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self.load_data()
        except FileNotFoundError:
            self.__create_file()
            self.load_data()

    def to_dict(self):
        return {
            "materials": self.materials.to_dict(),
            "material_densities": self.material_densities.to_dict(),
            "material_price_per_pounds": self.material_price_per_pounds.to_dict(),
        }
