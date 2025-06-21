import os
from datetime import datetime
from typing import Callable, Union

import msgspec
from natsort import natsorted
from PyQt6.QtCore import QThreadPool

from utils.inventory.category import Category
from utils.inventory.inventory import Inventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.paint_inventory import PaintInventory
from utils.workers.laser_cut_parts_inventory.add_laser_cut_part import (
    AddLaserCutPartWorker,
)
from utils.workers.laser_cut_parts_inventory.get_all_laser_cut_parts import (
    GetAllLaserCutPartsWorker,
)
from utils.workers.laser_cut_parts_inventory.get_categories import (
    GetLaserCutPartsCategoriesWorker,
)
from utils.workers.laser_cut_parts_inventory.get_laser_cut_part import (
    GetLaserCutPartWorker,
)
from utils.workers.laser_cut_parts_inventory.remove_laser_cut_parts import (
    RemoveLaserCutPartsWorker,
)
from utils.workers.laser_cut_parts_inventory.update_laser_cut_parts import (
    UpdateLaserCutPartsWorker,
)
from utils.workers.runnable_chain import RunnableChain
from utils.workspace.workspace_settings import WorkspaceSettings


class LaserCutInventory(Inventory):
    def __init__(
        self, paint_inventory: PaintInventory, workspace_settings: WorkspaceSettings
    ):
        super().__init__("laser_cut_inventory")
        self.paint_inventory = paint_inventory
        self.workspace_settings = workspace_settings

        self.laser_cut_parts: list[LaserCutPart] = []
        self.recut_parts: list[LaserCutPart] = []

    def get_all_part_names(self) -> list[str]:
        return [laser_cut_part.name for laser_cut_part in self.laser_cut_parts]

    def get_laser_cut_parts_by_category(
        self, category: str | Category
    ) -> list[LaserCutPart]:
        if isinstance(category, str):
            category = self.get_category(category)
        if category.name == "Recut":
            return self.recut_parts
        else:
            return [
                laser_cut_part
                for laser_cut_part in self.laser_cut_parts
                if category in laser_cut_part.categories
            ]

    def get_group_categories(
        self, laser_cut_parts: list[LaserCutPart]
    ) -> dict[str, list[LaserCutPart]]:
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

    def add_or_update_laser_cut_part(
        self, laser_cut_part_to_add: LaserCutPart, from_where: str
    ):
        if laser_cut_part_to_add.recut:
            new_recut_part = LaserCutPart(
                laser_cut_part_to_add.to_dict(),
                self,
            )
            new_recut_part.add_to_category(self.get_category("Recut"))
            if existing_recut_part := self.get_recut_part_by_name(
                laser_cut_part_to_add.name
            ):
                existing_recut_part.recut_count += 1
                new_recut_part.recut_count = existing_recut_part.recut_count
                new_recut_part.name = f"{new_recut_part.name} - (Recut count: {new_recut_part.recut_count})"
            new_recut_part.modified_date = f"{os.getlogin().title()} - Part added from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.add_recut_part(new_recut_part)
        elif existing_laser_cut_part := self.get_laser_cut_part_by_name(
            laser_cut_part_to_add.name
        ):
            existing_laser_cut_part.quantity += laser_cut_part_to_add.quantity

            existing_laser_cut_part.flowtag = laser_cut_part_to_add.flowtag

            existing_laser_cut_part.shelf_number = laser_cut_part_to_add.shelf_number

            existing_laser_cut_part.material = laser_cut_part_to_add.material
            existing_laser_cut_part.gauge = laser_cut_part_to_add.gauge

            existing_laser_cut_part.uses_primer = laser_cut_part_to_add.uses_primer
            existing_laser_cut_part.primer_name = laser_cut_part_to_add.primer_name
            existing_laser_cut_part.uses_paint = laser_cut_part_to_add.uses_paint
            existing_laser_cut_part.paint_name = laser_cut_part_to_add.paint_name
            existing_laser_cut_part.uses_powder = laser_cut_part_to_add.uses_powder
            existing_laser_cut_part.powder_name = laser_cut_part_to_add.powder_name
            existing_laser_cut_part.primer_overspray = (
                laser_cut_part_to_add.primer_overspray
            )
            existing_laser_cut_part.paint_overspray = (
                laser_cut_part_to_add.paint_overspray
            )
            existing_laser_cut_part.powder_transfer_efficiency = (
                laser_cut_part_to_add.powder_transfer_efficiency
            )
            existing_laser_cut_part.modified_date = f"{os.getlogin().title()} - Added {laser_cut_part_to_add.quantity} quantities from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.save_laser_cut_part(existing_laser_cut_part)
        else:
            if not (category := self.get_category("Uncategorized")):
                category = Category("Uncategorized")
                self.add_category(category)
            laser_cut_part_to_add.add_to_category(category)
            laser_cut_part_to_add.modified_date = f"{os.getlogin().title()} - Part added from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.add_laser_cut_part(laser_cut_part_to_add)

    def remove_laser_cut_part_quantity(
        self, laser_cut_part_to_update: LaserCutPart, from_where: str
    ):
        if existing_laser_cut_part := self.get_laser_cut_part_by_name(
            laser_cut_part_to_update.name
        ):
            existing_laser_cut_part.quantity -= laser_cut_part_to_update.quantity
            existing_laser_cut_part.modified_date = f"{os.getlogin().title()} - Removed {laser_cut_part_to_update.quantity} quantities from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        else:
            if not (category := self.get_category("Uncategorized")):
                category = Category("Uncategorized")
                self.add_category(category)
            laser_cut_part_to_update.add_to_category(category)
            laser_cut_part_to_update.quantity = 0
            laser_cut_part_to_update.modified_date = f"{os.getlogin().title()} - Part added from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.add_laser_cut_part(laser_cut_part_to_update)

    # ! TODO IMPLEMENT THIS
    def add_recut_part(self, laser_cut_part: LaserCutPart):
        raise NotImplementedError

    # ! TODO IMPLEMENT THIS
    def remove_recut_part(self, laser_cut_part: LaserCutPart):
        raise NotImplementedError

    def add_laser_cut_part(
        self, laser_cut_part: LaserCutPart, on_finished: Callable | None = None
    ):
        worker = AddLaserCutPartWorker(laser_cut_part)
        worker.signals.success.connect(self.add_laser_cut_part_response)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_laser_cut_part_response(self, response: tuple[dict, LaserCutPart]):
        data, laser_cut_part = response
        laser_cut_part.id = data["id"]
        self.laser_cut_parts.append(laser_cut_part)

    def remove_laser_cut_parts(
        self, laser_cut_parts: list[LaserCutPart], on_finished: Callable | None = None
    ):
        worker = RemoveLaserCutPartsWorker(laser_cut_parts)
        worker.signals.success.connect(self.remove_laser_cut_parts_response)
        QThreadPool.globalInstance().start(worker)

    def remove_laser_cut_part(
        self, laser_cut_part: LaserCutPart, on_finished: Callable | None = None
    ):
        self.remove_laser_cut_parts([laser_cut_part], on_finished)

    def remove_laser_cut_parts_response(
        self, response: tuple[list, list[LaserCutPart]]
    ):
        data, laser_cut_parts = response
        for laser_cut_part in laser_cut_parts:
            self.laser_cut_parts.remove(laser_cut_part)
        # self.save_local_copy()

    def save_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.save_laser_cut_parts([laser_cut_part])

    def save_laser_cut_parts(self, laser_cut_parts: list[LaserCutPart]):
        worker = UpdateLaserCutPartsWorker(laser_cut_parts)
        worker.signals.success.connect(self.save_local_copy)
        QThreadPool.globalInstance().start(worker)

    def get_laser_cut_part(
        self, laser_cut_part_id: int | str, on_finished: Callable | None = None
    ):
        worker = GetLaserCutPartWorker(laser_cut_part_id)
        worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def update_laser_cut_part_data(
        self,
        laser_cut_part_id: int,
        data: dict,
    ) -> LaserCutPart | None:
        for laser_cut_part in self.laser_cut_parts:
            if laser_cut_part.id == laser_cut_part_id:
                laser_cut_part.load_data(data)
                return laser_cut_part
        return None

    # def add_recut_part(self, laser_cut_part: LaserCutPart):
    #     self.recut_parts.append(laser_cut_part)

    # def remove_recut_part(self, laser_cut_part: LaserCutPart):
    #     self.recut_parts.remove(laser_cut_part)

    def duplicate_category(
        self, category_to_duplicate: Category, new_category_name: str
    ) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for laser_cut_part in self.get_laser_cut_parts_by_category(
            category_to_duplicate
        ):
            laser_cut_part.add_to_category(new_category)
        self.save_laser_cut_parts(self.get_laser_cut_parts_by_category(new_category))
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for laser_cut_part in self.get_laser_cut_parts_by_category(deleted_category):
            laser_cut_part.remove_from_category(deleted_category)
        self.save_laser_cut_parts(
            self.get_laser_cut_parts_by_category(deleted_category)
        )
        return deleted_category

    def rename_category(self, original: str | Category, new_name: str) -> Category:
        if isinstance(original, str):
            original = self.get_category(original)

        original_laser_cut_parts = self.get_laser_cut_parts_by_category(original)

        for laser_cut_part in original_laser_cut_parts:
            laser_cut_part.remove_from_category(original)

        original.rename(new_name)

        for laser_cut_part in self.get_laser_cut_parts_by_category(original):
            laser_cut_part.add_to_category(original)

        self.save_laser_cut_parts(self.get_laser_cut_parts_by_category(original))
        return original

    def get_laser_cut_part_by_name(self, laser_cut_part_name: str) -> LaserCutPart:
        return next(
            (
                laser_cut_part
                for laser_cut_part in self.laser_cut_parts
                if laser_cut_part.name == laser_cut_part_name
            ),
            None,
        )

    def get_recut_part_by_name(self, recut_part_name: str) -> LaserCutPart:
        return next(
            (
                recut_part
                for recut_part in self.recut_parts
                if recut_part.name == recut_part_name
            ),
            None,
        )

    def sort_by_quantity(self) -> list[LaserCutPart]:
        self.laser_cut_parts = natsorted(
            self.laser_cut_parts, key=lambda laser_cut_part: laser_cut_part.quantity
        )
        self.recut_parts = natsorted(
            self.recut_parts, key=lambda recut_part: recut_part.quantity
        )

    def save_local_copy(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self, on_loaded: Callable | None = None):
        self.chain = RunnableChain()

        get_categories_worker = GetLaserCutPartsCategoriesWorker()
        get_all_laser_cut_parts_worker = GetAllLaserCutPartsWorker()

        self.chain.add(get_categories_worker, self.get_categories_response)
        self.chain.add(
            get_all_laser_cut_parts_worker, self.get_all_laser_cut_parts_response
        )

        if on_loaded:
            self.chain.finished.connect(on_loaded)

        self.chain.start()

    def get_categories_response(self, response: list, next_step: Callable):
        try:
            self.categories.from_list(response)
        except Exception:
            self.categories.clear()
        next_step()

    def get_all_laser_cut_parts_response(self, response: dict, next_step: Callable):
        self.laser_cut_parts.clear()
        for component_data in response:
            component = LaserCutPart(component_data, self)
            self.laser_cut_parts.append(component)
        self.save_local_copy()
        next_step()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "laser_cut_parts": [
                laser_cut_part.to_dict() for laser_cut_part in self.laser_cut_parts
            ],
            "recut_parts": [recut_part.to_dict() for recut_part in self.recut_parts],
        }
