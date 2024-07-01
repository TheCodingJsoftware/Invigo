import contextlib
from typing import TYPE_CHECKING

import ujson as json

from utils.components_inventory.components_inventory import ComponentsInventory
from utils.inventory.inventory import Inventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.paint_inventory.paint import Paint
from utils.paint_inventory.powder import Powder
from utils.paint_inventory.primer import Primer

if TYPE_CHECKING:
    from main import MainWindow


class PaintInventory(Inventory):
    def __init__(self, parent):
        super().__init__("paint_inventory")
        self.parent: MainWindow = parent
        self.components_inventory: ComponentsInventory = self.parent.components_inventory

        self.primers: list[Primer] = []
        self.paints: list[Paint] = []
        self.powders: list[Powder] = []

        self.load_data()

    def add_primer(self, primer: Primer):
        self.primers.append(primer)

    def remove_primer(self, primer: Primer):
        self.primers.remove(primer)

    def get_primer(self, name: str) -> Primer:
        for primer in self.primers:
            if primer.name == name:
                return primer

    def get_all_primers(self) -> list[str]:
        return [primer.name for primer in self.primers]

    def get_primer_cost(self, laser_cut_part: LaserCutPart) -> float:
        with contextlib.suppress(ZeroDivisionError):
            if laser_cut_part.uses_primer:
                if primer := self.get_primer(laser_cut_part.primer_name):
                    primer_cost_per_gallon = primer.component.price
                    gallons_used = (((laser_cut_part.surface_area * 2) / 144) / primer.average_coverage) * ((laser_cut_part.primer_overspray / 100) + 1)
                    return primer_cost_per_gallon * gallons_used
        return 0.0

    def add_paint(self, paint: Paint):
        self.paints.append(paint)

    def remove_paint(self, paint: Paint):
        self.paints.remove(paint)

    def get_paint(self, name: str) -> Paint:
        for paint in self.paints:
            if paint.name == name:
                return paint

    def get_all_paints(self) -> list[str]:
        return [paint.name for paint in self.paints]

    def get_paint_cost(self, laser_cut_part: LaserCutPart) -> float:
        with contextlib.suppress(ZeroDivisionError):
            if laser_cut_part.uses_paint:
                if paint := self.get_paint(laser_cut_part.paint_name):
                    paint_cost_per_gallon = paint.component.price
                    gallons_used = (((laser_cut_part.surface_area * 2) / 144) / paint.average_coverage) * ((laser_cut_part.paint_overspray / 100) + 1)
                    return paint_cost_per_gallon * gallons_used
        return 0.0

    def add_powder(self, powder: Powder):
        self.powders.append(powder)

    def remove_powder(self, powder: Powder):
        self.powders.remove(powder)

    def get_powder(self, name: str) -> Powder:
        for powder in self.powders:
            if powder.name == name:
                return powder

    def get_all_powders(self) -> list[str]:
        return [powder.name for powder in self.powders]

    def get_powder_cost(self, laser_cut_part: LaserCutPart, mil_thickness: float) -> float:
        with contextlib.suppress(ZeroDivisionError):
            if laser_cut_part.uses_powder:
                if powder := self.get_powder(laser_cut_part.powder_name):
                    estimated_sq_ft_coverage = (192.3 / (powder.gravity * mil_thickness)) * (laser_cut_part.powder_transfer_efficiency / 100)
                    estimated_lbs_needed = ((laser_cut_part.surface_area * 2) / 144) / estimated_sq_ft_coverage
                    return estimated_lbs_needed * powder.component.price
        return 0.0

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=4)

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "r", encoding="utf-8") as file:
                data: dict[str, dict[str, object]] = json.load(file)
            self.categories.from_dict(["Primer", "Paint", "Powder"])
            self.primers.clear()
            self.paints.clear()
            self.powders.clear()
            for primer_name, primer_data in data["primers"].items():
                self.add_primer(Primer(primer_name, primer_data, self))
            for paint_name, paint_data in data["paints"].items():
                self.add_paint(Paint(paint_name, paint_data, self))
            for powder_name, powder_data in data["powders"].items():
                self.add_powder(Powder(powder_name, powder_data, self))
        except KeyError:  # Inventory was just created
            return
        except json.JSONDecodeError:  # Inventory file got cleared
            self._reset_file()

    def to_dict(self) -> dict:
        data: dict[str, dict[str, object]] = {
            "categories": self.categories.to_dict(),
            "primers": {},
            "paints": {},
            "powders": {},
        }
        for primer in self.primers:
            data["primers"][primer.name] = primer.to_dict()
        for paint in self.paints:
            data["paints"][paint.name] = paint.to_dict()
        for powder in self.powders:
            data["powders"][powder.name] = powder.to_dict()
        return data
