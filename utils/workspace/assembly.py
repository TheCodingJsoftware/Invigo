import copy
from typing import TYPE_CHECKING, Any, Union

from utils.components_inventory.component import Component
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.paint_inventory.paint import Paint
from utils.paint_inventory.powder import Powder
from utils.paint_inventory.primer import Primer
from utils.workspace.flow_tag import FlowTag
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from utils.workspace.group import Group


class Assembly:
    def __init__(self, name: str, assembly_data: dict[str, object], group) -> None:
        self.name = name

        self.group: Group = group
        self.paint_inventory = self.group.job.job_manager.paint_inventory
        self.parent_assembly: "Assembly" = None
        self.assembly_files: list[str] = []
        self.laser_cut_parts: list[LaserCutPart] = []
        self.components: list[Component] = []
        self.sub_assemblies: list[Assembly] = []

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

        self.expected_time_to_complete: float = 0.0
        self.has_items: bool = False
        self.has_sub_assemblies: bool = False
        self.flow_tag: FlowTag = None
        self.assembly_image: str = None
        # NOTE Used by user workspace
        self.timers: dict[str, dict] = {}
        self.display_name: str = ""
        self.completed: bool = False
        self.starting_date: str = ""
        self.ending_date: str = ""
        self.status: str = None
        self.current_flow_state: int = 0
        self.date_completed: str = ""

        # NOTE Non serializable variables
        self.workspace_settings: WorkspaceSettings = self.group.workspace_settings
        self.show = True

        self.load_data(assembly_data)

    def set_parent_assembly_value(self, key: str, value: Any) -> None:
        if key == "show":
            self.show = value
            if self.parent_assembly is not None:
                self.parent_assembly.show = value

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.append(laser_cut_part)

    def remove_laser_cut_part(self, laser_cut_part: LaserCutPart):
        self.laser_cut_parts.remove(laser_cut_part)

    def add_component(self, component: Component):
        self.components.append(component)

    def remove_component(self, component: Component):
        self.components.remove(component)

    def get_current_flow_state(self) -> str:
        return self.flow_tag[self.current_flow_state]

    def get_master_assembly(self) -> "Assembly":
        master_assembly = self
        while master_assembly.parent_assembly is not None:
            master_assembly = master_assembly.parent_assembly
        return master_assembly

    def add_sub_assembly(self, assembly: "Assembly"):
        assembly.parent_assembly = self
        assembly.group = self.group
        self.sub_assemblies.append(assembly)

    def remove_sub_assembly(self, assembly) -> "Assembly":
        self.sub_assemblies.remove(assembly)

    def get_sub_assemblies(self) -> list["Assembly"]:
        return self.sub_assemblies

    def get_sub_assembly(self, assembly_name: str) -> "Assembly":
        return next(
            (sub_assembly for sub_assembly in self.sub_assemblies if sub_assembly.name == assembly_name),
            None,
        )

    def rename(self, new_name: str) -> None:
        self.name = new_name

    def get_all_sub_assemblies(self) -> list["Assembly"]:
        assemblies: list["Assembly"] = []
        assemblies.extend(self.sub_assemblies)
        for sub_assembly in self.sub_assemblies:
            assemblies.extend(sub_assembly.get_all_sub_assemblies())
        return assemblies

    def load_data(self, data: dict[str, Union[float, bool, str, dict]]):
        assembly_data = data.get("assembly_data", {})
        self.expected_time_to_complete: float = assembly_data.get("expected_time_to_complete", 0.0)
        self.has_items: bool = assembly_data.get("has_items", False)
        self.has_sub_assemblies: bool = assembly_data.get("has_sub_assemblies", True)
        self.flow_tag: FlowTag = FlowTag("", assembly_data.get("flow_tag", {}), self.workspace_settings)
        self.assembly_image: str = assembly_data.get("assembly_image")
        self.assembly_files: list[str] = assembly_data.get("assembly_files", [])

        self.uses_primer: bool = assembly_data.get("uses_primer", False)
        self.primer_name: str = assembly_data.get("primer_name")
        self.primer_overspray: float = assembly_data.get("primer_overspray", 66.67)
        if self.uses_primer and self.primer_name:
            self.primer_item = self.paint_inventory.get_primer(self.primer_name)
        self.cost_for_primer = assembly_data.get("cost_for_primer", 0.0)

        self.uses_paint: bool = assembly_data.get("uses_paint", False)
        self.paint_name: str = assembly_data.get("paint_name")
        self.paint_overspray: float = assembly_data.get("paint_overspray", 66.67)
        if self.uses_paint and self.paint_name:
            self.paint_item = self.paint_inventory.get_paint(self.paint_name)
        self.cost_for_paint = assembly_data.get("cost_for_paint", 0.0)

        self.uses_powder: bool = assembly_data.get("uses_powder_coating", False)
        self.powder_name: str = assembly_data.get("powder_name")
        self.powder_transfer_efficiency: float = assembly_data.get("powder_transfer_efficiency", 66.67)
        if self.uses_powder and self.powder_name:
            self.powder_item = self.paint_inventory.get_powder(self.powder_name)
        self.cost_for_powder_coating = assembly_data.get("cost_for_powder_coating", 0.0)

        # NOTE Used by user workspace
        self.timers: dict[str, dict[str, object]] = assembly_data.get("timers", {})
        self.display_name: str = assembly_data.get("display_name", "")
        self.completed: bool = assembly_data.get("completed", False)
        self.starting_date: str = assembly_data.get("starting_date", "")
        self.ending_date: str = assembly_data.get("ending_date", "")
        self.status: str = assembly_data.get("status")
        self.current_flow_state: int = assembly_data.get("current_flow_state", 0)
        self.date_completed: str = assembly_data.get("date_completed", "")

        self.laser_cut_parts.clear()
        laser_cut_parts = data.get("laser_cut_parts", {})
        for laser_cut_part_name, laser_cut_part_data in laser_cut_parts.items():
            laser_cut_part = LaserCutPart(laser_cut_part_name, laser_cut_part_data, self.group.job.laser_cut_inventory)
            self.add_laser_cut_part(laser_cut_part)

        self.components.clear()
        components = data.get("components", {})
        for component_name, component_data in components.items():
            component = Component(component_name, component_data, self.group.job.components_inventory)
            self.add_component(component)

        self.sub_assemblies.clear()
        sub_assemblies = data.get("sub_assemblies", {})
        for sub_assembly_name, sub_assembly_data in sub_assemblies.items():
            sub_assembly = Assembly(sub_assembly_name, sub_assembly_data, self.group)
            self.sub_assemblies.append(sub_assembly)

    def to_dict(self, processed_assemblies: set["Assembly"] = None) -> dict:
        if processed_assemblies is None:
            processed_assemblies = set()
        processed_assemblies.add(self)

        data = {
            "assembly_data": {
                "display_name": self.display_name,
                "expected_time_to_complete": self.expected_time_to_complete,
                "has_items": self.has_items,
                "has_sub_assemblies": self.has_sub_assemblies,
                "flow_tag": self.flow_tag.to_dict(),
                "assembly_image": self.assembly_image,
                "assembly_files": self.assembly_files,
                "timers": self.timers,
                "completed": self.completed,
                "starting_date": self.starting_date,
                "ending_date": self.ending_date,
                "status": self.status,
                "current_flow_state": self.current_flow_state,
                "date_completed": self.date_completed,
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
            },
            "laser_cut_parts": {},
            "components": {},
            "sub_assemblies": {},
        }

        for laser_cut_part in self.laser_cut_parts:
            data["laser_cut_parts"][laser_cut_part.name] = laser_cut_part.to_dict()

        for component in self.components:
            data["components"][component.name] = component.to_dict()

        for sub_assembly in self.sub_assemblies:
            if sub_assembly not in processed_assemblies:
                data["sub_assemblies"][sub_assembly.name] = sub_assembly.to_dict(processed_assemblies)

        return data

    def set_timer(self, flow_tag: str, time: object) -> None:
        self.timers[flow_tag]["time_to_complete"] = time.value()
