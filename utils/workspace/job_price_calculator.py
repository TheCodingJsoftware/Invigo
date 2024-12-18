import math
from typing import TYPE_CHECKING

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.inventory.paint_inventory import PaintInventory
from utils.inventory.sheet import Sheet
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workspace.assembly import Assembly

if TYPE_CHECKING:
    from utils.workspace.job import Job


class JobPriceCalculator:
    def __init__(
        self,
        job,
        sheet_settings: SheetSettings,
        paint_inventory: PaintInventory,
        settings: dict[str, float],
    ):
        self.job: Job = job

        # These are percentages
        self.item_profit_margin = 0.3
        self.item_overhead = 0.18

        self.components_use_overhead = False
        self.components_use_profit_margin = False

        self.sheet_profit_margin = 0.3
        self.sheet_overhead = 0.18

        self.cost_for_laser = 150.0
        self.mil_thickness = 2.0

        self.match_item_cogs_to_sheet = False

        self.paint_inventory = paint_inventory
        self.sheet_settings = sheet_settings

        self.load_settings(settings)

    def calculate_laser_cut_part_overhead(
        self,
        cost: float,
        max_iterations: int = 10,
    ):
        unit_price = 0
        for _ in range(max_iterations):
            try:
                unit_price = (cost + (unit_price * self.item_overhead)) / (
                    1 - self.item_profit_margin
                )
            except ZeroDivisionError:
                unit_price = cost + (unit_price * self.item_overhead) / 0.00000001
        return unit_price

    def calculate_component_overhead(
        self, cost: float, max_iterations: int = 10
    ) -> float:
        profit_margin = (
            self.item_profit_margin if self.components_use_profit_margin else 0
        )
        overhead = self.item_overhead if self.components_use_overhead else 0

        unit_price = 0
        for _ in range(max_iterations):
            try:
                unit_price = (cost + (unit_price * overhead)) / (1 - profit_margin)
            except ZeroDivisionError:
                unit_price = cost + (unit_price * overhead) / 0.00000001
        return unit_price

    def calculate_sheet_overhead(
        self,
        cost: float,
        max_iterations: int = 10,
    ):
        unit_price = 0
        for _ in range(max_iterations):
            try:
                unit_price = (cost + (unit_price * self.sheet_overhead)) / (
                    1 - self.sheet_profit_margin
                )
            except ZeroDivisionError:
                unit_price = cost + (unit_price * self.sheet_overhead) / 0.00000001
        return unit_price

    def get_job_cost(self) -> float:
        total = 0.0
        for assembly in self.job.assemblies:
            total += self.get_assembly_cost(assembly)
        return total

    def get_assembly_cost(self, assembly: Assembly) -> float:
        total = (
            self.get_laser_cut_parts_cost(assembly.laser_cut_parts) * assembly.quantity
            + self.get_components_cost(assembly.components) * assembly.quantity
        )
        for sub_assembly in assembly.sub_assemblies:
            total += self.get_assembly_cost(sub_assembly)
        return total

    def get_laser_cut_parts_cost(self, laser_cut_parts: list[LaserCutPart]) -> float:
        total = 0.0
        for laser_cut_part in laser_cut_parts:
            total += (
                self.get_laser_cut_part_cost(laser_cut_part) * laser_cut_part.quantity
            )
        return total

    def get_laser_cut_part_cost_of_goods(self, laser_cut_part: LaserCutPart) -> float:
        if self.match_item_cogs_to_sheet:
            return laser_cut_part.matched_to_sheet_cost_price
        price_per_pound = self.sheet_settings.get_price_per_pound(
            laser_cut_part.material
        )
        return (laser_cut_part.machine_time * (self.cost_for_laser / 60)) + (
            laser_cut_part.weight * price_per_pound
        )

    def get_laser_cut_part_cost_for_painting(
        self, laser_cut_part: LaserCutPart
    ) -> float:
        cost_for_priming = self.paint_inventory.get_primer_cost(laser_cut_part)
        cost_for_painting = self.paint_inventory.get_paint_cost(laser_cut_part)
        cost_for_powder_coating = self.paint_inventory.get_powder_cost(
            laser_cut_part, self.mil_thickness
        )
        return (
            self.calculate_laser_cut_part_overhead(
                cost_for_priming,
            )
            + self.calculate_laser_cut_part_overhead(
                cost_for_painting,
            )
            + self.calculate_laser_cut_part_overhead(
                cost_for_powder_coating,
            )
        )

    def get_laser_cut_part_cost(self, laser_cut_part: LaserCutPart) -> float:
        return (
            self.calculate_laser_cut_part_overhead(
                self.get_laser_cut_part_cost_of_goods(laser_cut_part),
            )
            + self.calculate_laser_cut_part_overhead(
                laser_cut_part.bend_cost,
            )
            + self.calculate_laser_cut_part_overhead(
                laser_cut_part.labor_cost,
            )
            + self.get_laser_cut_part_cost_for_painting(laser_cut_part)
        )

    def get_components_cost(self, components: list[Component]) -> float:
        total = 0.0
        for component in components:
            total += self.get_component_cost(component) * component.quantity
        return total

    def get_component_cost(self, component: Component) -> float:
        if self.components_use_profit_margin or self.components_use_overhead:
            return self.calculate_component_overhead(component.price)
        return component.price

    def get_cutting_cost(self, nest: Nest) -> float:
        return ((nest.sheet_cut_time * nest.sheet_count) / 3600) * self.cost_for_laser

    def get_sheet_cost(self, sheet: Sheet) -> float:
        if price_per_pound := self.sheet_settings.get_price_per_pound(sheet.material):
            if pounds_per_square_foot := self.sheet_settings.get_pounds_per_square_foot(
                sheet.material, sheet.thickness
            ):
                pounds_per_sheet = (
                    (sheet.length * sheet.width) / 144
                ) * pounds_per_square_foot
                return price_per_pound * pounds_per_sheet
        return 0.0

    def get_nest_laser_cut_parts_cost(self, nest: Nest) -> float:
        return self.get_laser_cut_parts_cost(nest.laser_cut_parts) * nest.sheet_count

    def get_total_cost_for_sheets(self) -> float:
        total_sheet_cost = 0.0
        for nest in self.job.nests:
            total_sheet_cost += self.calculate_sheet_overhead(
                (
                    self.get_cutting_cost(nest)
                    + (self.get_sheet_cost(nest.sheet) * nest.sheet_count)
                ),
            )
        return total_sheet_cost

    def update_laser_cut_parts_to_sheet_price(self):
        target_value = self.get_total_cost_for_sheets()

        MAX_ITERATIONS = 200
        TOLERANCE = 1
        iteration_count = 0

        all_laser_cut_parts = self.job.get_all_laser_cut_parts()
        for laser_cut_part in all_laser_cut_parts:
            laser_cut_part.matched_to_sheet_cost_price = laser_cut_part.cost_of_goods

        def _adjust_item_price(laser_cut_parts: list[LaserCutPart], amount: float):
            for laser_cut_part in laser_cut_parts:
                laser_cut_part.matched_to_sheet_cost_price += amount

        new_item_cost = self.get_job_cost()
        difference = round(new_item_cost - target_value, 2)
        amount_changed: float = 0
        run_count: int = 0
        while abs(difference) > TOLERANCE and iteration_count < MAX_ITERATIONS:
            run_count += 1
            if difference > 0:  # Need to decrease cost for items
                _adjust_item_price(all_laser_cut_parts, -(abs(difference) / 1000))
            else:  # Need to increase cost for items
                _adjust_item_price(all_laser_cut_parts, abs(difference) / 1000)
            new_item_cost = self.get_job_cost()
            amount_changed += abs(difference) / 10000
            difference = round(new_item_cost - target_value, 2)
            iteration_count += 1
            if (math.isinf(difference) and difference > 0) or (
                math.isinf(difference) and difference < 0
            ):
                break

    def update_laser_cut_parts_cost(self):
        self.paint_inventory.load_data()
        for laser_cut_part in self.job.get_all_laser_cut_parts():
            laser_cut_part.cost_for_primer = self.paint_inventory.get_primer_cost(
                laser_cut_part
            )
            laser_cut_part.cost_for_paint = self.paint_inventory.get_paint_cost(
                laser_cut_part
            )
            laser_cut_part.cost_for_powder_coating = (
                self.paint_inventory.get_powder_cost(laser_cut_part, self.mil_thickness)
            )
            laser_cut_part.cost_of_goods = self.get_laser_cut_part_cost_of_goods(
                laser_cut_part
            )
            laser_cut_part.price = round(
                self.get_laser_cut_part_cost(laser_cut_part), 2
            )

    def load_settings(self, settings: dict[str, float]):
        self.item_profit_margin = settings.get("item_profit_margin", 0.3)
        self.item_overhead = settings.get("item_overhead", 0.18)
        self.sheet_profit_margin = settings.get("sheet_profit_margin", 0.3)
        self.sheet_overhead = settings.get("sheet_overhead", 0.18)
        self.cost_for_laser = settings.get("cost_for_laser", 150)
        self.mil_thickness = settings.get("mil_thickness", 2.0)
        self.match_item_cogs_to_sheet = settings.get("match_item_cogs_to_sheet", False)
        self.components_use_overhead = settings.get("components_use_overhead", False)
        self.components_use_profit_margin = settings.get(
            "components_use_profit_margin", False
        )

    def to_dict(self):
        return {
            "item_profit_margin": self.item_profit_margin,
            "item_overhead": self.item_overhead,
            "sheet_profit_margin": self.sheet_profit_margin,
            "sheet_overhead": self.sheet_overhead,
            "cost_for_laser": self.cost_for_laser,
            "mil_thickness": self.mil_thickness,
            "match_item_cogs_to_sheet": self.match_item_cogs_to_sheet,
            "components_use_overhead": self.components_use_overhead,
            "components_use_profit_margin": self.components_use_profit_margin,
        }
