import contextlib
from typing import Callable, Optional, Union

import msgspec
from PyQt6.QtCore import QThreadPool

from utils.inventory.coating_item import CoatingItem, CoatingTypes
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.inventory import Inventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.coatings_inventory.get_all_coatings import GetAllCoatingsWorker
from utils.workers.coatings_inventory.update_coatings import UpdateCoatingsWorker
from utils.workers.runnable_chain import RunnableChain


class PaintInventory(Inventory):
    def __init__(self, components_inventory: ComponentsInventory):
        super().__init__("paint_inventory")
        self.components_inventory = components_inventory

        self.primers: list[CoatingItem] = []
        self.paints: list[CoatingItem] = []
        self.powders: list[CoatingItem] = []

    def add_primer(self, primer: CoatingItem):
        self.primers.append(primer)

    def remove_primer(self, primer: CoatingItem):
        with contextlib.suppress(ValueError):  # Already removed
            self.primers.remove(primer)

    def get_primer(self, name: str) -> Optional[CoatingItem]:
        return next((primer for primer in self.primers if primer.part_name == name), None)

    def get_all_primers(self) -> list[str]:
        return [primer.part_name for primer in self.primers]

    def get_primer_cost(self, laser_cut_part: LaserCutPart) -> float:
        with contextlib.suppress(ZeroDivisionError, AttributeError):
            if laser_cut_part.uses_primer:
                if primer := self.get_primer(laser_cut_part.primer_name):
                    if primer.component:
                        primer_cost_per_gallon = primer.component.price
                        gallons_used = (((laser_cut_part.surface_area * 2) / 144) / primer.average_coverage) * ((laser_cut_part.primer_overspray / 100) + 1)
                        return primer_cost_per_gallon * gallons_used
        return 0.0

    def add_paint(self, paint: CoatingItem):
        self.paints.append(paint)

    def remove_paint(self, paint: CoatingItem):
        with contextlib.suppress(ValueError):  # Already removed
            self.paints.remove(paint)

    def get_paint(self, name: str) -> Optional[CoatingItem]:
        return next((paint for paint in self.paints if paint.part_name == name), None)

    def get_all_paints(self) -> list[str]:
        return [paint.part_name for paint in self.paints]

    def get_paint_cost(self, laser_cut_part: LaserCutPart) -> float:
        with contextlib.suppress(ZeroDivisionError, AttributeError):
            if laser_cut_part.uses_paint:
                if paint := self.get_paint(laser_cut_part.paint_name):
                    if paint.component:
                        paint_cost_per_gallon = paint.component.price
                        gallons_used = (((laser_cut_part.surface_area * 2) / 144) / paint.average_coverage) * ((laser_cut_part.paint_overspray / 100) + 1)
                        return paint_cost_per_gallon * gallons_used
        return 0.0

    def add_powder(self, powder: CoatingItem):
        self.powders.append(powder)

    def remove_powder(self, powder: CoatingItem):
        with contextlib.suppress(ValueError):  # Already removed
            self.powders.remove(powder)

    def get_powder(self, name: str) -> Optional[CoatingItem]:
        return next((powder for powder in self.powders if powder.part_name == name), None)

    def get_all_powders(self) -> list[str]:
        return [powder.part_name for powder in self.powders]

    def get_powder_cost(self, laser_cut_part: LaserCutPart, mil_thickness: float) -> float:
        with contextlib.suppress(ZeroDivisionError, AttributeError):
            if laser_cut_part.uses_powder:
                if powder := self.get_powder(laser_cut_part.powder_name):
                    if powder.component:
                        estimated_sq_ft_coverage = (192.3 / (powder.gravity * mil_thickness)) * (laser_cut_part.powder_transfer_efficiency / 100)
                        estimated_lbs_needed = ((laser_cut_part.surface_area * 2) / 144) / estimated_sq_ft_coverage
                        return estimated_lbs_needed * powder.component.price
        return 0.0

    def save_coatings(self, coatings: list[CoatingItem]):
        worker = UpdateCoatingsWorker(coatings)
        worker.signals.finished.connect(self.save_local_copy)
        QThreadPool.globalInstance().start(worker)

    def save(self):
        self.save_coatings(self.primers + self.paints + self.powders)

    def save_local_copy(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self, on_loaded: Callable | None = None):
        try:
            self.categories.from_list(
                [
                    CoatingTypes.POWDER.value,
                    CoatingTypes.PAINT.value,
                    CoatingTypes.PRIMER.value,
                ]
            )

            self.chain = RunnableChain()

            get_all_coatings_worker = GetAllCoatingsWorker()

            self.chain.add(get_all_coatings_worker, self.load_data_response)

            if on_loaded:
                self.chain.finished.connect(on_loaded)

            self.chain.start()
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self._reset_file()
            self.load_data()

    def load_data_response(self, response: dict[str, list[dict[str, object]]], next_step: Callable):
        self.primers.clear()
        self.paints.clear()
        self.powders.clear()

        for coating_data in response:
            if coating_data["coating_type"] == CoatingTypes.PRIMER.value:
                self.add_primer(CoatingItem(coating_data, self))
            elif coating_data["coating_type"] == CoatingTypes.PAINT.value:
                self.add_paint(CoatingItem(coating_data, self))
            elif coating_data["coating_type"] == CoatingTypes.POWDER.value:
                self.add_powder(CoatingItem(coating_data, self))
        next_step()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "coatings": [coating.to_dict() for coating in self.primers + self.paints + self.powders],
        }
