from typing import override

from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_settings import WorkspaceSettings


class ProductionPlan(Workspace):
    def __init__(
        self,
        workspace_settings: WorkspaceSettings,
        job_manager: JobManager,
        filename: str = "production_plan",
    ):
        super().__init__(workspace_settings, job_manager, filename)

    @override
    def add_job(self, job: Job) -> Job:
        new_job = Job(job.to_dict(), self.job_manager)
        new_job.flowtag_timeline = job.flowtag_timeline
        new_job.load_settings(job.to_dict())
        self.jobs.append(new_job)
        return new_job
