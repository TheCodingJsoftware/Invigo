import os

import ujson as json

from utils.workspace.job import Job
from utils.workspace.workspace_settings import WorkspaceSettings


class Workspace:
    def __init__(self, file_name: str) -> None:
        self.jobs: list[Job] = []

        self.file_name: str = file_name
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"

        self.workspace_settings = WorkspaceSettings()

        self.__create_file()
        self.load_data()

    def add_job(self, job: Job):
        self.jobs.append(job)

    def remove_job(self, job: Job):
        self.jobs.remove(job)

    def get_job(self, job_name: str) -> Job:
        return next((job for job in self.jobs if job.name == job_name), None)

    def to_dict(self) -> dict:
        return {job.name: job.to_dict() for job in self.jobs}

    def __create_file(self) -> None:
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
                json_file.write("{}")

    def save(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.to_dict(), json_file, ensure_ascii=False)

    def load_data(self) -> None:
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except json.JSONDecodeError:
            return

        self.jobs.clear()

        for job_name, job_data in data.items():
            job = Job(job_name, job_data)
            self.jobs.append(job)
