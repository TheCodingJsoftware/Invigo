import os

import msgspec
from natsort import natsorted

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager
from utils.workspace.workspace_settings import WorkspaceSettings


class Workspace:
    def __init__(self, workspace_settings: WorkspaceSettings, job_manager: JobManager) -> None:
        self.jobs: list[Job] = []

        self.filename: str = "workspace"
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"

        self.workspace_settings = workspace_settings
        self.job_manager = job_manager

        # NOTE Non serialized variables
        self.grouped_components: list[Component] = []
        self.grouped_laser_cut_parts: list[LaserCutPart] = []

        self.__create_file()
        self.load_data()

    def add_job(self, job: Job):
        self.jobs.append(job)

    def remove_job(self, job: Job):
        self.jobs.remove(job)

    def get_job(self, job_name: str) -> Job:
        return next((job for job in self.jobs if job.name == job_name), None)

    def group_laser_cut_parts(self):
        laser_cut_part_dict: dict[str, LaserCutPart] = {}
        for assembly in self.get_all_assemblies():
            for assembly_laser_cut_part in assembly.laser_cut_parts:
                unit_quantity = assembly_laser_cut_part.quantity
                new_laser_cut_part = LaserCutPart(assembly_laser_cut_part.to_dict(), self.laser_cut_inventory)
                new_laser_cut_part.quantity = unit_quantity * assembly.quantity

                if existing_component := laser_cut_part_dict.get(new_laser_cut_part.name):
                    existing_component.quantity += new_laser_cut_part.quantity
                else:
                    laser_cut_part_dict[new_laser_cut_part.name] = new_laser_cut_part
                # This is because we group the data, so all nest reference is lost.
                new_laser_cut_part.quantity_in_nest = None

        self.grouped_laser_cut_parts = laser_cut_part_dict.values()
        self.sort_laser_cut_parts()

    def sort_laser_cut_parts(self):
        self.grouped_laser_cut_parts = natsorted(self.grouped_laser_cut_parts, key=lambda laser_cut_part: laser_cut_part.name)

    def get_all_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        for job in self.jobs:
            assemblies.extend(job.get_all_assemblies())
        return assemblies

    def get_all_laser_cut_parts(self) -> list[LaserCutPart]:
        """Laser cut parts in all assemblies."""
        laser_cut_parts: list[LaserCutPart] = []
        for assembly in self.get_all_assemblies():
            laser_cut_parts.extend(assembly.laser_cut_parts)
        return laser_cut_parts

    def get_all_nested_laser_cut_parts(self) -> list[LaserCutPart]:
        laser_cut_parts: list[LaserCutPart] = []
        for job in self.jobs:
            laser_cut_parts.extend(job.get_all_nested_laser_cut_parts())
        return laser_cut_parts

    def get_grouped_laser_cut_parts(self) -> list[LaserCutPart]:
        self.group_laser_cut_parts()
        return self.grouped_laser_cut_parts

    def get_all_components(self) -> list[Component]:
        components: list[Component] = []
        for assembly in self.get_all_assemblies():
            components.extend(assembly.components)
        return components

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

        for job in data:
            for job_data in job:
                job = Job(job_data, self.job_manager)
                self.jobs.append(job)
