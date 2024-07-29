from typing import Union

from utils.inventory.nest import Nest
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.inventory.laser_cut_inventory import LaserCutInventory


class Workorder:
    def __init__(self, data: list[dict[str, object]], sheet_settings: SheetSettings, laser_cut_inventory: LaserCutInventory):
        self.nests: list[Nest] = []
        self.sheet_settings = sheet_settings
        self.laser_cut_inventory = laser_cut_inventory
        self.load_data(data)

    def load_data(self, data: list[dict[str, object]]):
        self.nests.clear()
        for nest_data in data:
            nest = Nest(nest_data, self.sheet_settings, self.laser_cut_inventory)
            self.nests.append(nest)

    def to_dict(self) -> list[dict[str, Union[float, int, str]]]:
        data: list[dict[str, Union[float, int, str]]] = []
        for nest in self.nests:
            data.append(nest.to_dict())
        return data
