from enum import Enum

class SortingMethod(Enum):
    A_Z = "A ➜ Z"
    Z_A = "Z ➜ A"
    MOST_LEAST = "Most ➜ Least"
    LEAST_MOST = "Least ➜ Most"
    HEAVY_LIGHT = "Heavy ➜ Light"
    LIGHT_HEAVY = "Light ➜ Heavy"
    LARGE_SMALL = "Large ➜ Small"
    SMALL_LARGE = "Small ➜ Large"


class WorkspaceFilter:
    def __init__(self):
        self.current_tag: str = None
        self.search_text: str = ""
        self.material_filter: dict[str, bool] = {}
        self.thickness_filter: dict[str, bool] = {}
        self.paint_filter: dict[str, bool] = {}
        self.sorting_method: SortingMethod = ""