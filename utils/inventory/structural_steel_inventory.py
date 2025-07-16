from typing import Union

import msgspec

from utils.inventory.angle_bar import AngleBar
from utils.inventory.category import Category
from utils.inventory.dom_round_tube import DOMRoundTube
from utils.inventory.flat_bar import FlatBar
from utils.inventory.inventory import Inventory
from utils.inventory.pipe import Pipe
from utils.inventory.rectangular_bar import RectangularBar
from utils.inventory.rectangular_tube import RectangularTube
from utils.inventory.round_bar import RoundBar
from utils.inventory.round_tube import RoundTube
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile
from utils.structural_steel_settings.structural_steel_settings import (
    StructuralSteelSettings,
)
from utils.workspace.workspace_settings import WorkspaceSettings


class StructuralSteelInventory(Inventory):
    def __init__(
        self,
        structural_steel_settings: StructuralSteelSettings,
        workspace_settings: WorkspaceSettings,
    ):
        super().__init__("structural_steel_inventory")
        self.structural_steel_settings = structural_steel_settings
        self.workspace_settings = workspace_settings

        self.angle_bars: list[AngleBar] = []
        self.flat_bars: list[FlatBar] = []
        self.rectangular_bars: list[RectangularBar] = []
        self.rectangular_tubes: list[RectangularTube] = []
        self.round_bars: list[RoundBar] = []
        self.round_tubes: list[RoundTube] = []
        self.DOM_round_tubes: list[DOMRoundTube] = []
        self.pipes: list[Pipe] = []
        self.load_data()

    def duplicate_category(self, category_to_duplicate: Category, new_category_name: str) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for sheet in self.get_items_by_category(category_to_duplicate):
            sheet.add_to_category(new_category)
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for item in self.get_items_by_category(deleted_category):
            item.remove_from_category(deleted_category)
        return deleted_category

    def get_items_by_profile_type(
        self,
        items: list[RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar],
    ) -> list[ProfilesTypes]:
        profile_types: set[ProfilesTypes] = set()
        for item in items:
            profile_types.add(item.PROFILE_TYPE)
        return list(profile_types)

    def get_items_by_category(self, category: str | Category) -> list[RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar]:
        if isinstance(category, str):
            category = self.get_category(category)
        return [item for item in self.get_all_items() if category in item.categories]

    def sort_by_quantity(self):
        self.angle_bars.sort(key=lambda item: item.quantity, reverse=True)
        self.flat_bars.sort(key=lambda item: item.quantity, reverse=True)
        self.rectangular_bars.sort(key=lambda item: item.quantity, reverse=True)
        self.rectangular_tubes.sort(key=lambda item: item.quantity, reverse=True)
        self.round_bars.sort(key=lambda item: item.quantity, reverse=True)
        self.round_tubes.sort(key=lambda item: item.quantity, reverse=True)
        self.DOM_round_tubes.sort(key=lambda item: item.quantity, reverse=True)
        self.pipes.sort(key=lambda item: item.quantity, reverse=True)

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def add_angle_bar(self, item_data: dict[str, Union[str, int, float, bool]] | AngleBar) -> AngleBar:
        if isinstance(item_data, AngleBar):
            item = item_data
        else:
            item = AngleBar(item_data, self)
        self.angle_bars.append(item)
        return item

    def remove_angle_bar(self, item: AngleBar):
        self.angle_bars.remove(item)

    def add_flat_bar(self, item_data: dict[str, Union[str, int, float, bool]] | FlatBar) -> FlatBar:
        if isinstance(item_data, FlatBar):
            item = item_data
        else:
            item = FlatBar(item_data, self)
        self.flat_bars.append(item)
        return item

    def remove_flat_bar(self, item: FlatBar):
        self.flat_bars.remove(item)

    def add_rectangular_bar(self, item_data: dict[str, Union[str, int, float, bool]] | RectangularBar) -> RectangularBar:
        if isinstance(item_data, RectangularBar):
            item = item_data
        else:
            item = RectangularBar(item_data, self)
        self.rectangular_bars.append(item)
        return item

    def remove_rectangular_bar(self, item: RectangularBar):
        self.rectangular_bars.remove(item)

    def add_rectangular_tube(self, item_data: dict[str, Union[str, int, float, bool]] | RectangularTube) -> RectangularTube:
        if isinstance(item_data, RectangularTube):
            item = item_data
        else:
            item = RectangularTube(item_data, self)
        self.rectangular_tubes.append(item)
        return item

    def remove_rectangular_tube(self, item: RectangularTube):
        self.rectangular_tubes.remove(item)

    def add_round_bar(self, item_data: dict[str, Union[str, int, float, bool]] | RoundBar) -> RoundBar:
        if isinstance(item_data, RoundBar):
            item = item_data
        else:
            item = RoundBar(item_data, self)
        self.round_bars.append(item)
        return item

    def remove_round_bar(self, item: RoundBar):
        self.round_bars.remove(item)

    def add_round_tube(self, item_data: dict[str, Union[str, int, float, bool]] | RoundTube) -> RoundTube:
        if isinstance(item_data, RoundTube):
            item = item_data
        else:
            item = RoundTube(item_data, self)
        self.round_tubes.append(item)
        return item

    def remove_round_tube(self, item: RoundTube):
        self.round_tubes.remove(item)

    def add_DOM_round_tube(self, item_data: dict[str, Union[str, int, float, bool]] | DOMRoundTube) -> DOMRoundTube:
        if isinstance(item_data, DOMRoundTube):
            item = item_data
        else:
            item = DOMRoundTube(item_data, self)
        self.DOM_round_tubes.append(item)
        return item

    def remove_DOM_round_tube(self, item: DOMRoundTube):
        self.DOM_round_tubes.remove(item)

    def add_pipe(self, item_data: dict[str, Union[str, int, float, bool]] | Pipe) -> Pipe:
        if isinstance(item_data, Pipe):
            item = item_data
        else:
            item = Pipe(item_data, self)
        self.pipes.append(item)
        return item

    def remove_pipe(self, item: Pipe):
        self.pipes.remove(item)

    def remove_item(
        self,
        item: RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar,
    ):
        if isinstance(item, RoundBar):
            self.remove_round_bar(item)
        elif isinstance(item, RectangularBar):
            self.remove_rectangular_bar(item)
        elif isinstance(item, AngleBar):
            self.remove_angle_bar(item)
        elif isinstance(item, RectangularTube):
            self.remove_rectangular_tube(item)
        elif isinstance(item, RoundTube):
            self.remove_round_tube(item)
        elif isinstance(item, DOMRoundTube):
            self.remove_DOM_round_tube(item)
        elif isinstance(item, Pipe):
            self.remove_pipe(item)
        elif isinstance(item, FlatBar):
            self.remove_flat_bar(item)

    def get_all_items(
        self,
    ) -> list[RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar]:
        return self.angle_bars + self.flat_bars + self.rectangular_bars + self.rectangular_tubes + self.round_bars + self.round_tubes + self.DOM_round_tubes + self.pipes

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "r", encoding="utf-8") as file:
                data: dict[str, dict[str, object]] = msgspec.json.decode(file.read())
            self.categories.from_list(data["categories"])
            self.angle_bars.clear()
            self.flat_bars.clear()
            self.rectangular_bars.clear()
            self.rectangular_tubes.clear()
            self.round_bars.clear()
            self.round_tubes.clear()
            self.DOM_round_tubes.clear()
            self.pipes.clear()
            for item_data in data["angle_bars"]:
                self.add_angle_bar(item_data)
            for item_data in data["flat_bars"]:
                self.add_flat_bar(item_data)
            for item_data in data["rectangular_bars"]:
                self.add_rectangular_bar(item_data)
            for item_data in data["rectangular_tubes"]:
                self.add_rectangular_tube(item_data)
            for item_data in data["round_bars"]:
                self.add_round_bar(item_data)
            for item_data in data["round_tubes"]:
                self.add_round_tube(item_data)
            for item_data in data["DOM_round_tubes"]:
                self.add_DOM_round_tube(item_data)
            for item_data in data["pipes"]:
                self.add_pipe(item_data)
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self._reset_file()
            self.load_data()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "angle_bars": [item.to_dict() for item in self.angle_bars],
            "flat_bars": [item.to_dict() for item in self.flat_bars],
            "rectangular_bars": [item.to_dict() for item in self.rectangular_bars],
            "rectangular_tubes": [item.to_dict() for item in self.rectangular_tubes],
            "round_bars": [item.to_dict() for item in self.round_bars],
            "round_tubes": [item.to_dict() for item in self.round_tubes],
            "DOM_round_tubes": [item.to_dict() for item in self.DOM_round_tubes],
            "pipes": [item.to_dict() for item in self.pipes],
        }
