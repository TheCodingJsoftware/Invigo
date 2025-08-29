import dataclasses
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Optional, TypedDict, cast

from utils.inventory.angle_bar import AngleBar
from utils.inventory.component import Component, ComponentDict
from utils.inventory.dom_round_tube import DOMRoundTube
from utils.inventory.flat_bar import FlatBar
from utils.inventory.laser_cut_part import LaserCutPart, LaserCutPartDict
from utils.inventory.paint import PaintData, PaintDataDict
from utils.inventory.pipe import Pipe
from utils.inventory.powder import PowderData, PowderDataDict
from utils.inventory.primer import PrimerData, PrimerDataDict
from utils.inventory.rectangular_bar import RectangularBar
from utils.inventory.rectangular_tube import RectangularTube
from utils.inventory.round_bar import RoundBar
from utils.inventory.round_tube import RoundTube
from utils.workspace.flowtag import Flowtag, FlowtagDict
from utils.workspace.flowtag_data import FlowtagData, FlowtagDataDict
from utils.workspace.tag import Tag
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from utils.workspace.job import Job


class PricesDict(TypedDict):
    cost_for_paint: float
    cost_for_primer: float
    cost_for_powder_coating: float


@dataclass
class Prices:
    cost_for_paint: float = 0.0
    cost_for_primer: float = 0.0
    cost_for_powder_coating: float = 0.0

    def __init__(self, data: Optional[PricesDict]):
        for f in fields(self.__class__):
            if f.default is not dataclasses.MISSING:
                setattr(self, f.name, f.default)
            elif f.default_factory is not dataclasses.MISSING:
                setattr(self, f.name, f.default_factory())

        if data:
            for f in fields(self.__class__):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PricesDict:
        return cast(PricesDict, {f.name: getattr(self, f.name) for f in fields(self)})


class MetaDataDict(TypedDict):
    assembly_image: str
    not_part_of_process: bool
    quantity: int
    color: str


@dataclass
class MetaData:
    assembly_image: str = ""
    not_part_of_process: bool = False
    has_serial_number: bool = False
    quantity: int = 1
    color: str = ""

    def __init__(self, data: Optional[MetaDataDict]):
        for f in fields(self.__class__):
            if f.default is not dataclasses.MISSING:
                setattr(self, f.name, f.default)
            elif f.default_factory is not dataclasses.MISSING:
                setattr(self, f.name, f.default_factory())

        if data:
            for f in fields(self.__class__):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> MetaDataDict:
        return cast(MetaDataDict, {f.name: getattr(self, f.name) for f in fields(self)})


class WorkspaceDataDict(TypedDict):
    starting_date: str
    ending_date: str
    expected_time_to_complete: int
    assembly_files: list[str]
    flow_tag: FlowtagDict
    flow_tag_data: FlowtagDataDict


@dataclass
class WorkspaceData:
    starting_date: str = ""
    ending_date: str = ""
    expected_time_to_complete: int = 0
    assembly_files: list[str] = field(default_factory=list)
    flowtag: Optional[Flowtag] = None
    flowtag_data: Optional[FlowtagData] = None

    def __init__(self, data: Optional[WorkspaceDataDict], workspace_settings: WorkspaceSettings):
        self.workspace_settings = workspace_settings

        for f in fields(self.__class__):
            if f.default is not dataclasses.MISSING:
                setattr(self, f.name, f.default)
            elif f.default_factory is not dataclasses.MISSING:
                setattr(self, f.name, f.default_factory())
            else:
                setattr(self, f.name, None)  # Fallback if no default

        if data:
            for f in fields(self.__class__):
                if f.name in ["flowtag", "flow_tag_data"]:
                    continue
                if f.name in data:
                    setattr(self, f.name, data[f.name])

        self.flowtag = Flowtag(data.get("flowtag", {}), self.workspace_settings)
        self.flowtag_data = FlowtagData(self.flowtag)
        self.flowtag_data.load_data(data.get("flow_tag_data", {}))

    def to_dict(self) -> WorkspaceDataDict:
        result: dict[str, Any] = {}
        for f in fields(self.__class__):
            value = getattr(self, f.name)
            result[f.name] = value.to_dict() if hasattr(value, "to_dict") else value
        return cast(WorkspaceDataDict, result)


class AssemblyDict(TypedDict):
    id: int
    name: str
    meta_data: MetaDataDict
    prices: PricesDict
    workspace_data: WorkspaceDataDict
    primer_data: PrimerDataDict
    paint_data: PaintDataDict
    powder_data: PowderDataDict
    laser_cut_parts: list[LaserCutPartDict]
    components: list[ComponentDict]
    # structural_steel_components: list[StructuralProfileDict]
    sub_assemblies: list["AssemblyDict"]


class Assembly:
    id: int
    name: str
    meta_data: MetaData
    workspace_data: WorkspaceData
    paint_data: PaintData
    primer_data: PrimerData
    powder_data: PowderData
    laser_cut_parts: list[LaserCutPart]
    components: list[Component]
    sub_assemblies: list["Assembly"]

    def __init__(self, assembly_data: AssemblyDict, job: "Job"):
        self.job = job

        self.workspace_settings: WorkspaceSettings = self.job.workspace_settings
        self.paint_inventory = self.job.job_manager.paint_inventory
        self.parent_assembly: "Assembly | None" = None

        self.id = assembly_data.get("id", -1)
        self.name = assembly_data.get("name", "")
        self.meta_data = MetaData(assembly_data.get("meta_data", {}))
        self.workspace_data = WorkspaceData(assembly_data.get("workspace_data", {}), self.workspace_settings)
        self.prices = Prices(assembly_data.get("prices", {}))
        self.primer_data = PrimerData(assembly_data.get("primer_data", {}))
        self.primer_data.primer_item = self.paint_inventory.get_primer(self.primer_data.primer_name)
        self.paint_data = PaintData(assembly_data.get("paint_data", {}))
        self.paint_data.paint_item = self.paint_inventory.get_paint(self.paint_data.paint_name)
        self.powder_data = PowderData(assembly_data.get("powder_data", {}))
        self.powder_data.powder_item = self.paint_inventory.get_powder(self.powder_data.powder_name)

        self.laser_cut_parts: list[LaserCutPart] = []
        self.components: list[Component] = []
        self.structural_steel_items: list[Pipe | RectangularBar | AngleBar | FlatBar | RoundBar | RectangularTube | RoundTube | DOMRoundTube] = []
        self.sub_assemblies: list[Assembly] = []

        # self.current_flow_tag_index = 0
        # self.current_flow_tag_status_index = 0

        self.load_data(assembly_data)

    def is_assembly_finished(self) -> bool:
        return
        return self.current_flow_tag_index >= len(self.workspace_data.flowtag.tags)

    def move_to_next_process(self):
        return
        self.timer.stop(self.get_current_tag())
        if not self.is_assembly_finished():
            self.current_flow_tag_index += 1
            self.current_flow_tag_status_index = 0
            self.timer.start(self.get_current_tag())

    def all_laser_cut_parts_complete(self) -> bool:
        return
        for laser_cut_part in self.laser_cut_parts:
            if not laser_cut_part.is_process_finished():
                return False
        return True

    def all_sub_assemblies_complete(self) -> bool:
        return
        for sub_assembly in self.sub_assemblies:
            if not sub_assembly.is_assembly_finished():
                return False
        return True

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.append(laser_cut_part)

    def remove_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.remove(laser_cut_part)

    def add_component(self, component: Component):
        self.components.append(component)

    def remove_component(self, component: Component):
        self.components.remove(component)

    def get_current_tag(self) -> Optional[Tag]:
        try:
            return self.workspace_data.flowtag.tags[self.current_flow_tag_index]
        except IndexError:
            return None

    def get_all_paints(self) -> str:
        name = ""
        if self.primer_data.uses_primer and self.primer_data.primer_item:
            name += f"{self.primer_data.primer_item.part_name}\n"
        if self.paint_data.uses_paint and self.paint_data.paint_item:
            name += f"{self.paint_data.paint_item.part_name}\n"
        if self.powder_data.uses_powder and self.powder_data.powder_item:
            name += f"{self.powder_data.powder_item.part_name}\n"
        return name

    def get_weight(self) -> float:
        weight: float = 0.0
        for laser_cut_part in self.laser_cut_parts:
            weight += laser_cut_part.meta_data.weight
        return weight

    def get_master_assembly(self) -> "Assembly":
        master_assembly = self
        while master_assembly.parent_assembly is not None:
            master_assembly = master_assembly.parent_assembly
        return master_assembly

    def add_sub_assembly(self, assembly: "Assembly"):
        assembly.parent_assembly = self
        assembly.job = self.job
        self.sub_assemblies.append(assembly)

    def remove_sub_assembly(self, assembly) -> "Assembly":
        self.sub_assemblies.remove(assembly)
        return assembly

    def get_sub_assemblies(self) -> list["Assembly"]:
        return self.sub_assemblies

    def get_sub_assembly(self, assembly_name: str) -> "Assembly | None":
        return next(
            (sub_assembly for sub_assembly in self.sub_assemblies if sub_assembly.name == assembly_name),
            None,
        )

    def rename(self, new_name: str):
        self.name = new_name

    def get_all_sub_assemblies(self) -> list["Assembly"]:
        assemblies: list["Assembly"] = []
        assemblies.extend(self.sub_assemblies)
        for sub_assembly in self.sub_assemblies:
            assemblies.extend(sub_assembly.get_all_sub_assemblies())
        return assemblies

    def get_all_laser_cut_parts(self) -> list[LaserCutPart]:
        return self.laser_cut_parts + [part for sub_assembly in self.get_all_sub_assemblies() for part in sub_assembly.laser_cut_parts]

    def get_expected_time_to_complete(self) -> int:
        total_time: int = sum(laser_cut_part.get_expected_time_to_complete() * laser_cut_part.inventory_data.quantity for laser_cut_part in self.laser_cut_parts)
        if self.workspace_data.flowtag_data:
            for tag in self.workspace_data.flowtag_data.tags_data:
                if expected_time_to_complete := self.workspace_data.flowtag_data.get_tag_data(tag, "expected_time_to_complete"):
                    total_time += expected_time_to_complete
        for sub_assembly in self.sub_assemblies:
            total_time += sub_assembly.get_expected_time_to_complete()
        return total_time * self.meta_data.quantity

    def load_data(self, data):
        self.laser_cut_parts.clear()
        laser_cut_parts = data.get("laser_cut_parts", [])
        for laser_cut_part_data in laser_cut_parts:
            laser_cut_part = LaserCutPart(
                laser_cut_part_data,
                self.job.laser_cut_inventory,
            )
            self.add_laser_cut_part(laser_cut_part)

        self.components.clear()
        components = data.get("components", {})
        for component_data in components:
            component = Component(component_data, self.job.components_inventory)
            self.add_component(component)

        # self.structural_steel_items.clear()
        # structural_steel_components = data.get("structural_steel_components", [])
        # for structural_steel_component_data in structural_steel_components:
        #     if structural_steel_component_data.get("profile_type") == ProfilesTypes.RECTANGULAR_BAR.value:
        #         structural_steel_component = RectangularBar(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.ROUND_BAR.value:
        #         structural_steel_component = RoundBar(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.FLAT_BAR.value:
        #         structural_steel_component = FlatBar(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.ANGLE_BAR.value:
        #         structural_steel_component = AngleBar(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.RECTANGULAR_TUBE.value:
        #         structural_steel_component = RectangularTube(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.ROUND_TUBE.value:
        #         structural_steel_component = RoundTube(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.DOM_ROUND_TUBE.value:
        #         structural_steel_component = DOMRoundTube(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     elif structural_steel_component_data.get("profile_type") == ProfilesTypes.PIPE.value:
        #         structural_steel_component = Pipe(
        #             structural_steel_component_data,
        #             self.job.structural_steel_inventory,
        #         )
        #     else:
        #         continue
        # self.structural_steel_items.append(structural_steel_component)

        self.sub_assemblies.clear()
        sub_assemblies = data.get("sub_assemblies", [])
        for sub_assembly_data in sub_assemblies:
            sub_assembly = Assembly(sub_assembly_data, self.job)
            self.sub_assemblies.append(sub_assembly)

    def to_dict(self) -> AssemblyDict:
        return {
            "id": self.id,
            "name": self.name,
            "meta_data": self.meta_data.to_dict(),
            "prices": self.prices.to_dict(),
            "paint_data": self.paint_data.to_dict(),
            "primer_data": self.primer_data.to_dict(),
            "powder_data": self.powder_data.to_dict(),
            "workspace_data": self.workspace_data.to_dict(),
            "laser_cut_parts": [laser_cut_part.to_dict() for laser_cut_part in self.laser_cut_parts],
            "components": [component.to_dict() for component in self.components],
            # "structural_steel_components": [structural_steel_component.to_dict() for structural_steel_component in self.structural_steel_items],
            "sub_assemblies": [sub_assembly.to_dict() for sub_assembly in self.sub_assemblies],
        }
