import os

import msgspec
from natsort import natsorted

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager
from utils.workspace.workspace_settings import WorkspaceSettings
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup
from utils.workspace.workspace_filter import WorkspaceFilter


class Workspace:
    def __init__(self, workspace_settings: WorkspaceSettings, job_manager: JobManager) -> None:
        self.jobs: list[Job] = []

        self.filename: str = "workspace"
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"

        self.workspace_settings = workspace_settings
        self.job_manager = job_manager
        self.laser_cut_inventory = self.job_manager.laser_cut_inventory
        self.components_inventory = self.job_manager.components_inventory
        self.workspace_filter = WorkspaceFilter()

        # NOTE Non serialized variables
        self.grouped_components: list[Component] = []
        self.grouped_laser_cut_parts: list[LaserCutPart] = []

        self.__create_file()
        self.load_data()

    def deep_split_job_copy(self, job: Job) -> Job:
        new_job = Job({}, self.job_manager)
        new_job.load_settings(job.to_dict())
        self.copy_assemblies(job.assemblies, new_job)
        return new_job

    def copy_assemblies(self, assemblies: list[Assembly], job: Job):
        for assembly in assemblies:
            for _ in range(int(assembly.quantity)):
                new_assembly = Assembly({}, job)
                new_assembly.load_settings(assembly.to_dict())
                new_assembly.quantity = 1
                job.add_assembly(new_assembly)
                if assembly.laser_cut_parts:
                    self.copy_laser_cut_parts(assembly.laser_cut_parts, new_assembly)
                if assembly.components:
                    self.copy_components(assembly.components, new_assembly)
                if assembly.sub_assemblies:
                    self.copy_assemblies(assembly.sub_assemblies, job)

    def copy_components(self, components: list[Component], assembly: Assembly):
        for component in components:
            new_component = Component(component.to_dict(), self.components_inventory)
            assembly.add_component(new_component)

    def copy_laser_cut_parts(self, laser_cut_parts: list[LaserCutPart], assembly: Assembly):
        for part in laser_cut_parts:
            for _ in range(int(part.quantity)):
                new_part = LaserCutPart(part.to_dict(), self.laser_cut_inventory)
                new_part.quantity = 1
                assembly.add_laser_cut_part(new_part)

    def add_job(self, job: Job):
        new_job = self.deep_split_job_copy(job)
        self.jobs.append(new_job)

    def remove_job(self, job: Job):
        self.jobs.remove(job)

    def get_job(self, job_name: str) -> Job:
        return next((job for job in self.jobs if job.name == job_name), None)

    def get_filtered_assemblies(self, job: Job) -> list[Assembly]:
        assemblies: list[Assembly] = []
        for assembly in job.get_all_assemblies():
            if assembly.is_process_finished():
                continue
            if not assembly.all_laser_cut_parts_complete():
                continue
            if current_tag := assembly.get_current_tag():
                if current_tag.name != self.workspace_filter.current_tag:
                    continue
            if self.workspace_filter.search_text.lower() not in assembly.name.lower():
                continue

            assemblies.append(assembly)
        return assemblies

    def get_filtered_parts(self, job: Job) -> list[LaserCutPart]:
        parts: list[LaserCutPart] = []
        for laser_cut_part in job.get_all_laser_cut_parts():
            if laser_cut_part.is_process_finished():
                continue
            if laser_cut_part.recut:
                continue
            if current_tag := laser_cut_part.get_current_tag():
                if current_tag.name != self.workspace_filter.current_tag:
                    continue
            search_text = self.workspace_filter.search_text.lower()
            paint_text = laser_cut_part.get_all_paints().lower()
            if search_text:
                name_match = search_text in laser_cut_part.name.lower()
                material_match = search_text in f"{laser_cut_part.gauge} {laser_cut_part.material}".lower()
                paint_match = search_text in paint_text

                if not (name_match or material_match or paint_match):
                    continue

            parts.append(laser_cut_part)
        return parts

    def get_grouped_laser_cut_parts(self, laser_cut_parts: list[LaserCutPart]) -> list[WorkspaceLaserCutPartGroup]:
        grouped_laser_cut_parts: list[WorkspaceLaserCutPartGroup] = []
        parts_group: dict[str, WorkspaceLaserCutPartGroup] = {}
        for laser_cut_part in laser_cut_parts:
            if group := parts_group.get(laser_cut_part.name):
                group.add_laser_cut_part(laser_cut_part)
            else:
                group = WorkspaceLaserCutPartGroup()
                group.add_laser_cut_part(laser_cut_part)
                grouped_laser_cut_parts.append(group)
                parts_group.update({laser_cut_part.name: group})
        return grouped_laser_cut_parts

    def to_list(self) -> list[dict[str, object]]:
        return [job.to_dict() for job in self.jobs]

    def __create_file(self) -> None:
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.filename}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "w", encoding="utf-8") as json_file:
                json_file.write("[]")

    def save(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_list()))

    def load_data(self) -> None:
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: list[dict[str, object]] = msgspec.json.decode(file.read())
        except msgspec.DecodeError:
            return

        self.jobs.clear()

        for job_data in data:
            job = Job(job_data, self.job_manager)
            self.jobs.append(job)
