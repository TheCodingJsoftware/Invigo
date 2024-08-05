import copy
from typing import TYPE_CHECKING, Optional, Union

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.paint import Paint
from utils.inventory.powder import Powder
from utils.inventory.primer import Primer
from utils.workspace.flow_tag import FlowTag
from utils.workspace.tag import Tag
from utils.workspace.workspace_settings import WorkspaceSettings
from utils.workspace.workspace_timer import WorkspaceTimer

if TYPE_CHECKING:
    from utils.workspace.job import Job


class Assembly:
    def __init__(self, assembly_data: dict[str, object], job):
        self.job: Job = job

        self.name = ""
        self.color = ""
        self.paint_inventory = self.job.job_manager.paint_inventory
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

        self.starting_date: str = ""
        self.ending_date: str = ""
        self.expected_time_to_complete: float = 0.0
        self.flow_tag: FlowTag = None
        self.current_flow_tag_index: int = 0
        self.current_flow_tag_status_index: int = 0
        self.assembly_image: str = None
        self.quantity: int = 1

        self.timer: WorkspaceTimer = None

        # NOTE Non serializable variables
        self.workspace_settings: WorkspaceSettings = self.job.workspace_settings

        self.load_data(assembly_data)

    def is_assembly_finished(self) -> bool:
        return self.current_flow_tag_index >= len(self.flow_tag.tags)

    def move_to_next_process(self):
        self.timer.stop(self.get_current_tag())
        if not self.is_assembly_finished():
            self.current_flow_tag_index += 1
            self.current_flow_tag_status_index = 0
            self.recut = False
            self.timer.start(self.get_current_tag())

    def all_laser_cut_parts_complete(self) -> bool:
        for laser_cut_part in self.laser_cut_parts:
            if not laser_cut_part.is_process_finished():
                return False
        return True

    def all_sub_assemblies_complete(self) -> bool:
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
            return self.flow_tag.tags[self.current_flow_tag_index]
        except IndexError:
            return None

    def get_all_paints(self) -> str:
        name = ""
        if self.uses_primer and self.primer_item:
            name += f"{self.primer_item.name}\n"
        if self.uses_paint and self.paint_item:
            name += f"{self.paint_item.name}\n"
        if self.uses_powder and self.powder_item:
            name += f"{self.powder_item.name}\n"
        return name

    def get_weight(self) -> float:
        weight: float = 0.0
        for laser_cut_part in self.laser_cut_parts:
            weight += laser_cut_part.weight
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

    def get_sub_assemblies(self) -> list["Assembly"]:
        return self.sub_assemblies

    def get_sub_assembly(self, assembly_name: str) -> "Assembly":
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

    def load_settings(self, data: dict[str, Union[float, bool, str, dict]]):
        assembly_data = data.get("assembly_data", {})
        self.name = assembly_data.get("name", "Assembly")
        self.starting_date: str = assembly_data.get("starting_date", "")
        self.expected_time_to_complete: float = assembly_data.get("expected_time_to_complete", 0.0)
        self.ending_date: str = assembly_data.get("ending_date", "")
        self.flow_tag = FlowTag("", assembly_data.get("flow_tag", {}), self.workspace_settings)
        self.current_flow_tag_index = assembly_data.get("current_flow_tag_index", 0)
        self.current_flow_tag_status_index = assembly_data.get("current_flow_tag_status_index", 0)
        self.assembly_image: str = assembly_data.get("assembly_image")
        self.assembly_files: list[str] = assembly_data.get("assembly_files", [])
        self.quantity: int = assembly_data.get("quantity", 1)
        self.color = assembly_data.get("color", "#3daee9")
        # If deepcopy is not done, than a reference is kept in the original object it was copied from
        # and then it messes everything up, specifically it will mess up laser cut parts
        # when you add a job to workspace
        self.timer = WorkspaceTimer(copy.deepcopy(assembly_data.get("timer", {})), self.flow_tag)

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

    def load_data(self, data: dict[str, Union[float, bool, str, dict]]):
        self.load_settings(data)

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

        self.sub_assemblies.clear()
        sub_assemblies = data.get("sub_assemblies", [])
        for sub_assembly_data in sub_assemblies:
            sub_assembly = Assembly(sub_assembly_data, self.job)
            self.sub_assemblies.append(sub_assembly)

    def to_dict(self) -> dict[str, dict[str, Union[list[dict[str, object]], object]]]:
        return {
            "assembly_data": {
                "name": self.name,
                "color": self.color,
                "starting_date": self.starting_date,
                "expected_time_to_complete": self.expected_time_to_complete,
                "ending_date": self.ending_date,
                "assembly_image": self.assembly_image,
                "quantity": self.quantity,
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
                "assembly_files": self.assembly_files,
                "flow_tag": self.flow_tag.to_dict(),
                "current_flow_tag_index": self.current_flow_tag_index,
                "current_flow_tag_status_index": self.current_flow_tag_status_index,
                "timer": self.timer.to_dict(),
            },
            "laser_cut_parts": [laser_cut_part.to_dict() for laser_cut_part in self.laser_cut_parts],
            "components": [component.to_dict() for component in self.components],
            "sub_assemblies": [sub_assembly.to_dict() for sub_assembly in self.sub_assemblies],
        }
