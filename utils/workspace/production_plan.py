from utils.workspace.workspace_settings import WorkspaceSettings
from utils.workspace.job_manager import JobManager
from utils.workspace.workspace import Workspace

class ProductionPlan(Workspace):
    def __init__(self, workspace_settings: WorkspaceSettings, job_manager: JobManager, filename: str = "production_plan"):
        super().__init__(workspace_settings, job_manager, filename)