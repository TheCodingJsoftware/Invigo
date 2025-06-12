from enum import Enum

from PyQt6.QtCore import QDate


class SortingMethod(Enum):
    A_TO_Z = "A ➜ Z"
    Z_TO_A = "Z ➜ A"
    PROCESS = "Current Process"
    MOST_TO_LEAST = "Most ➜ Least"
    LEAST_TO_MOST = "Least ➜ Most"
    HEAVY_TO_LIGHT = "Heavy ➜ Light"
    LIGHT_TO_HEAVY = "Light ➜ Heavy"
    LARGE_TO_SMALL = "Large ➜ Small"
    SMALL_TO_LARGE = "Small ➜ Large"


class WorkspaceFilter:
    def __init__(self):
        self.current_tag: str = None
        self.search_text: str = ""
        self.material_filter: dict[str, bool] = {}
        self.thickness_filter: dict[str, bool] = {}
        self.paint_filter: dict[str, bool] = {}
        self.sorting_method: SortingMethod = SortingMethod.A_TO_Z
        self.date_range: tuple[QDate, QDate] = ()
        self.enable_date_range: bool = False
