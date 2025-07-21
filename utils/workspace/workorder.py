from typing import Callable

from PyQt6.QtCore import QThreadPool

from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest, NestDict
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workers.workorders.save_workorder import SaveWorkorderWorker


class Workorder:
    def __init__(
        self,
        nests: list[Nest],
        sheet_settings: SheetSettings,
        laser_cut_inventory: LaserCutInventory,
    ):
        self.nests = nests
        self.sheet_settings = sheet_settings
        self.laser_cut_inventory = laser_cut_inventory

    def get_all_laser_cut_parts(self) -> list[LaserCutPart]:
        laser_cut_parts: list[LaserCutPart] = []
        for nest in self.nests:
            laser_cut_parts.extend(nest.laser_cut_parts)
        return laser_cut_parts

    def open_workorder(self, on_finished: Callable | None = None):
        save_workorder_worker = SaveWorkorderWorker(self)
        save_workorder_worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(save_workorder_worker)

    def to_dict(self) -> dict[str, list[NestDict]]:
        data: dict[str, list[NestDict]] = {"nests": []}
        for nest in self.nests:
            data["nests"].append(nest.to_dict())
        return data
