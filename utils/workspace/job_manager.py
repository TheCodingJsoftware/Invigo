import glob
import os

import ujson as json

from utils.components_inventory.components_inventory import ComponentsInventory
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.paint_inventory.paint_inventory import PaintInventory
from utils.sheet_settings import SheetSettings
from utils.workspace.job import Job
from utils.workspace.workspace_settings import WorkspaceSettings


class JobManager:
    def __init__(self, parent) -> None:
        self.parent = parent

        self.jobs: list[Job] = []

        self.file_name: str = "jobs"
        self.FOLDER_LOCATION: str = f"{os.getcwd()}\\data"
        self.JOBS_FOLDER_LOCATION: str = f"{self.FOLDER_LOCATION}\\jobs"

        self.sheet_settings: SheetSettings = self.parent.sheet_settings
        self.workspace_settings: WorkspaceSettings = self.parent.workspace_settings
        self.components_inventory: ComponentsInventory = self.parent.components_inventory
        self.laser_cut_inventory: LaserCutInventory = self.parent.laser_cut_inventory
        self.paint_inventory: PaintInventory = self.parent.paint_inventory

        # self.load_all_jobs()

    def add_job(self, job: Job):
        self.jobs.append(job)

    def remove_job(self, job: Job):
        self.jobs.remove(job)

    def get_job(self, job_name: str) -> Job:
        return next((job for job in self.jobs if job.name == job_name), None)

    def save_job(self, job: Job):
        with open(f"{self.JOBS_FOLDER_LOCATION}\\{job.name}.job", "w", encoding="utf-8") as json_file:
            json.dump(job.to_dict(), json_file, ensure_ascii=False, indent=4)

    def load_job(self, job_name: str) -> Job:
        job_name = job_name.replace(".json", "").replace(".job", "")
        with open(f"{self.JOBS_FOLDER_LOCATION}\\{job_name}.job", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        return Job(job_name, data, self)

    def get_all_jobs(self) -> list[str]:
        files = glob.glob(os.path.join(self.JOBS_FOLDER_LOCATION, "*.job"))
        return [os.path.basename(file) for file in files]

    def load_all_jobs(self):
        self.jobs.clear()
        for job_name in self.get_all_jobs():
            self.jobs.append(self.load_job(job_name))

    def sync_changes(self):
        self.parent.sync_changes()
