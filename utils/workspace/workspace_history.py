import os
from datetime import datetime

import msgspec

from config.environments import Environment
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager


class WorkspaceHistory:
    def __init__(self, job_manager: JobManager):
        self.jobs: list[Job] = []

        self.filename: str = f"workspace_{datetime.now().year}_history"
        self.FOLDER_LOCATION: str = f"{Environment.DATA_PATH}/data"
        self.job_manager = job_manager

        self.__create_file()
        self.load_data()

    def add_job(self, job: Job):
        new_job = Job(job.to_dict(), self.job_manager)
        self.jobs.append(new_job)

    def remove_job(self, job: Job):
        self.jobs.remove(job)

    def to_list(self) -> list[object]:
        return [job.to_dict() for job in self.jobs]

    def __create_file(self):
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.filename}.json"):
            with open(
                f"{self.FOLDER_LOCATION}/{self.filename}.json", "w", encoding="utf-8"
            ) as json_file:
                json_file.write("[]")

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_list()))

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: list[dict[str, object]] = msgspec.json.decode(file.read())
        except msgspec.DecodeError:
            return

        self.jobs.clear()

        for job_data in data:
            job = Job(job_data, self.job_manager)
            self.jobs.append(job)
