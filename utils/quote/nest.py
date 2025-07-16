from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.sheet import Sheet
from utils.sheet_settings.sheet_settings import SheetSettings


class Nest:
    def __init__(
        self,
        name: str,
        data: dict[str, object],
        sheet_settings: SheetSettings,
        laser_cut_inventory: LaserCutInventory,
    ):
        self.name: str = name
        self.sheet_settings = sheet_settings
        self.laser_cut_inventory = laser_cut_inventory
        self.sheet_count: int = 0
        self.scrap_percentage: float = 0.0
        self.sheet_cut_time: float = 0.0
        self.image_path: str = "404.jpeg"
        self.laser_cut_parts: list[LaserCutPart] = []
        self.sheet: Sheet = None
        self.is_custom: bool = False
        self.load_data(data)

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.append(laser_cut_part)

    def remove_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.remove(laser_cut_part)

    def get_total_cutting_time(self) -> str:
        total_seconds = self.sheet_cut_time * self.sheet_count
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def calculate_scrap_percentage(self) -> float:
        sheet_surface_area = self.sheet.length * self.sheet.width
        total_laser_cut_part_surface_area = 0.0
        for laser_cut_part in self.laser_cut_parts:
            total_laser_cut_part_surface_area += laser_cut_part.surface_area
        try:
            return (1 - (total_laser_cut_part_surface_area / sheet_surface_area)) * 100
        except ZeroDivisionError:
            return 0.0

    def get_sheet_cost(self) -> float:
        if price_per_pound := self.sheet_settings.get_price_per_pound(self.sheet.material):
            if pounds_per_square_foot := self.sheet_settings.get_pounds_per_square_foot(self.sheet.material, self.sheet.thickness):
                pounds_per_sheet = ((self.sheet.length * self.sheet.width) / 144) * pounds_per_square_foot
                return price_per_pound * pounds_per_sheet
        return 0.0

    def get_machining_time(self) -> float:
        return self.sheet_cut_time * self.sheet_count

    def get_sheet_dimension(self) -> str:
        return f"{self.sheet.length:.3f}x{self.sheet.width:.3f}"

    def get_name(self) -> str:
        return f"{self.sheet.thickness} {self.sheet.material} {self.get_sheet_dimension()} {self.name}"

    def load_data(self, data: dict[str, float | int | str | dict[str, float | str]]):
        self.sheet_count = data.get("sheet_count", 0)
        self.scrap_percentage = data.get("scrap_percentage", 0.0)
        self.sheet_cut_time = data.get("sheet_cut_time", 0.0)
        self.image_path = data.get("image_path", "images/404.jpeg")
        self.laser_cut_parts.clear()
        for laser_cut_part_data in data.get("laser_cut_parts", []):
            try:
                laser_cut_part = LaserCutPart(laser_cut_part_data, self.laser_cut_inventory)
            except AttributeError:  # Old inventory format
                laser_cut_part = LaserCutPart(
                    data["laser_cut_parts"][laser_cut_part_data],
                    self.laser_cut_inventory,
                )
                laser_cut_part.name = laser_cut_part_data
            laser_cut_part.nest = self
            self.laser_cut_parts.append(laser_cut_part)
        try:
            sheet_name = list(data["sheet"].keys())[0]
            self.sheet = Sheet(
                data["sheet"][sheet_name],
                None,
            )
        except KeyError:  # Generated from load_nests.py
            self.sheet = Sheet(
                {
                    "thickness": data.get("gauge", ""),
                    "material": data.get("material", ""),
                },
                None,
            )

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "sheet_count": self.sheet_count,
            "scrap_percentage": self.scrap_percentage,
            "sheet_cut_time": self.sheet_cut_time,
            "image_path": self.image_path,
            "laser_cut_parts": {laser_cut_part.name: laser_cut_part.to_dict() for laser_cut_part in self.laser_cut_parts},
            "sheet": {self.sheet.get_name(): self.sheet.to_dict()},
        }
