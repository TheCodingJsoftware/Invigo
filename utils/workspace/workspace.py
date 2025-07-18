import os
from datetime import datetime, timedelta
from typing import Union

import msgspec

from config.environments import Environment
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager
from utils.workspace.workspace_assemply_group import WorkspaceAssemblyGroup
from utils.workspace.workspace_filter import SortingMethod, WorkspaceFilter
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup
from utils.workspace.workspace_settings import WorkspaceSettings


class Workspace:
    def __init__(
        self,
        workspace_settings: WorkspaceSettings,
        job_manager: JobManager,
        filename: str = "workspace",
    ):
        self.jobs: list[Job] = []

        self.filename = filename
        self.FOLDER_LOCATION = f"{Environment.DATA_PATH}/data"

        self.workspace_settings = workspace_settings
        self.job_manager = job_manager
        self.laser_cut_inventory = self.job_manager.laser_cut_inventory
        self.components_inventory = self.job_manager.components_inventory
        self.workspace_filter = WorkspaceFilter()

        # NOTE Non serialized variables
        self.grouped_components: list[Component] = []
        self.grouped_laser_cut_parts: list[LaserCutPart] = []

        # self.__create_file()
        # self.load_data()

    def deep_split_job_copy(self, job: Job) -> Job:
        new_job = Job({}, self.job_manager)
        new_job.load_settings(job.to_dict())
        new_job.flowtag_timeline = job.flowtag_timeline
        self.copy_assemblies(job.assemblies, new_job, job.ending_date)
        return new_job

    def copy_assemblies(
        self,
        assemblies: list[Assembly],
        parent: Union[Job, Assembly],
        job_ending_date: str,
    ):
        for assembly in assemblies:
            for _ in range(int(assembly.quantity)):
                new_assembly = Assembly({}, parent if isinstance(parent, Job) else parent.job)
                new_assembly.load_settings(assembly.to_dict())

                parent_starting_date = datetime.strptime(parent.starting_date, "%Y-%m-%d %I:%M %p")

                calculated_starting_date = parent_starting_date - timedelta(days=7.0)
                calculated_ending_date = calculated_starting_date + timedelta(days=assembly.expected_time_to_complete)

                new_assembly.starting_date = calculated_starting_date.strftime("%Y-%m-%d %I:%M %p")
                new_assembly.ending_date = calculated_ending_date.strftime("%Y-%m-%d %I:%M %p")

                new_assembly.quantity = 1

                if isinstance(parent, Job):
                    parent.add_assembly(new_assembly)
                else:
                    parent.add_sub_assembly(new_assembly)

                if assembly.laser_cut_parts:
                    self.copy_laser_cut_parts(assembly.laser_cut_parts, new_assembly)
                if assembly.components:
                    self.copy_components(assembly.components, new_assembly)
                if assembly.sub_assemblies:
                    self.copy_assemblies(assembly.sub_assemblies, new_assembly, job_ending_date)

    def copy_components(self, components: list[Component], assembly: Assembly):
        for component in components:
            new_component = Component(component.to_dict(), self.components_inventory)
            assembly.add_component(new_component)

    def copy_laser_cut_parts(self, laser_cut_parts: list[LaserCutPart], assembly: Assembly):
        for part in laser_cut_parts:
            for _ in range(int(part.inventory_data.quantity)):
                new_part = LaserCutPart(part.to_dict(), self.laser_cut_inventory)
                new_part.inventory_data.quantity = 1
                assembly.add_laser_cut_part(new_part)

    def add_job(self, job: Job) -> Job:
        new_job = self.deep_split_job_copy(job)
        self.jobs.append(new_job)
        return new_job

    def remove_job(self, job: Job):
        self.jobs.remove(job)

    def get_all_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        for job in self.jobs:
            assemblies.extend(job.get_all_assemblies())
        return assemblies

    def get_filtered_assemblies(self, job: Job) -> list[Assembly]:
        assemblies: list[Assembly] = []
        for assembly in job.get_all_assemblies():
            # For assemblies marked as not part of process, show them when their parts are complete
            # until their parent assembly is finished
            # if assembly.not_part_of_process:
            #     if (
            #         not assembly.all_laser_cut_parts_complete()
            #         or not assembly.all_sub_assemblies_complete()
            #     ):
            #         continue
            # Get parent assembly and check if it's finished
            # parent = assembly.parent_assembly
            # if parent and parent.is_assembly_finished():
            #     continue
            # else:
            # Normal assembly filtering
            # if assembly.is_assembly_finished():
            #     continue
            # if not assembly.all_laser_cut_parts_complete():
            #     continue
            # if not assembly.all_sub_assemblies_complete():
            #     continue
            # if current_tag := assembly.get_current_tag():
            #     if current_tag.name != self.workspace_filter.current_tag:
            #         continue

            if any(self.workspace_filter.paint_filter.values()):
                paints = assembly.get_all_paints()
                if not any(self.workspace_filter.paint_filter.get(paint, False) for paint in paints.split()):
                    continue

            search_text = self.workspace_filter.search_text.lower()
            search_queries = [query.strip() for query in search_text.split(",")] if search_text else []

            if search_queries:
                name_match = any(query in assembly.name.lower() for query in search_queries)
                paint_match = any(query in assembly.get_all_paints().lower() for query in search_queries)

                if not (name_match or paint_match):
                    continue

            assemblies.append(assembly)
        return self.sort_assemblies(assemblies)

    def sort_assemblies(self, assemblies: list[Assembly]) -> list[Assembly]:
        if not self.workspace_filter.sorting_method or self.workspace_filter.sorting_method in [SortingMethod.LARGE_TO_SMALL, SortingMethod.SMALL_TO_LARGE]:
            return assemblies

        if self.workspace_filter.sorting_method == SortingMethod.A_TO_Z:
            assemblies.sort(key=lambda assembly: assembly.name)
        elif self.workspace_filter.sorting_method == SortingMethod.Z_TO_A:
            assemblies.sort(key=lambda assembly: assembly.name, reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.MOST_TO_LEAST:
            assemblies.sort(key=lambda assembly: assembly.quantity, reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.LEAST_TO_MOST:
            assemblies.sort(key=lambda assembly: assembly.quantity)
        elif self.workspace_filter.sorting_method == SortingMethod.HEAVY_TO_LIGHT:
            assemblies.sort(key=lambda assembly: assembly.get_weight(), reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.LIGHT_TO_HEAVY:
            assemblies.sort(key=lambda assembly: assembly.get_weight())

        return assemblies

    def get_all_laser_cut_parts_with_similar_tag(self, query: str) -> list[LaserCutPart]:
        laser_cut_parts: list[LaserCutPart] = []
        for job in self.jobs:
            for laser_cut_part in job.get_all_laser_cut_parts():
                if not (current_tag := laser_cut_part.get_current_tag()):
                    continue
                if query.lower() in current_tag.name.lower():
                    laser_cut_parts.append(laser_cut_part)
        return laser_cut_parts

    def is_within_date_range(self, laser_cut_part: LaserCutPart, job: Job) -> bool:
        if not (self.workspace_filter.enable_date_range and self.workspace_filter.date_range):
            return True

        filter_start = self.workspace_filter.date_range[0].toPyDate() if self.workspace_filter.date_range[0] else None
        filter_end = self.workspace_filter.date_range[1].toPyDate() if self.workspace_filter.date_range[1] else None

        tag = laser_cut_part.get_current_tag()
        if not tag:
            return False

        tag_data = job.flowtag_timeline.tags_data.get(tag)
        if not tag_data:
            return False

        def parse_date(value: str):
            try:
                return datetime.strptime(value, "%Y-%m-%d %I:%M %p").date()
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%d").date()

        tag_start = parse_date(tag_data["starting_date"])
        tag_end = parse_date(tag_data["ending_date"])

        if filter_start and not filter_end:
            return tag_start <= filter_start <= tag_end
        elif filter_start and filter_end:
            return not (tag_end < filter_start or tag_start > filter_end)
        return True

    def is_material_match(self, part: LaserCutPart) -> bool:
        if not any(self.workspace_filter.material_filter.values()):
            return True
        return self.workspace_filter.material_filter.get(part.meta_data.material, False)

    def is_thickness_match(self, part: LaserCutPart) -> bool:
        if not any(self.workspace_filter.thickness_filter.values()):
            return True
        return self.workspace_filter.thickness_filter.get(part.meta_data.gauge, False)

    def is_paint_match(self, part: LaserCutPart) -> bool:
        if not any(self.workspace_filter.paint_filter.values()):
            return True
        return any(self.workspace_filter.paint_filter.get(p, False) for p in part.get_all_paints().split())

    def is_text_search_match(self, part: LaserCutPart) -> bool:
        text = self.workspace_filter.search_text.lower().strip()
        if not text:
            return True

        queries = [q.strip() for q in text.split(",")]
        name = part.name.lower()
        material = f"{part.meta_data.gauge} {part.meta_data.material}".lower()
        paints = part.get_all_paints().lower()

        return any(q in name or q in material or q in paints for q in queries)

    def get_filtered_laser_cut_parts(self, job: Job) -> list[LaserCutPart]:
        parts: list[LaserCutPart] = []

        for part in job.get_all_laser_cut_parts():
            if not self.is_within_date_range(part, job):
                continue
            if not self.is_material_match(part):
                continue
            if not self.is_thickness_match(part):
                continue
            if not self.is_paint_match(part):
                continue
            if not self.is_text_search_match(part):
                continue

            parts.append(part)

        return parts

    def is_part_group_hidden(self, group: WorkspaceLaserCutPartGroup, job: Job) -> bool:
        for part in group.laser_cut_parts:
            if (
                self.is_within_date_range(part, job)
                and self.is_material_match(part)
                and self.is_thickness_match(part)
                and self.is_paint_match(part)
                and self.is_text_search_match(part)
            ):
                return False  # At least one part is visible — group should be shown

        return True  # All parts failed filters — group should be hidden

    def sort_grouped_laser_cut_parts(self, grouped_laser_cut_parts: list[WorkspaceLaserCutPartGroup]) -> list[WorkspaceLaserCutPartGroup]:
        if not self.workspace_filter.sorting_method:
            return grouped_laser_cut_parts

        if self.workspace_filter.sorting_method == SortingMethod.A_TO_Z:
            grouped_laser_cut_parts.sort(key=lambda group: group.base_part.name)
        elif self.workspace_filter.sorting_method == SortingMethod.Z_TO_A:
            grouped_laser_cut_parts.sort(key=lambda group: group.base_part.name, reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.PROCESS:
            grouped_laser_cut_parts.sort(key=lambda group: group.get_process_status())
        elif self.workspace_filter.sorting_method == SortingMethod.MOST_TO_LEAST:
            grouped_laser_cut_parts.sort(key=lambda group: group.get_count(), reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.LEAST_TO_MOST:
            grouped_laser_cut_parts.sort(key=lambda group: group.get_count())
        elif self.workspace_filter.sorting_method == SortingMethod.HEAVY_TO_LIGHT:
            grouped_laser_cut_parts.sort(key=lambda group: group.base_part.meta_data.weight, reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.LIGHT_TO_HEAVY:
            grouped_laser_cut_parts.sort(key=lambda group: group.base_part.meta_data.weight)
        elif self.workspace_filter.sorting_method == SortingMethod.LARGE_TO_SMALL:
            grouped_laser_cut_parts.sort(key=lambda group: group.base_part.meta_data.surface_area, reverse=True)
        elif self.workspace_filter.sorting_method == SortingMethod.SMALL_TO_LARGE:
            grouped_laser_cut_parts.sort(key=lambda group: group.base_part.meta_data.surface_area)

        return grouped_laser_cut_parts

    def get_grouped_assemblies(self, assemblies: list[Assembly]) -> list[WorkspaceAssemblyGroup]:
        grouped_assemblies: list[WorkspaceAssemblyGroup] = []
        parts_group: dict[str, WorkspaceAssemblyGroup] = {}

        def create_part_group(base_assembly: Assembly):
            group = WorkspaceAssemblyGroup()
            group.add_assembly(base_assembly)
            grouped_assemblies.append(group)
            parts_group[base_assembly.name] = group

        for assembly in assemblies:
            if group := parts_group.get(assembly.name):
                group.add_assembly(assembly)
            else:
                create_part_group(assembly)

        return grouped_assemblies

    def get_grouped_laser_cut_parts(self, laser_cut_parts: list[LaserCutPart]) -> list[WorkspaceLaserCutPartGroup]:
        grouped_laser_cut_parts: list[WorkspaceLaserCutPartGroup] = []
        parts_group: dict[str, WorkspaceLaserCutPartGroup] = {}

        def create_part_group(base_part: LaserCutPart):
            group = WorkspaceLaserCutPartGroup()
            group.add_laser_cut_part(base_part)
            grouped_laser_cut_parts.append(group)
            parts_group[(base_part.name, base_part.recut, base_part.recoat)] = group

        for laser_cut_part in laser_cut_parts:
            group_key = (
                laser_cut_part.name,
                laser_cut_part.recut,
                laser_cut_part.recoat,
            )
            if group := parts_group.get(group_key):
                group.add_laser_cut_part(laser_cut_part)
            else:
                create_part_group(laser_cut_part)

        return self.sort_grouped_laser_cut_parts(grouped_laser_cut_parts)

    def to_dict(self) -> dict[str, Union[dict[str, object], list[dict[str, object]]]]:
        return {"jobs": [job.to_dict() for job in self.jobs]}

    def __create_file(self):
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.filename}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "w", encoding="utf-8") as json_file:
                json_file.write("{}")

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: dict[str, list[dict[str, object]]] = msgspec.json.decode(file.read())
        except msgspec.DecodeError:
            return

        self.jobs.clear()

        jobs = data.get("jobs", [])

        for job_data in jobs:
            job = Job(job_data, self.job_manager)
            self.jobs.append(job)
