from typing import TYPE_CHECKING, Union

from utils.workspace.assembly import Assembly
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from utils.workspace.job import Job


class Group:
    def __init__(self, name: str, data: dict[str, dict[str, Union[str, dict[str, object]]]], job) -> None:
        self.name = name
        self.color: str = "#3daee9"  # default

        self.job: Job = job
        self.assemblies: list[Assembly] = []

        self.workspace_settings: WorkspaceSettings = self.job.workspace_settings

        self.load_data(data)

    def add_assembly(self, assembly: Assembly):
        self.assemblies.append(assembly)

    def remove_assembly(self, assembly: Assembly):
        self.assemblies.remove(assembly)

    def get_assembly(self, assembly_name: str) -> Assembly:
        return next(
            (assembly for assembly in self.assemblies if assembly.name == assembly_name),
            None,
        )

    def load_assembly(self, assembly_name: str, data: dict) -> Assembly:
        assembly = Assembly(assembly_name, data, self)
        for sub_assembly_name, sub_assembly_data in data["sub_assemblies"].items():
            self.load_assembly(sub_assembly_name, sub_assembly_data)
        return assembly

    def get_all_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        assemblies.extend(self.assemblies)
        for assembly in self.assemblies:
            assemblies.extend(assembly.get_all_sub_assemblies())
        return assemblies

    def load_data(self, data: dict[str, dict[str, dict]]):
        if not data:
            return

        group_data = data.get("group_data", {})
        assemblies = data.get("assemblies", {})

        self.color = group_data.get("color", "#3daee9")

        self.assemblies.clear()
        for assembly_name, assembly_data in assemblies.items():
            assembly = self.load_assembly(assembly_name, assembly_data)
            self.assemblies.append(assembly)

    def to_dict(self) -> dict:
        return {
            "group_data": {"color": self.color},
            "assemblies": {assembly.name: assembly.to_dict(set()) for assembly in self.assemblies},
        }
