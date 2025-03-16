import copy
from typing import TYPE_CHECKING, Optional, Union

from utils.inventory.category import Category
from utils.inventory.inventory_item import InventoryItem
from utils.inventory.paint import Paint
from utils.inventory.powder import Powder
from utils.inventory.primer import Primer
from utils.workspace.flowtag import Flowtag
from utils.workspace.flowtag_data import FlowtagData
from utils.workspace.flowtag_timer import FlowtagTimer
from utils.workspace.tag import Tag
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from utils.inventory.laser_cut_inventory import LaserCutInventory
    from utils.inventory.nest import Nest
    from utils.inventory.paint_inventory import PaintInventory


class LaserCutPart(InventoryItem):
    def __init__(
        self,
        data: dict[str, Union[str, float, int, dict[str, object], list[object]]],
        laser_cut_inventory,
    ):
        super().__init__()

        self.laser_cut_inventory: LaserCutInventory = laser_cut_inventory
        self.paint_inventory: PaintInventory = self.laser_cut_inventory.paint_inventory
        self.workspace_settings: WorkspaceSettings = (
            self.laser_cut_inventory.workspace_settings
        )

        self.quantity: int = 0
        self.red_quantity_limit: int = 10
        self.yellow_quantity_limit: int = 20
        self.category_quantities: dict[Category, float] = {}

        self.machine_time: float = 0.0
        self.weight: float = 0.0
        self.part_number: str = ""
        self.image_index: str = ""
        self.surface_area: float = 0.0
        self.cutting_length: float = 0.0
        self.file_name: str = ""
        self.piercing_time: float = 0.0
        self.piercing_points: int = 0
        self.gauge: str = ""
        self.material: str = ""
        self.recut: bool = False
        self.recut_count: int = 0
        self.shelf_number: str = ""
        self.sheet_dim: str = ""
        self.part_dim: str = ""
        self.geofile_name: str = ""
        self.modified_date: str = ""
        self.notes: str = ""

        self.price: float = 0.0
        self.cost_of_goods: float = 0.0
        self.bend_cost: float = 0.0
        self.labor_cost: float = 0.0

        # Paint Items
        self.recoat: bool = False
        self.recoat_count: int = 0

        self.uses_primer: bool = False
        self.primer_name: str = None
        self.primer_item: Primer = None
        self.primer_overspray: float = 66.67
        self.cost_for_primer: float = 0.0

        self.uses_paint: bool = False
        self.paint_name: str = None
        self.paint_item: Paint = None
        self.paint_overspray: float = 66.67
        self.cost_for_paint: float = 0.0

        self.uses_powder: bool = False
        self.powder_name: str = None
        self.powder_item: Powder = None
        self.powder_transfer_efficiency: float = 66.67
        self.cost_for_powder_coating: float = 0.0

        self.flowtag: Flowtag = None
        self.current_flow_tag_index: int = 0
        self.current_flow_tag_status_index: int = 0
        self.bending_files: list[str] = []
        self.welding_files: list[str] = []
        self.cnc_milling_files: list[str] = []
        self.timer: FlowtagTimer = None
        self.flowtag_data: FlowtagData = None

        # NOTE Only for Quote Generator and load_nest.py
        self.recut_count_notes: int = 0
        self.nest: Nest = None
        self.quantity_on_sheet: int = None
        self.matched_to_sheet_cost_price: float = 0.0

        # NOTE Non serializable variables
        self.id = -1

        self.load_data(data)

    def is_process_finished(self) -> bool:
        return self.current_flow_tag_index >= len(self.flowtag.tags)

    def get_first_tag_index_with_similar_keyword(self, keywords: list[str]) -> int:
        for index in range(len(self.flowtag.tags) - 1, -1, -1):
            tag_name = self.flowtag.tags[index].name.lower()
            if any(keyword in tag_name for keyword in keywords):
                return index
        return 0

    def mark_as_recoat(self):
        self.timer.stop(self.get_current_tag())
        self.current_flow_tag_index = self.get_first_tag_index_with_similar_keyword(
            ["powder", "coating", "liquid", "paint", "gloss", "prime"]
        )
        self.current_flow_tag_status_index = 0
        self.recoat = True
        self.recoat_count += 1

    def unmark_as_recoat(self):
        self.recoat = False
        self.move_to_next_process()

    def mark_as_recut(self):
        self.timer.stop(self.get_current_tag())
        self.current_flow_tag_index = 0
        self.current_flow_tag_status_index = 0
        self.recut = True
        self.recut_count += 1

    def unmark_as_recut(self):
        self.recut = False
        self.move_to_next_process()

    def move_to_next_process(self):
        self.timer.stop(self.get_current_tag())
        self.check_update_quantity_tags()
        if not self.is_process_finished():
            self.current_flow_tag_index += 1
            self.current_flow_tag_status_index = 0
            self.recut = False
            self.recoat = False
            self.timer.start(self.get_current_tag())

    def check_update_quantity_tags(self):
        if (
            self.flowtag.add_quantity_tag
            and self.get_current_tag().name == self.flowtag.add_quantity_tag.name
        ):
            self.laser_cut_inventory.add_or_update_laser_cut_part(
                self, f"workspace tag: {self.get_current_tag().name}"
            )
        if (
            self.flowtag.remove_quantity_tag
            and self.get_current_tag().name == self.flowtag.remove_quantity_tag.name
        ):
            self.laser_cut_inventory.remove_laser_cut_part_quantity(
                self, f"workspace tag: {self.get_current_tag().name}"
            )

    def get_current_tag(self) -> Optional[Tag]:
        try:
            return self.flowtag.tags[self.current_flow_tag_index]
        except IndexError:
            return None

    def get_next_tag_name(self) -> str:
        try:
            return self.flowtag.tags[self.current_flow_tag_index + 1].name
        except IndexError:
            return "Done"

    def get_all_paints(self) -> str:
        name = ""
        if self.uses_primer and self.primer_item:
            name += f"{self.primer_item.name}\n"
        if self.uses_paint and self.paint_item:
            name += f"{self.paint_item.name}\n"
        if self.uses_powder and self.powder_item:
            name += f"{self.powder_item.name}\n"
        return name

    def get_expected_time_to_complete(self) -> int:
        total_time: int = 0
        for tag in self.flowtag_data.tags_data:
            total_time += self.flowtag_data.get_tag_data(
                tag, "expected_time_to_complete"
            )
        return total_time

    def move_to_category(self, from_category: Category, to_category: Category):
        super().remove_from_category(from_category)
        self.add_to_category(to_category)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.laser_cut_inventory.remove_laser_cut_part(self)

    def get_category_quantity(self, category: Union[str, Category]) -> float:
        if isinstance(category, str):
            category = self.laser_cut_inventory.get_category(category)
        try:
            return self.category_quantities[category]
        except KeyError:
            return 1.0

    def set_category_quantity(
        self, category: Union[str, Category], quantity: float
    ) -> float:
        if isinstance(category, str):
            category = self.laser_cut_inventory.get_category(category)
        self.category_quantities[category] = quantity

    def print_category_quantities(self) -> str:
        return "".join(
            f"{i + 1}. {category.name}: {self.get_category_quantity(category)}\n"
            for i, category in enumerate(self.categories)
        )

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        self.name = data.get("name", "")
        self.quantity = data.get(
            "quantity", 0
        )  # In the context of assemblies, quantity is unit_quantity
        self.red_quantity_limit = data.get("red_quantity_limit", 10)
        self.yellow_quantity_limit = data.get("yellow_quantity_limit", 20)
        self.category_quantities.clear()
        for category_name, unit_quantity in data.get("category_quantities", {}).items():
            category = self.laser_cut_inventory.get_category(category_name)
            self.category_quantities.update({category: unit_quantity})
        self.machine_time = data.get("machine_time", 0.0)
        self.weight = data.get("weight", 0.0)
        self.part_number = data.get("part_number", "")
        self.image_index = data.get("image_index", "")
        self.surface_area = data.get("surface_area", 0.0)
        self.cutting_length = data.get("cutting_length", 0.0)
        self.file_name = data.get("file_name", "")
        self.piercing_time = data.get("piercing_time", 0.0)
        self.piercing_points = data.get("piercing_points", 0)
        self.gauge = data.get("gauge", "")
        self.material = data.get("material", "")
        self.price = data.get("price", 0.0)
        self.cost_of_goods = data.get("cost_of_goods", 0.0)
        self.recut = data.get("recut", False)
        self.recut_count = data.get("recut_count", 0)
        self.recut_count_notes = data.get("recut_count_notes", 0)
        self.shelf_number = data.get("shelf_number", "")
        self.sheet_dim = data.get("sheet_dim", "")
        self.part_dim = data.get("part_dim", "")
        self.geofile_name = data.get("geofile_name", "")
        self.modified_date = data.get("modified_date", "")
        self.notes = data.get("notes", "")
        self.bend_cost = data.get("bend_cost", 0.0)
        self.labor_cost = data.get("labor_cost", 0.0)

        self.uses_primer = data.get("uses_primer", False)
        self.primer_name = data.get("primer_name")
        self.primer_overspray = data.get("primer_overspray", 66.67)
        if self.uses_primer and self.primer_name:
            self.primer_item = self.paint_inventory.get_primer(self.primer_name)
        self.cost_for_primer = data.get("cost_for_primer", 0.0)

        self.uses_paint = data.get("uses_paint", False)
        self.paint_name = data.get("paint_name")
        self.paint_overspray = data.get("paint_overspray", 66.67)
        if self.uses_paint and self.paint_name:
            self.paint_item = self.paint_inventory.get_paint(self.paint_name)
        self.cost_for_paint = data.get("cost_for_paint", 0.0)

        self.uses_powder = data.get("uses_powder_coating", False)
        self.powder_name = data.get("powder_name")
        self.powder_transfer_efficiency = data.get("powder_transfer_efficiency", 66.67)
        if self.uses_powder and self.powder_name:
            self.powder_item = self.paint_inventory.get_powder(self.powder_name)
        self.cost_for_powder_coating = data.get("cost_for_powder_coating", 0.0)

        self.recoat = data.get("recoat", False)
        self.recoat_count = data.get("recoat_count", 0)

        self.flowtag = Flowtag(
            data.get("flow_tag", {}), self.workspace_settings
        )
        self.current_flow_tag_index = data.get("current_flow_tag_index", 0)
        self.current_flow_tag_status_index = data.get(
            "current_flow_tag_status_index", 0
        )
        self.bending_files.clear()
        self.bending_files = data.get("bending_files", [])
        self.welding_files.clear()
        self.welding_files = data.get("welding_files", [])
        self.cnc_milling_files.clear()
        self.cnc_milling_files = data.get("cnc_milling_files", [])
        # If deepcopy is not done, than a reference is kept in the original object it was copied from
        # and then it messes everything up, specifically it will mess up laser cut parts
        # when you add a job to workspace
        self.timer = FlowtagTimer(copy.deepcopy(data.get("timer", {})), self.flowtag)
        self.flowtag_data = FlowtagData(self.flowtag)
        self.flowtag_data.load_data(data.get("flow_tag_data", {}))
        if tag := self.flowtag.get_tag_with_similar_name("laser"):
            self.flowtag_data.set_tag_data(
                tag, "expected_time_to_complete", int(self.machine_time * 60)
            )
        elif tag := self.flowtag.get_tag_with_similar_name("picking"):
            self.flowtag_data.set_tag_data(
                tag, "expected_time_to_complete", self.weight
            )
        self.quantity_on_sheet = data.get("quantity_on_sheet", 0)

        self.categories.clear()
        categories = data.get("categories", [])
        for category in self.laser_cut_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)

    def load_part_data(self, data: dict[str, Union[str, int, float, bool]]):
        """Only updates part information from nest files."""
        self.machine_time = data.get("machine_time", 0.0)
        self.weight = data.get("weight", 0.0)
        self.part_number = data.get("part_number", "")
        self.image_index = data.get("image_index", "")
        self.surface_area = data.get("surface_area", 0.0)
        self.cutting_length = data.get("cutting_length", 0.0)
        self.file_name = data.get("file_name", "")
        self.piercing_time = data.get("piercing_time", 0.0)
        self.piercing_points = data.get("piercing_points", 0)
        self.gauge = data.get("gauge", "")
        self.material = data.get("material", "")
        self.sheet_dim = data.get("sheet_dim", "")
        self.part_dim = data.get("part_dim", "")
        self.geofile_name = data.get("geofile_name", "")
        self.quantity_on_sheet = data.get("quantity_on_sheet")

    def get_copy(self) -> "LaserCutPart":
        return copy.deepcopy(self)

    def to_dict(self) -> dict[str, dict]:
        return {
            "name": self.name,
            "part_number": self.part_number,
            "gauge": self.gauge,
            "material": self.material,
            "part_dim": self.part_dim,
            "machine_time": self.machine_time,
            "weight": self.weight,
            "surface_area": self.surface_area,
            "cutting_length": self.cutting_length,
            "piercing_time": self.piercing_time,
            "piercing_points": self.piercing_points,
            "shelf_number": self.shelf_number,
            "sheet_dim": self.sheet_dim,
            "file_name": self.file_name,
            "geofile_name": self.geofile_name,
            "modified_date": self.modified_date,
            "notes": self.notes,
            "image_index": self.image_index,
            "price": self.price,
            "cost_of_goods": self.cost_of_goods,
            "bend_cost": self.bend_cost,
            "labor_cost": self.labor_cost,
            "recut": self.recut,
            "recut_count": self.recut_count,
            "recut_count_notes": self.recut_count_notes,
            "uses_primer": self.uses_primer,
            "primer_name": None if self.primer_name == "None" else self.primer_name,
            "primer_overspray": self.primer_overspray,
            "cost_for_primer": self.cost_for_primer,
            "uses_paint": self.uses_paint,
            "paint_name": None if self.paint_name == "None" else self.paint_name,
            "paint_overspray": self.paint_overspray,
            "cost_for_paint": self.cost_for_paint,
            "uses_powder_coating": self.uses_powder,
            "powder_name": None if self.powder_name == "None" else self.powder_name,
            "powder_transfer_efficiency": self.powder_transfer_efficiency,
            "cost_for_powder_coating": self.cost_for_powder_coating,
            "recoat": self.recoat,
            "recoat_count": self.recoat_count,
            "bending_files": self.bending_files,
            "welding_files": self.welding_files,
            "cnc_milling_files": self.cnc_milling_files,
            "categories": [category.name for category in self.categories],
            "category_quantities": {
                category.name: self.category_quantities.get(category, 1.0)
                for category in self.categories
            },
            "quantity": self.quantity,
            "quantity_on_sheet": self.quantity_on_sheet,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
            "flow_tag": self.flowtag.to_dict(),
            "current_flow_tag_index": self.current_flow_tag_index,
            "current_flow_tag_status_index": self.current_flow_tag_status_index,
            "timer": self.timer.to_dict(),
            "flow_tag_data": self.flowtag_data.to_dict(),
        }
