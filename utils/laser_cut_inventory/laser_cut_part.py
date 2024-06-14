import copy
from typing import Union

from utils.inventory.category import Category
from utils.inventory.inventory_item import InventoryItem
from utils.paint_inventory.paint import Paint
from utils.paint_inventory.powder import Powder
from utils.paint_inventory.primer import Primer
from utils.workspace.flow_tag import FlowTag
from utils.workspace.workspace_settings import WorkspaceSettings


class LaserCutPart(InventoryItem):
    def __init__(self, name: str, data: dict, laser_cut_inventory):
        super().__init__(name)
        from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
        from utils.paint_inventory.paint_inventory import PaintInventory

        self.laser_cut_inventory: LaserCutInventory = laser_cut_inventory
        self.paint_inventory: PaintInventory = self.laser_cut_inventory.paint_inventory
        self.workspace_settings: WorkspaceSettings = self.laser_cut_inventory.workspace_settings

        self.quantity: int = 0
        self.red_quantity_limit: int = 10
        self.yellow_quantity_limit: int = 20
        self.unit_quantity: int = 1

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
        self.custom: bool = False
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

        self.flow_tag: FlowTag = None
        self.bending_files: list[str] = []
        self.welding_files: list[str] = []
        self.cnc_milling_files: list[str] = []

        # NOTE Non serializable variables
        self.unit_price: float = 0.0

        # NOTE Only for Quote Generator and load_nest.py
        self.nest = None
        self.quoted_price: float = 0.0
        self.quantity_in_nest: int = None
        self.matched_to_sheet_cost_price: float = 0.0

        self.load_data(data)

    def move_to_category(self, from_category: Category, to_category: Category):
        super().remove_from_category(from_category)
        self.add_to_category(to_category)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.laser_cut_inventory.remove_laser_cut_part(self)

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        self.quantity: int = data.get("quantity", 0)
        self.red_quantity_limit: int = data.get("red_quantity_limit", 10)
        self.yellow_quantity_limit: int = data.get("yellow_quantity_limit", 20)
        self.unit_quantity: int = data.get("unit_quantity", 1)
        self.machine_time: float = data.get("machine_time", 0.0)
        self.weight: float = data.get("weight", 0.0)
        self.part_number: str = data.get("part_number", "")
        self.image_index: str = data.get("image_index", "")
        self.surface_area: float = data.get("surface_area", 0.0)
        self.cutting_length: float = data.get("cutting_length", 0.0)
        self.file_name: str = data.get("file_name", "")
        self.piercing_time: float = data.get("piercing_time", 0.0)
        self.piercing_points: int = data.get("piercing_points", 0)
        self.gauge: str = data.get("gauge", "")
        self.material: str = data.get("material", "")
        self.price: float = data.get("price", 0.0)
        self.cost_of_goods: float = data.get("cost_of_goods", 0.0)
        self.recut: bool = data.get("recut", False)
        self.custom: bool = data.get("custom", False)
        self.recut_count: int = data.get("recut_count", 0)
        self.shelf_number: str = data.get("shelf_number", "")
        self.sheet_dim: str = data.get("sheet_dim", "")
        self.part_dim: str = data.get("part_dim", "")
        self.geofile_name: str = data.get("geofile_name", "")
        self.modified_date: str = data.get("modified_date", "")
        self.notes: str = data.get("notes", "")
        self.bend_cost: float = data.get("bend_cost", 0.0)
        self.labor_cost: float = data.get("labor_cost", 0.0)

        self.uses_primer: bool = data.get("uses_primer", False)
        self.primer_name: str = data.get("primer_name")
        self.primer_overspray: float = data.get("primer_overspray", 66.67)
        if self.uses_primer and self.primer_name:
            self.primer_item = self.paint_inventory.get_primer(self.primer_name)
        self.cost_for_primer = data.get("cost_for_primer", 0.0)

        self.uses_paint: bool = data.get("uses_paint", False)
        self.paint_name: str = data.get("paint_name")
        self.paint_overspray: float = data.get("paint_overspray", 66.67)
        if self.uses_paint and self.paint_name:
            self.paint_item = self.paint_inventory.get_paint(self.paint_name)
        self.cost_for_paint = data.get("cost_for_paint", 0.0)

        self.uses_powder: bool = data.get("uses_powder_coating", False)
        self.powder_name: str = data.get("powder_name")
        self.powder_transfer_efficiency: float = data.get("powder_transfer_efficiency", 66.67)
        if self.uses_powder and self.powder_name:
            self.powder_item = self.paint_inventory.get_powder(self.powder_name)
        self.cost_for_powder_coating = data.get("cost_for_powder_coating", 0.0)

        self.flow_tag = FlowTag("", data.get("flow_tag", {"name": "", "tags": []}), self.workspace_settings)
        self.bending_files.clear()
        self.bending_files = data.get("bending_files", [])
        self.welding_files.clear()
        self.welding_files = data.get("welding_files", [])
        self.cnc_milling_files.clear()
        self.cnc_milling_files = data.get("cnc_milling_files", [])

        self.quantity_in_nest = data.get("quantity_in_nest")

        self.categories.clear()
        categories = data.get("categories", [])
        for category in self.laser_cut_inventory.get_categories():
            if category.name in categories:
                self.categories.append(category)

    def get_copy(self) -> "LaserCutPart":
        return copy.deepcopy(self)

    def to_dict(self) -> dict[str, dict]:
        return {
            "part_number": self.part_number,
            "part_dim": self.part_dim,
            "quantity": self.quantity,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
            "unit_quantity": self.unit_quantity,
            "machine_time": self.machine_time,
            "weight": self.weight,
            "surface_area": self.surface_area,
            "cutting_length": self.cutting_length,
            "piercing_time": self.piercing_time,
            "piercing_points": self.piercing_points,
            "price": self.price,
            "cost_of_goods": self.cost_of_goods,
            "gauge": self.gauge,
            "material": self.material,
            "custom": self.custom,
            "recut": self.recut,
            "recut_count": self.recut_count,
            "shelf_number": self.shelf_number,
            "sheet_dim": self.sheet_dim,
            "file_name": self.file_name,
            "geofile_name": self.geofile_name,
            "modified_date": self.modified_date,
            "notes": self.notes,
            "image_index": self.image_index,
            "bend_cost": self.bend_cost,
            "labor_cost": self.labor_cost,
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
            "quantity_in_nest": self.quantity_in_nest,
            "flow_tag": self.flow_tag.to_dict(),
            "bending_files": self.bending_files,
            "welding_files": self.welding_files,
            "cnc_milling_files": self.cnc_milling_files,
            "categories": [category.name for category in self.categories],
        }
