import msgspec
from natsort import natsorted
from typing import Union

from utils.inventory.category import Category
from utils.inventory.inventory import Inventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.paint_inventory import PaintInventory
from utils.workspace.workspace_settings import WorkspaceSettings


class LaserCutInventory(Inventory):
    def __init__(self, paint_inventory: PaintInventory, workspace_settings: WorkspaceSettings):
        super().__init__("laser_cut_inventory")
        self.paint_inventory = paint_inventory
        self.workspace_settings = workspace_settings

        self.laser_cut_parts: list[LaserCutPart] = []
        self.recut_parts: list[LaserCutPart] = []
        self.load_data()

    def get_all_part_names(self) -> list[str]:
        return [laser_cut_part.name for laser_cut_part in self.laser_cut_parts]

    def get_laser_cut_parts_by_category(self, category: str | Category) -> list[LaserCutPart]:
        if isinstance(category, str):
            category = self.get_category(category)
        if category.name == "Recut":
            return self.recut_parts
        else:
            return [laser_cut_part for laser_cut_part in self.laser_cut_parts if category in laser_cut_part.categories]

    def get_group_categories(self, laser_cut_parts: list[LaserCutPart]) -> dict[str, list[LaserCutPart]]:
        group: dict[str, list[LaserCutPart]] = {}
        for laser_cut_part in laser_cut_parts:
            group_name = f"{laser_cut_part.material};{laser_cut_part.gauge}"
            group.setdefault(group_name, [])
            group[group_name].append(laser_cut_part)

        return {key: group[key] for key in natsorted(group.keys())}

    def get_category_parts_total_stock_cost(self, category: Category):
        total_stock_cost = 0.0
        for laser_cut_part in self.get_laser_cut_parts_by_category(category):
            total_stock_cost += laser_cut_part.price * laser_cut_part.quantity
        return total_stock_cost

    def get_recut_parts_total_stock_cost(self) -> float:
        total_stock_cost = 0.0
        for recut_part in self.recut_parts:
            total_stock_cost += recut_part.price * recut_part.quantity
        return total_stock_cost

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.append(laser_cut_part)

    def remove_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.remove(laser_cut_part)

    def add_recut_part(self, laser_cut_part: LaserCutPart):
        self.recut_parts.append(laser_cut_part)

    def remove_recut_part(self, laser_cut_part: LaserCutPart):
        self.recut_parts.remove(laser_cut_part)

    def duplicate_category(self, category_to_duplicate: Category, new_category_name: str) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for laser_cut_part in self.get_laser_cut_parts_by_category(category_to_duplicate):
            laser_cut_part.add_to_category(new_category)
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for laser_cut_part in self.get_laser_cut_parts_by_category(deleted_category):
            laser_cut_part.remove_from_category(deleted_category)
        return deleted_category

    def get_laser_cut_part_by_name(self, laser_cut_part_name: str) -> LaserCutPart:
        return next(
            (laser_cut_part for laser_cut_part in self.laser_cut_parts if laser_cut_part.name == laser_cut_part_name),
            None,
        )

    def get_recut_part_by_name(self, recut_part_name: str) -> LaserCutPart:
        return next(
            (recut_part for recut_part in self.recut_parts if recut_part.name == recut_part_name),
            None,
        )

    def sort_by_quantity(self) -> list[LaserCutPart]:
        self.laser_cut_parts = natsorted(self.laser_cut_parts, key=lambda laser_cut_part: laser_cut_part.quantity)
        self.recut_parts = natsorted(self.recut_parts, key=lambda recut_part: recut_part.quantity)

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: dict[str, dict[str, object]] = msgspec.json.decode(file.read())
            self.categories.from_dict(data["categories"])
            self.laser_cut_parts.clear()
            self.recut_parts.clear()
            for laser_cut_part_data in data["laser_cut_parts"]:
                try:
                    laser_cut_part = LaserCutPart(laser_cut_part_data, self)
                except AttributeError: # Old inventory format
                    laser_cut_part = LaserCutPart(data["laser_cut_parts"][laser_cut_part_data], self)
                    laser_cut_part.name = laser_cut_part_data
                self.add_laser_cut_part(laser_cut_part)

            for recut_part_data in data["recut_parts"]:
                try:
                    recut_part = LaserCutPart(recut_part_data, self)
                except AttributeError: # Old inventory format
                    recut_part = LaserCutPart(data["recut_parts"][recut_part_data], self)
                    recut_part.name = recut_part_data
                self.add_recut_part(recut_part)
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self._reset_file()
            self.load_data()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "laser_cut_parts": [laser_cut_part.to_dict() for laser_cut_part in self.laser_cut_parts],
            "recut_parts": [recut_part.to_dict() for recut_part in self.recut_parts],
        }
