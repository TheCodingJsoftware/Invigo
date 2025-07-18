import copy
from ast import In
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Optional, TypedDict, Union, cast

from utils.dxf_analyzer import DxfAnalyzer
from utils.inventory import categories, inventory
from utils.inventory.category import Category
from utils.inventory.coating_item import CoatingItem
from utils.inventory.inventory_item import InventoryItem
from utils.inventory.paint import Paint
from utils.inventory.powder import Powder
from utils.inventory.primer import Primer
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workspace.flowtag import Flowtag, FlowtagDict
from utils.workspace.flowtag_data import FlowtagData, FlowtagDataDict
from utils.workspace.flowtag_timer import FlowtagTimer
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


class PaintDataDict(TypedDict):
    uses_paint: bool
    paint_name: str
    paint_item: Paint | None
    paint_overspray: float


@dataclass
class PaintData:
    uses_paint: bool = False
    paint_name: str = ""
    paint_item: Optional[CoatingItem] = None
    paint_overspray: float = 66.67

    def __init__(self, data: Optional[PaintDataDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PaintDataDict:
        return cast(PaintDataDict, {f.name: getattr(self, f.name) for f in fields(self)})


class PrimerDataDict(TypedDict):
    uses_primer: bool
    primer_name: str
    primer_item: Primer | None
    primer_overspray: float


@dataclass
class PrimerData:
    uses_primer: bool = False
    primer_name: str = ""
    primer_item: Optional[CoatingItem] = None
    primer_overspray: float = 66.67

    def __init__(self, data: Optional[PrimerDataDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PrimerDataDict:
        return cast(PrimerDataDict, {f.name: getattr(self, f.name) for f in fields(self)})


class PowderDataDict(TypedDict):
    uses_powder: bool
    powder_name: str
    powder_item: Powder | None
    powder_transfer_efficiency: float


@dataclass
class PowderData:
    uses_powder: bool = False
    powder_name: str = ""
    powder_item: Optional[CoatingItem] = None
    powder_transfer_efficiency: float = 66.67

    def __init__(self, data: Optional[PowderDataDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PowderDataDict:
        return cast(PowderDataDict, {f.name: getattr(self, f.name) for f in fields(self)})


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

    def __init__(
        self,
        data: LaserCutPartDict,
        laser_cut_inventory: "LaserCutInventory",
    ):
        super().__init__()

        self.laser_cut_inventory = laser_cut_inventory
        self.paint_inventory: PaintInventory = self.laser_cut_inventory.paint_inventory
        self.workspace_settings: WorkspaceSettings = self.laser_cut_inventory.workspace_settings
        self.sheet_settings: SheetSettings = self.laser_cut_inventory.sheet_settings

        self.id = data.get("id", -1)
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

        self.paint_item = self.paint_inventory.get_paint(self.paint_data.paint_name)
        self.primer_item = self.paint_inventory.get_primer(self.primer_data.primer_name)
        self.powder_item = self.paint_inventory.get_powder(self.powder_data.powder_name)

        if flowtag := self.flowtag:
            if flowtag_data := self.flowtag_data:
                if tag := flowtag.get_tag_with_similar_name("laser"):
                    flowtag_data.set_tag_data(tag, "expected_time_to_complete", int(self.machine_time * 60))
                elif tag := flowtag.get_tag_with_similar_name("picking"):
                    flowtag_data.set_tag_data(tag, "expected_time_to_complete", self.weight)

        # NOTE Only for Quote Generator and load_nest.py
        self.recut_count_notes: int = 0
        self.nest: Nest | None = None

        # self.load_data(data)

    @property
    def quantity(self) -> int:
        return self.inventory_data.quantity

    @quantity.setter
    def quantity(self, value: int):
        self.inventory_data.quantity = value

    @property
    def red_quantity_limit(self) -> int:
        return self.inventory_data.red_quantity_limit

    @red_quantity_limit.setter
    def red_quantity_limit(self, value: int):
        self.inventory_data.red_quantity_limit = value

    @property
    def yellow_quantity_limit(self) -> int:
        return self.inventory_data.yellow_quantity_limit

    @yellow_quantity_limit.setter
    def yellow_quantity_limit(self, value: int):
        self.inventory_data.yellow_quantity_limit = value

    @property
    def machine_time(self) -> float:
        return self.meta_data.machine_time

    @machine_time.setter
    def machine_time(self, value: float):
        self.meta_data.machine_time = value

    @property
    def weight(self) -> float:
        return self.meta_data.weight

    @weight.setter
    def weight(self, value: float):
        self.meta_data.weight = value

    @property
    def part_number(self) -> str:
        return self.meta_data.part_number

    @part_number.setter
    def part_number(self, value: str):
        self.meta_data.part_number = value

    @property
    def image_index(self) -> str:
        return self.meta_data.image_index

    @image_index.setter
    def image_index(self, value: str):
        self.meta_data.image_index = value

    @property
    def surface_area(self) -> float:
        return self.meta_data.surface_area

    @surface_area.setter
    def surface_area(self, value: float):
        self.meta_data.surface_area = value

    @property
    def cutting_length(self) -> float:
        return self.meta_data.cutting_length

    @cutting_length.setter
    def cutting_length(self, value: float):
        self.meta_data.cutting_length = value

    @property
    def file_name(self) -> str:
        return self.meta_data.file_name

    @file_name.setter
    def file_name(self, value: str):
        self.meta_data.file_name = value

    @property
    def piercing_time(self) -> float:
        return self.meta_data.piercing_time

    @piercing_time.setter
    def piercing_time(self, value: float):
        self.meta_data.piercing_time = value

    @property
    def piercing_points(self) -> int:
        return self.meta_data.piercing_points

    @piercing_points.setter
    def piercing_points(self, value: int):
        self.meta_data.piercing_points = value

    @property
    def gauge(self) -> str:
        return self.meta_data.gauge

    @gauge.setter
    def gauge(self, value: str):
        self.meta_data.gauge = value

    @property
    def material(self) -> str:
        return self.meta_data.material

    @material.setter
    def material(self, value: str):
        self.meta_data.material = value

    @property
    def shelf_number(self) -> str:
        return self.meta_data.shelf_number

    @shelf_number.setter
    def shelf_number(self, value: str):
        self.meta_data.shelf_number = value

    @property
    def sheet_dim(self) -> str:
        return self.meta_data.sheet_dim

    @sheet_dim.setter
    def sheet_dim(self, value: str):
        self.meta_data.sheet_dim = value

    @property
    def part_dim(self) -> str:
        return self.meta_data.part_dim

    @part_dim.setter
    def part_dim(self, value: str):
        self.meta_data.part_dim = value

    @property
    def geofile_name(self) -> str:
        return self.meta_data.geofile_name

    @geofile_name.setter
    def geofile_name(self, value: str):
        self.meta_data.geofile_name = value

    @property
    def modified_date(self) -> str:
        return self.meta_data.modified_date

    @modified_date.setter
    def modified_date(self, value: str):
        self.meta_data.modified_date = value

    @property
    def bend_hits(self) -> int:
        return self.meta_data.bend_hits

    @bend_hits.setter
    def bend_hits(self, value: int):
        self.meta_data.bend_hits = value

    @property
    def notes(self) -> str:
        return self.meta_data.notes

    @notes.setter
    def notes(self, value: str):
        self.meta_data.notes = value

    @property
    def quantity_on_sheet(self) -> int:
        return self.meta_data.quantity_on_sheet

    @quantity_on_sheet.setter
    def quantity_on_sheet(self, value: int):
        self.meta_data.quantity_on_sheet = value

    @property
    def price(self) -> float:
        return self.prices.price

    @price.setter
    def price(self, value: float):
        self.prices.price = value

    @property
    def cost_of_goods(self) -> float:
        return self.prices.cost_of_goods

    @cost_of_goods.setter
    def cost_of_goods(self, value: float):
        self.prices.cost_of_goods = value

    @property
    def bend_cost(self) -> float:
        return self.prices.bend_cost

    @bend_cost.setter
    def bend_cost(self, value: float):
        self.prices.bend_cost = value

    @property
    def labor_cost(self) -> float:
        return self.prices.labor_cost

    @labor_cost.setter
    def labor_cost(self, value: float):
        self.prices.labor_cost = value

    @property
    def cost_for_paint(self) -> float:
        return self.prices.cost_for_paint

    @cost_for_paint.setter
    def cost_for_paint(self, value: float):
        self.prices.cost_for_paint = value

    @property
    def cost_for_primer(self) -> float:
        return self.prices.cost_for_primer

    @cost_for_primer.setter
    def cost_for_primer(self, value: float):
        self.prices.cost_for_primer = value

    @property
    def cost_for_powder_coating(self) -> float:
        return self.prices.cost_for_powder_coating

    @cost_for_powder_coating.setter
    def cost_for_powder_coating(self, value: float):
        self.prices.cost_for_powder_coating = value

    @property
    def matched_to_sheet_cost_price(self) -> float:
        return self.prices.matched_to_sheet_cost_price

    @matched_to_sheet_cost_price.setter
    def matched_to_sheet_cost_price(self, value: float):
        self.prices.matched_to_sheet_cost_price = value

    @property
    def uses_paint(self) -> bool:
        return self.paint_data.uses_paint

    @uses_paint.setter
    def uses_paint(self, value: bool):
        self.paint_data.uses_paint = value

    @property
    def paint_name(self) -> str:
        return self.paint_data.paint_name

    @paint_name.setter
    def paint_name(self, value: str):
        self.paint_data.paint_name = value

    @property
    def paint_item(self) -> Optional[CoatingItem]:
        return self.paint_data.paint_item

    @paint_item.setter
    def paint_item(self, value: Optional[CoatingItem]):
        self.paint_data.paint_item = value

    @property
    def paint_overspray(self) -> float:
        return self.paint_data.paint_overspray

    @paint_overspray.setter
    def paint_overspray(self, value: float):
        self.paint_data.paint_overspray = value

    @property
    def uses_primer(self) -> bool:
        return self.primer_data.uses_primer

    @uses_primer.setter
    def uses_primer(self, value: bool):
        self.primer_data.uses_primer = value

    @property
    def primer_name(self) -> str:
        return self.primer_data.primer_name

    @primer_name.setter
    def primer_name(self, value: str):
        self.primer_data.primer_name = value

    @property
    def primer_item(self) -> Optional[CoatingItem]:
        return self.primer_data.primer_item

    @primer_item.setter
    def primer_item(self, value: Optional[CoatingItem]):
        self.primer_data.primer_item = value

    @property
    def primer_overspray(self) -> float:
        return self.primer_data.primer_overspray

    @primer_overspray.setter
    def primer_overspray(self, value: float):
        self.primer_data.primer_overspray = value

    @property
    def uses_powder(self) -> bool:
        return self.powder_data.uses_powder

    @uses_powder.setter
    def uses_powder(self, value: bool):
        self.powder_data.uses_powder = value

    @property
    def powder_name(self) -> str:
        return self.powder_data.powder_name

    @powder_name.setter
    def powder_name(self, value: str):
        self.powder_data.powder_name = value

    @property
    def powder_item(self) -> Optional[CoatingItem]:
        return self.powder_data.powder_item

    @powder_item.setter
    def powder_item(self, value: Optional[CoatingItem]):
        self.powder_data.powder_item = value

    @property
    def powder_transfer_efficiency(self) -> float:
        return self.powder_data.powder_transfer_efficiency

    @powder_transfer_efficiency.setter
    def powder_transfer_efficiency(self, value: float):
        self.powder_data.powder_transfer_efficiency = value

    @property
    def bending_files(self) -> list:
        return self.workspace_data.bending_files

    @bending_files.setter
    def bending_files(self, value: list):
        self.workspace_data.bending_files = value

    @property
    def welding_files(self) -> list:
        return self.workspace_data.welding_files

    @welding_files.setter
    def welding_files(self, value: list):
        self.workspace_data.welding_files = value

    @property
    def cnc_milling_files(self) -> list:
        return self.workspace_data.cnc_milling_files

    @cnc_milling_files.setter
    def cnc_milling_files(self, value: list):
        self.workspace_data.cnc_milling_files = value

    @property
    def flowtag(self) -> Optional[Flowtag]:
        return self.workspace_data.flowtag

    @flowtag.setter
    def flowtag(self, value: Optional[Flowtag]):
        self.workspace_data.flowtag = value

    @property
    def flowtag_data(self) -> Optional[FlowtagData]:
        return self.workspace_data.flowtag_data

    @flowtag_data.setter
    def flowtag_data(self, value: Optional[FlowtagData]):
        self.workspace_data.flowtag_data = value

    def is_process_finished(self) -> bool:
        return self.current_flow_tag_index >= len(self.flowtag.tags)

    def get_first_tag_index_with_similar_keyword(self, keywords: list[str]) -> int:
        for index in range(len(self.flowtag.tags) - 1, -1, -1):
            tag_name = self.flowtag.tags[index].name.lower()
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
        files = getattr(self, file_type)
        all_files: set[str] = set(files)
        return list(all_files)

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
            name += f"{self.primer_item.part_name}\n"
        if self.uses_paint and self.paint_item:
            name += f"{self.paint_item.part_name}\n"
        if self.uses_powder and self.powder_item:
            name += f"{self.powder_item.part_name}\n"
        return name

    def get_expected_time_to_complete(self) -> int:
        total_time: int = sum(self.flowtag_data.get_tag_data(tag, "expected_time_to_complete") for tag in self.flowtag_data.tags_data)
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
        if pounds_per_square_foot := self.sheet_settings.get_pounds_per_square_foot(self.material, self.gauge):
            pounds_per_square_inch = pounds_per_square_foot / 144  # convert lb/ft² → lb/in²
            return self.surface_area * pounds_per_square_inch
        return 0.0

    def load_dxf_settings(self, dxf_analyzer: DxfAnalyzer):
        self.surface_area = dxf_analyzer.get_cutting_area()
        self.cutting_length = dxf_analyzer.get_cutting_length()
        self.piercing_points = dxf_analyzer.get_piercing_points()
        dimensions = dxf_analyzer.get_dimensions()
        self.part_dim = f"{dimensions['length']} x {dimensions['width']}"
        self.piercing_time = self.calculate_piercing_time(self.cutting_length, self.piercing_points)
        self.machine_time = self.calculate_machine_time_from_length_and_piercing_points(self.cutting_length, self.piercing_points)
        self.weight = self.calculate_weight()

    def load_part_data(self, data: dict):
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
        self.quantity_on_sheet = data.get("quantity_on_sheet", 0)

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


if __name__ == "__main__":
    from typing import get_type_hints

    def generate_properties(cls_name: str, source_attr: str):
        cls = globals()[cls_name]
        annotations = get_type_hints(cls)
        result = []
        for name, typ in annotations.items():
            result.extend(
                (
                    f"    @property\n    def {name}(self) -> {typ.__name__}:\n        return self.{source_attr}.{name}\n",
                    f"    @{name}.setter\n    def {name}(self, value: {typ.__name__}):\n        self.{source_attr}.{name} = value\n",
                )
            )
        return "\n".join(result)

    print(generate_properties("InventoryData", "inventory_data"))
    print(generate_properties("MetaData", "meta_data"))
    print(generate_properties("Prices", "prices"))
    print(generate_properties("PaintData", "paint_data"))
    print(generate_properties("PrimerData", "primer_data"))
    print(generate_properties("PowderData", "powder_data"))
    print(generate_properties("WorkspaceData", "workspace_data"))
