from enum import Enum

from utils.components_inventory.component import Component
from utils.components_inventory.components_inventory import ComponentsInventory
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.sheet_settings import SheetSettings
from utils.workspace.assembly import Assembly
from utils.workspace.group import Group
from utils.workspace.workspace_settings import WorkspaceSettings


class JobType(Enum):
    PLANNING = 0
    QUOTING = 1
    QUOTED = 2
    WORKSPACE = 3
    ARCHIVE = 4


class Job:
    def __init__(self, name: str, data: dict, job_manager) -> None:
        self.name: str = name
        self.order_number: float = 0.0
        self.ship_to: str = ""
        self.date_shipped: str = ""
        self.date_expected: str = ""
        self.groups: list[Group] = []
        from utils.workspace.job_manager import JobManager

        self.job_manager: JobManager = job_manager
        self.job_type = JobType.PLANNING

        # NOTE Non serialized variables
        self.sheet_settings: SheetSettings = self.job_manager.sheet_settings
        self.workspace_settings: WorkspaceSettings = self.job_manager.workspace_settings
        self.components_inventory: ComponentsInventory = self.job_manager.components_inventory
        self.laser_cut_inventory: LaserCutInventory = self.job_manager.laser_cut_inventory

        self.unsaved_changes = False
        self.downloaded_from_server = False

        self.load_data(data)

    def changes_made(self):
        self.unsaved_changes = True

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
        self.job_type = JobType(job_data.get("type", 0))

        groups_data = data.get("groups", {})

        self.groups.clear()
        for group_name, group_data in groups_data.items():
            group = Group(group_name, group_data, self)
            self.add_group(group)

    def to_dict(self) -> dict:
        self.unsaved_changes = False
        return {
            "job_data": {
                "type": self.job_type.value,
                "order_number": self.order_number,
                "ship_to": self.ship_to,
                "date_shipped": self.date_shipped,
                "date_expected": self.date_expected,
            },
            "groups": {group.name: group.to_dict() for group in self.groups},
        }
