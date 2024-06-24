from enum import Enum, auto

from utils.components_inventory.component import Component
from utils.components_inventory.components_inventory import ComponentsInventory
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.sheet_settings import SheetSettings
from utils.workspace.assembly import Assembly
from utils.workspace.group import Group
from utils.workspace.nest import Nest
from utils.workspace.workspace_settings import WorkspaceSettings


class JobStatus(Enum):
    PLANNING = auto()
    QUOTING = auto()
    QUOTED = auto()
    TEMPLATE = auto()
    WORKSPACE = auto()
    ARCHIVE = auto()


class JobColor(Enum):
    PLANNING = ("#3daee9", JobStatus.PLANNING)
    QUOTING = ("#eabf3e", JobStatus.QUOTING)
    QUOTED = ("#eabf3e", JobStatus.QUOTED)
    TEMPLATE = ("#ea693e", JobStatus.TEMPLATE)
    WORKSPACE = ("#69ea3e", JobStatus.WORKSPACE)
    ARCHIVE = ("#943eea", JobStatus.ARCHIVE)

    @classmethod
    def get_color(cls, job_status):
        return next(
            (color.value[0] for color in cls if color.value[1] == job_status), None
        )

class Job:
    def __init__(self, name: str, data: dict, job_manager) -> None:
        self.name: str = name
        self.order_number: float = 0.0
        self.ship_to: str = ""
        self.date_shipped: str = ""
        self.date_expected: str = ""
        self.color: str = "#3daee9"  # default
        self.groups: list[Group] = []
        self.nests: list[Nest] = []
        from utils.workspace.job_manager import JobManager

        self.job_manager: JobManager = job_manager
        self.job_status = JobStatus.PLANNING

        # NOTE Non serialized variables
        self.sheet_settings: SheetSettings = self.job_manager.sheet_settings
        self.workspace_settings: WorkspaceSettings = self.job_manager.workspace_settings
        self.components_inventory: ComponentsInventory = self.job_manager.components_inventory
        self.laser_cut_inventory: LaserCutInventory = self.job_manager.laser_cut_inventory

        self.unsaved_changes = False
        self.downloaded_from_server = False

        self.load_data(data)

    def get_color(self):
        if self.job_status == JobStatus.PLANNING:
            return "#3daee9"
        elif self.job_status == JobStatus.TEMPLATE:
            return "#ea693e"
        elif self.job_status == JobStatus.QUOTING | JobStatus.QUOTED:
            return "#eabf3e"
        elif self.job_status == JobStatus.WORKSPACE:
            return "#69ea3e"
        elif self.job_status == JobStatus.ARCHIVE:
            return "#943eea"

    def changes_made(self):
        self.unsaved_changes = True

    def add_nest(self, nest: Nest):
        self.groups.append(nest)

    def remove_nest(self, nest: Nest):
        self.groups.remove(nest)

    def add_group(self, group: Group):
        self.groups.append(group)

    def remove_group(self, group: Group):
        self.groups.remove(group)

    def get_group(self, group_name: str) -> Group:
        return next((group for group in self.groups if group.name == group_name), None)

    def get_all_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        for group in self.groups:
            assemblies.extend(group.get_all_assemblies())
        return assemblies

    def get_all_laser_cut_parts(self) -> list[LaserCutPart]:
        laser_cut_parts: list[LaserCutPart] = []
        for assembly in self.get_all_assemblies():
            laser_cut_parts.extend(assembly.laser_cut_parts)
        return laser_cut_parts

    def get_all_components(self) -> list[Component]:
        components: list[Component] = []
        for assembly in self.get_all_assemblies():
            components.extend(assembly.components)
        return components

    def load_data(self, data: dict[str, dict[str, object]]):
        if not data:
            return

        job_data = data.get("job_data", {})
        self.order_number = job_data.get("order_number", 0.0)
        self.ship_to = job_data.get("ship_to", "")
        self.date_shipped = job_data.get("date_shipped", "")
        self.date_expected = job_data.get("date_expected", "")
        self.job_status = JobStatus(int(job_data.get("type", 0))) # Just in case we cast, trust me
        self.color = self.get_color()

        nests_data = data.get("nests", {})

        self.nests.clear()
        for nest_name, nest_data in nests_data.items():
            nest = Nest(nest_name, nest_data, self.sheet_settings, self.laser_cut_inventory)
            self.add_nest(nest)

        groups_data = data.get("groups", {})

        self.groups.clear()
        for group_name, group_data in groups_data.items():
            group = Group(group_name, group_data, self)
            self.add_group(group)

    def to_dict(self) -> dict:
        self.unsaved_changes = False

        for laser_cut_part in self.get_all_laser_cut_parts():
            if inventory_laser_cut_part := self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.name):
                inventory_laser_cut_part.bending_files = laser_cut_part.bending_files
                inventory_laser_cut_part.welding_files = laser_cut_part.welding_files
                inventory_laser_cut_part.cnc_milling_files = laser_cut_part.cnc_milling_files
                inventory_laser_cut_part.flow_tag = laser_cut_part.flow_tag
        self.laser_cut_inventory.save()

        for component in self.get_all_components():
            if inventory_component := self.components_inventory.get_component_by_name(component.name):
                inventory_component.image_path = component.image_path
        self.components_inventory.save()

        return {
            "job_data": {
                "type": self.job_status.value,
                "order_number": self.order_number,
                "ship_to": self.ship_to,
                "date_shipped": self.date_shipped,
                "date_expected": self.date_expected,
                "color": self.get_color(),
            },
            "nests": {nest.name: nest.to_dict() for nest in self.nests},
            "groups": {group.name: group.to_dict() for group in self.groups},
        }
