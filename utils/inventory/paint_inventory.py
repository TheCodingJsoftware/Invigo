import contextlib
from typing import Union, Optional

import msgspec

from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.inventory import Inventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.paint import Paint
from utils.inventory.powder import Powder
from utils.inventory.primer import Primer


class PaintInventory(Inventory):
    def __init__(self, components_inventory: ComponentsInventory):
        super().__init__("paint_inventory")
        self.components_inventory = components_inventory

        self.primers: list[Primer] = []
        self.paints: list[Paint] = []
        self.powders: list[Powder] = []

        self.load_data()

    def add_primer(self, primer: Primer):
        self.primers.append(primer)

    def remove_primer(self, primer: Primer):
        with contextlib.suppress(ValueError):  # Already removed
            self.primers.remove(primer)

    def get_primer(self, name: str) -> Optional[Primer]:
        for primer in self.primers:
            if primer.name == name:
                return primer
        return None

    def get_all_primers(self) -> list[str]:
        return [primer.name for primer in self.primers]

    def get_primer_cost(self, laser_cut_part: LaserCutPart) -> float:
        with contextlib.suppress(ZeroDivisionError, AttributeError):
            if laser_cut_part.uses_primer:
                if primer := self.get_primer(laser_cut_part.primer_name):
                    if primer.component:
                        primer_cost_per_gallon = primer.component.price
                        gallons_used = (((laser_cut_part.surface_area * 2) / 144) / primer.average_coverage) * ((laser_cut_part.primer_overspray / 100) + 1)
                        return primer_cost_per_gallon * gallons_used
        return 0.0

    def add_paint(self, paint: Paint):
        self.paints.append(paint)

    def remove_paint(self, paint: Paint):
        with contextlib.suppress(ValueError):  # Already removed
            self.paints.remove(paint)

    def get_paint(self, name: str) -> Optional[Paint]:
        for paint in self.paints:
            if paint.name == name:
                return paint
        return None

    def get_all_paints(self) -> list[str]:
        return [paint.name for paint in self.paints]

    def get_paint_cost(self, laser_cut_part: LaserCutPart) -> float:
        with contextlib.suppress(ZeroDivisionError, AttributeError):
            if laser_cut_part.uses_paint:
                if paint := self.get_paint(laser_cut_part.paint_name):
                    if paint.component:
                        paint_cost_per_gallon = paint.component.price
                        gallons_used = (((laser_cut_part.surface_area * 2) / 144) / paint.average_coverage) * ((laser_cut_part.paint_overspray / 100) + 1)
                        return paint_cost_per_gallon * gallons_used
        return 0.0

    def add_powder(self, powder: Powder):
        self.powders.append(powder)

    def remove_powder(self, powder: Powder):
        with contextlib.suppress(ValueError):  # Already removed
            self.powders.remove(powder)

    def get_powder(self, name: str) -> Optional[Powder]:
        for powder in self.powders:
            if powder.name == name:
                return powder
        return None

    def get_all_powders(self) -> list[str]:
        return [powder.name for powder in self.powders]

    def get_powder_cost(self, laser_cut_part: LaserCutPart, mil_thickness: float) -> float:
        with contextlib.suppress(ZeroDivisionError, AttributeError):
            if laser_cut_part.uses_powder:
                if powder := self.get_powder(laser_cut_part.powder_name):
                    if powder.component:
                        estimated_sq_ft_coverage = (192.3 / (powder.gravity * mil_thickness)) * (laser_cut_part.powder_transfer_efficiency / 100)
                        estimated_lbs_needed = ((laser_cut_part.surface_area * 2) / 144) / estimated_sq_ft_coverage
                        return estimated_lbs_needed * powder.component.price
        return 0.0

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: dict[str, dict[str, object]] = msgspec.json.decode(file.read())
            self.categories.from_dict(["Primer", "Paint", "Powder"])
            self.primers.clear()
            self.paints.clear()
            self.powders.clear()
            for primer_data in data["primers"]:
                try:
                    primer = Primer(primer_data, self)
                except AttributeError:  # Old inventory format
                    primer = Primer(data["primers"][primer_data], self)
                    primer.name = primer_data
                self.add_primer(primer)
            for paint_data in data["paints"]:
                try:
                    paint = Paint(paint_data, self)
                except AttributeError:  # Old inventory format
                    paint = Paint(data["paints"][paint_data], self)
                    paint.name = paint_data
                self.add_paint(paint)
            for powder_data in data["powders"]:
                try:
                    powder = Powder(powder_data, self)
                except AttributeError:  # Old inventory format
                    powder = Powder(data["powders"][powder_data], self)
                    powder.name = powder_data
                self.add_powder(powder)
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self._reset_file()
            self.load_data()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "primers": [primer.to_dict() for primer in self.primers],
            "paints": [paint.to_dict() for paint in self.paints],
            "powders": [powder.to_dict() for powder in self.powders],
        }
