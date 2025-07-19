import copy
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Optional, TypedDict, Union, cast

from utils.dxf_analyzer import DxfAnalyzer
from utils.inventory.category import Category
from utils.inventory.inventory_item import InventoryItem
from utils.inventory.paint import PaintData, PaintDataDict
from utils.inventory.powder import PowderData, PowderDataDict
from utils.inventory.primer import PrimerData, PrimerDataDict
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workspace.flowtag import Flowtag, FlowtagDict
from utils.workspace.flowtag_data import FlowtagData, FlowtagDataDict
from utils.workspace.tag import Tag
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from utils.inventory.laser_cut_inventory import LaserCutInventory
    from utils.inventory.nest import Nest
    from utils.inventory.paint_inventory import PaintInventory


class InventoryDataDict(TypedDict):
    quantity: int
    red_quantity_limit: int
    yellow_quantity_limit: int


@dataclass
class InventoryData:
    quantity: int = 0
    red_quantity_limit: int = 4
    yellow_quantity_limit: int = 10

    def __init__(self, data: Optional[InventoryDataDict], laser_cut_inventory: "LaserCutInventory"):
        self.laser_cut_inventory = laser_cut_inventory

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> InventoryDataDict:
        return {
            "quantity": self.quantity,
            "red_quantity_limit": self.red_quantity_limit,
            "yellow_quantity_limit": self.yellow_quantity_limit,
        }


class MetaDataDict(TypedDict):
    machine_time: float
    weight: float
    part_number: str
    image_index: str
    surface_area: float
    cutting_length: float
    file_name: str
    piercing_time: float
    piercing_points: int
    gauge: str
    material: str
    shelf_number: str
    sheet_dim: str
    part_dim: str
    geofile_name: str
    modified_date: str
    bend_hits: int
    notes: str
    quamtity_on_sheet: int


@dataclass
class MetaData:
    machine_time: float = 0.0
    weight: float = 0.0
    part_number: str = ""
    image_index: str = ""
    surface_area: float = 0.0
    cutting_length: float = 0.0
    file_name: str = ""
    piercing_time: float = 0.0
    piercing_points: int = 0
    gauge: str = ""
    material: str = ""
    shelf_number: str = ""
    sheet_dim: str = ""
    part_dim: str = ""
    geofile_name: str = ""
    modified_date: str = ""
    bend_hits: int = 0
    notes: str = ""
    quantity_on_sheet: int = 0

    def __init__(self, data: Optional[MetaDataDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> MetaDataDict:
        return cast(MetaDataDict, {f.name: getattr(self, f.name) for f in fields(self)})


class PricesDict(TypedDict):
    price: float
    cost_of_goods: float
    bend_cost: float
    labor_cost: float
    cost_for_paint: float
    cost_for_primer: float
    cost_for_powder_coating: float
    matched_to_sheet_cost_price: float


@dataclass
class Prices:
    price: float = 0.0
    cost_of_goods: float = 0.0
    bend_cost: float = 0.0
    labor_cost: float = 0.0
    cost_for_paint: float = 0.0
    cost_for_primer: float = 0.0
    cost_for_powder_coating: float = 0.0
    matched_to_sheet_cost_price: float = 0.0

    def __init__(self, data: Optional[PricesDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PricesDict:
        return cast(PricesDict, {f.name: getattr(self, f.name) for f in fields(self)})


class WorkspaceDataDict(TypedDict):
    bending_files: list[str]
    welding_files: list[str]
    cnc_milling_files: list[str]
    flowtag: FlowtagDict
    flow_tag_data: FlowtagDataDict


@dataclass
class WorkspaceData:
    bending_files: list[str] = field(default_factory=list)
    welding_files: list[str] = field(default_factory=list)
    cnc_milling_files: list[str] = field(default_factory=list)
    flowtag: Optional[Flowtag] = None
    flowtag_data: Optional[FlowtagData] = None

    def __init__(self, data: Optional[WorkspaceDataDict], workspace_settings: WorkspaceSettings):
        self.workspace_settings = workspace_settings
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in ["flowtag", "flow_tag_data"]:
                    continue
                if f.name in data:
                    setattr(self, f.name, data[f.name])

            self.flowtag = Flowtag(data.get("flowtag", {}), self.workspace_settings)
            self.flowtag_data = FlowtagData(self.flowtag)
            self.flowtag_data.load_data(data.get("flow_tag_data", {}))

    def to_dict(self) -> WorkspaceDataDict:
        result: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            result[f.name] = value.to_dict() if hasattr(value, "to_dict") else value
        return cast(WorkspaceDataDict, result)


class LaserCutPartDict(TypedDict):
    id: int
    name: str
    categories: list[str]
    category_quantities: dict[str, float]
    inventory_data: InventoryDataDict
    meta_data: MetaDataDict
    prices: PricesDict
    paint_data: PaintDataDict
    primer_data: PrimerDataDict
    powder_data: PowderDataDict
    workspace_data: WorkspaceDataDict


class LaserCutPart(InventoryItem):
    PIERCING_TIME = 2.73157894737  # seconds per piercing point
    CUT_TIME_PER_INCH = 2.87897096597  # seconds per inch of cutting length
    inventory_data: InventoryData
    meta_data: MetaData
    prices: Prices
    paint_data: PaintData
    primer_data: PrimerData
    powder_data: PowderData
    workspace_data: WorkspaceData

    def __init__(
        self,
        data: LaserCutPartDict,
        laser_cut_inventory: "LaserCutInventory",
    ):
        super().__init__()
        self.id = data.get("id", -1)
        self.name = data.get("name", "")
        self.laser_cut_inventory = laser_cut_inventory
        self.paint_inventory: PaintInventory = self.laser_cut_inventory.paint_inventory
        self.workspace_settings: WorkspaceSettings = self.laser_cut_inventory.workspace_settings
        self.sheet_settings: SheetSettings = self.laser_cut_inventory.sheet_settings

        self.inventory_data = InventoryData(data.get("inventory_data", {}), self.laser_cut_inventory)
        self.meta_data = MetaData(data.get("meta_data", {}))
        self.prices = Prices(data.get("prices", {}))
        self.paint_data = PaintData(data.get("paint_data", {}))
        self.primer_data = PrimerData(data.get("primer_data", {}))
        self.powder_data = PowderData(data.get("powder_data", {}))
        self.workspace_data = WorkspaceData(data.get("workspace_data", {}), self.workspace_settings)

        category_names = set(data.get("categories", []))
        self.categories = [category for category in self.laser_cut_inventory.get_categories() if category.name in category_names]

        self.category_quantities: dict[Category, float] = {}
        for name, qty in data.get("category_quantities", {}).items():
            if category := self.laser_cut_inventory.get_category(name):
                self.category_quantities[category] = qty

        self.paint_data.paint_item = self.paint_inventory.get_paint(self.paint_data.paint_name)
        self.primer_data.primer_item = self.paint_inventory.get_primer(self.primer_data.primer_name)
        self.powder_data.powder_item = self.paint_inventory.get_powder(self.powder_data.powder_name)

        if flowtag := self.workspace_data.flowtag:
            if flowtag_data := self.workspace_data.flowtag_data:
                if tag := flowtag.get_tag_with_similar_name("laser"):
                    flowtag_data.set_tag_data(tag, "expected_time_to_complete", int(self.meta_data.machine_time * 60))
                elif tag := flowtag.get_tag_with_similar_name("picking"):
                    flowtag_data.set_tag_data(tag, "expected_time_to_complete", self.meta_data.weight)

        # NOTE Only for Quote Generator and load_nest.py
        self.recut_count_notes: int = 0
        self.nest: Nest | None = None

        # self.load_data(data)

    @property
    def bending_files(self) -> list[str]:
        return self.workspace_data.bending_files

    @property
    def welding_files(self) -> list[str]:
        return self.workspace_data.welding_files

    @property
    def cnc_milling_files(self) -> list[str]:
        return self.workspace_data.cnc_milling_files

    def get_first_tag_index_with_similar_keyword(self, keywords: list[str]) -> int:
        for index in range(len(self.workspace_data.flowtag.tags) - 1, -1, -1):
            tag_name = self.workspace_data.flowtag.tags[index].name.lower()
            if any(keyword in tag_name for keyword in keywords):
                return index
        return 0

    def mark_as_recoat(self):
        return
        if current_tag := self.get_current_tag():
            self.timer.stop(current_tag)
            self.current_flow_tag_index = self.get_first_tag_index_with_similar_keyword(["powder", "coating", "liquid", "paint", "gloss", "prime"])
            self.current_flow_tag_status_index = 0
            self.recoat = True
            self.recoat_count += 1

    def unmark_as_recoat(self):
        self.recoat = False
        self.move_to_next_process()

    def mark_as_recut(self):
        return
        if current_tag := self.get_current_tag():
            self.timer.stop(current_tag)
            self.current_flow_tag_index = 0
            self.current_flow_tag_status_index = 0
            self.recut = True
            self.recut_count += 1

    def unmark_as_recut(self):
        self.recut = False
        self.move_to_next_process()

    def move_to_next_process(self):
        return
        if current_tag := self.get_current_tag():
            self.timer.stop(current_tag)
            if not self.is_process_finished():
                self.current_flow_tag_index += 1
                self.current_flow_tag_status_index = 0
                self.recut = False
                self.recoat = False
                self.timer.start(current_tag)

    def get_files(self, file_type: str) -> list[str]:
        files = getattr(self.workspace_data, file_type)
        all_files: set[str] = set(files)
        return list(all_files)

    def get_current_tag(self) -> Optional[Tag]:
        try:
            return self.workspace_data.flowtag.tags[self.current_flow_tag_index]
        except IndexError:
            return None

    def get_next_tag_name(self) -> str:
        try:
            return self.workspace_data.flowtag.tags[self.current_flow_tag_index + 1].name
        except IndexError:
            return "Done"

    def get_all_paints(self) -> str:
        name = ""
        if self.primer_data.uses_primer and self.primer_data.primer_item:
            name += f"{self.primer_data.primer_item.part_name}\n"
        if self.paint_data.uses_paint and self.paint_data.paint_item:
            name += f"{self.paint_data.paint_item.part_name}\n"
        if self.powder_data.uses_powder and self.powder_data.powder_item:
            name += f"{self.powder_data.powder_item.part_name}\n"
        return name

    def get_expected_time_to_complete(self) -> int:
        total_time: int = sum(self.workspace_data.flowtag_data.get_tag_data(tag, "expected_time_to_complete") for tag in self.workspace_data.flowtag_data.tags_data)
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
            if category_obj := self.laser_cut_inventory.get_category(category):
                return self.category_quantities[category_obj]
        elif isinstance(category, Category):
            return self.category_quantities[category]
        return 1.0

    def set_category_quantity(self, category: Union[str, Category], quantity: float) -> float:
        if isinstance(category, str):
            if category_obj := self.laser_cut_inventory.get_category(category):
                self.category_quantities[category_obj] = quantity
        elif isinstance(category, Category):
            self.category_quantities[category] = quantity
        return quantity

    def print_category_quantities(self) -> str:
        return "".join(f"{i + 1}. {category.name}: {self.get_category_quantity(category)}\n" for i, category in enumerate(self.categories))

    def calculate_machine_time_from_length(self, L: float) -> float:
        return 0.00001 * L**2 + 0.00389 * L + 0.25198

    def calculate_machine_time_from_length_and_piercing_points(self, L: float, P: float) -> float:
        return (
            0.00000 * L**3 + 0.00000 * L**2 * P + -0.00000 * L * P**2 + 0.00000 * P**3 + -0.00001 * L**2 + -0.00010 * L * P + 0.00011 * P**2 + 0.00816 * L + 0.01222 * P + 0.04308
        )

    def calculate_piercing_time(self, L: float, P: float) -> float:
        return 0.00000 * L**2 * P + -0.00000 * L * P**2 + 0.00000 * P**3 + -0.00010 * L * P + 0.00011 * P**2 + 0.01222 * P

    def calculate_weight(self) -> float:
        if pounds_per_square_foot := self.sheet_settings.get_pounds_per_square_foot(self.meta_data.material, self.meta_data.gauge):
            pounds_per_square_inch = pounds_per_square_foot / 144  # convert lb/ft² → lb/in²
            return self.meta_data.surface_area * pounds_per_square_inch
        return 0.0

    def load_dxf_settings(self, dxf_analyzer: DxfAnalyzer):
        self.meta_data.surface_area = dxf_analyzer.get_cutting_area()
        self.meta_data.cutting_length = dxf_analyzer.get_cutting_length()
        self.meta_data.piercing_points = dxf_analyzer.get_piercing_points()
        dimensions = dxf_analyzer.get_dimensions()
        self.meta_data.part_dim = f"{dimensions['length']} x {dimensions['width']}"
        self.meta_data.piercing_time = self.calculate_piercing_time(self.meta_data.cutting_length, self.meta_data.piercing_points)
        self.meta_data.machine_time = self.calculate_machine_time_from_length_and_piercing_points(self.meta_data.cutting_length, self.meta_data.piercing_points)
        self.meta_data.weight = self.calculate_weight()

    def load_part_data(self, data: MetaDataDict):
        """Only updates part information from nest files."""
        self.meta_data.machine_time = data.get("machine_time", 0.0)
        self.meta_data.weight = data.get("weight", 0.0)
        self.meta_data.part_number = data.get("part_number", "")
        self.meta_data.image_index = data.get("image_index", "")
        self.meta_data.surface_area = data.get("surface_area", 0.0)
        self.meta_data.cutting_length = data.get("cutting_length", 0.0)
        self.meta_data.file_name = data.get("file_name", "")
        self.meta_data.piercing_time = data.get("piercing_time", 0.0)
        self.meta_data.piercing_points = data.get("piercing_points", 0)
        self.meta_data.gauge = data.get("gauge", "")
        self.meta_data.material = data.get("material", "")
        self.meta_data.sheet_dim = data.get("sheet_dim", "")
        self.meta_data.part_dim = data.get("part_dim", "")
        self.meta_data.geofile_name = data.get("geofile_name", "")
        self.meta_data.quantity_on_sheet = data.get("quantity_on_sheet", 0)

    def get_copy(self) -> "LaserCutPart":
        return copy.deepcopy(self)

    def to_dict(self) -> LaserCutPartDict:
        return {
            "id": self.id,
            "name": self.name,
            "categories": [category.name for category in self.categories],
            "category_quantities": {category.name: self.category_quantities.get(category, 1.0) for category in self.categories},
            "inventory_data": self.inventory_data.to_dict(),
            "meta_data": self.meta_data.to_dict(),
            "prices": self.prices.to_dict(),
            "paint_data": self.paint_data.to_dict(),
            "primer_data": self.primer_data.to_dict(),
            "powder_data": self.powder_data.to_dict(),
            "workspace_data": self.workspace_data.to_dict(),
        }
